import maya.cmds as cmds

if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.setAttr('defaultRenderGlobals.currentRenderer', 'arnold', type='string')
try:
    import mtoa.core as mtoa_core
    mtoa_core.createOptions()
except Exception as err:
    print('Note: could not create the Arnold options node yet:', err)

if cmds.objExists('preview_sky'):
    cmds.delete('preview_sky')
shape = cmds.createNode('aiSkyDomeLight', name='preview_skyShape')
transform = cmds.listRelatives(shape, parent=True)[0]
cmds.rename(transform, 'preview_sky')
sky_shape = cmds.listRelatives('preview_sky', shapes=True)[0]
cmds.setAttr(sky_shape + '.intensity', 1.0)

cam_shape = cmds.listRelatives('render_cam', shapes=True)[0]
for cam in cmds.ls(type='camera'):
    cmds.setAttr(cam + '.renderable', 1 if cam == cam_shape else 0)

cmds.setAttr('defaultResolution.width', 960)
cmds.setAttr('defaultResolution.height', 540)
cmds.setAttr('defaultResolution.deviceAspectRatio', 960 / 540)

draft = {'AASamples': 2, 'GIDiffuseSamples': 1, 'GISpecularSamples': 1,
         'GITransmissionSamples': 1, 'GISssSamples': 1, 'GIVolumeSamples': 1}
applied = []
for attr, value in draft.items():
    try:
        cmds.setAttr('defaultArnoldRenderOptions.' + attr, value)
        applied.append(attr)
    except Exception:
        print('Could not set', attr)

cmds.currentTime(1)

print('Sky dome lights      :', len(cmds.ls(type='aiSkyDomeLight')))
print('Renderable camera    :', cam_shape)
print('Image size           :', cmds.getAttr('defaultResolution.width'), 'x',
      cmds.getAttr('defaultResolution.height'))
print('Draft settings set   :', len(applied), 'of', len(draft))
print('Current frame        :', cmds.currentTime(query=True))
print('Renderer             :', cmds.getAttr('defaultRenderGlobals.currentRenderer'))
