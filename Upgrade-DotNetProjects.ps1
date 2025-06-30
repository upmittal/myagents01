#Requires -Version 5.1

<#
.SYNOPSIS
    Recursively upgrades .csproj files by changing TargetFrameworkVersion and converts packages.config to PackageReference format.

.DESCRIPTION
    This PowerShell script performs automated upgrades of .NET projects in a directory tree:
    - Changes TargetFrameworkVersion in .csproj files
    - Converts packages.config to PackageReference format using nuget.exe migrate
    - Creates backups of modified files
    - Optionally checks files into TFS using tf.exe
    - Logs all operations with timestamps
    - Handles errors gracefully with detailed logging

.PARAMETER RootPath
    The root directory to search for .csproj files. Defaults to current directory.

.PARAMETER TargetVersion
    The target .NET Framework version (e.g., "v4.8", "v4.7.2"). Defaults to "v4.8".

.PARAMETER EnableTFVC
    Enable Team Foundation Version Control operations (checkout/checkin). Defaults to $false.

.PARAMETER EnableLogging
    Enable detailed logging to file. Defaults to $true.

.PARAMETER LogPath
    Path for the log file. If not specified, creates a timestamped log in the script directory.

.PARAMETER NuGetPath
    Path to nuget.exe. If not specified, attempts to find in PATH or common locations.

.PARAMETER TfPath
    Path to tf.exe for TFS operations. If not specified, attempts to find in common Visual Studio locations.

.PARAMETER CheckinComment
    Comment for TFS checkin operation. Defaults to auto-generated comment with target version.

.PARAMETER WhatIf
    Preview operations without making actual changes.

.EXAMPLE
    .\Upgrade-DotNetProjects.ps1 -RootPath "C:\Source\MyProject" -TargetVersion "v4.8"
    
    Upgrades all .csproj files in C:\Source\MyProject to .NET Framework 4.8

.EXAMPLE
    .\Upgrade-DotNetProjects.ps1 -RootPath "." -TargetVersion "v4.7.2" -EnableTFVC $true -CheckinComment "Upgrade to .NET 4.7.2"
    
    Upgrades projects and checks them into TFS with custom comment

.EXAMPLE
    .\Upgrade-DotNetProjects.ps1 -WhatIf
    
    Preview what would be changed without making modifications
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $false)]
    [string]$RootPath = (Get-Location).Path,
    
    [Parameter(Mandatory = $false)]
    [ValidatePattern('^v\d+\.\d+(\.\d+)?$')]
    [string]$TargetVersion = "v4.8",
    
    [Parameter(Mandatory = $false)]
    [bool]$EnableTFVC = $false,
    
    [Parameter(Mandatory = $false)]
    [bool]$EnableLogging = $true,
    
    [Parameter(Mandatory = $false)]
    [string]$LogPath = "",
    
    [Parameter(Mandatory = $false)]
    [string]$NuGetPath = "",
    
    [Parameter(Mandatory = $false)]
    [string]$TfPath = "",
    
    [Parameter(Mandatory = $false)]
    [string]$CheckinComment = "",
    
    [Parameter(Mandatory = $false)]
    [switch]$WhatIf
)

# Global variables for tracking operations
$script:LogFile = ""
$script:ModifiedFiles = @()
$script:BackupFiles = @()
$script:ErrorCount = 0
$script:SuccessCount = 0
$script:SkippedCount = 0

# Folders to skip during recursive search
$script:SkipFolders = @("bin", "obj", ".vs", "packages", ".git", ".svn", "node_modules")

#region Logging Functions

function Initialize-Logging {
    if (-not $EnableLogging) { return }
    
    if ([string]::IsNullOrEmpty($LogPath)) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $script:LogFile = Join-Path $PSScriptRoot "DotNetUpgrade_$timestamp.log"
    } else {
        $script:LogFile = $LogPath
    }
    
    try {
        $logDir = Split-Path $script:LogFile -Parent
        if (-not (Test-Path $logDir)) {
            New-Item -Path $logDir -ItemType Directory -Force | Out-Null
        }
        
        $header = @"
==========================================
.NET Project Upgrade Log
Started: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Root Path: $RootPath
Target Version: $TargetVersion
TFVC Enabled: $EnableTFVC
What-If Mode: $WhatIf
==========================================

"@
        $header | Out-File -FilePath $script:LogFile -Encoding UTF8
        Write-Host "Logging enabled: $script:LogFile" -ForegroundColor Green
    }
    catch {
        Write-Warning "Failed to initialize logging: $($_.Exception.Message)"
        $script:EnableLogging = $false
    }
}

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Console output with colors
    switch ($Level) {
        "INFO"    { Write-Host $logEntry -ForegroundColor White }
        "WARNING" { Write-Warning $logEntry }
        "ERROR"   { Write-Error $logEntry }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
    }
    
    # File output
    if ($EnableLogging -and -not [string]::IsNullOrEmpty($script:LogFile)) {
        try {
            $logEntry | Out-File -FilePath $script:LogFile -Append -Encoding UTF8
        }
        catch {
            Write-Warning "Failed to write to log file: $($_.Exception.Message)"
        }
    }
}

#endregion

#region Tool Discovery Functions

function Find-NuGetExe {
    if (-not [string]::IsNullOrEmpty($NuGetPath) -and (Test-Path $NuGetPath)) {
        return $NuGetPath
    }
    
    # Try common locations
    $commonPaths = @(
        "nuget.exe",
        ".\nuget.exe",
        ".\tools\nuget.exe",
        "$env:ProgramFiles\NuGet\nuget.exe",
        "$env:ProgramFiles(x86)\NuGet\nuget.exe"
    )
    
    foreach ($path in $commonPaths) {
        try {
            $resolved = Get-Command $path -ErrorAction SilentlyContinue
            if ($resolved) {
                Write-Log "Found nuget.exe at: $($resolved.Source)" -Level "SUCCESS"
                return $resolved.Source
            }
        }
        catch { }
    }
    
    Write-Log "nuget.exe not found. Package migration will be skipped." -Level "WARNING"
    return $null
}

function Find-TfExe {
    if (-not $EnableTFVC) { return $null }
    
    if (-not [string]::IsNullOrEmpty($TfPath) -and (Test-Path $TfPath)) {
        return $TfPath
    }
    
    # Try common Visual Studio locations
    $commonPaths = @(
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\tf.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\tf.exe",
        "${env:ProgramFiles}\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\tf.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Enterprise\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\tf.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\tf.exe",
        "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019\Community\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\tf.exe"
    )
    
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            Write-Log "Found tf.exe at: $path" -Level "SUCCESS"
            return $path
        }
    }
    
    try {
        $tfCommand = Get-Command "tf.exe" -ErrorAction SilentlyContinue
        if ($tfCommand) {
            Write-Log "Found tf.exe in PATH: $($tfCommand.Source)" -Level "SUCCESS"
            return $tfCommand.Source
        }
    }
    catch { }
    
    Write-Log "tf.exe not found. TFVC operations will be skipped." -Level "WARNING"
    return $null
}

#endregion

#region File Operation Functions

function Backup-File {
    param(
        [string]$FilePath
    )
    
    try {
        $backupPath = "$FilePath.bak"
        $counter = 1
        
        # Create unique backup name if .bak already exists
        while (Test-Path $backupPath) {
            $backupPath = "$FilePath.bak$counter"
            $counter++
        }
        
        if ($WhatIf) {
            Write-Log "WHAT-IF: Would backup $FilePath to $backupPath" -Level "INFO"
            return $backupPath
        }
        
        Copy-Item -Path $FilePath -Destination $backupPath -Force
        $script:BackupFiles += $backupPath
        Write-Log "Created backup: $backupPath" -Level "INFO"
        return $backupPath
    }
    catch {
        Write-Log "Failed to backup file $FilePath`: $($_.Exception.Message)" -Level "ERROR"
        $script:ErrorCount++
        return $null
    }
}

function Update-CsprojTargetFramework {
    param(
        [string]$CsprojPath,
        [string]$NewVersion
    )
    
    try {
        Write-Log "Processing: $CsprojPath" -Level "INFO"
        
        # Read the XML content
        $xml = New-Object System.Xml.XmlDocument
        $xml.PreserveWhitespace = $true
        $xml.Load($CsprojPath)
        
        # Find TargetFrameworkVersion elements
        $targetFrameworkNodes = $xml.SelectNodes("//TargetFrameworkVersion")
        
        if ($targetFrameworkNodes.Count -eq 0) {
            Write-Log "No TargetFrameworkVersion found in $CsprojPath" -Level "WARNING"
            $script:SkippedCount++
            return $false
        }
        
        $modified = $false
        foreach ($node in $targetFrameworkNodes) {
            $currentVersion = $node.InnerText
            if ($currentVersion -ne $NewVersion) {
                Write-Log "Changing TargetFrameworkVersion from '$currentVersion' to '$NewVersion' in $CsprojPath" -Level "INFO"
                
                if (-not $WhatIf) {
                    $node.InnerText = $NewVersion
                    $modified = $true
                }
            } else {
                Write-Log "TargetFrameworkVersion already set to '$NewVersion' in $CsprojPath" -Level "INFO"
            }
        }
        
        if ($modified -and -not $WhatIf) {
            $xml.Save($CsprojPath)
            $script:ModifiedFiles += $CsprojPath
            Write-Log "Updated: $CsprojPath" -Level "SUCCESS"
            $script:SuccessCount++
        } elseif ($WhatIf) {
            Write-Log "WHAT-IF: Would update $CsprojPath" -Level "INFO"
        }
        
        return $modified
    }
    catch {
        Write-Log "Failed to update $CsprojPath`: $($_.Exception.Message)" -Level "ERROR"
        $script:ErrorCount++
        return $false
    }
}

function Convert-PackagesConfig {
    param(
        [string]$CsprojPath,
        [string]$NuGetExePath
    )
    
    if ([string]::IsNullOrEmpty($NuGetExePath)) {
        return $false
    }
    
    $projectDir = Split-Path $CsprojPath -Parent
    $packagesConfigPath = Join-Path $projectDir "packages.config"
    
    if (-not (Test-Path $packagesConfigPath)) {
        Write-Log "No packages.config found for $CsprojPath" -Level "INFO"
        return $false
    }
    
    try {
        Write-Log "Converting packages.config to PackageReference for: $CsprojPath" -Level "INFO"
        
        # Backup packages.config
        $backupResult = Backup-File -FilePath $packagesConfigPath
        if (-not $backupResult) {
            Write-Log "Failed to backup packages.config, skipping migration" -Level "WARNING"
            return $false
        }
        
        if ($WhatIf) {
            Write-Log "WHAT-IF: Would run nuget migrate on $CsprojPath" -Level "INFO"
            return $true
        }
        
        # Run nuget migrate command
        $migrateArgs = @("migrate", $CsprojPath, "-PackageReference")
        $process = Start-Process -FilePath $NuGetExePath -ArgumentList $migrateArgs -Wait -PassThru -NoNewWindow -RedirectStandardOutput "nuget_output.tmp" -RedirectStandardError "nuget_error.tmp"
        
        # Read output
        $output = if (Test-Path "nuget_output.tmp") { Get-Content "nuget_output.tmp" -Raw } else { "" }
        $errorOutput = if (Test-Path "nuget_error.tmp") { Get-Content "nuget_error.tmp" -Raw } else { "" }
        
        # Clean up temp files
        @("nuget_output.tmp", "nuget_error.tmp") | ForEach-Object { if (Test-Path $_) { Remove-Item $_ -Force } }
        
        if ($process.ExitCode -eq 0) {
            Write-Log "Successfully migrated packages.config to PackageReference for: $CsprojPath" -Level "SUCCESS"
            $script:ModifiedFiles += $CsprojPath
            return $true
        } else {
            Write-Log "NuGet migrate failed for $CsprojPath. Exit code: $($process.ExitCode). Error: $errorOutput" -Level "ERROR"
            $script:ErrorCount++
            return $false
        }
    }
    catch {
        Write-Log "Exception during packages.config migration for $CsprojPath`: $($_.Exception.Message)" -Level "ERROR"
        $script:ErrorCount++
        return $false
    }
}

#endregion

#region TFVC Functions

function Invoke-TfCheckout {
    param(
        [string[]]$FilePaths,
        [string]$TfExePath
    )
    
    if ([string]::IsNullOrEmpty($TfExePath) -or $FilePaths.Count -eq 0) {
        return $false
    }
    
    try {
        Write-Log "Checking out $($FilePaths.Count) files from TFS" -Level "INFO"
        
        if ($WhatIf) {
            Write-Log "WHAT-IF: Would checkout files: $($FilePaths -join ', ')" -Level "INFO"
            return $true
        }
        
        foreach ($file in $FilePaths) {
            $checkoutArgs = @("checkout", $file)
            $process = Start-Process -FilePath $TfExePath -ArgumentList $checkoutArgs -Wait -PassThru -NoNewWindow
            
            if ($process.ExitCode -ne 0) {
                Write-Log "Failed to checkout $file from TFS. Exit code: $($process.ExitCode)" -Level "WARNING"
            } else {
                Write-Log "Checked out: $file" -Level "INFO"
            }
        }
        
        return $true
    }
    catch {
        Write-Log "Exception during TFS checkout: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

function Invoke-TfCheckin {
    param(
        [string[]]$FilePaths,
        [string]$TfExePath,
        [string]$Comment
    )
    
    if ([string]::IsNullOrEmpty($TfExePath) -or $FilePaths.Count -eq 0) {
        return $false
    }
    
    try {
        if ([string]::IsNullOrEmpty($Comment)) {
            $Comment = "Automated .NET Framework upgrade to $TargetVersion - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        }
        
        Write-Log "Checking in $($FilePaths.Count) files to TFS with comment: $Comment" -Level "INFO"
        
        if ($WhatIf) {
            Write-Log "WHAT-IF: Would checkin files with comment: $Comment" -Level "INFO"
            return $true
        }
        
        # Build checkin arguments
        $checkinArgs = @("checkin")
        $checkinArgs += $FilePaths
        $checkinArgs += @("/comment:$Comment")
        
        $process = Start-Process -FilePath $TfExePath -ArgumentList $checkinArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-Log "Successfully checked in files to TFS" -Level "SUCCESS"
            return $true
        } else {
            Write-Log "TFS checkin failed. Exit code: $($process.ExitCode)" -Level "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Exception during TFS checkin: $($_.Exception.Message)" -Level "ERROR"
        return $false
    }
}

#endregion

#region Main Processing Functions

function Get-CsprojFiles {
    param(
        [string]$Path
    )
    
    Write-Log "Searching for .csproj files in: $Path" -Level "INFO"
    
    $csprojFiles = @()
    
    try {
        Get-ChildItem -Path $Path -Recurse -Filter "*.csproj" | ForEach-Object {
            $relativePath = $_.DirectoryName.Substring($Path.Length).TrimStart('\', '/')
            $pathParts = $relativePath -split '[\\/]'
            
            # Check if any part of the path contains skip folders
            $shouldSkip = $false
            foreach ($part in $pathParts) {
                if ($script:SkipFolders -contains $part) {
                    $shouldSkip = $true
                    break
                }
            }
            
            if (-not $shouldSkip) {
                $csprojFiles += $_.FullName
                Write-Log "Found: $($_.FullName)" -Level "INFO"
            } else {
                Write-Log "Skipped (in excluded folder): $($_.FullName)" -Level "INFO"
                $script:SkippedCount++
            }
        }
    }
    catch {
        Write-Log "Error searching for .csproj files: $($_.Exception.Message)" -Level "ERROR"
        $script:ErrorCount++
    }
    
    Write-Log "Found $($csprojFiles.Count) .csproj files to process" -Level "INFO"
    return $csprojFiles
}

function Process-Projects {
    param(
        [string[]]$CsprojFiles,
        [string]$NuGetExePath,
        [string]$TfExePath
    )
    
    if ($CsprojFiles.Count -eq 0) {
        Write-Log "No .csproj files to process" -Level "WARNING"
        return
    }
    
    # Checkout files from TFS if enabled
    if ($EnableTFVC -and -not [string]::IsNullOrEmpty($TfExePath)) {
        Invoke-TfCheckout -FilePaths $CsprojFiles -TfExePath $TfExePath
    }
    
    # Process each project
    foreach ($csprojPath in $CsprojFiles) {
        Write-Log "Processing project: $csprojPath" -Level "INFO"
        
        # Backup the .csproj file
        $backupResult = Backup-File -FilePath $csprojPath
        if (-not $backupResult) {
            Write-Log "Skipping $csprojPath due to backup failure" -Level "WARNING"
            continue
        }
        
        # Update target framework
        $frameworkUpdated = Update-CsprojTargetFramework -CsprojPath $csprojPath -NewVersion $TargetVersion
        
        # Convert packages.config if it exists
        $packagesConverted = Convert-PackagesConfig -CsprojPath $csprojPath -NuGetExePath $NuGetExePath
        
        if ($frameworkUpdated -or $packagesConverted) {
            Write-Log "Successfully processed: $csprojPath" -Level "SUCCESS"
        }
    }
    
    # Checkin files to TFS if enabled and files were modified
    if ($EnableTFVC -and -not [string]::IsNullOrEmpty($TfExePath) -and $script:ModifiedFiles.Count -gt 0) {
        Invoke-TfCheckin -FilePaths $script:ModifiedFiles -TfExePath $TfExePath -Comment $CheckinComment
    }
}

#endregion

#region Main Script Execution

function Main {
    try {
        Write-Host "=== .NET Project Upgrade Script ===" -ForegroundColor Cyan
        Write-Host "Root Path: $RootPath"
        Write-Host "Target Version: $TargetVersion"
        Write-Host "TFVC Enabled: $EnableTFVC"
        Write-Host "What-If Mode: $WhatIf"
        Write-Host ""
        
        # Initialize logging
        Initialize-Logging
        
        # Validate root path
        if (-not (Test-Path $RootPath)) {
            Write-Log "Root path does not exist: $RootPath" -Level "ERROR"
            return 1
        }
        
        # Find required tools
        $nugetExe = Find-NuGetExe
        $tfExe = Find-TfExe
        
        # Find all .csproj files
        $csprojFiles = Get-CsprojFiles -Path $RootPath
        
        if ($csprojFiles.Count -eq 0) {
            Write-Log "No .csproj files found in the specified directory tree" -Level "WARNING"
            return 0
        }
        
        # Process projects
        Process-Projects -CsprojFiles $csprojFiles -NuGetExePath $nugetExe -TfExePath $tfExe
        
        # Summary
        Write-Log "" -Level "INFO"
        Write-Log "=== OPERATION SUMMARY ===" -Level "INFO"
        Write-Log "Files processed successfully: $script:SuccessCount" -Level "SUCCESS"
        Write-Log "Files skipped: $script:SkippedCount" -Level "INFO"
        Write-Log "Errors encountered: $script:ErrorCount" -Level "INFO"
        Write-Log "Modified files: $($script:ModifiedFiles.Count)" -Level "INFO"
        Write-Log "Backup files created: $($script:BackupFiles.Count)" -Level "INFO"
        
        if ($script:ModifiedFiles.Count -gt 0) {
            Write-Log "Modified files:" -Level "INFO"
            $script:ModifiedFiles | ForEach-Object { Write-Log "  - $_" -Level "INFO" }
        }
        
        if ($script:BackupFiles.Count -gt 0) {
            Write-Log "Backup files created:" -Level "INFO"
            $script:BackupFiles | ForEach-Object { Write-Log "  - $_" -Level "INFO" }
        }
        
        Write-Host "`n=== Script completed ===" -ForegroundColor Cyan
        
        return if ($script:ErrorCount -gt 0) { 1 } else { 0 }
    }
    catch {
        Write-Log "Unhandled exception in main script: $($_.Exception.Message)" -Level "ERROR"
        Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
        return 1
    }
}

#endregion

# Script entry point
if ($MyInvocation.InvocationName -ne '.') {
    $exitCode = Main
    exit $exitCode
}
