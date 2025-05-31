class TfsCodeRetrieverTool(BaseTool):
    def run(self, tfs_repo_url: str, local_path: str):
        try:
            self._log(f"Fetching code from TFS: {tfs_repo_url}")
            # Simulate TFS checkout (replace with actual TFS CLI commands)
            subprocess.run(["tf", "get", tfs_repo_url, "/recursive"], check=True, cwd=local_path)
            
            # Initialize Git
            subprocess.run(["git", "init"], cwd=local_path, check=True)
            subprocess.run(["git", "add", "."], cwd=local_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=local_path, check=True)
            
            self._log(f"Code retrieved and Git initialized at {local_path}")
            return {"status": "success", "path": local_path}
        except subprocess.CalledProcessError as e:
            error_msg = f"TFS/Git command failed: {str(e)}"
            self._log(error_msg, "error")
            suggestion = self._call_llm(f"Fix TFS checkout/git init error: {error_msg}")
            return {"status": "error", "error": error_msg, "suggestion": suggestion}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self._log(error_msg, "error")
            return {"status": "error", "error": error_msg}