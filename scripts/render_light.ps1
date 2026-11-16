$render = 'C:\Program Files\Autodesk\Maya2023\bin\Render.exe'
$scenes = 'C:\MayaScripts\OrangeTree\scenes'
$out    = 'C:\MayaScripts\OrangeTree\renders'
$names  = 'light1_sun3p5_dome1p2', 'light2_sun2p0_dome0p8', 'light3_sun1p5_dome0p6', 'light4_sun3p0_dome0p5'
$summaryFile = Join-Path $out 'light_summary.txt'

Add-Type -Namespace Win32 -Name Power -ErrorAction SilentlyContinue -MemberDefinition @'
[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);
'@

New-Item -ItemType Directory -Force -Path $out | Out-Null
Remove-Item (Join-Path $out 'light*.png') -ErrorAction SilentlyContinue
Remove-Item $summaryFile -ErrorAction SilentlyContinue

$lines = New-Object System.Collections.Generic.List[string]
try {
    [Win32.Power]::SetThreadExecutionState([uint32]2147483649) | Out-Null
    foreach ($n in $names) {
        $scene = Join-Path $scenes ($n + '.ma')
        $log = Join-Path $out ("log_{0}.txt" -f $n)
        Write-Host ("Rendering {0} ..." -f $n)
        $watch = [System.Diagnostics.Stopwatch]::StartNew()
        & $render -r arnold -s 1 -e 1 -b 1 -rd $out -im $n -of png -pad 4 -x 480 -y 270 -cam render_cam $scene *> $log
        $watch.Stop()
        $line = ("{0}: {1:N1} minutes" -f $n, $watch.Elapsed.TotalMinutes)
        Write-Host $line
        $lines.Add($line)
    }
} finally {
    [Win32.Power]::SetThreadExecutionState([uint32]2147483648) | Out-Null
}

$images = @(Get-ChildItem $out -Filter 'light*.png')
$lines.Add('')
$lines.Add(("Images produced: {0} of {1}" -f $images.Count, $names.Count))
if ($images.Count -lt $names.Count) {
    $lines.Add('WARNING: some renders failed. Last lines of the first log:')
    foreach ($l in (Get-Content (Join-Path $out 'log_light1_sun3p5_dome1p2.txt') -Tail 25)) { $lines.Add($l) }
}
$lines | Out-File $summaryFile -Encoding ascii
Write-Host ''
Write-Host 'Finished. Go back to Maya and run block B.'
