import os
import maya.cmds as cmds

FOLDER = 'C:/MayaScripts/OrangeTree'
SCENES = FOLDER + '/scenes'
BASE = SCENES + '/orange_tree_v011.ma'
OUT = SCENES + '/orange_tree_v012.ma'
if not os.path.exists(BASE):
    raise RuntimeError('orange_tree_v011.ma was not found.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')

def set_if(node, attr, value):
    try:
        cmds.setAttr(node + '.' + attr, value)
    except Exception:
        pass

def link(shape):
    parent = cmds.listRelatives(shape, parent=True)[0]
    members = cmds.sets('defaultLightSet', query=True) or []
    if shape in members or parent in members:
        return 'already linked'
    try:
        cmds.sets(shape, add='defaultLightSet')
    except Exception:
        pass
    members = cmds.sets('defaultLightSet', query=True) or []
    if shape in members or parent in members:
        return 'linked with sets'
    for src in (shape + '.instObjGroups', shape + '.instObjGroups[0]'):
        try:
            cmds.connectAttr(src, 'defaultLightSet.dagSetMembers', nextAvailable=True)
            break
        except Exception:
            continue
    members = cmds.sets('defaultLightSet', query=True) or []
    return 'linked with connectAttr' if (shape in members or parent in members) else 'FAILED'

cmds.file(BASE, open=True, force=True)
lights = cmds.ls(type='aiSkyDomeLight') + cmds.ls(type='directionalLight')
if not lights:
    raise RuntimeError('No lights were found in the scene.')
print('Lights found              :', lights)
print('In defaultLightSet before :', len(cmds.sets('defaultLightSet', query=True) or []))
for shape in lights:
    print('   ', shape, '->', link(shape))
members = cmds.sets('defaultLightSet', query=True) or []
print('In defaultLightSet after  :', len(members), members)
if len(members) < len(lights):
    raise RuntimeError('The lights could not be linked. Paste the output above.')
cmds.currentTime(1)
cmds.file(rename=OUT)
cmds.file(save=True, type='mayaAscii')
print('Saved', OUT)

def dome():
    return cmds.ls(type='aiSkyDomeLight')[0]

def sun():
    return cmds.ls(type='directionalLight')[0]

VARIANTS = [('light1_sun3p5_dome1p2', 3.5, 1.2), ('light2_sun2p0_dome0p8', 2.0, 0.8),
            ('light3_sun1p5_dome0p6', 1.5, 0.6), ('light4_sun3p0_dome0p5', 3.0, 0.5)]
for name, sun_i, dome_i in VARIANTS:
    cmds.file(OUT, open=True, force=True)
    opts = 'defaultArnoldRenderOptions'
    for attr, value in (('AASamples', 3), ('GIDiffuseSamples', 2), ('GISpecularSamples', 2),
                        ('GITransmissionSamples', 1), ('GISssSamples', 1), ('GIVolumeSamples', 1),
                        ('motion_blur_enable', 0)):
        set_if(opts, attr, value)
    set_if(sun(), 'intensity', sun_i)
    set_if(dome(), 'intensity', dome_i)
    cmds.currentTime(1)
    cmds.file(rename=SCENES + '/' + name + '.ma')
    cmds.file(save=True, type='mayaAscii')
    print('Prepared', name)

cmds.file(OUT, open=True, force=True)
print('Reopened', OUT)
