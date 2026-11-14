import os
import sys
import json
import maya.cmds as cmds
import maya.api.OpenMaya as om

FOLDER = 'C:/MayaScripts/OrangeTree'
SCENES = FOLDER + '/scenes'
NEEDED = ('fall_03', 'grass_a', 'render_cam_aim', 'sun_light', 'ground_mat', 'bark_mat')

def has_all(path, names):
    with open(path, 'rb') as f:
        data = f.read()
    return all(('"' + n + '"').encode() in data for n in names)

def find_scene():
    found = []
    for fname in os.listdir(SCENES):
        if fname.lower().endswith('.ma') and not fname.startswith(('WRONG_', 'backup')):
            p = SCENES + '/' + fname
            if has_all(p, NEEDED):
                found.append((os.path.getmtime(p), p))
    return max(found)[1] if found else None

base = find_scene()
if base is None:
    print('No finished scene found yet. Running finish_stage9.py first (a few minutes)...')
    fpath = FOLDER + '/scripts/finish_stage9.py'
    if not os.path.exists(fpath):
        raise RuntimeError('finish_stage9.py is missing. Run the finish_stage9 block from my earlier message first.')
    with open(fpath) as f:
        code = f.read()
    exec(compile(code, fpath, 'exec'), globals())
    base = find_scene()
if base is None:
    raise RuntimeError('Still no finished scene. Paste the output above so we can fix the grass step.')

print()
print('Opening', base)
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.file(base, open=True, force=True)

with open(FOLDER + '/tree_data.json') as f:
    payload = json.load(f)
TREE = payload['TREE']
TREE.setdefault('wind_speed', 800.0)
TREE.setdefault('wind_angle', 20)
data = [(om.MVector(*s), om.MVector(*e), d) for s, e, d in payload['data']]

try:
    import mtoa.core as mtoa_core
    mtoa_core.createOptions()
except Exception as err:
    print('Note: Arnold options node:', err)
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')
if FOLDER not in sys.path:
    sys.path.append(FOLDER)

skipped = []

def set_if(node, attr, value, string=False):
    try:
        if string:
            cmds.setAttr(node + '.' + attr, value, type='string')
        else:
            cmds.setAttr(node + '.' + attr, value)
    except Exception:
        skipped.append(node + '.' + attr)

def read_if(node, attr):
    try:
        return cmds.getAttr(node + '.' + attr)
    except Exception:
        return 'n/a'

cmds.setAttr('defaultResolution.width', 1920)
cmds.setAttr('defaultResolution.height', 1080)
cmds.setAttr('defaultResolution.deviceAspectRatio', 1920 / 1080)
cam_shape = cmds.listRelatives('render_cam', shapes=True)[0]
for cam in cmds.ls(type='camera'):
    cmds.setAttr(cam + '.renderable', 1 if cam == cam_shape else 0)

opts = 'defaultArnoldRenderOptions'
for attr, value in (('AASamples', 8), ('GIDiffuseSamples', 3), ('GISpecularSamples', 3),
                    ('GITransmissionSamples', 3), ('GISssSamples', 3), ('GIVolumeSamples', 2),
                    ('motion_blur_enable', 1), ('motion_steps', 2), ('motion_frames', 0.5)):
    set_if(opts, attr, value)

for shape in cmds.ls(type='aiSkyDomeLight'):
    set_if(shape, 'aiSamples', 4)
for shape in cmds.ls(type='directionalLight'):
    set_if(shape, 'aiSamples', 3)

set_if('defaultRenderGlobals', 'startFrame', 1)
set_if('defaultRenderGlobals', 'endFrame', 300)
set_if('defaultRenderGlobals', 'animation', 1)
set_if('defaultRenderGlobals', 'putFrameBeforeExt', 1)
set_if('defaultRenderGlobals', 'extensionPadding', 4)
set_if('defaultArnoldDriver', 'aiTranslator', 'png', string=True)

smoothed = 0
for t in ['trunk_guide'] + cmds.ls('branch_???', transforms=True):
    shapes = cmds.listRelatives(t, shapes=True, fullPath=True) or []
    if not shapes:
        continue
    try:
        cmds.setAttr(shapes[0] + '.aiSubdivType', 1)
        cmds.setAttr(shapes[0] + '.aiSubdivIterations', 3 if t == 'trunk_guide' else 2)
        smoothed += 1
    except Exception:
        skipped.append('aiSubdivType / aiSubdivIterations on the branch shapes')
        break

cmds.playbackOptions(minTime=1, maxTime=300, animationStartTime=1, animationEndTime=300)
cmds.currentTime(1)

os.makedirs(FOLDER + '/renders', exist_ok=True)
cmds.file(rename=SCENES + '/orange_tree_v011.ma')
cmds.file(save=True, type='mayaAscii')

print()
print('CINEMA QUALITY SCENE')
print('  Image size              :', cmds.getAttr('defaultResolution.width'), 'x', cmds.getAttr('defaultResolution.height'))
print('  Anti-aliasing samples   :', read_if(opts, 'AASamples'))
print('  Diffuse / spec / trans  :', read_if(opts, 'GIDiffuseSamples'), '/', read_if(opts, 'GISpecularSamples'), '/', read_if(opts, 'GITransmissionSamples'))
print('  Motion blur             :', read_if(opts, 'motion_blur_enable'))
print('  Branch shapes smoothed  :', smoothed)
print('  Leaves / oranges        :', len(cmds.ls('leaf_0*', transforms=True)), '/', len(cmds.ls('orange_??', transforms=True)))
print('  Fall groups / grass     :', len(cmds.ls('fall_??', transforms=True)), '/', len([g for g in ('grass_a', 'grass_b') if cmds.objExists(g)]))
print('  Dome lights / suns      :', len(cmds.ls(type='aiSkyDomeLight')), '/', len(cmds.ls(type='directionalLight')))
if skipped:
    print('  Settings this Maya/Arnold version did not accept:')
    for s in skipped:
        print('    ', s)
print('  Saved                   :', cmds.file(query=True, sceneName=True))
