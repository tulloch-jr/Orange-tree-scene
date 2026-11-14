import os
import sys
import json
import time
import maya.cmds as cmds
import maya.api.OpenMaya as om

FOLDER = 'C:/MayaScripts/OrangeTree'
SCENES = FOLDER + '/scenes'

def has_all(path, names):
    with open(path, 'rb') as f:
        data = f.read()
    return all(('"' + n + '"').encode() in data for n in names)

base = None
for fname in ('orange_tree_v010_wip.ma', 'orange_tree_v009_wip.ma', 'orange_tree_v008.ma'):
    p = SCENES + '/' + fname
    if os.path.exists(p) and has_all(p, ('fall_03', 'bjoint_001')):
        base = p
        break
if base is None:
    raise RuntimeError('No complete scene was found in ' + SCENES)
print('Opening', base)
if 'v008' in base:
    print('NOTE: this is the Stage 8 scene, so the ground, bark and lighting are missing. Run rebuild_stage9.py instead.')

if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.file(base, open=True, force=True)

with open(FOLDER + '/tree_data.json') as f:
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
if FOLDER not in sys.path:
    sys.path.append(FOLDER)
cmds.currentTime(1)

print('Leaves / oranges    :', len(cmds.ls('leaf_0*', transforms=True)), '/', len(cmds.ls('orange_??', transforms=True)))
print('Joints / fall groups:', len(cmds.ls('bjoint_*', transforms=True)), '/', len(cmds.ls('fall_??', transforms=True)))

STEPS = ('stage9_grass.py', 'stage10_step1_preflight.py')

def run_script(script_name):
    path = FOLDER + '/scripts/' + script_name
    if not os.path.exists(path):
        raise RuntimeError('missing file ' + script_name)
    with open(path) as f:
        code = f.read()
    exec(compile(code, path, 'exec'), globals())

def main():
    report = []
    for n, script_name in enumerate(STEPS, 1):
        print()
        print('===== [' + str(n) + '/' + str(len(STEPS)) + '] ' + script_name + ' =====')
        t0 = time.time()
        try:
            run_script(script_name)
            report.append((script_name, True, time.time() - t0, ''))
        except Exception as err:
            print('FAILED:', repr(err))
            report.append((script_name, False, time.time() - t0, repr(err)))
    return report

report = main()

print()
print('==================== SUMMARY ====================')
for script_name, ok, secs, err in report:
    print(('OK      ' if ok else 'FAILED  ') + f'{script_name:32} {secs / 60:5.1f} min  {err}')
print('Scene now           :', cmds.file(query=True, sceneName=True))
print('Fall groups / grass :', len(cmds.ls('fall_??', transforms=True)), '/',
      len([g for g in ('grass_a', 'grass_b') if cmds.objExists(g)]))
print('Scene files, Stage 9 and 10:')
for n in sorted(os.listdir(SCENES)):
    if n.startswith('orange_tree_v0') and n.lower().endswith('.ma') and int(n.split('_v')[1][:3]) >= 9:
        print(f'  {n:30} {os.path.getsize(SCENES + "/" + n) / 1048576:6.1f} MB')
