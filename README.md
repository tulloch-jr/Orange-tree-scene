# Orange Tree VFX

A procedural orange tree scene built with Python in Autodesk Maya 2023 and rendered with Arnold.
It is built one stage at a time, and every stage ends with a saved scene and an automatic check.

## Progress

1. Scene setup: centimetre units, 24 fps, ground, trunk guide and camera
2. Procedural tree: recursive branching with curvature and tapering (186 branch tubes)
3. Foliage: a leaf prototype and 816 instanced leaves in three shades of green
4. Orange asset: lumpy peel with pores, stem and calyx, and an Arnold material
5. Fruit placement: valid attachment points under the branches, no overlaps (13 oranges)
6. Wind: sine-wave branch sway, orange swing and leaf flutter, all keyframed
7. Physics engine: gravity, quadratic air drag, wind and RK4 integration
8. Fall simulation: 8 oranges detach at the peak of the swing, fly, bounce, spin, roll and settle
9. Environment and camera: in progress (ground material done)
10. Final render: planned

## Files

- `orange_physics.py`: the physics engine (`Body`, `simulate`, `make_wind`)
- `orange_ground.py`: ground contact with restitution, friction and rolling
- `maya_git.py`: commit and push from the Maya Script Editor
- `scripts/`: one script per step
- `tree_data.json`, `fall_plan.json`: saved settings and plans
- Scene files are not stored here because they are large

## Starting a new Maya session

In the Script Editor (Python tab) run:

    exec(open('C:/MayaScripts/OrangeTree/scripts/restore_session.py').read())

This opens the latest scene and restores the tree settings.
