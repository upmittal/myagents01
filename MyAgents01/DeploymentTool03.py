class DeploymentTool(BaseTool):
    def run(self, project_path: str, iis_site_name: str):
        try:
            self._log(f"Deploying {project_path} to IIS site {iis_site_name}")
            # Publish
            subprocess.run(["dotnet", "publish", project_path], check=True)
            publish_path = os.path.join(project_path, "bin", "Debug", "net8.0", "publish")
            
            # Deploy to IIS
            subprocess.run([
                "msdeploy", "-verb:sync", 
                f"-source:iisApp={publish_path}", 
                f"-dest:iisApp={iis_site_name}"
            ], check=True)
            
            self._log("Deployment successful")
            return {"status": "success", "url": f"http://{iis_site_name}"}
        except subprocess.CalledProcessError as e:
            error_msg = f"Deployment failed: {str(e)}"
            self._log(error_msg, "error")
            suggestion = self._call_llm("Fix IIS deployment error: {error_msg}")
            return {"status": "error", "error": error_msg, "suggestion": suggestion}