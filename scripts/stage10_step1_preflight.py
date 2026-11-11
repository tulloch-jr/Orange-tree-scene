import os
import maya.cmds as cmds

if not cmds.objExists('render_cam') or not cmds.objExists('ground'):
    raise RuntimeError('The scene is not open. Open orange_tree_v009.ma (or v009_wip) first.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')

QUALITY = 'final'
FOLDER = 'C:/MayaScripts/OrangeTree'
RENDERS = FOLDER + '/renders'

PRESETS = {
    'draft':   {'w': 640,  'h': 360, 'aa': 2, 'diffuse': 1, 'spec': 1, 'trans': 1, 'sss': 1, 'blur': 0},
    'preview': {'w': 960,  'h': 540, 'aa': 3, 'diffuse': 2, 'spec': 2, 'trans': 2, 'sss': 2, 'blur': 0},
    'final':   {'w': 1280, 'h': 720, 'aa': 5, 'diffuse': 2, 'spec': 2, 'trans': 2, 'sss': 2, 'blur': 1},
}
P = PRESETS[QUALITY]

skipped = []
checks = []

def set_if(node, attr, value, string=False):
    try:
        if string:
            cmds.setAttr(f'{node}.{attr}', value, type='string')
        else:
            cmds.setAttr(f'{node}.{attr}', value)
    except Exception:
        skipped.append(f'{node}.{attr}')

def check(name, ok, detail=''):
    checks.append((name, bool(ok), str(detail)))

os.makedirs(RENDERS, exist_ok=True)

cmds.setAttr('defaultResolution.width', P['w'])
cmds.setAttr('defaultResolution.height', P['h'])
cmds.setAttr('defaultResolution.deviceAspectRatio', P['w'] / P['h'])
cam_shape = cmds.listRelatives('render_cam', shapes=True)[0]
for cam in cmds.ls(type='camera'):
    cmds.setAttr(cam + '.renderable', 1 if cam == cam_shape else 0)

opts = 'defaultArnoldRenderOptions'
set_if(opts, 'AASamples', P['aa'])
set_if(opts, 'GIDiffuseSamples', P['diffuse'])
set_if(opts, 'GISpecularSamples', P['spec'])
set_if(opts, 'GITransmissionSamples', P['trans'])
set_if(opts, 'GISssSamples', P['sss'])
set_if(opts, 'GIVolumeSamples', 1)
set_if(opts, 'motion_blur_enable', P['blur'])
set_if(opts, 'motion_steps', 2)
set_if(opts, 'motion_frames', 0.5)
set_if('defaultRenderGlobals', 'startFrame', 1)
set_if('defaultRenderGlobals', 'endFrame', 300)
set_if('defaultRenderGlobals', 'animation', 1)
set_if('defaultRenderGlobals', 'putFrameBeforeExt', 1)
set_if('defaultRenderGlobals', 'extensionPadding', 4)
set_if('defaultRenderGlobals', 'imageFilePrefix', RENDERS + '/orange', string=True)
set_if('defaultArnoldDriver', 'aiTranslator', 'png', string=True)
cmds.playbackOptions(minTime=1, maxTime=300, animationStartTime=1, animationEndTime=300)
cmds.currentTime(1)

renderable = [c for c in cmds.ls(type='camera') if cmds.getAttr(c + '.renderable')]
check('One render camera', renderable == [cam_shape], renderable)
check('Arnold loaded', cmds.pluginInfo('mtoa', query=True, loaded=True))
domes = cmds.ls(type='aiSkyDomeLight')
suns = cmds.ls(type='directionalLight')
check('Sky dome and sun', len(domes) >= 1 and len(suns) >= 1, f'{len(domes)} dome, {len(suns)} sun')
sun_ok = bool(suns) and cmds.getAttr(suns[0] + '.intensity') > 0
check('Sun has light', sun_ok, cmds.getAttr(suns[0] + '.intensity') if suns else 'none')
check('Frame range 1 to 300', cmds.playbackOptions(query=True, minTime=True) == 1
      and cmds.playbackOptions(query=True, maxTime=True) == 300)
leaves = len(cmds.ls('leaf_0*', transforms=True))
oranges = len(cmds.ls('orange_??', transforms=True))
falls = len(cmds.ls('fall_??', transforms=True))
grass = [n for n in ('grass_a', 'grass_b') if cmds.objExists(n)]
check('816 leaves', leaves == 816, leaves)
check('13 hanging oranges', oranges == 13, oranges)
check('8 fall groups', falls == 8, falls)
check('2 grass meshes', len(grass) == 2, grass)

expressions = cmds.ls(type='expression')
extra_scripts = [s for s in cmds.ls(type='script')
                 if s not in ('sceneConfigurationScriptNode', 'uiConfigurationScriptNode')]
curves = len(cmds.ls(type='animCurve'))
check('No expressions', not expressions, len(expressions))
check('No script nodes', not extra_scripts, len(extra_scripts))
check('Animation is keyframed', curves > 1000, f'{curves} animation curves')

faces = 0
for path in cmds.ls(type='mesh', long=True):
    try:
        faces += cmds.polyEvaluate(path, face=True)
    except Exception:
        pass
check('Polygons to render counted', faces > 0, f'{faces:,} faces (instances counted)')

try:
    test_file = RENDERS + '/.write_test'
    with open(test_file, 'w') as f:
        f.write('ok')
    os.remove(test_file)
    check('Output folder writable', True, RENDERS)
except Exception as err:
    check('Output folder writable', False, err)

ps1 = r"""param(
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
"""
with open(FOLDER + '/scripts/render_frames.ps1', 'w') as f:
    f.write(ps1)
check('Batch render script written', os.path.exists(FOLDER + '/scripts/render_frames.ps1'), 'scripts/render_frames.ps1')

print(f'Quality preset: {QUALITY} ({P["w"]} x {P["h"]}, AA {P["aa"]}, motion blur {"on" if P["blur"] else "off"})')
print()
for name, ok, detail in checks:
    print(('OK      ' if ok else 'FAILED  ') + f'{name:28} {detail}')
if skipped:
    print()
    print('Settings this Maya/Arnold version did not accept:', ', '.join(skipped))

scene_folder = FOLDER + '/scenes'
os.makedirs(scene_folder, exist_ok=True)
cmds.file(rename=scene_folder + '/orange_tree_v010_wip.ma')
cmds.file(save=True, type='mayaAscii')
all_ok = all(ok for name, ok, detail in checks)
if all_ok:
    cmds.file(rename=scene_folder + '/orange_tree_v010.ma')
    cmds.file(save=True, type='mayaAscii')
print()
print('Saved:', cmds.file(query=True, sceneName=True))
print('Stage 10 step 1 result:', 'PASSED' if all_ok else 'CHECK THE FAILED LINES ABOVE')
