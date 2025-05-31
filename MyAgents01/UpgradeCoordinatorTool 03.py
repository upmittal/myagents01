class UpgradeCoordinatorTool(BaseTool):
    def run(self, project_path: str, target_framework: str):
        try:
            self._log(f"Upgrading {project_path} to {target_framework}")
            # Modify .csproj
            with open(project_path, "r") as f:
                content = f.read()
            content = re.sub(
                r"<TargetFramework>.*?</TargetFramework>", 
                f"<TargetFramework>{target_framework}</TargetFramework>", content
            )
            with open(project_path, "w") as f:
                f.write(content)
            
            # Build and resolve errors
            result = subprocess.run(
                ["dotnet", "build", project_path], 
                capture_output=True, text=True
            )
            if "error" in result.stderr:
                error_msg = result.stderr
                self._log(f"Build errors detected: {error_msg}", "error")
                suggestion = self._call_llm(f"Fix .NET build errors: {error_msg}")
                user_choice = self._ask_human_feedback(
                    f"Suggested fix: {suggestion}. Apply? (Y/N)"
                )
                return {"status": "build_error", "suggestion": suggestion, "user_choice": user_choice}
            
            return {"status": "success", "framework": target_framework}
        except Exception as e:
            error_msg = f"Upgrade failed: {str(e)}"
            self._log(error_msg, "error")
            return {"status": "error", "error": error_msg}