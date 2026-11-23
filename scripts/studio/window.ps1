# Окно Studio или Roblox Player на этом ПК (Windows, user32): снимок, размер, вывод вперёд, нажатия клавиш.
# Нужен, потому что MCP screen_capture не снимает CoreGui (верхнюю панель Roblox) и не меняет размер вида.
#   -Action info   — заголовок и прямоугольник окна
#   -Action front  — вывести вперёд (трюк с Alt: без него SetForegroundWindow не срабатывает, кадр чёрный)
#   -Action size -Width W -Height H — окно W×H; вид игры = окно − 455 × 563 px (панели нынешней раскладки Studio):
#       1299×953 → 844×390 (телефон), 1122×938 → 667×375, 1735×1283 → 1280×720 (ПК)
#   -Action max    — развернуть
#   -Action shot -Out файл.png — снимок клиентской области окна (вид игры потом вырезает crop_view.py)
#   -Action keys -Text "%p" — SendKeys в окно (так публиковали Alt+P; публикация — только с разрешения владельца)
# Пример: .\scripts\studio\window.ps1 -Action size -Process RobloxStudioBeta -Width 1299 -Height 953
# Ни от чего в репозитории не зависит.
param(
	[string]$Action = "shot",       # shot | keys | info | front | size | max
	[string]$Process = "RobloxPlayerBeta",
	[string]$Out = "",
	[string]$Text = "",
	[int]$Width = 0,
	[int]$Height = 0
)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public class RW {
	[DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
	[DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
	[DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool repaint);
	[DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
	[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
	[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
	[DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
	[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
	[DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
	[DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
	public struct RECT { public int L, T, R, B; }
	public struct POINT { public int X, Y; }
}
"@
[RW]::SetProcessDPIAware() | Out-Null
$p = Get-Process $Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { "no window for $Process"; exit 1 }
$h = $p.MainWindowHandle
function Front {
	if ([RW]::IsIconic($h)) { [RW]::ShowWindow($h, 9) | Out-Null } else { [RW]::ShowWindow($h, 5) | Out-Null }
	[RW]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)
	[RW]::SetForegroundWindow($h) | Out-Null
	[RW]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
	Start-Sleep -Milliseconds 400
	return ([RW]::GetForegroundWindow() -eq $h)
}
switch ($Action) {
	"info" {
		$r = New-Object RW+RECT; [RW]::GetWindowRect($h, [ref]$r) | Out-Null
		"title=" + $p.MainWindowTitle + " rect=" + "$($r.L),$($r.T),$($r.R),$($r.B)" + " pid=" + $p.Id + " start=" + $p.StartTime
	}
	"front" { "front=" + (Front) }
	"size" {
		[RW]::ShowWindow($h, 9) | Out-Null
		Start-Sleep -Milliseconds 200
		[RW]::MoveWindow($h, 40, 40, $Width, $Height, $true) | Out-Null
		[RW]::SetForegroundWindow($h) | Out-Null
		"sized ${Width}x${Height}"
	}
	"max" {
		[RW]::ShowWindow($h, 3) | Out-Null
		[RW]::SetForegroundWindow($h) | Out-Null
		"maximized"
	}
	"shot" {
		$ok = Front
		$c = New-Object RW+RECT; [RW]::GetClientRect($h, [ref]$c) | Out-Null
		$pt = New-Object RW+POINT; [RW]::ClientToScreen($h, [ref]$pt) | Out-Null
		$w = $c.R - $c.L; $hh = $c.B - $c.T
		$bmp = New-Object System.Drawing.Bitmap $w, $hh
		$g = [System.Drawing.Graphics]::FromImage($bmp)
		$g.CopyFromScreen($pt.X, $pt.Y, 0, 0, (New-Object System.Drawing.Size $w, $hh))
		$bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
		$g.Dispose(); $bmp.Dispose()
		"front=$ok size=${w}x${hh} -> $Out"
	}
	"keys" {
		$ok = Front
		if (-not $ok) { "not in front, keys not sent"; exit 1 }
		[System.Windows.Forms.SendKeys]::SendWait($Text)
		"sent"
	}
}
