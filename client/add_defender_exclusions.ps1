# Windows Defender Exclusions for Dart & Flutter Development
# Run this script as Administrator

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    Write-Host 'ERROR: This script requires Administrator privileges!' -ForegroundColor Red
    Write-Host 'Please right-click on PowerShell and select Run as Administrator' -ForegroundColor Yellow
    Write-Host 'Then navigate to this directory and run: .\add_defender_exclusions.ps1' -ForegroundColor Yellow
    Read-Host 'Press Enter to exit'
    exit 1
}

Write-Host 'Adding Windows Defender exclusions for Dart & Flutter development...' -ForegroundColor Green
Write-Host 'Project: bruno_ai_v2' -ForegroundColor Cyan
Write-Host ''

# Define the exclusion paths
$exclusionPaths = @(
    "$env:USERPROFILE\AppData\Local\Pub\Cache",
    "$env:USERPROFILE\AppData\Local\Pub", 
    "C:\tools\flutter",
    "D:\projects\2025\bruno_ai_v2\client"
)

$successCount = 0
$failCount = 0

foreach ($path in $exclusionPaths) {
    try {
        # Check if path exists (optional - Defender will still add the exclusion)
        $exists = Test-Path $path
        $existsText = if ($exists) { "[EXISTS]" } else { "[PATH NOT FOUND]" }
        
        Add-MpPreference -ExclusionPath $path
        Write-Host "Added exclusion: $path $existsText" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host "Failed to add exclusion: $path" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ''
Write-Host "Results: $successCount successful, $failCount failed" -ForegroundColor Yellow

if ($successCount -gt 0) {
    Write-Host ''
    Write-Host 'Verifying exclusions were added:' -ForegroundColor Yellow
    try {
        $currentExclusions = Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
        $relevantExclusions = $currentExclusions | Where-Object { 
            $_ -match 'Pub|flutter|bruno_ai_v2' 
        } | Sort-Object
        
        if ($relevantExclusions) {
            foreach ($exclusion in $relevantExclusions) {
                Write-Host "  -> $exclusion" -ForegroundColor Cyan
            }
        } else {
            Write-Host "  No matching exclusions found (this might be normal)" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Could not verify exclusions" -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'Restarting Microsoft Defender Antivirus Service...' -ForegroundColor Yellow
try {
    Restart-Service -Name "WinDefend" -Force
    Write-Host 'Microsoft Defender Antivirus Service restarted successfully' -ForegroundColor Green
}
catch {
    Write-Host 'Failed to restart service. You may need to reboot.' -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ''
Write-Host 'Exclusions setup complete!' -ForegroundColor Green
Write-Host 'You can now delete this script file if desired.' -ForegroundColor Gray
Read-Host 'Press Enter to exit'
