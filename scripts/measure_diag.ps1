Add-Type -AssemblyName System.Drawing
$out = 'C:\MayaScripts\OrangeTree\renders'
$report = New-Object System.Collections.Generic.List[string]
$report.Add('image                          bright    top R G B        middle R G B      bottom R G B')

function Get-RegionMean($bmp, $x0, $x1, $y0, $y1) {
    $n = 0; $r = 0.0; $g = 0.0; $b = 0.0
    for ($y = $y0; $y -lt $y1; $y += 2) {
        for ($x = $x0; $x -lt $x1; $x += 2) {
            $c = $bmp.GetPixel($x, $y)
            $r += $c.R; $g += $c.G; $b += $c.B; $n++
        }
    }
    if ($n -eq 0) { return @(0.0, 0.0, 0.0) }
    return @(($r / $n), ($g / $n), ($b / $n))
}

foreach ($img in Get-ChildItem $out -Filter 'diag*.png' | Sort-Object Name) {
    $bmp = New-Object System.Drawing.Bitmap $img.FullName
    $w = $bmp.Width
    $h = $bmp.Height
    $top = Get-RegionMean $bmp 0 $w 0 ([int]($h * 0.2))
    $mid = Get-RegionMean $bmp ([int]($w * 0.3)) ([int]($w * 0.7)) ([int]($h * 0.3)) ([int]($h * 0.7))
    $bot = Get-RegionMean $bmp 0 $w ([int]($h * 0.8)) $h
    $all = Get-RegionMean $bmp 0 $w 0 $h
    $lum = 0.2126 * $all[0] + 0.7152 * $all[1] + 0.0722 * $all[2]
    $line = ('{0,-30} {1,5:N0}    {2,4:N0} {3,4:N0} {4,4:N0}    {5,4:N0} {6,4:N0} {7,4:N0}    {8,4:N0} {9,4:N0} {10,4:N0}' -f $img.BaseName, $lum, $top[0], $top[1], $top[2], $mid[0], $mid[1], $mid[2], $bot[0], $bot[1], $bot[2])
    $report.Add($line)
    $bmp.Dispose()
}
if ($report.Count -eq 1) { $report.Add('No diag*.png images were found.') }
$report | Out-File (Join-Path $out 'diag_measure.txt') -Encoding ascii
