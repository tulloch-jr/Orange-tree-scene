import os
import maya.cmds as cmds

FOLDER = 'C:/MayaScripts/OrangeTree'
SCENES = FOLDER + '/scenes'
BASE = SCENES + '/orange_tree_v011.ma'
if not os.path.exists(BASE):
    raise RuntimeError('orange_tree_v011.ma was not found.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')

def set_if(node, attr, value):
    try:
        cmds.setAttr(node + '.' + attr, value)
    except Exception:
        pass

def disconnect_all(node, attr):
    src = cmds.listConnections(node + '.' + attr, source=True, destination=False, plugs=True) or []
    for s in src:
        cmds.disconnectAttr(s, node + '.' + attr)

def quick():
    opts = 'defaultArnoldRenderOptions'
    for attr, value in (('AASamples', 2), ('GIDiffuseSamples', 1), ('GISpecularSamples', 1),
                        ('GITransmissionSamples', 1), ('GISssSamples', 1), ('GIVolumeSamples', 1),
                        ('motion_blur_enable', 0)):
        set_if(opts, attr, value)
    cmds.currentTime(1)

def dome():
    return cmds.ls(type='aiSkyDomeLight')[0]

def sun():
    return cmds.ls(type='directionalLight')[0]

def base():
    pass

def no_texture():
    for mat, rgb in (('ground_mat', (0.15, 0.30, 0.08)), ('bark_mat', (0.12, 0.08, 0.05))):
        if cmds.objExists(mat):
            disconnect_all(mat, 'baseColor')
            disconnect_all(mat, 'normalCamera')
            cmds.setAttr(mat + '.baseColor', rgb[0], rgb[1], rgb[2], type='double3')

def const_dome():
    d = dome()
    disconnect_all(d, 'color')
    cmds.setAttr(d + '.color', 0.5, 0.6, 0.85, type='double3')

def sun_only():
    set_if(dome(), 'intensity', 0.0)

def dome_only():
    set_if(sun(), 'intensity', 0.0)

def extra_sun():
    shape = cmds.createNode('directionalLight', name='diag_downShape')
    tr = cmds.listRelatives(shape, parent=True)[0]
    cmds.setAttr(tr + '.rotateX', -90)
    cmds.setAttr(shape + '.intensity', 3.0)

def no_grass():
    for g in ('grass_a', 'grass_b'):
        if cmds.objExists(g):
            cmds.hide(g)

VARIANTS = [('diagA_base', base), ('diagB_no_texture', no_texture), ('diagC_const_dome', const_dome),
            ('diagD_sun_only', sun_only), ('diagE_dome_only', dome_only),
            ('diagF_extra_sun', extra_sun), ('diagG_no_grass', no_grass)]

for name, change in VARIANTS:
    cmds.file(BASE, open=True, force=True)
    quick()
    change()
    cmds.file(rename=SCENES + '/' + name + '.ma')
    cmds.file(save=True, type='mayaAscii')
    print('Prepared', name)

cmds.file(BASE, open=True, force=True)
print('Reopened', BASE)
