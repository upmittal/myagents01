import re

class DependencyAnalyzerTool:
    def run(self, solution_path: str):
        try:
            # Scan for ITASCA namespaces
            itasca_usage = self._scan_itasca(solution_path)
            
            # List NuGet packages
            nuget_packages = self._list_nugets(solution_path)
            
            # Flag outdated packages (use NuGet CLI or API)
            outdated = self._check_outdated_packages(nuget_packages)
            
            return {
                "itasca_usage": itasca_usage,
                "nuget_packages": nuget_packages,
                "outdated_packages": outdated
            }
        except Exception as e:
            return f"Analysis error: {str(e)}"
    
    def _scan_itasca(self, path: str):
        # Search for ITASCA namespace
        matches = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".cs"):
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()
                        if "ITASCA" in content:
                            matches.append(file)
        return matches
    
    def _list_nugets(self, path: str):
        # Parse .csproj files for PackageReference
        packages = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".csproj"):
                    with open(os.path.join(root, file), "r") as f:
                        content = f.read()
                        packages.extend(re.findall(r"<PackageReference Include=\"(.*?)\"", content))
        return packages
    
    def _check_outdated_packages(self, packages):
        # Use NuGet CLI: nuget list <package> -AllVersions
        outdated = []
        for package in packages:
            result = subprocess.run(
                ["nuget", "list", package, "-AllVersions"],
                capture_output=True, text=True
            )
            if "outdated" in result.stdout:
                outdated.append(package)
        return outdated