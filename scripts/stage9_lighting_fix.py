import os
import maya.cmds as cmds

if not cmds.objExists('render_cam'):
    raise RuntimeError('The scene is not open. Open orange_tree_v009_wip.ma (or v008) first.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')

skipped = []

def set_if(node, attr, value, string=False):
    try:
        if string:
            cmds.setAttr(f'{node}.{attr}', value, type='string')
        else:
            cmds.setAttr(f'{node}.{attr}', value)
    except Exception:
        skipped.append(f'{node}.{attr}')

def describe_lights(title):
    print(title)
    found = 0
    for kind in ('aiSkyDomeLight', 'directionalLight', 'aiAreaLight', 'pointLight', 'spotLight', 'areaLight'):
        for shape in cmds.ls(type=kind):
            found += 1
            try:
                intensity = round(cmds.getAttr(shape + '.intensity'), 3)
            except Exception:
                intensity = 'n/a'
            src = cmds.listConnections(shape + '.color', source=True, destination=False) or []
            print(f'  {shape:22} {kind:16} intensity {intensity} | colour from: {src[0] if src else "constant"}')
    if not found:
        print('  (no lights at all)')
    return found

def colour_info():
    for label, flag in (('colour management on', 'cmEnabled'), ('rendering space', 'renderingSpaceName'),
                        ('view transform', 'viewTransformName')):
        try:
            print(f'  {label:20}:', cmds.colorManagementPrefs(query=True, **{flag: True}))
        except Exception as err:
            print(f'  {label:20}: could not read ({err})')

before = describe_lights('LIGHTS BEFORE')
print('COLOUR SETTINGS')
colour_info()
print()

for n in ('preview_sky', 'sky_dome', 'sky_physical', 'sky_ramp', 'sun_light'):
    if cmds.objExists(n):
        cmds.delete(n)

dome_shape = cmds.createNode('aiSkyDomeLight', name='sky_domeShape')
cmds.rename(cmds.listRelatives(dome_shape, parent=True)[0], 'sky_dome')
dome_shape = cmds.listRelatives('sky_dome', shapes=True)[0]

ramp = cmds.createNode('ramp', name='sky_ramp')
stops = ((0.0, (0.22, 0.20, 0.17)), (0.5, (0.80, 0.88, 0.98)), (1.0, (0.18, 0.40, 0.85)))
for i, (pos, rgb) in enumerate(stops):
    cmds.setAttr(f'{ramp}.colorEntryList[{i}].position', pos)
    cmds.setAttr(f'{ramp}.colorEntryList[{i}].color', rgb[0], rgb[1], rgb[2], type='double3')
set_if(ramp, 'interpolation', 1)
cmds.connectAttr(ramp + '.outColor', dome_shape + '.color', force=True)
set_if(dome_shape, 'intensity', 1.2)
set_if(dome_shape, 'aiSamples', 3)

sun_shape = cmds.createNode('directionalLight', name='sun_lightShape')
cmds.rename(cmds.listRelatives(sun_shape, parent=True)[0], 'sun_light')
sun_shape = cmds.listRelatives('sun_light', shapes=True)[0]
cmds.setAttr('sun_light.rotateX', -40)
cmds.setAttr('sun_light.rotateY', -45)
cmds.setAttr('sun_light.rotateZ', 0)
cmds.setAttr(sun_shape + '.color', 1.0, 0.93, 0.80, type='double3')
cmds.setAttr(sun_shape + '.intensity', 3.5)
set_if(sun_shape, 'aiAngle', 0.6)
set_if(sun_shape, 'aiSamples', 2)

cmds.currentTime(1)
after = describe_lights('LIGHTS AFTER')
if skipped:
    print('Settings this Maya/Arnold version did not accept:', ', '.join(skipped))

scene_folder = f'{folder}/scenes'
os.makedirs(scene_folder, exist_ok=True)
cmds.file(rename=f'{scene_folder}/orange_tree_v009_wip.ma')
cmds.file(save=True, type='mayaAscii')
print('Saved:', cmds.file(query=True, sceneName=True))
print('Lighting rebuilt:', 'OK' if after == 2 else 'CHECK: expected 2 lights, found ' + str(after))
