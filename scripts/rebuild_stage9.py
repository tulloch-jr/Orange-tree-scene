import os
import sys
import json
import time
import maya.cmds as cmds
import maya.api.OpenMaya as om

folder = 'C:/MayaScripts/OrangeTree'
scenes = folder + '/scenes'
base = scenes + '/orange_tree_v008.ma'

if not os.path.exists(base):
    raise RuntimeError('orange_tree_v008.ma was not found.')
with open(base, 'rb') as f:
    text = f.read()
if b'"fall_03"' not in text or b'"bjoint_001"' not in text:
    raise RuntimeError('orange_tree_v008.ma does not look like the finished Stage 8 scene.')
del text

old = scenes + '/orange_tree_v009_wip.ma'
if os.path.exists(old):
    with open(old, 'rb') as f:
        complete = b'"fall_03"' in f.read()
    if not complete:
        new_name = scenes + '/WRONG_' + time.strftime('%H%M%S') + '_orange_tree_v009_wip.ma'
        os.rename(old, new_name)
        print('Renamed the incomplete v009_wip to', new_name.split('/')[-1])

if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
print('Opening', base)
cmds.file(base, open=True, force=True)

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

print('Leaves / oranges    :', len(cmds.ls('leaf_0*', transforms=True)), '/', len(cmds.ls('orange_??', transforms=True)))
print('Joints / fall groups:', len(cmds.ls('bjoint_*', transforms=True)), '/', len(cmds.ls('fall_??', transforms=True)))

STEPS = ['stage9_step1_ground_material.py', 'stage9_step2_tree_materials.py',
         'stage9_environment_all.py', 'stage9_lighting_fix.py', 'stage10_step1_preflight.py']

def run_script(script_name):
    path = folder + '/scripts/' + script_name
    if not os.path.exists(path):
        raise RuntimeError('missing file ' + script_name)
    with open(path) as f:
        code = f.read()
    exec(compile(code, path, 'exec'), globals())

def main():
    report = []
    for n, script_name in enumerate(STEPS, 1):
        print()
        print(f'===== [{n}/{len(STEPS)}] {script_name} =====')
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
    print(('OK      ' if ok else 'FAILED  ') + f'{script_name:36} {secs / 60:5.1f} min  {err}')
print()
print('Scene now          :', cmds.file(query=True, sceneName=True))
print('Leaves / oranges   :', len(cmds.ls('leaf_0*', transforms=True)), '/', len(cmds.ls('orange_??', transforms=True)))
print('Fall groups / grass:', len(cmds.ls('fall_??', transforms=True)), '/', len([g for g in ('grass_a', 'grass_b') if cmds.objExists(g)]))
print('Dome lights / suns :', len(cmds.ls(type='aiSkyDomeLight')), '/', len(cmds.ls(type='directionalLight')))
print('Animation curves   :', len(cmds.ls(type='animCurve')))
print('Scene files saved:')
for n in sorted(os.listdir(scenes)):
    if n.lower().endswith('.ma') and n.startswith('orange_tree_v0') and int(n.split('_v')[1][:3]) >= 9:
        print(f'  {n:34} {os.path.getsize(scenes + "/" + n) / 1048576:6.1f} MB')
