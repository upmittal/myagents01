import os
import subprocess
import logging
import json
from datetime import datetime
from typing import Any, Optional
from crewai.tools import BaseTool

# Assuming core_components.py is in the same directory or accessible in PYTHONPATH
from .core_components import log_error, LLMApiClient, HumanFeedback, logger

class TFSTool(BaseTool):
    name: str = "TFSTool"
    description: str = "Retrieves code from a Team Foundation Server (TFS) repository. Input should be the TFS repository URL and the destination path."

    @log_error
    def _run(self, tfs_repo_url: str, destination_path: str) -> str:
        '''
        Simulates retrieving code from TFS.
        In a real scenario, this would use 'tf.exe' or TFS APIs.
        '''
        logger.info(f"Attempting to retrieve code from TFS repo: {tfs_repo_url} to {destination_path}")

        # Create destination directory if it doesn't exist
        os.makedirs(destination_path, exist_ok=True)

        # Simulate TFS get command
        try:
            # Placeholder: In a real implementation, you would use subprocess to call 'tf get'
            # For example:
            # process = subprocess.run(['tf', 'get', tfs_repo_url, '/destination:' + destination_path], check=True, capture_output=True, text=True)
            # logger.info(f"TFS get command output: {process.stdout}")

            # Simulate success by creating a dummy file
            dummy_file_path = os.path.join(destination_path, "retrieved_from_tfs.txt")
            with open(dummy_file_path, "w") as f:
                f.write(f"Simulated code retrieved from {tfs_repo_url} at {datetime.now()}")

            result_message = f"Successfully simulated retrieving code from {tfs_repo_url} to {destination_path}. Dummy file created: {dummy_file_path}"
            logger.info(result_message)
            return result_message
        except subprocess.CalledProcessError as e:
            error_message = f"TFSTool: Failed to execute TFS command. Error: {e.stderr}"
            logger.error(error_message)
            # Optionally, ask for human feedback on failure
            # action = HumanFeedback.get_feedback(f"TFS operation failed: {e.stderr}. Options:", ["Retry", "Skip", "Manual Intervention"])
            # if action == "Retry": return self._run(tfs_repo_url, destination_path)
            # if action == "Skip": return "TFS operation skipped by user."
            return error_message
        except Exception as e:
            error_message = f"TFSTool: An unexpected error occurred: {e}"
            logger.error(error_message)
            return error_message

class GitInitTool(BaseTool):
    name: str = "GitInitTool"
    description: str = "Initializes a new Git repository in a specified directory, adds all files, and makes an initial commit. Input should be the directory path."

    @log_error
    def _run(self, directory_path: str) -> str:
        '''
        Initializes a Git repository, adds all files, and commits.
        '''
        logger.info(f"Initializing Git repository in {directory_path}")

        if not os.path.isdir(directory_path):
            error_message = f"GitInitTool: Directory not found: {directory_path}"
            logger.error(error_message)
            return error_message

        try:
            # Check if it's already a git repository
            is_git_repo_check = subprocess.run(['git', '-C', directory_path, 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True)
            if is_git_repo_check.stdout.strip() == 'true':
                message = f"GitInitTool: Directory {directory_path} is already a Git repository."
                logger.info(message)
                # Optionally, you could add logic to pull latest, or clean and re-init based on requirements.
                # For now, we just report and don't re-initialize.
                return message


            # Git init
            subprocess.run(['git', 'init'], cwd=directory_path, check=True, capture_output=True, text=True)
            logger.info(f"Git repository initialized in {directory_path}")

            # Git add .
            subprocess.run(['git', 'add', '.'], cwd=directory_path, check=True, capture_output=True, text=True)
            logger.info("Added all files to staging area.")

            # Git commit
            commit_message = "Initial commit by DotNetUpgradeAgents"
            subprocess.run(['git', 'commit', '-m', commit_message], cwd=directory_path, check=True, capture_output=True, text=True)
            logger.info(f"Initial commit made with message: '{commit_message}'")

            return f"Successfully initialized Git repository in {directory_path} and made initial commit."
        except subprocess.CalledProcessError as e:
            error_message = f"GitInitTool: Git command failed. Error: {e.stderr}"
            logger.error(error_message)
            # HumanFeedback could be integrated here too if needed
            return error_message
        except Exception as e:
            error_message = f"GitInitTool: An unexpected error occurred: {e}"
            logger.error(error_message)
            return error_message

class VBToCSTool(BaseTool):
    name: str = "VBToCSTool"
    description: str = "Converts VB.NET code to C# using an LLM. Input should be the path to a VB.NET file."
    llm_client: LLMApiClient #  = None

    def __init__(self, llm_client: LLMApiClient, **kwargs): #] = None
        super().__init__(**kwargs)
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = LLMApiClient() # Use default if not provided
        logger.info("VBToCSTool initialized.")

    @log_error
    def _run(self, vb_file_path: str) -> str:
        logger.info(f"Attempting to convert VB.NET file: {vb_file_path} to C#")

        if not os.path.isfile(vb_file_path):
            return f"VBToCSTool: VB.NET file not found: {vb_file_path}"

        try:
            with open(vb_file_path, 'r', encoding='utf-8') as f:
                vb_code = f.read()

            if not vb_code.strip():
                return f"VBToCSTool: VB.NET file is empty: {vb_file_path}"

            # Note: Prompt effectiveness can vary with the LLM. For smaller local models (e.g., via Ollama),
            # more explicit instructions or few-shot examples might improve conversion quality.
            # This prompt is a general starting point.
            prompt = f"Convert the following VB.NET code to C#: vb_file_path {vb_code}"
            cs_code = self.llm_client.generate_code(prompt)

            if cs_code.startswith("# ERROR:"):
                logger.error(f"VBToCSTool: LLM code generation failed for {vb_file_path}. LLM Client Response: {cs_code}")

                prompt_text = f"LLM failed to convert VB.NET file '{vb_file_path}'. Error: {cs_code}\nHow would you like to proceed?"
                options = ["Retry conversion", "Skip this file", "Mark for manual conversion"]
                choice = HumanFeedback.get_feedback(prompt_text, options)

                if choice == "Retry conversion":
                    logger.info(f"VBToCSTool: User chose to retry conversion for {vb_file_path}.")
                    return self._run(vb_file_path) # Recursive call to retry
                elif choice == "Skip this file":
                    logger.info(f"VBToCSTool: User chose to skip conversion for {vb_file_path}.")
                    return f"VBToCSTool: Conversion of {vb_file_path} skipped by user."
                elif choice == "Mark for manual conversion":
                    logger.warn(f"VBToCSTool: {vb_file_path} marked for manual conversion by user.")
                    return f"VBToCSTool: {vb_file_path} marked for manual conversion. Original error: {cs_code}"
                else: # Should not happen with given options
                    return f"VBToCSTool: Unexpected choice for {vb_file_path}. Error: {cs_code}"

            cs_file_path = vb_file_path.replace(".vb", ".cs").replace(".VB", ".cs") # Handle different extensions
            if cs_file_path == vb_file_path: # Avoid overwriting if extension didn't change
                cs_file_path += ".cs"

            with open(cs_file_path, 'w', encoding='utf-8') as f:
                f.write(cs_code)

            logger.info(f"Successfully converted {vb_file_path} to {cs_file_path}")
            return f"Successfully converted {vb_file_path} to {cs_file_path}. Output: {cs_code[:200]}..."

        except Exception as e:
            error_message = f"VBToCSTool: An unexpected error occurred during conversion of {vb_file_path}: {e}"
            logger.error(error_message)
            return error_message

class DependencyAnalyzerTool(BaseTool):
    name: str = "DependencyAnalyzerTool"
    description: str = "Analyzes .NET project dependencies from a .csproj file or a solution file. Identifies NuGet packages, custom libraries, and checks for specific namespaces like 'ITASCA'. Input should be the path to a .csproj or .sln file."

    @log_error
    def _run(self, project_or_solution_path: str) -> dict:
        logger.info(f"Analyzing dependencies for: {project_or_solution_path}")

        if not os.path.isfile(project_or_solution_path):
            return {"error": f"DependencyAnalyzerTool: File not found: {project_or_solution_path}"}

        dependencies = {
            "project_file": project_or_solution_path,
            "nuget_packages": [],
            "custom_libraries": [],
            "itasca_namespace_found": False,
            "itasca_action_taken": None,
            "analysis_errors": []
        }

        # This is a simplified simulation. Real analysis would involve parsing XML (.csproj)
        # or using 'dotnet list package' or MSBuild Structured Log Viewer.
        try:
            with open(project_or_solution_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simulate finding NuGet packages (looking for PackageReference)
            if "<PackageReference Include=" in content:
                # A more robust parser would be needed here. This is just a placeholder.
                import re
                package_matches = re.findall(r'<PackageReference Include="([^"]+)" Version="([^"]+)"', content)
                for pkg_name, pkg_version in package_matches:
                    dependencies["nuget_packages"].append({"name": pkg_name, "version": pkg_version})
                if not package_matches: # Fallback if regex finds nothing but tag exists
                    dependencies["nuget_packages"].append({"name": "SimulatedPackage", "version": "1.0.0"})


            # Simulate finding custom libraries (e.g., ProjectReference)
            if "<ProjectReference Include=" in content:
                dependencies["custom_libraries"].append({"name": "SimulatedCustomLib.csproj"})

            # Simulate checking for ITASCA namespace
            if "ITASCA" in content or "itasca" in content: # Case-insensitive check might be better
                dependencies["itasca_namespace_found"] = True
                logger.warning(f"ITASCA namespace potentially found in {project_or_solution_path}.")

                # Human feedback for ITASCA
                # This interaction should ideally be managed by the agent, not directly in the tool run,
                # but for now, we'll include the call here as per the plan.
                prompt = f"Namespace 'ITASCA' detected in {project_or_solution_path}. How should the upgrade proceed with this namespace?"
                options = ["Attempt to upgrade/replace automatically", "Keep as is (may cause issues)", "Flag for manual review and skip for now", "Halt process for immediate manual check"]
                action = HumanFeedback.get_feedback(prompt, options)
                dependencies["itasca_action_taken"] = action
                logger.info(f"Human feedback received for ITASCA namespace: {action}")
                if action == "Halt process for immediate manual check":
                    # This could raise a specific exception or return a special status
                    dependencies["analysis_errors"].append("Process halted by user for ITASCA namespace check.")
                    # raise Exception("Process halted by user for ITASCA namespace check.") # Or handle as per crew's flow

            logger.info(f"Dependency analysis complete for {project_or_solution_path}. Found: {len(dependencies['nuget_packages'])} NuGet packages, {len(dependencies['custom_libraries'])} custom libs. ITASCA found: {dependencies['itasca_namespace_found']}")
            return dependencies

        except Exception as e:
            error_message = f"DependencyAnalyzerTool: Error analyzing {project_or_solution_path}: {e}"
            logger.error(error_message)
            dependencies["analysis_errors"].append(error_message)
            return dependencies

class ProjectUpgradeTool(BaseTool):
    name: str = "ProjectUpgradeTool"
    description: str = "Upgrades a .csproj file to a target .NET Framework version using an LLM. Input should be the .csproj file path and the target framework (e.g., 'net48', 'net6.0')."
    llm_client: LLMApiClient #] = None

    def __init__(self, llm_client: LLMApiClient, **kwargs): #]  = None
        super().__init__(**kwargs)
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = LLMApiClient() # Use default if not provided
        logger.info("ProjectUpgradeTool initialized.")

    @log_error
    def _run(self, csproj_path: str, target_framework: str) -> str| Any:
        logger.info(f"Attempting to upgrade {csproj_path} to target framework: {target_framework}")

        if not os.path.isfile(csproj_path):
            return f"ProjectUpgradeTool: .csproj file not found: {csproj_path}"

        try:
            with open(csproj_path, 'r', encoding='utf-8') as f:
                original_csproj_content = f.read()

            if not original_csproj_content.strip():
                return f"ProjectUpgradeTool: .csproj file is empty: {csproj_path}"


            # Note: This is a detailed prompt. Ensure your chosen LLM (especially local models via Ollama)
            # can handle long contexts and complex instructions effectively.
            # The instruction "Only output the raw XML..." is crucial for this tool to work correctly.
            # If the LLM struggles, simplifying the request or breaking it down might be necessary.
            prompt = """
            Upgrade the following .NET .csproj content to target framework {target_framework}. Ensure all necessary changes for compatibility are made, including updating SDK style if appropriate, and framework-specific package versions if known. Only output the raw XML of the modified .csproj file.

                        Original .csproj content:
                        {original_csproj_content}
            """

            upgraded_csproj_content = self.llm_client.generate_code(prompt)

            if upgraded_csproj_content.startswith("# ERROR:"): # Check specifically for LLM client errors
                logger.error(f"ProjectUpgradeTool: LLM .csproj upgrade failed for {csproj_path}. LLM Client Response: {upgraded_csproj_content}") # Log full error

                prompt_text = f"LLM failed to upgrade .csproj file '{csproj_path}'. Error: {upgraded_csproj_content}\nHow would you like to proceed?"
                options = ["Retry upgrade", "Skip this project", "Mark for manual upgrade"]
                choice = HumanFeedback.get_feedback(prompt_text, options)

                if choice == "Retry upgrade":
                    logger.info(f"ProjectUpgradeTool: User chose to retry upgrade for {csproj_path}.")
                    return self._run(csproj_path, target_framework)
                elif choice == "Skip this project":
                    logger.info(f"ProjectUpgradeTool: User chose to skip upgrade for {csproj_path}.")
                    return f"ProjectUpgradeTool: Upgrade of {csproj_path} skipped by user."
                elif choice == "Mark for manual upgrade":
                    logger.warn(f"ProjectUpgradeTool: {csproj_path} marked for manual upgrade by user.")
                    return f"ProjectUpgradeTool: {csproj_path} marked for manual upgrade. Original error: {upgraded_csproj_content}"
            elif not upgraded_csproj_content.strip().startswith("<Project"): # Handle invalid XML that wasn't an LLM error
                logger.error(f"""ProjectUpgradeTool: LLM output for {csproj_path} was not valid XML: {upgraded_csproj_content[:200]}... Ensure the LLM is configured to output only raw XML for .csproj.""")
                return f"""ProjectUpgradeTool: Failed to upgrade {csproj_path} due to invalid XML response from LLM (but not an API error): {upgraded_csproj_content[:200]}..."""

            # It's good practice to backup the original file before overwriting
            backup_path = csproj_path + ".bak"
            logger.info(f"""Backing up original {csproj_path} to {backup_path}""")
            import shutil
            shutil.copy(csproj_path, backup_path)

            with open(csproj_path, 'w', encoding='utf-8') as f:
                f.write(upgraded_csproj_content)

            logger.info(f"Successfully upgraded {csproj_path} to {target_framework}. Backup created at {backup_path}")
            return f"""Successfully upgraded {csproj_path} to {target_framework}. Backup: {backup_path}. Upgraded content (first 200 chars): {upgraded_csproj_content[:200]}..."""

        except Exception as e:
            error_message = f"ProjectUpgradeTool: An unexpected error occurred during upgrade of {csproj_path}: {e}"
            logger.error(error_message)
            return error_message

class BuildTool(BaseTool):
    name: str = "BuildTool"
    description: str = "Builds a .NET project or solution using 'dotnet build'. If errors occur, it can optionally use an LLM to suggest fixes. Input is the path to the .csproj or .sln file."
    llm_client: LLMApiClient #= None

    def __init__(self, llm_client: LLMApiClient, **kwargs):
        super().__init__(**kwargs)
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = LLMApiClient() # Use default if not provided
        logger.info("BuildTool initialized.")

    @log_error
    def _run(self, project_or_solution_path: str) -> str | Any:
        logger.info(f"Attempting to build: {project_or_solution_path}")

        if not os.path.isfile(project_or_solution_path):
            return f"BuildTool: Project or solution file not found: {project_or_solution_path}"

        project_dir = os.path.dirname(project_or_solution_path) if os.path.isfile(project_or_solution_path) else project_or_solution_path


        try:
            # First attempt to build
            # Using -v q for quiet, -nologo. Adjust verbosity as needed.
            process = subprocess.run(
                ['dotnet', 'build', project_or_solution_path, '-nologo'],
                cwd=project_dir, # Run in the project's directory context
                capture_output=True,
                text=True,
                check=False # Do not throw exception on non-zero exit code initially
            )

            if process.returncode == 0:
                success_message = f"""BuildTool: Build successful for {project_or_solution_path}.
                                        Output:
                                        {process.stdout}"""
                logger.info(success_message)
                return success_message
            else:
                error_output = process.stderr if process.stderr else process.stdout
                logger.error(f"""BuildTool: Build failed for {project_or_solution_path}. Return code: {process.returncode}
                                    Errors:
                                    {error_output}""")

                # Ask user if they want to attempt LLM fix
                # In a real agent flow, this decision might be pre-configured or made by an agent
                choice = HumanFeedback.get_feedback(
                    f"""Build failed for {project_or_solution_path}. Do you want to attempt an LLM-based fix for the errors?""",
                    options=["Yes, attempt LLM fix", "No, log error and continue"]
                )

                if choice == "Yes, attempt LLM fix":
                    logger.info("Attempting to use LLM to find a fix for build errors.")
                    # This requires project context, so we might need to read file contents
                    # For simplicity, we just send the error log to LLM
                    # A more advanced implementation would send relevant code snippets.

                    # Try to find the relevant .cs or .vb files to provide context
                    # This is a very basic attempt, could be improved
                    code_context = ""
                    project_files_dir = os.path.dirname(project_or_solution_path)
                    for root, _, files in os.walk(project_files_dir):
                        for file_name in files:
                            if file_name.endswith((".cs", ".vb")): # Add other relevant extensions if needed
                                try:
                                    with open(os.path.join(root, file_name), 'r', encoding='utf-8') as f_code:
                                        code_context += f"\n--- Content of {file_name} ---\n{f_code.read(2000)}" # Read first 2000 chars
                                except Exception as e_read:
                                    logger.warning(f"Could not read file {file_name} for LLM context: {e_read}")
                        if len(code_context) > 8000: # Limit context size
                            break

                    # Note: Providing build errors and code context to an LLM for bug fixing is complex.
                    # The quality of the suggested fix will heavily depend on the LLM's coding and reasoning capabilities.
                    # For local models (Ollama), larger, more capable models are recommended for this task.
                    # The instruction "Output the suggested fix clearly" is important.
                    prompt = f"""The .NET build for project '{project_or_solution_path}' failed with the following errors:
                                {error_output}

                                Here is some code context from the project (first 2000 characters of .cs/.vb files):
                                {code_context}

                        Please provide a detailed explanation of the likely cause and a specific suggested code modification or .csproj file change to fix these errors. Focus on common issues related to framework upgrades or package incompatibilities. Output the suggested fix clearly."""

                    suggested_fix = self.llm_client.generate_code(prompt)

                    # logger.info(f"""LLM suggested fix:\n{suggested_fix}""") # Already logged by decorator

                    if suggested_fix.startswith("# ERROR:"):
                        logger.error(f"BuildTool: LLM failed to provide a fix suggestion for {project_or_solution_path}. LLM Client Error: {suggested_fix}")
                        prompt_text = f"LLM failed to provide a fix suggestion for build errors in '{project_or_solution_path}'. Error: {suggested_fix}\nHow would you like to proceed?"
                        options = ["Log build errors and continue (no fix)", "Retry getting LLM suggestion"]
                        llm_error_choice = HumanFeedback.get_feedback(prompt_text, options)

                        if llm_error_choice == "Retry getting LLM suggestion":
                            logger.info(f"BuildTool: User chose to retry getting LLM suggestion for {project_or_solution_path}.")
                            suggested_fix = self.llm_client.generate_code(prompt) # Retry the call
                            if suggested_fix.startswith("# ERROR:"):
                                 return f"BuildTool: Build failed. LLM also failed on retry to provide fix: {suggested_fix}"
                            # Fall through to normal suggestion handling if retry is successful
                        else: # Log build errors and continue
                            return f"BuildTool: Build failed for {project_or_solution_path}. LLM failed to provide fix: {suggested_fix}. Errors logged."

                    apply_choice = HumanFeedback.get_feedback(
                        f"LLM suggested the following fix for '{project_or_solution_path}'. Should the system attempt to apply it (simulated - this is risky)?\n\n{suggested_fix[:500]}...\n",
                        options=["Yes, attempt to apply (simulated)", "No, just log the suggestion"]
                    )

                    if apply_choice == "Yes, attempt to apply (simulated)":
                        # In a real scenario, applying fixes is highly complex and risky.
                        # It would involve parsing the LLM output, identifying file paths, and making precise code changes.
                        # This is a placeholder for that complex logic.
                        logger.warning("Simulating application of LLM fix. In a real system, this would be a complex operation.")
                        # Here you might try to re-run the build after a simulated fix or a simple file touch.
                        return f"""BuildTool: Build failed. LLM suggested a fix (simulated application):
                                {suggested_fix}"
                                    else:
                                        return f"BuildTool: Build failed. LLM suggested a fix (not applied):
                                {suggested_fix}"
                                    else:
                                        return f"BuildTool: Build failed for {project_or_solution_path}. No LLM fix attempted.
                                Errors:
                                    {error_output}"""

        except subprocess.TimeoutExpired:
            error_message = f"BuildTool: Build command timed out for {project_or_solution_path}."
            logger.error(error_message)
            return error_message
        except Exception as e:
            error_message = f"BuildTool: An unexpected error occurred during build of {project_or_solution_path}: {e}"
            logger.error(error_message)
            return error_message

class IISTool(BaseTool):
    name: str = "IISTool"
    description: str = "Simulates deployment of a .NET application to IIS. Input should be the path to the built application (e.g., a directory with binaries and web.config) and the IIS site name."

    @log_error
    def _run(self, application_path: str, iis_site_name: str) -> str:
        logger.info(f"Attempting to deploy application from {application_path} to IIS site: {iis_site_name}")

        if not os.path.isdir(application_path):
            return f"IISTool: Application path not found or not a directory: {application_path}"

        # This is a simulation. Real IIS deployment would involve:
        # - Using PowerShell cmdlets (e.g., New-Website, Set-ItemProperty)
        # - Or using MSDeploy.exe
        # - Or interacting with IIS Administration APIs.
        try:
            # Simulate checking if site exists or creating/updating it
            logger.info(f"Simulating check/creation of IIS site: {iis_site_name}")
            logger.info(f"Simulating configuring site physical path to: {application_path}")
            logger.info(f"Simulating setting application pool, bindings, etc.")

            # Create a dummy file in the app path to signify "deployment"
            deployed_marker_path = os.path.join(application_path, f"deployed_to_iis_{iis_site_name}.marker")
            with open(deployed_marker_path, "w", encoding='utf-8') as f:
                f.write(f"Simulated deployment to {iis_site_name} at {datetime.now()}")

            success_message = f"IISTool: Successfully simulated deployment of {application_path} to IIS site '{iis_site_name}'. Marker file created: {deployed_marker_path}"
            logger.info(success_message)
            return success_message

        except Exception as e:
            error_message = f"IISTool: An unexpected error occurred during simulated IIS deployment: {e}"
            logger.error(error_message)
            # HumanFeedback could be used here for retry/skip logic
            return error_message

class NeoLoadTool(BaseTool):
    name: str = "NeoLoadTool"
    description: str = "Simulates running a NeoLoad test. Input should be the path to the NeoLoad project file or a test scenario ID, and number of users."

    @log_error
    def _run(self, neoload_project_or_id: str, user_count: int = 1) -> str:
        logger.info(f"Attempting to run NeoLoad test for: {neoload_project_or_id} with {user_count} user(s)")

        # This is a simulation. Real NeoLoad execution would involve:
        # - Using NeoLoad Command Line Interface (CLI)
        # - Or using NeoLoad APIs.
        try:
            # Example CLI command (illustrative):
            # cmd = ['NeoLoadCmd', '-project', neoload_project_or_id, '-scenario', 'YourScenarioName', '-users', str(user_count), '-report', 'report.xml']
            # process = subprocess.run(cmd, check=True, capture_output=True, text=True)
            # logger.info(f"NeoLoad command output: {process.stdout}")

            # Simulate test execution
            logger.info(f"Simulating NeoLoad test execution for {neoload_project_or_id}...")
            import time
            time.sleep(2) # Simulate test duration

            report_summary = {
                "project": neoload_project_or_id,
                "users": user_count,
                "status": "Success (Simulated)",
                "avg_response_time_ms": 120,
                "error_rate_percent": 0
            }
            logger.info(f"NeoLoad test simulation complete. Summary: {report_summary}")

            return f"NeoLoadTool: Successfully simulated NeoLoad test for '{neoload_project_or_id}'. Test Summary: {report_summary}"

        except subprocess.CalledProcessError as e:
            error_message = f"NeoLoadTool: NeoLoad command failed. Error: {e.stderr}"
            logger.error(error_message)
            return error_message
        except Exception as e:
            error_message = f"NeoLoadTool: An unexpected error occurred during NeoLoad test simulation: {e}"
            logger.error(error_message)
            return error_message

class ReportTool(BaseTool):
    name: str = "ReportTool"
    description: str = "Generates an upgrade report from collected details. Input should be a dictionary of details."

    @log_error
    def _run(self, upgrade_details: dict, report_format: str = "json") -> str | Any:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file_name = f"upgrade_report_{timestamp_str}.{report_format.lower()}"
        report_path = os.path.join(os.getcwd(), report_file_name) # Save in current working directory or specify a path

        logger.info(f"Generating upgrade report. Details: {json.dumps(upgrade_details, indent=2, default=str)}")

        try:
            report_content = {
                "report_generated_at": datetime.now().isoformat(),
                "upgrade_process_summary": "Details of the .NET upgrade process.",
                "details": upgrade_details
            }

            if report_format.lower() == "json":
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report_content, f, indent=4, default=str) # default=str for non-serializable like datetime
            elif report_format.lower() == "txt":
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(f"""Upgrade Report - {report_content['report_generated_at']}""")
                    f.write("""=" * 30 + """)
                    f.write(f"Summary: {report_content['upgrade_process_summary']}")
                    for key, value in report_content['details'].items():
                        f.write(f"{key.replace('_', ' ').title()}: {json.dumps(value, indent=2, default=str)}")
            else:
                return f"ReportTool: Unsupported report format '{report_format}'. Supported formats: json, txt."

            logger.info(f"Successfully generated {report_format.upper()} report at: {report_path}")
            return f"ReportTool: Successfully generated {report_format.upper()} report at: {report_path}"

        except Exception as e:
            error_message = f"ReportTool: An unexpected error occurred during report generation: {e}"
            logger.error(error_message)
            return error_message

if __name__ == '__main__':
    logger.info("Testing agent tools...")

    # --- Setup Test Environment ---
    test_root_dir = "temp_dot_net_upgrade_test"
    if os.path.exists(test_root_dir):
        import shutil
        logger.info(f"Removing existing test directory: {test_root_dir}")
        shutil.rmtree(test_root_dir)
    os.makedirs(test_root_dir, exist_ok=True)
    logger.info(f"Test directory created: {test_root_dir}")

    test_dir_tfs = os.path.join(test_root_dir, "tfs_retrieval")
    test_dir_project = os.path.join(test_root_dir, "sample_net_project")
    test_dir_app_build = os.path.join(test_dir_project, "bin", "Release", "net6.0") # Simulated build output path
    os.makedirs(test_dir_tfs, exist_ok=True)
    os.makedirs(test_dir_project, exist_ok=True)
    os.makedirs(test_dir_app_build, exist_ok=True) # Create simulated build output directory

    # Create dummy files
    vb_file_path = os.path.join(test_dir_project, "Calculator.vb")
    with open(vb_file_path, "w", encoding='utf-8') as f:
        f.write("Public Class Calculator\nEnd Class")

    initial_csproj_content = """
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net472</TargetFramework></PropertyGroup>
  <ItemGroup><PackageReference Include="Newtonsoft.Json" Version="12.0.3" /><PackageReference Include="ITASCA.Core" Version="1.1.0" /></ItemGroup>
</Project>"""
    csproj_file_path = os.path.join(test_dir_project, "MyApp.csproj")
    with open(csproj_file_path, "w", encoding='utf-8') as f:
        f.write(initial_csproj_content)

    program_cs_content = "namespace MyApp { class Program { static void Main(string[] args) { System.Console.WriteLine(\"Hello World!\"); } } }"
    program_cs_path = os.path.join(test_dir_project, "Program.cs")
    with open(program_cs_path, "w", encoding='utf-8') as f:
        f.write(program_cs_content)

    # Dummy build output file
    with open(os.path.join(test_dir_app_build, "MyApp.exe"), "w", encoding='utf-8') as f:
        f.write("simulated exe")
    with open(os.path.join(test_dir_app_build, "web.config"), "w", encoding='utf-8') as f:
        f.write("<configuration></configuration>")


    logger.info(f"Test files created in {test_dir_project} and {test_dir_app_build}")

    # --- Initialize Shared Components ---
    llm_client_instance = LLMApiClient()

    # --- Test TFSTool ---
    tfs_tool = TFSTool()
    print(f"TFSTool Result: {tfs_tool._run(tfs_repo_url='tfs://your_server/your_project', destination_path=test_dir_tfs)}")

    # --- Test GitInitTool ---
    git_tool = GitInitTool()
    print(f"GitInitTool Result: {git_tool._run(directory_path=test_dir_project)}")
    print(f"GitInitTool Rerun Result: {git_tool._run(directory_path=test_dir_project)}")

    # --- Test VBToCSTool ---
    vb_tool = VBToCSTool(llm_client=llm_client_instance)
    print(f"VBToCSTool Result: {vb_tool._run(vb_file_path=vb_file_path)}")
    if os.path.exists(vb_file_path.replace('.vb','.cs')): print("VBToCSTool: .cs file created.")
    else: print("VBToCSTool: .cs file NOT created.")

    # --- Test DependencyAnalyzerTool ---
    dep_analyzer_tool = DependencyAnalyzerTool()
    print("\nTesting DependencyAnalyzerTool. If ITASCA prompt appears, select an option...")
    dep_analysis_result = dep_analyzer_tool._run(project_or_solution_path=csproj_file_path)
    print(f"DependencyAnalyzerTool Result: {json.dumps(dep_analysis_result, indent=2)}")

    # --- Test ProjectUpgradeTool ---
    print("\nTesting ProjectUpgradeTool...")
    csproj_for_upgrade_path = os.path.join(test_dir_project, "MyAppToUpgrade.csproj")
    import shutil
    shutil.copy(csproj_file_path, csproj_for_upgrade_path)
    upgrade_tool = ProjectUpgradeTool(llm_client=llm_client_instance)
    target_framework_version = "net6.0"
    upgrade_result = upgrade_tool._run(csproj_path=csproj_for_upgrade_path, target_framework=target_framework_version)
    print(f"ProjectUpgradeTool Result: {upgrade_result}")

    # --- Test BuildTool ---
    print("\nTesting BuildTool. This may require .NET SDK. Prompts may appear if build fails...")
    build_tool = BuildTool(llm_client=llm_client_instance)
    build_result_original = build_tool._run(project_or_solution_path=csproj_file_path)
    print(f"BuildTool Result (Original): {build_result_original}")
    if os.path.exists(csproj_for_upgrade_path) and "Successfully upgraded" in upgrade_result:
        print(f"\nAttempting to build the LLM-upgraded project: {csproj_for_upgrade_path}")
        build_result_upgraded = build_tool._run(project_or_solution_path=csproj_for_upgrade_path)
        print(f"BuildTool Result (Upgraded to {target_framework_version}): {build_result_upgraded}")

    # --- Test IISTool ---
    print("\nTesting IISTool...")
    iis_tool = IISTool()
    # Assuming the build output path is where the application to be deployed resides
    iis_deployment_result = iis_tool._run(application_path=test_dir_app_build, iis_site_name="TestUpgradeSite")
    print(f"IISTool Result: {iis_deployment_result}")
    if os.path.exists(os.path.join(test_dir_app_build, "deployed_to_iis_TestUpgradeSite.marker")):
        print("IISTool: Deployment marker file created.")

    # --- Test NeoLoadTool ---
    print("\nTesting NeoLoadTool...")
    neoload_tool = NeoLoadTool()
    neoload_result = neoload_tool._run(neoload_project_or_id="UpgradeTestScenario.nlp", user_count=5)
    print(f"NeoLoadTool Result: {neoload_result}")

    # --- Test ReportTool ---
    print("\nTesting ReportTool...")
    report_tool = ReportTool()
    collected_data_for_report = {
        "tfs_retrieval": tfs_tool._run(tfs_repo_url='tfs://your_server/your_project', destination_path=test_dir_tfs),
        "git_initialization": git_tool._run(directory_path=test_dir_project),
        "vb_conversion": vb_tool._run(vb_file_path=vb_file_path),
        "dependency_analysis": dep_analysis_result, # from previous run
        "project_upgrade_net6": upgrade_result, # from previous run
        "build_original_project": build_result_original, # from previous run
        # "build_upgraded_project": build_result_upgraded, # from previous run, if it exists
        "iis_deployment": iis_deployment_result, # from previous run
        "neoload_test": neoload_result, # from previous run
        "overall_status": "Partial Success (Simulated)",
        "issues_encountered": ["ITASCA namespace required manual intervention.", "Build of upgraded project required LLM suggestion."]
    }
    report_json_result = report_tool._run(upgrade_details=collected_data_for_report, report_format="json")
    print(f"ReportTool JSON Result: {report_json_result}")
    report_txt_result = report_tool._run(upgrade_details=collected_data_for_report, report_format="txt")
    print(f"ReportTool TXT Result: {report_txt_result}")
    # Check if report files were created (e.g., by listing current dir or checking paths from results)
    if os.path.exists(report_json_result.split(": ")[-1]): print(f"ReportTool: JSON report file created at {report_json_result.split(': ')[-1]}")
    if os.path.exists(report_txt_result.split(": ")[-1]): print(f"ReportTool: TXT report file created at {report_txt_result.split(': ')[-1]}")


    # --- Clean up dummy directories (optional, uncomment to use) ---
    # try:
    #     logger.info(f"Attempting to clean up temporary test directory: {test_root_dir}")
    #     shutil.rmtree(test_root_dir)
    #     logger.info(f"Cleaned up temporary test directory: {test_root_dir}")
    # except OSError as e:
    #     logger.error(f"Error cleaning up test directory {test_root_dir}: {e.strerror}")

    logger.info("Agent tools test completed.")
