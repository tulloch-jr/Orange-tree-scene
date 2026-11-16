Add-Type -AssemblyName System.Drawing
$out = 'C:\MayaScripts\OrangeTree\renders'
$report = New-Object System.Collections.Generic.List[string]

function Measure-Image($path) {
    $bmp = New-Object System.Drawing.Bitmap $path
    $w = $bmp.Width
    $h = $bmp.Height
    $n = 0; $lumSum = 0.0; $dark = 0; $bright = 0; $satSum = 0.0
    $skyN = 0; $skyR = 0.0; $skyG = 0.0; $skyB = 0.0
    $gndN = 0; $gndR = 0.0; $gndG = 0.0; $gndB = 0.0
    for ($y = 0; $y -lt $h; $y += 6) {
        for ($x = 0; $x -lt $w; $x += 6) {
            $c = $bmp.GetPixel($x, $y)
            $r = [int]$c.R; $g = [int]$c.G; $b = [int]$c.B
            $lum = 0.2126 * $r + 0.7152 * $g + 0.0722 * $b
            $mx = [math]::Max($r, [math]::Max($g, $b))
            $mn = [math]::Min($r, [math]::Min($g, $b))
            $n++
            $lumSum += $lum
            if ($lum -lt 20) { $dark++ }
            if ($lum -gt 235) { $bright++ }
            if ($mx -gt 0) { $satSum += ($mx - $mn) / $mx }
            if ($y -lt $h * 0.2) { $skyN++; $skyR += $r; $skyG += $g; $skyB += $b }
            if ($y -gt $h * 0.8) { $gndN++; $gndR += $r; $gndG += $g; $gndB += $b }
        }
    }
    $bmp.Dispose()
    $report.Add(("  size               : {0} x {1}" -f $w, $h))
    $report.Add(("  average brightness : {0:N0} of 255   (healthy is about 70 to 150)" -f ($lumSum / $n)))
    $report.Add(("  almost black       : {0:N1} %" -f (100.0 * $dark / $n)))
    $report.Add(("  almost white       : {0:N1} %" -f (100.0 * $bright / $n)))
    $report.Add(("  colourfulness      : {0:N2}      (below 0.12 looks grey)" -f ($satSum / $n)))
    $report.Add(("  top 20 % (sky)     : R {0:N0}  G {1:N0}  B {2:N0}" -f ($skyR / $skyN), ($skyG / $skyN), ($skyB / $skyN)))
    $report.Add(("  bottom 20 % (grass): R {0:N0}  G {1:N0}  B {2:N0}" -f ($gndR / $gndN), ($gndG / $gndN), ($gndB / $gndN)))
}

foreach ($img in Get-ChildItem $out -Filter 'look*.png' | Sort-Object Name) {
    $report.Add($img.Name)
    Measure-Image $img.FullName
    $report.Add('')
}
if ($report.Count -eq 0) { $report.Add('No look*.png images were found.') }
$report | Out-File (Join-Path $out 'looktest_measure.txt') -Encoding ascii
