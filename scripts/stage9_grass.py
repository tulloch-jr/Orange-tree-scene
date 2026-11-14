import math
import random
import traceback
import maya.cmds as cmds
import maya.api.OpenMaya as om

WIND_ANGLE = 20
RADIUS = 420.0
ROOTS = 15000

for n in ('grass_test', 'grass_a', 'grass_b', 'grass_a_ai', 'grass_b_ai', 'grass_a_SG', 'grass_b_SG'):
    if cmds.objExists(n):
        cmds.delete(n)

def make_mesh(name, pts, counts, conn):
    fn = om.MFnMesh()
    obj = fn.create(om.MPointArray(pts), om.MIntArray(counts), om.MIntArray(conn))
    if obj.hasFn(om.MFn.kMesh):
        obj = om.MFnDagNode(obj).parent(0)
    return cmds.rename(om.MFnDagNode(obj).fullPathName(), name)

try:
    test_pts = [om.MPoint(0, 0, 0), om.MPoint(1, 0, 0), om.MPoint(1, 5, 0),
                om.MPoint(0, 5, 0), om.MPoint(0.5, 8, 0)]
    test_name = make_mesh('grass_test', test_pts, [4, 3], [0, 1, 2, 3, 3, 2, 4])
    print('Mesh creation test      : OK (' + test_name + ')')
    cmds.delete(test_name)
except Exception:
    print('Mesh creation test      : FAILED')
    print(traceback.format_exc())
    raise RuntimeError('Grass mesh creation failed. See the traceback printed above.')

cmds.currentTime(300)
rest = []
for grp in cmds.ls('fall_??', transforms=True):
    kids = cmds.listRelatives(grp, children=True, fullPath=True) or []
    if kids:
        b = cmds.exactWorldBoundingBox(kids[0] + '|orange_proto')
        rest.append(((b[0] + b[3]) / 2, (b[2] + b[5]) / 2))
cmds.currentTime(1)
print('Fallen oranges found    :', len(rest))

rng = random.Random(808)
wa = math.radians(WIND_ANGLE)
wind_x = math.cos(wa)
wind_z = math.sin(wa)
parts = {'a': ([], [], []), 'b': ([], [], [])}

def add_blade(part, x, z):
    pts, counts, conn = part
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
    base = len(pts)
    mx = x + bx * lean * 0.25
    mz = z + bz * lean * 0.25
    mw = w * 0.7
    pts.append(om.MPoint(x - wx * w / 2, 0.0, z - wz * w / 2))
    pts.append(om.MPoint(x + wx * w / 2, 0.0, z + wz * w / 2))
    pts.append(om.MPoint(mx - wx * mw / 2, h * 0.5, mz - wz * mw / 2))
    pts.append(om.MPoint(mx + wx * mw / 2, h * 0.5, mz + wz * mw / 2))
    pts.append(om.MPoint(x + bx * lean, h * 0.95, z + bz * lean))
    counts.extend([4, 3])
    conn.extend([base + i for i in (0, 1, 3, 2, 2, 3, 4)])

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
print('Blades generated        :', blades)

colors = {'a': (0.10, 0.28, 0.05), 'b': (0.17, 0.36, 0.07)}
for key in ('a', 'b'):
    pts, counts, conn = parts[key]
    try:
        mesh_name = make_mesh('grass_' + key, pts, counts, conn)
    except Exception:
        print(traceback.format_exc())
        raise RuntimeError('Could not create the grass_' + key + ' mesh. See the traceback above.')
    rgb = colors[key]
    ai = cmds.shadingNode('aiStandardSurface', asShader=True, name='grass_' + key + '_ai')
    cmds.setAttr(ai + '.baseColor', rgb[0], rgb[1], rgb[2], type='double3')
    cmds.setAttr(ai + '.diffuseRoughness', 0.6)
    cmds.setAttr(ai + '.specular', 0.2)
    cmds.setAttr(ai + '.specularRoughness', 0.5)
    for attr, value in (('transmission', 0.15), ('thinWalled', 1)):
        try:
            cmds.setAttr(ai + '.' + attr, value)
        except Exception:
            print('Skipped', attr)
    try:
        cmds.setAttr(ai + '.transmissionColor', rgb[0], rgb[1], rgb[2], type='double3')
    except Exception:
        print('Skipped transmissionColor')
    sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name='grass_' + key + '_SG')
    cmds.connectAttr(ai + '.outColor', sg + '.surfaceShader', force=True)
    cmds.sets(mesh_name, edit=True, forceElement=sg)
    shape = cmds.listRelatives(mesh_name, shapes=True, fullPath=True)[0]
    assigned = ('grass_' + key + '_SG') in (cmds.listSets(object=shape, type=1) or [])
    print(f'{mesh_name:24}: {cmds.polyEvaluate(mesh_name, face=True):,} faces | material assigned: {assigned}')
