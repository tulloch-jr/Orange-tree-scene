import os
import sys
import json
import time
import maya.cmds as cmds
import maya.api.OpenMaya as om

folder = 'C:/MayaScripts/OrangeTree'
scenes = folder + '/scenes'

LETTERS = {'bjoint_001': 'B', 'orange_13': 'O', 'fall_03': 'F', 'ground_mat': 'G', 'bark_mat': 'K',
           'grass_a': 'R', 'sky_physical': 'S', 'sky_ramp': 'Y', 'sun_light': 'U', 'render_cam_aim': 'C'}

def scan(path):
    needles = {m: ('"' + m + '"').encode() for m in LETTERS}
    keep = max(len(n) for n in needles.values()) + 2
    found = set()
    tail = b''
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            data = tail + chunk
            for m, n in needles.items():
                if m not in found and n in data:
                    found.add(m)
            tail = data[-keep:]
    return found

names = sorted(n for n in os.listdir(scenes) if n.lower().endswith('.ma'))
rows = []
for n in names:
    p = scenes + '/' + n
    rows.append([n, os.path.getsize(p) / 1048576, os.path.getmtime(p), scan(p)])

for row in rows:
    n, mb, mt, found = row
    if n == 'orange_tree_v010_wip.ma' and 'fall_03' not in found:
        os.rename(scenes + '/' + n, scenes + '/WRONG_' + n)
        row[0] = 'WRONG_' + n
        print('Renamed the wrong file', n, '->', row[0])

print()
print('Legend: B joints, O orange 13, F falling orange, G ground material, K bark, R grass,')
print('        S physical sky, Y sky ramp, U sun light, C camera constraint')
print(f'{"scene file":40} {"MB":>8}  {"saved":16}  markers')
for n, mb, mt, found in rows:
    marks = ''.join(LETTERS[m] if m in found else '.' for m in LETTERS)
    print(f'{n:40} {mb:8.1f}  {time.strftime("%Y-%m-%d %H:%M", time.localtime(mt)):16}  {marks}')

need = {'fall_03', 'grass_a', 'render_cam_aim'}
candidates = [r for r in rows if need <= r[3] and not r[0].startswith(('WRONG_', 'backup'))]
if not candidates:
    raise RuntimeError('No complete scene was found. Paste the table above and we will decide what to open.')
best = max(candidates, key=lambda r: ('sun_light' in r[3], r[2]))
target = scenes + '/' + best[0]
print()
print('Opening the newest complete scene:', target)

if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
if cmds.file(query=True, modified=True):
    cmds.file(rename=scenes + '/backup_before_open_' + time.strftime('%H%M') + '.ma')
    cmds.file(save=True, type='mayaAscii')
cmds.file(target, open=True, force=True)

with open(folder + '/tree_data.json') as f:
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
if folder not in sys.path:
    sys.path.append(folder)
cmds.currentTime(1)

print('Scene opened       :', cmds.file(query=True, sceneName=True))
print('Leaves / oranges   :', len(cmds.ls('leaf_0*', transforms=True)), '/', len(cmds.ls('orange_??', transforms=True)))
print('Fall groups / grass:', len(cmds.ls('fall_??', transforms=True)), '/', len([n for n in ('grass_a', 'grass_b') if cmds.objExists(n)]))
print('Dome lights / suns :', len(cmds.ls(type='aiSkyDomeLight')), '/', len(cmds.ls(type='directionalLight')))
print('Animation curves   :', len(cmds.ls(type='animCurve')))

pre = folder + '/scripts/stage10_step1_preflight.py'
if os.path.exists(pre):
    print()
    print('--- Preflight ---')
    exec(compile(open(pre).read(), pre, 'exec'))
