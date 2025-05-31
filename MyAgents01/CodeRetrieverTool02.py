import subprocess

class TfsCodeRetrieverTool:
    def run(self, tfs_repo_url: str, local_path: str):
        try:
            # Simulate TFS checkout (replace with actual TFS CLI commands)
            print(f"Fetching code from TFS: {tfs_repo_url}")
            subprocess.run(["tf", "get", tfs_repo_url, "/recursive"], check=True)
            
            # Initialize Git
            subprocess.run(["git", "init"], cwd=local_path, check=True)
            subprocess.run(["git", "add", "."], cwd=local_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=local_path, check=True)
            return f"Code retrieved and Git initialized at {local_path}"
        except Exception as e:
            return f"Error: {str(e)}"