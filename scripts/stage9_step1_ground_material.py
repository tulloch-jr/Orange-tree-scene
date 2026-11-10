import os
import maya.cmds as cmds

if not cmds.objExists('ground'):
    raise RuntimeError('ground is missing. Open orange_tree_v008.ma first.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')

before = cmds.exactWorldBoundingBox('ground')

for node in ('ground_mat', 'ground_SG', 'ground_patch', 'ground_fine', 'ground_patch_uv',
             'ground_fine_uv', 'ground_remap', 'ground_blend', 'ground_bump'):
    if cmds.objExists(node):
        cmds.delete(node)

TILING = ('coverage', 'translateFrame', 'rotateFrame', 'mirrorU', 'mirrorV', 'stagger',
          'wrapU', 'wrapV', 'repeatUV', 'offset', 'rotateUV', 'noiseUV',
          'vertexUvOne', 'vertexUvTwo', 'vertexUvThree', 'vertexCameraOne')

def make_noise(name, repeat):
    place = cmds.shadingNode('place2dTexture', asUtility=True, name=f'{name}_uv')
    tex = cmds.shadingNode('noise', asTexture=True, name=name)
    cmds.setAttr(f'{place}.repeatUV', repeat, repeat, type='double2')
    cmds.connectAttr(f'{place}.outUV', f'{tex}.uv', force=True)
    cmds.connectAttr(f'{place}.outUvFilterSize', f'{tex}.uvFilterSize', force=True)
    for attr in TILING:
        if cmds.attributeQuery(attr, node=tex, exists=True):
            cmds.connectAttr(f'{place}.{attr}', f'{tex}.{attr}', force=True)
    return tex

patch = make_noise('ground_patch', 5)
fine = make_noise('ground_fine', 120)

remap = cmds.shadingNode('setRange', asUtility=True, name='ground_remap')
cmds.setAttr(f'{remap}.minX', 0)
cmds.setAttr(f'{remap}.maxX', 1)
cmds.setAttr(f'{remap}.oldMinX', 0.3)
cmds.setAttr(f'{remap}.oldMaxX', 0.7)
cmds.connectAttr(f'{patch}.outAlpha', f'{remap}.valueX', force=True)

blend = cmds.shadingNode('blendColors', asUtility=True, name='ground_blend')
cmds.setAttr(f'{blend}.color1', 0.09, 0.19, 0.04, type='double3')
cmds.setAttr(f'{blend}.color2', 0.30, 0.34, 0.09, type='double3')
cmds.connectAttr(f'{remap}.outValueX', f'{blend}.blender', force=True)

shader = cmds.shadingNode('aiStandardSurface', asShader=True, name='ground_mat')
cmds.setAttr(f'{shader}.base', 1.0)
cmds.setAttr(f'{shader}.diffuseRoughness', 0.6)
cmds.setAttr(f'{shader}.specular', 0.15)
cmds.setAttr(f'{shader}.specularRoughness', 0.8)
cmds.connectAttr(f'{blend}.output', f'{shader}.baseColor', force=True)

bump = cmds.shadingNode('bump2d', asUtility=True, name='ground_bump')
cmds.setAttr(f'{bump}.bumpDepth', 0.25)
cmds.connectAttr(f'{fine}.outAlpha', f'{bump}.bumpValue', force=True)
cmds.connectAttr(f'{bump}.outNormal', f'{shader}.normalCamera', force=True)

sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='ground_SG')
cmds.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)
cmds.sets('ground', edit=True, forceElement=sg)

shape = cmds.listRelatives('ground', shapes=True, fullPath=True)[0]
assigned = 'ground_SG' in (cmds.listSets(object=shape, type=1) or [])
after = cmds.exactWorldBoundingBox('ground')
moved = max(abs(a - b) for a, b in zip(before, after))

print('Arnold loaded        :', cmds.pluginInfo('mtoa', query=True, loaded=True))
print('Ground material      :', shader, '| assigned:', assigned)
print('Bump connected       :', cmds.isConnected(f'{bump}.outNormal', f'{shader}.normalCamera'))
print('Colour mix connected :', cmds.isConnected(f'{blend}.output', f'{shader}.baseColor'))
print('Ground geometry moved:', round(moved, 6), 'cm (should be 0)')
print('Ground height range  :', round(after[1], 4), 'to', round(after[4], 4), 'cm (should be 0 to 0)')

scene_folder = 'C:/MayaScripts/OrangeTree/scenes'
os.makedirs(scene_folder, exist_ok=True)
cmds.file(rename=f'{scene_folder}/orange_tree_v009_wip.ma')
cmds.file(save=True, type='mayaAscii')
print('Saved                :', cmds.file(query=True, sceneName=True))
