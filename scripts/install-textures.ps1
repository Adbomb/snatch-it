# Копирует LEGO-текстуры из assets/textures в content/textures/snatch установленной Roblox Studio.
# Там их видно по адресам rbxasset://textures/snatch/<файл>.png (только в Studio на этом компьютере).
# После обновления Studio папка версии меняется — запустите скрипт ещё раз:
#   powershell -ExecutionPolicy Bypass -File scripts/install-textures.ps1

$ErrorActionPreference = 'Stop'

$source = Join-Path $PSScriptRoot '..\assets\textures'
$files = Get-ChildItem -Path $source -Filter 'lego_studs_*.png'
if ($files.Count -eq 0) {
    throw "Нет текстур в $source"
}

# Папка Studio: у запущенной Studio — её собственная, иначе самая новая версия, где есть RobloxStudioBeta.exe.
$studioDir = $null
$running = Get-Process RobloxStudioBeta -ErrorAction SilentlyContinue | Select-Object -First 1
if ($running -and $running.Path) {
    $studioDir = Split-Path $running.Path
} else {
    $versions = Join-Path $env:LOCALAPPDATA 'Roblox\Versions'
    $studioDir = Get-ChildItem -Path $versions -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName 'RobloxStudioBeta.exe') } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1 -ExpandProperty FullName
}
if (-not $studioDir) {
    throw 'Не нашёл установленную Roblox Studio'
}

$target = Join-Path $studioDir 'content\textures\snatch'
New-Item -ItemType Directory -Force -Path $target | Out-Null
foreach ($file in $files) {
    Copy-Item -Path $file.FullName -Destination $target -Force
}
Write-Output ("Скопировано {0} файлов в {1}" -f $files.Count, $target)
