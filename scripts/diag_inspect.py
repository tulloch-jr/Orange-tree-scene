import os
import math
import maya.cmds as cmds
import maya.api.OpenMaya as om

BASE = 'C:/MayaScripts/OrangeTree/scenes/orange_tree_v011.ma'
if not os.path.exists(BASE):
    raise RuntimeError('orange_tree_v011.ma was not found.')
if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.file(BASE, open=True, force=True)
cmds.currentTime(1)

def val(node, attr):
    try:
        return cmds.getAttr(node + '.' + attr)
    except Exception:
        return 'n/a'

def first_shape(obj):
    shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
    return shapes[0] if shapes else None

print('=' * 70)
print('1. SHADER TYPES USED BY OBJECTS (Arnold draws unsupported ones black)')
types = {}
for sg in cmds.ls(type='shadingEngine'):
    members = cmds.sets(sg, query=True) or []
    if not members:
        continue
    src = cmds.listConnections(sg + '.surfaceShader', source=True, destination=False) or []
    node_type = cmds.nodeType(src[0]) if src else 'none'
    types.setdefault(node_type, []).append((sg, len(members)))
for node_type, items in sorted(types.items()):
    flag = '' if node_type == 'aiStandardSurface' else '   <-- check this'
    print(f'   {node_type:20} {len(items):3} groups{flag}')
    if node_type != 'aiStandardSurface':
        for sg, n in items:
            print(f'        {sg} ({n} objects)')

print()
print('2. THE GROUND')
gshape = first_shape('ground')
print('   shading groups     :', cmds.listSets(object=gshape, type=1) if gshape else 'no shape')
for sg in (cmds.listSets(object=gshape, type=1) or []) if gshape else []:
    src = cmds.listConnections(sg + '.surfaceShader', source=True, destination=False) or []
    kind = cmds.nodeType(src[0]) if src else ''
    print('   ground shader      :', src[0] if src else 'none', '(' + kind + ')')
print('   visibility         :', val('ground', 'visibility'), '| primaryVisibility:', val(gshape, 'primaryVisibility') if gshape else 'n/a')
print('   rampShader nodes   :', len(cmds.ls(type='rampShader')))

print()
print('3. THE CAMERA AT FRAME 1')
cam = 'render_cam'
cshape = first_shape(cam)
focal = val(cshape, 'focalLength')
hfa = val(cshape, 'horizontalFilmAperture')
vfa = val(cshape, 'verticalFilmAperture')
print('   renderable cameras :', [c for c in cmds.ls(type='camera') if val(c, 'renderable')])
print('   focal / near / far :', focal, '/', val(cshape, 'nearClipPlane'), '/', val(cshape, 'farClipPlane'))
pos = om.MVector(*cmds.xform(cam, query=True, translation=True, worldSpace=True))
m = cmds.xform(cam, query=True, matrix=True, worldSpace=True)
xa = om.MVector(m[0], m[1], m[2])
ya = om.MVector(m[4], m[5], m[6])
za = om.MVector(m[8], m[9], m[10])
print('   position           :', [round(c, 1) for c in (pos.x, pos.y, pos.z)])
print('   looking direction  :', [round(c, 2) for c in (-za.x, -za.y, -za.z)])
tan_h = (hfa * 25.4 / 2.0) / focal
tan_v = (vfa * 25.4 / 2.0) / focal
print(f'   field of view      : {math.degrees(2 * math.atan(tan_h)):.0f} degrees wide, {math.degrees(2 * math.atan(tan_v)):.0f} degrees tall')
points = (('trunk base', (0, 0, 0)), ('trunk top', (0, 180, 0)), ('canopy top', (0, 500, 0)),
          ('canopy left', (-220, 300, 0)), ('canopy right', (220, 300, 0)))
print('   tree points on screen (inside the picture when x and y are both between -1 and 1):')
for label, p in points:
    d = om.MVector(*p) - pos
    depth = -(d * za)
    if depth <= 0:
        print(f'      {label:13} BEHIND the camera')
        continue
    sx = (d * xa) / depth / tan_h
    sy = (d * ya) / depth / tan_v
    print(f'      {label:13} x {sx:6.2f}  y {sy:6.2f}   distance {depth:6.0f} cm')

print()
print('4. VISIBILITY')
for obj in ('ground', 'trunk_guide', 'tree_branches_grp', 'leaf_0001', 'orange_01', 'grass_a', 'sky_dome', 'sun_light'):
    if not cmds.objExists(obj):
        print(f'   {obj:18} MISSING')
        continue
    shp = first_shape(obj)
    prim = val(shp, 'primaryVisibility') if shp else 'n/a'
    print(f'   {obj:18} visibility {val(obj, "visibility")} | primaryVisibility {prim}')
hidden_prim = [s for s in cmds.ls(type='mesh', long=True) if val(s, 'primaryVisibility') is False]
print('   meshes with primaryVisibility off:', len(hidden_prim))

print()
print('5. ARNOLD DEBUG FLAGS (all should be 0 / False)')
opts = 'defaultArnoldRenderOptions'
flag_names = [a for a in (cmds.listAttr(opts) or []) if a.lower().startswith(('ignore', 'abort'))]
if not flag_names:
    print('   none found')
for a in flag_names:
    print(f'   {a:30} {val(opts, a)}')
print('   renderer           :', val('defaultRenderGlobals', 'currentRenderer'))

print()
print('6. LIGHTS')
for shape in cmds.ls(type='aiSkyDomeLight') + cmds.ls(type='directionalLight'):
    tr = cmds.listRelatives(shape, parent=True)[0]
    print(f'   {tr} ({cmds.nodeType(shape)})')
    print('      intensity / color     :', val(shape, 'intensity'), '/', val(shape, 'color'))
    print('      visibility            :', val(tr, 'visibility'))
    print('      rotate                :', [round(c, 1) for c in cmds.xform(tr, query=True, rotation=True)])
    print('      scale                 :', [round(c, 2) for c in cmds.xform(tr, query=True, scale=True, relative=True)])
    print('      illuminates by default:', val(shape, 'illuminatesByDefault'))
    print('      diffuse / specular x  :', val(shape, 'aiDiffuse'), '/', val(shape, 'aiSpecular'))
print('   members of defaultLightSet :', len(cmds.sets('defaultLightSet', query=True) or []))
print('=' * 70)
print('Done. Nothing was changed or saved.')
