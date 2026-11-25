# Не даёт экрану погаснуть N минут (по умолчанию 120), чтобы Roblox Studio рисовал кадр, пока владелец не у компьютера.
# Зачем: при погасшем экране (схема питания — «отключать экран через 45 мин») Studio не рисует кадры — снимки MCP
# обрываются по таймауту, а плавные переходы (TweenService) стоят (docs/memory/BUGS.md, 2026-11-25).
# Как: запрос питания ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED и раз в 30 с «движение мыши» на 0 пикселей
# (будит уже погасший экран). Настройки питания не меняет; по окончании запрос снимается.
# Запуск фоном из сессии: powershell -NoProfile -File scripts\keep-display.ps1 120

param([int]$Minutes = 120)

$sig = @'
using System; using System.Runtime.InteropServices;
public class KeepDisplay {
	[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);
	[DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, UIntPtr e);
}
'@
Add-Type $sig
$end = (Get-Date).AddMinutes($Minutes)
while ((Get-Date) -lt $end) {
	[KeepDisplay]::mouse_event(0x0001, 0, 0, 0, [UIntPtr]::Zero)
	[void][KeepDisplay]::SetThreadExecutionState(0x80000003)
	Start-Sleep -Seconds 30
}
[void][KeepDisplay]::SetThreadExecutionState(0x80000000)
