$ProjectRoot = 'C:\Users\mickh\Desktop\MicksMusikkiste'
$StarterPath = Join-Path $ProjectRoot 'Start_Micks_Musikkiste.cmd'
$DesktopPath = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath 'Micks Musikkiste starten.lnk'
$ComfyIcon = Join-Path $env:LOCALAPPDATA 'Programs\ComfyUI\ComfyUI.exe'

if (-not (Test-Path -LiteralPath $StarterPath)) {
    Write-Error "Starter-Datei nicht gefunden: $StarterPath"
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $StarterPath
$Shortcut.WorkingDirectory = $ProjectRoot

if (Test-Path -LiteralPath $ComfyIcon) {
    $Shortcut.IconLocation = "$ComfyIcon,0"
} else {
    $Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,220"
}

$Shortcut.Save()

Write-Host "Desktop-Verknuepfung erstellt/aktualisiert: $ShortcutPath"
