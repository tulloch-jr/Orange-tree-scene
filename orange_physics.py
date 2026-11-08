import math
import maya.api.OpenMaya as om

GRAVITY = om.MVector(0, -981.0, 0)


def make_wind(speed, angle_degrees):
    a = math.radians(angle_degrees)
    return om.MVector(math.cos(a), 0, math.sin(a)) * speed


class Body:
    def __init__(self, position, velocity=None, mass=0.20, radius=3.7,
                 cd=0.47, rho=1.2, wind=None):
        self.pos = om.MVector(position)
        self.vel = om.MVector(velocity) if velocity is not None else om.MVector(0, 0, 0)
        self.mass = mass
        self.radius = radius
        area = math.pi * (radius / 100.0) ** 2
        self.k = (0.5 * rho * cd * area / mass) / 100.0
        self.wind = om.MVector(wind) if wind is not None else om.MVector(0, 0, 0)
        self.time = 0.0

    def acceleration(self, vel):
        rel = vel - self.wind
        return GRAVITY - rel * (self.k * rel.length())

    def step(self, dt):
        p = self.pos
        v = self.vel
        k1v = self.acceleration(v)
        k1p = v
        k2v = self.acceleration(v + k1v * (dt / 2))
        k2p = v + k1v * (dt / 2)
        k3v = self.acceleration(v + k2v * (dt / 2))
        k3p = v + k2v * (dt / 2)
        k4v = self.acceleration(v + k3v * dt)
        k4p = v + k3v * dt
        self.pos = p + (k1p + k2p * 2 + k3p * 2 + k4p) * (dt / 6)
        self.vel = v + (k1v + k2v * 2 + k3v * 2 + k4v) * (dt / 6)
        self.time += dt


def simulate(start, dt, radius=3.7, wind=None, ground_y=0.0,
             velocity=None, cd=0.47, max_time=20.0):
    body = Body(start, velocity=velocity, radius=radius, cd=cd, wind=wind)
    target = ground_y + radius
    if body.pos.y <= target:
        raise ValueError('The body starts at or below the ground.')
    path = [om.MVector(start)]
    while body.time < max_time:
        prev = om.MVector(body.pos)
        t_prev = body.time
        body.step(dt)
        if body.pos.y <= target:
            frac = (prev.y - target) / (prev.y - body.pos.y)
            contact = prev + (body.pos - prev) * frac
            return path, t_prev + dt * frac, contact
        path.append(om.MVector(body.pos))
    raise RuntimeError('The body never reached the ground.')
