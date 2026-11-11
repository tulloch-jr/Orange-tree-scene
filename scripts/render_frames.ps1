param(
    [int]$Start = 1,
    [int]$End = 1,
    [string]$Name = 'orange',
    [string]$Scene = 'C:\MayaScripts\OrangeTree\scenes\orange_tree_v010.ma'
)

$render = 'C:\Program Files\Autodesk\Maya2023\bin\Render.exe'
$out = 'C:\MayaScripts\OrangeTree\renders'
New-Item -ItemType Directory -Force -Path $out | Out-Null

$watch = [System.Diagnostics.Stopwatch]::StartNew()
& $render -r arnold -s $Start -e $End -b 1 -rd $out -im $Name -of png -pad 4 -cam render_cam $Scene
$watch.Stop()
Write-Host ('Rendered frames {0} to {1} in {2:N1} minutes' -f $Start, $End, $watch.Elapsed.TotalMinutes)
