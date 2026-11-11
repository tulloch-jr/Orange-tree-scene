import os
import math
import random
import maya.cmds as cmds
import maya.api.OpenMaya as om

QUALITY = 'preview'

if not cmds.objExists('render_cam') or not cmds.objExists('ground'):
    raise RuntimeError('The scene is not open. Open orange_tree_v008.ma or orange_tree_v009_wip.ma first.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')
try:
    import mtoa.core as mtoa_core
    mtoa_core.createOptions()
except Exception as err:
    print('Note: Arnold options node:', err)

WIND_ANGLE = 20
results = []
skipped = []

def run(name, fn):
    try:
        detail = fn()
        results.append((name, True, detail or ''))
    except Exception as err:
        results.append((name, False, repr(err)))

def set_if(node, attr, value, string=False):
    try:
        if string:
            cmds.setAttr(f'{node}.{attr}', value, type='string')
        else:
            cmds.setAttr(f'{node}.{attr}', value)
    except Exception:
        skipped.append(f'{node}.{attr}')


def lighting():
    for n in ('preview_sky', 'sky_dome', 'sky_physical'):
        if cmds.objExists(n):
            cmds.delete(n)
    shape = cmds.createNode('aiSkyDomeLight', name='sky_domeShape')
    cmds.rename(cmds.listRelatives(shape, parent=True)[0], 'sky_dome')
    shape = cmds.listRelatives('sky_dome', shapes=True)[0]
    sky = cmds.createNode('aiPhysicalSky', name='sky_physical')
    set_if(sky, 'elevation', 38.0)
    set_if(sky, 'azimuth', 140.0)
    set_if(sky, 'intensity', 1.0)
    set_if(sky, 'sunSize', 1.5)
    cmds.connectAttr(sky + '.outColor', shape + '.color', force=True)
    set_if(shape, 'aiSamples', 3)
    return 'sky dome with physical sky, sun elevation 38 degrees'


def grass():
    for n in ('grass_a', 'grass_b', 'grass_a_ai', 'grass_b_ai', 'grass_a_SG', 'grass_b_SG'):
        if cmds.objExists(n):
            cmds.delete(n)

    cmds.currentTime(300)
    rest = []
    for grp in cmds.ls('fall_??', transforms=True):
        kids = cmds.listRelatives(grp, children=True, fullPath=True) or []
        if kids:
            b = cmds.exactWorldBoundingBox(kids[0] + '|orange_proto')
            rest.append(((b[0] + b[3]) / 2, (b[2] + b[5]) / 2))
    cmds.currentTime(1)

    rng = random.Random(808)
    RADIUS = 420.0
    ROOTS = 15000
    wa = math.radians(WIND_ANGLE)
    wind_x = math.cos(wa)
    wind_z = math.sin(wa)
    parts = {k: {'pts': om.MPointArray(), 'counts': om.MIntArray(), 'conn': om.MIntArray()}
             for k in ('a', 'b')}

    def add_blade(part, x, z):
        h = rng.uniform(4.0, 8.0)
        w = rng.uniform(0.35, 0.6)
        theta = rng.uniform(0, 2 * math.pi)
        wx = math.cos(theta)
        wz = math.sin(theta)
        bx = -wz + wind_x * 0.5
        bz = wx + wind_z * 0.5
        n = math.hypot(bx, bz)
        bx /= n
        bz /= n
        lean = rng.uniform(0.1, 0.5) * h
        pts = part['pts']
        base = pts.length()
        pts.append(om.MPoint(x - wx * w / 2, 0.0, z - wz * w / 2))
        pts.append(om.MPoint(x + wx * w / 2, 0.0, z + wz * w / 2))
        mx = x + bx * lean * 0.25
        mz = z + bz * lean * 0.25
        mw = w * 0.7
        pts.append(om.MPoint(mx - wx * mw / 2, h * 0.5, mz - wz * mw / 2))
        pts.append(om.MPoint(mx + wx * mw / 2, h * 0.5, mz + wz * mw / 2))
        pts.append(om.MPoint(x + bx * lean, h * 0.95, z + bz * lean))
        part['counts'].append(4)
        part['counts'].append(3)
        for i in (0, 1, 3, 2, 2, 3, 4):
            part['conn'].append(base + i)

    blades = 0
    for _ in range(ROOTS):
        r = RADIUS * math.sqrt(rng.random())
        ang = rng.uniform(0, 2 * math.pi)
        x = r * math.cos(ang)
        z = r * math.sin(ang)
        if math.hypot(x, z) < 26.0:
            continue
        if any(math.hypot(x - ox, z - oz) < 9.0 for ox, oz in rest):
            continue
        part = parts['a' if rng.random() < 0.5 else 'b']
        for _b in range(3):
            add_blade(part, x + rng.uniform(-1.5, 1.5), z + rng.uniform(-1.5, 1.5))
            blades += 1

    colors = {'a': (0.10, 0.28, 0.05), 'b': (0.17, 0.36, 0.07)}
    for key, part in parts.items():
        obj = om.MFnMesh().create(part['pts'], part['counts'], part['conn'])
        if obj.hasFn(om.MFn.kMesh):
            obj = om.MFnDagNode(obj).parent(0)
        cmds.rename(om.MFnDagNode(obj).partialPathName(), f'grass_{key}')

        rgb = colors[key]
        ai = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'grass_{key}_ai')
        cmds.setAttr(f'{ai}.baseColor', rgb[0], rgb[1], rgb[2], type='double3')
        cmds.setAttr(f'{ai}.diffuseRoughness', 0.6)
        cmds.setAttr(f'{ai}.specular', 0.2)
        cmds.setAttr(f'{ai}.specularRoughness', 0.5)
        set_if(ai, 'transmission', 0.15)
        cmds.setAttr(f'{ai}.transmissionColor', rgb[0], rgb[1], rgb[2], type='double3')
        set_if(ai, 'thinWalled', 1)
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f'grass_{key}_SG')
        cmds.connectAttr(f'{ai}.outColor', f'{sg}.surfaceShader', force=True)
        cmds.sets(f'grass_{key}', edit=True, forceElement=sg)

    return f'{blades} blades in 2 meshes, {len(rest)} fallen oranges kept clear'


def camera():
    if cmds.objExists('render_cam_aim'):
        cmds.delete('render_cam_aim')
    for obj in ('render_cam', 'camera_target'):
        if cmds.keyframe(obj, query=True, keyframeCount=True):
            cmds.cutKey(obj, clear=True)
    cmds.keyTangent(g=True, itt='spline', ott='spline')
    cmds.aimConstraint('camera_target', 'render_cam', aimVector=(0, 0, -1), upVector=(0, 1, 0),
                       worldUpType='vector', worldUpVector=(0, 1, 0), name='render_cam_aim')
    moves = ((1, -10, 1000, 320), (100, 5, 900, 260), (200, 15, 850, 210), (300, 25, 800, 170))
    for f, deg, radius, height in moves:
        a = math.radians(deg)
        cmds.setKeyframe('render_cam', attribute='translateX', time=f, value=radius * math.sin(a))
        cmds.setKeyframe('render_cam', attribute='translateY', time=f, value=height)
        cmds.setKeyframe('render_cam', attribute='translateZ', time=f, value=radius * math.cos(a))
    for f, y in ((1, 250), (150, 200), (300, 120)):
        cmds.setKeyframe('camera_target', attribute='translateY', time=f, value=y)
    seen = []
    for f in (1, 150, 300):
        cmds.currentTime(f)
        p = cmds.xform('render_cam', query=True, translation=True, worldSpace=True)
        seen.append(f'frame {f}: ({p[0]:.0f}, {p[1]:.0f}, {p[2]:.0f})')
    cmds.currentTime(1)
    return 'camera path ' + ' | '.join(seen)


def render_settings():
    final = (QUALITY == 'final')
    w, h = (1920, 1080) if final else (960, 540)
    cmds.setAttr('defaultResolution.width', w)
    cmds.setAttr('defaultResolution.height', h)
    cmds.setAttr('defaultResolution.deviceAspectRatio', w / h)
    cam_shape = cmds.listRelatives('render_cam', shapes=True)[0]
    for cam in cmds.ls(type='camera'):
        cmds.setAttr(cam + '.renderable', 1 if cam == cam_shape else 0)
    opts = 'defaultArnoldRenderOptions'
    levels = {'AASamples': 6 if final else 3, 'GIDiffuseSamples': 3 if final else 2,
              'GISpecularSamples': 3 if final else 2, 'GITransmissionSamples': 2,
              'GISssSamples': 3 if final else 2, 'GIVolumeSamples': 1}
    for attr, value in levels.items():
        set_if(opts, attr, value)
    set_if(opts, 'motion_blur_enable', 1 if final else 0)
    set_if(opts, 'motion_steps', 2)
    set_if(opts, 'motion_frames', 0.5)
    renders = 'C:/MayaScripts/OrangeTree/renders'
    os.makedirs(renders, exist_ok=True)
    set_if('defaultRenderGlobals', 'startFrame', 1)
    set_if('defaultRenderGlobals', 'endFrame', 300)
    set_if('defaultRenderGlobals', 'animation', 1)
    set_if('defaultRenderGlobals', 'putFrameBeforeExt', 1)
    set_if('defaultRenderGlobals', 'extensionPadding', 4)
    set_if('defaultRenderGlobals', 'imageFilePrefix', renders + '/orange', string=True)
    set_if('defaultArnoldDriver', 'aiTranslator', 'png', string=True)
    return f'{QUALITY}: {w} x {h}, frames 1 to 300, images to {renders}'


run('Lighting', lighting)
run('Grass', grass)
run('Camera animation', camera)
run('Render settings', render_settings)

cmds.playbackOptions(minTime=1, maxTime=300, animationStartTime=1, animationEndTime=300)
cmds.currentTime(1)

print()
for name, ok, detail in results:
    print(('OK      ' if ok else 'FAILED  ') + f'{name:18} {detail}')
if skipped:
    print('Settings this Maya/Arnold version did not accept:', ', '.join(skipped))
print('Sky dome lights :', len(cmds.ls(type='aiSkyDomeLight')))
print('Grass meshes    :', [n for n in ('grass_a', 'grass_b') if cmds.objExists(n)])
print('Camera keyframes:', cmds.keyframe('render_cam', query=True, keyframeCount=True))

scene_folder = 'C:/MayaScripts/OrangeTree/scenes'
os.makedirs(scene_folder, exist_ok=True)
cmds.file(rename=f'{scene_folder}/orange_tree_v009_wip.ma')
cmds.file(save=True, type='mayaAscii')
all_ok = all(ok for name, ok, detail in results)
if all_ok:
    cmds.file(rename=f'{scene_folder}/orange_tree_v009.ma')
    cmds.file(save=True, type='mayaAscii')
print('Saved:', cmds.file(query=True, sceneName=True))
print('Stage 9 result:', 'PASSED' if all_ok else 'CHECK THE FAILED LINES ABOVE')
