import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import shutil
import subprocess
import logging # Added for logger.setLevel

# Adjust path to import tools from DotNetUpgradeAgents package
# This assumes 'tests' is a top-level directory and DotNetUpgradeAgents is a sibling.
import sys
# Add the parent directory of 'DotNetUpgradeAgents' to sys.path
# This allows 'from DotNetUpgradeAgents.tools import ...' to work
# Assumes script is run from repository root or 'tests' dir.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DotNetUpgradeAgents.tools import TFSTool, GitInitTool, VBToCSTool, ReportTool
from DotNetUpgradeAgents.core_components import LLMApiClient, HumanFeedback, logger

# Disable most logging during tests for cleaner output, can be enabled for debugging.
logger.setLevel(logging.WARNING)


class TestAgentTools(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for tools to operate on
        self.test_dir = "temp_test_tools_dir"
        os.makedirs(self.test_dir, exist_ok=True)

        # Path for TFSTool destination
        self.tfs_checkout_path = os.path.join(self.test_dir, "tfs_code")
        os.makedirs(self.tfs_checkout_path, exist_ok=True)

        # Path for GitInitTool
        self.git_repo_path = os.path.join(self.test_dir, "git_project")
        os.makedirs(self.git_repo_path, exist_ok=True)
        with open(os.path.join(self.git_repo_path, "dummy.txt"), "w") as f:
            f.write("hello")

    def tearDown(self):
        # Remove the temporary directory after tests
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('DotNetUpgradeAgents.tools.subprocess.run')
    @patch('DotNetUpgradeAgents.tools.os.makedirs')
    def test_tfs_tool_success(self, mock_makedirs, mock_subprocess_run):
        # Configure subprocess.run mock for TFSTool if it were real
        # For the current simulation, it just writes a file, so we test that.
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Simulated TFS output", stderr="")

        tfs_tool = TFSTool()
        result = tfs_tool._run(tfs_repo_url="tfs://fake_url", destination_path=self.tfs_checkout_path)

        self.assertTrue("Successfully simulated retrieving code" in result)
        # Check if the dummy file was created by the simulation
        self.assertTrue(os.path.exists(os.path.join(self.tfs_checkout_path, "retrieved_from_tfs.txt")))
        mock_makedirs.assert_called_with(self.tfs_checkout_path, exist_ok=True)


    @patch('DotNetUpgradeAgents.tools.subprocess.run')
    def test_git_init_tool_success(self, mock_subprocess_run):
        # Configure subprocess.run mock for GitInitTool
        # Simulate a sequence of git commands: rev-parse (not a repo), init, add, commit
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="Not a git repository"), # rev-parse
            MagicMock(returncode=0, stdout="Git init success", stderr=""),     # git init
            MagicMock(returncode=0, stdout="Git add success", stderr=""),       # git add .
            MagicMock(returncode=0, stdout="Git commit success", stderr=""),    # git commit
        ]

        git_tool = GitInitTool()
        result = git_tool._run(directory_path=self.git_repo_path)

        self.assertTrue("Successfully initialized Git repository" in result)
        self.assertEqual(mock_subprocess_run.call_count, 4)
        # Check calls (example for git init)
        self.assertEqual(mock_subprocess_run.call_args_list[1][0][0][1], 'init')


    @patch('DotNetUpgradeAgents.tools.subprocess.run')
    def test_git_init_tool_already_git_repo(self, mock_subprocess_run):
        # Simulate 'git rev-parse --is-inside-work-tree' returning true
        mock_subprocess_run.return_value = MagicMock(stdout='true\n') # Git typically adds a newline

        git_tool = GitInitTool()
        result = git_tool._run(directory_path=self.git_repo_path)

        self.assertIn("already a Git repository", result)
        mock_subprocess_run.assert_called_once_with(
            ['git', '-C', self.git_repo_path, 'rev-parse', '--is-inside-work-tree'],
            capture_output=True, text=True
        )

    @patch('DotNetUpgradeAgents.tools.LLMApiClient.generate_code')
    @patch('DotNetUpgradeAgents.tools.open', new_callable=mock_open, read_data="Public Class Test\nEnd Class")
    def test_vb_to_cs_tool_success(self, mock_file_open, mock_generate_code):
        vb_file = os.path.join(self.test_dir, "test.vb")
        # mock_open doesn't create the file, so we don't need to write it for this test.
        # It will mock the read.

        mock_generate_code.return_value = "public class Test { }"

        # Instantiate LLMApiClient mock explicitly if VBToCSTool expects one,
        # or ensure the default instantiation within VBToCSTool uses the patched one.
        # The current VBToCSTool creates its own if not provided.
        # So, patching at DotNetUpgradeAgents.tools.LLMApiClient will affect the default one.

        vb_tool = VBToCSTool() # Uses the patched LLMApiClient
        result = vb_tool._run(vb_file_path=vb_file)

        self.assertTrue("Successfully converted" in result)
        mock_file_open.assert_any_call(vb_file, 'r', encoding='utf-8') # Check read
        cs_file_path = vb_file.replace(".vb", ".cs")
        mock_file_open.assert_any_call(cs_file_path, 'w', encoding='utf-8') # Check write
        # Check if write was called with the correct C# code
        # mock_file_open().write.assert_called_once_with("public class Test { }") # This is more complex with multiple open calls

        # A simpler check for the write content with mock_open:
        handle = mock_file_open()
        # Find the call that wrote the C# code
        write_call_args = None
        for call in handle.write.call_args_list:
            if call[0][0] == "public class Test { }":
                write_call_args = call
                break
        self.assertIsNotNone(write_call_args, "LLM generated C# code was not written to file.")


    @patch('DotNetUpgradeAgents.tools.open', new_callable=mock_open)
    def test_report_tool_json(self, mock_file_open):
        report_tool = ReportTool()
        details = {"step1": "done", "errors": []}
        result = report_tool._run(upgrade_details=details, report_format="json")

        self.assertTrue("Successfully generated JSON report" in result)
        report_file_path = result.split("at: ")[-1]
        self.assertTrue(report_file_path.endswith(".json"))

        # Check that open was called with the correct path and mode
        mock_file_open.assert_called_once_with(report_file_path, 'w', encoding='utf-8')
        # Check that json.dump (or similar for text) was called via the handle
        # This requires deeper mocking of json.dump or checking the string written
        handle = mock_file_open()
        # Example: check if write was called (json.dump calls write)
        handle.write.assert_called()
        # More specific: check content written (might need to capture args to write)
        # args, _ = handle.write.call_args
        # written_content = args[0]
        # self.assertIn(""step1": "done"", written_content)


if __name__ == '__main__':
    unittest.main()
