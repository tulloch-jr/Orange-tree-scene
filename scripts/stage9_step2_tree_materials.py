import os
import maya.cmds as cmds

for name in ('trunk_guide', 'leaf_light_SG', 'leaf_medium_SG', 'leaf_dark_SG', 'stem_matSG'):
    if not cmds.objExists(name):
        raise RuntimeError(name + ' is missing. Open orange_tree_v008.ma or orange_tree_v009_wip.ma first.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')

for node in ('bark_mat', 'bark_SG', 'bark_noise', 'bark_noise_uv', 'bark_detail',
             'bark_detail_uv', 'bark_remap', 'bark_blend', 'bark_bump',
             'leaf_light_ai', 'leaf_medium_ai', 'leaf_dark_ai', 'stem_ai'):
    if cmds.objExists(node):
        cmds.delete(node)

TILING = ('coverage', 'translateFrame', 'rotateFrame', 'mirrorU', 'mirrorV', 'stagger',
          'wrapU', 'wrapV', 'repeatUV', 'offset', 'rotateUV', 'noiseUV',
          'vertexUvOne', 'vertexUvTwo', 'vertexUvThree', 'vertexCameraOne')

def make_noise(name, repeat_u, repeat_v):
    place = cmds.shadingNode('place2dTexture', asUtility=True, name=f'{name}_uv')
    tex = cmds.shadingNode('noise', asTexture=True, name=name)
    cmds.setAttr(f'{place}.repeatUV', repeat_u, repeat_v, type='double2')
    cmds.connectAttr(f'{place}.outUV', f'{tex}.uv', force=True)
    cmds.connectAttr(f'{place}.outUvFilterSize', f'{tex}.uvFilterSize', force=True)
    for attr in TILING:
        if cmds.attributeQuery(attr, node=tex, exists=True):
            cmds.connectAttr(f'{place}.{attr}', f'{tex}.{attr}', force=True)
    return tex

noise = make_noise('bark_noise', 18, 2)
detail = make_noise('bark_detail', 60, 6)

remap = cmds.shadingNode('setRange', asUtility=True, name='bark_remap')
cmds.setAttr(f'{remap}.minX', 0)
cmds.setAttr(f'{remap}.maxX', 1)
cmds.setAttr(f'{remap}.oldMinX', 0.35)
cmds.setAttr(f'{remap}.oldMaxX', 0.65)
cmds.connectAttr(f'{noise}.outAlpha', f'{remap}.valueX', force=True)

blend = cmds.shadingNode('blendColors', asUtility=True, name='bark_blend')
cmds.setAttr(f'{blend}.color1', 0.07, 0.045, 0.03, type='double3')
cmds.setAttr(f'{blend}.color2', 0.24, 0.18, 0.13, type='double3')
cmds.connectAttr(f'{remap}.outValueX', f'{blend}.blender', force=True)

bark = cmds.shadingNode('aiStandardSurface', asShader=True, name='bark_mat')
cmds.setAttr(f'{bark}.base', 1.0)
cmds.setAttr(f'{bark}.diffuseRoughness', 0.8)
cmds.setAttr(f'{bark}.specular', 0.1)
cmds.setAttr(f'{bark}.specularRoughness', 0.9)
cmds.connectAttr(f'{blend}.output', f'{bark}.baseColor', force=True)

bump = cmds.shadingNode('bump2d', asUtility=True, name='bark_bump')
cmds.setAttr(f'{bump}.bumpDepth', 0.5)
cmds.connectAttr(f'{detail}.outAlpha', f'{bump}.bumpValue', force=True)
cmds.connectAttr(f'{bump}.outNormal', f'{bark}.normalCamera', force=True)

bark_sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='bark_SG')
cmds.connectAttr(f'{bark}.outColor', f'{bark_sg}.surfaceShader', force=True)

tubes = cmds.ls('branch_???', transforms=True)
targets = ['trunk_guide'] + tubes
cmds.sets(targets, edit=True, forceElement=bark_sg)

LEAVES = (('leaf_light', (0.24, 0.60, 0.12)),
          ('leaf_medium', (0.10, 0.45, 0.10)),
          ('leaf_dark', (0.05, 0.30, 0.08)))
for base, rgb in LEAVES:
    ai = cmds.shadingNode('aiStandardSurface', asShader=True, name=f'{base}_ai')
    cmds.setAttr(f'{ai}.baseColor', rgb[0], rgb[1], rgb[2], type='double3')
    cmds.setAttr(f'{ai}.base', 0.8)
    cmds.setAttr(f'{ai}.diffuseRoughness', 0.4)
    cmds.setAttr(f'{ai}.specular', 0.35)
    cmds.setAttr(f'{ai}.specularRoughness', 0.35)
    cmds.setAttr(f'{ai}.transmission', 0.25)
    cmds.setAttr(f'{ai}.transmissionColor', rgb[0], rgb[1], rgb[2], type='double3')
    cmds.setAttr(f'{ai}.thinWalled', 1)
    cmds.connectAttr(f'{ai}.outColor', f'{base}_SG.surfaceShader', force=True)
    if cmds.objExists(f'{base}_mat'):
        cmds.delete(f'{base}_mat')

stem = cmds.shadingNode('aiStandardSurface', asShader=True, name='stem_ai')
cmds.setAttr(f'{stem}.baseColor', 0.22, 0.33, 0.09, type='double3')
cmds.setAttr(f'{stem}.diffuseRoughness', 0.6)
cmds.setAttr(f'{stem}.specular', 0.2)
cmds.setAttr(f'{stem}.specularRoughness', 0.6)
cmds.connectAttr(f'{stem}.outColor', 'stem_matSG.surfaceShader', force=True)
if cmds.objExists('stem_mat'):
    cmds.delete('stem_mat')

bark_count = 0
for t in targets:
    shape = cmds.listRelatives(t, shapes=True, fullPath=True)[0]
    if 'bark_SG' in (cmds.listSets(object=shape, type=1) or []):
        bark_count += 1

leaf_groups = ('leaf_light_SG', 'leaf_medium_SG', 'leaf_dark_SG')
counts = {g: 0 for g in leaf_groups}
for lf in cmds.ls('leaf_0*', transforms=True):
    shape = cmds.listRelatives(lf, shapes=True, fullPath=True)[0]
    for s in (cmds.listSets(object=shape, type=1) or []):
        if s in counts:
            counts[s] += 1

def shader_type(group):
    src = cmds.listConnections(f'{group}.surfaceShader', source=True, destination=False)
    return cmds.nodeType(src[0]) if src else 'none'

print('Bark                 : objects with bark', bark_count, 'of', len(targets))
for g in leaf_groups:
    print(f'{g:15}      : {shader_type(g)} | {counts[g]} leaves')
print('Stem and sepals      :', shader_type('stem_matSG'))
print('Bark shading group   :', shader_type('bark_SG'))
print('Leaves with material :', sum(counts.values()), 'of 816')

ok = (bark_count == len(targets) and sum(counts.values()) == 816
      and all(shader_type(g) == 'aiStandardSurface' for g in leaf_groups + ('stem_matSG', 'bark_SG')))
print('Step result          :', 'PASSED' if ok else 'CHECK ABOVE')

scene_folder = 'C:/MayaScripts/OrangeTree/scenes'
os.makedirs(scene_folder, exist_ok=True)
cmds.file(rename=f'{scene_folder}/orange_tree_v009_wip.ma')
cmds.file(save=True, type='mayaAscii')
print('Saved                :', cmds.file(query=True, sceneName=True))
