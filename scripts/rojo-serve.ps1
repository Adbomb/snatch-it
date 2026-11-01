# Держит `rojo serve` запущенным: если Rojo упал или его закрыли, через 2 с запускает снова.
# Запуск отдельно от сессий Claude (окно можно свернуть):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\rojo-serve.ps1
# Второй экземпляр не стартует, если порт 34872 уже занят. Журнал — %TEMP%\snatch-it-rojo.log.
# Зачем: Rojo 7.7.1 падает при удалении папки в src во время работы (change_processor.rs:179) — см. docs/memory/BUGS.md.

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $env:TEMP "snatch-it-rojo.log"
$port = 34872

if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
	"Порт $port уже занят — Rojo уже запущен, второй не нужен."
	exit 0
}

$rojo = (Get-Command rojo -ErrorAction SilentlyContinue).Source
if (-not $rojo) { $rojo = Join-Path $env:USERPROFILE ".aftman\bin\rojo.exe" }

Set-Location $root
while ($true) {
	Add-Content -Path $log -Encoding UTF8 -Value "$(Get-Date -Format s) запуск rojo serve"
	& $rojo serve default.project.json --port $port 2>&1 | ForEach-Object {
		$line = "$_"
		Add-Content -Path $log -Encoding UTF8 -Value $line
		$line
	}
	Add-Content -Path $log -Encoding UTF8 -Value "$(Get-Date -Format s) rojo завершился (код $LASTEXITCODE), перезапуск через 2 с"
	Start-Sleep -Seconds 2
}
