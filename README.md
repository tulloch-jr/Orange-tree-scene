# Orange Tree VFX

A procedural orange tree built with Python in Autodesk Maya 2023 and rendered with Arnold.

## What is in this project

- Procedural tree: recursive branching, curvature and tapering
- Leaves and oranges placed with instancing and spatial rules
- Wind: sine-wave branch sway, orange swing and leaf flutter
- A custom physics engine (`orange_physics.py`): gravity, air drag, wind and RK4 integration
- Fruit that detaches and falls, then bounces, rolls and settles

## Folders

- `orange_physics.py`: the physics engine
- `scripts/`: the Maya scripts for each step
- `*.json`: small data files (tree settings, fall plan)

Scene files (`scenes/`) are not stored in this repository because they are large.
