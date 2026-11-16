$render = 'C:\Program Files\Autodesk\Maya2023\bin\Render.exe'
$scene  = 'C:\MayaScripts\OrangeTree\scenes\orange_tree_v011.ma'
$out    = 'C:\MayaScripts\OrangeTree\renders'
$summaryFile = Join-Path $out 'looktest_summary.txt'

Add-Type -Namespace Win32 -Name Power -ErrorAction SilentlyContinue -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
'@

New-Item -ItemType Directory -Force -Path $out | Out-Null
Remove-Item (Join-Path $out 'look*.png') -ErrorAction SilentlyContinue
Remove-Item $summaryFile -ErrorAction SilentlyContinue

$lines = New-Object System.Collections.Generic.List[string]
$minutes = @()
try {
    [Win32.Power]::SetThreadExecutionState([uint32]2147483649) | Out-Null
    foreach ($f in 1, 150, 300) {
        $log = Join-Path $out ("log_look_{0}.txt" -f $f)
        Write-Host ("Rendering frame {0} ..." -f $f)
        $watch = [System.Diagnostics.Stopwatch]::StartNew()
        & $render -r arnold -s $f -e $f -b 1 -rd $out -im look -of png -pad 4 -x 960 -y 540 -cam render_cam $scene *> $log
        $watch.Stop()
        $minutes += $watch.Elapsed.TotalMinutes
        $line = ("Frame {0}: {1:N1} minutes at 960 x 540" -f $f, $watch.Elapsed.TotalMinutes)
        Write-Host $line
        $lines.Add($line)
    }
} finally {
    [Win32.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null
}

$avg = ($minutes | Measure-Object -Average).Average
$full = $avg * 4
$lines.Add('')
$lines.Add(("Average: {0:N1} minutes per frame at 960 x 540" -f $avg))
$lines.Add(("Projected: about {0:N1} minutes per frame at 1920 x 1080" -f $full))
$lines.Add(("Projected: 300 frames = about {0:N1} hours" -f ($full * 300 / 60)))

$images = @(Get-ChildItem $out -Filter 'look*.png')
$lines.Add('')
$lines.Add(("Images produced: {0} of 3" -f $images.Count))
foreach ($img in $images) { $lines.Add(("  {0}  {1:N2} MB" -f $img.Name, ($img.Length / 1MB))) }
if ($images.Count -lt 3) {
    $lines.Add('')
    $lines.Add('WARNING: fewer than 3 images. Last lines of the first log:')
    foreach ($l in (Get-Content (Join-Path $out 'log_look_1.txt') -Tail 25)) { $lines.Add($l) }
}
$lines | Out-File $summaryFile -Encoding ascii
Write-Host ''
Write-Host 'Finished. Go back to Maya and run block B.'
