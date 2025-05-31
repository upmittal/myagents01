class DeploymentTool:
    def run(self, project_path: str, iis_site_name: str):
        try:
            # Publish and deploy to IIS
            subprocess.run(["dotnet", "publish", project_path], check=True)
            publish_path = os.path.join(project_path, "bin", "Debug", "net8.0", "publish")
            
            # Use MSDeploy or AppCmd to deploy
            subprocess.run([
                "msdeploy", "-verb:sync", 
                f"-source:iisApp={publish_path}", 
                f"-dest:iisApp={iis_site_name}"
            ], check=True)
            
            return f"Deployed to IIS site: {iis_site_name}"
        except Exception as e:
            return f"Deployment failed: {str(e)}"