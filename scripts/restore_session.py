import os
import sys
import json
import maya.cmds as cmds
import maya.api.OpenMaya as om

folder = 'C:/MayaScripts/OrangeTree'
scenes = f'{folder}/scenes'

target = None
for name in ('orange_tree_v008.ma', 'orange_tree_v008_wip.ma', 'orange_tree_v007.ma'):
    if os.path.exists(f'{scenes}/{name}'):
        target = f'{scenes}/{name}'
        break
if target is None:
    raise RuntimeError('No saved scene was found in ' + scenes)

if cmds.file(query=True, modified=True):
    backup = f'{scenes}/backup_before_restore.ma'
    cmds.file(rename=backup)
    cmds.file(save=True, type='mayaAscii')
    print('Saved a backup of the open scene as', backup)

if not cmds.pluginInfo('mtoa', query=True, loaded=True):
    cmds.loadPlugin('mtoa')
cmds.file(target, open=True, force=True)

with open(f'{folder}/tree_data.json') as f:
    payload = json.load(f)
TREE = payload['TREE']
TREE.setdefault('wind_speed', 800.0)
TREE.setdefault('wind_angle', 20)
data = [(om.MVector(*s), om.MVector(*e), d) for s, e, d in payload['data']]
cmds.currentTime(1)

if folder not in sys.path:
    sys.path.append(folder)

print('Scene opened      :', cmds.file(query=True, sceneName=True))
print('Segments in data  :', len(data))
print('Leaves            :', len(cmds.ls('leaf_0*', transforms=True)))
print('Hanging oranges   :', len(cmds.ls('orange_??', transforms=True)))
print('Fall groups       :', len(cmds.ls('fall_??', transforms=True)))
