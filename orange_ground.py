import math
import maya.api.OpenMaya as om
import orange_physics

G = 981.0
UP = om.MVector(0, 1, 0)


def _impact(body, omega, radius, restitution, mu):
    r_c = UP * (-radius)
    v_c = body.vel + (omega ^ r_c)
    vn = v_c * UP
    jn = -(1.0 + restitution) * vn
    vt = v_c - UP * vn
    vt_len = vt.length()
    t_hat = om.MVector(0, 0, 0)
    jt = 0.0
    if vt_len > 1e-9:
        t_hat = vt * (-1.0 / vt_len)
        jt = min(mu * jn, vt_len / 3.5)
    impulse = UP * jn + t_hat * jt
    body.vel = body.vel + impulse
    return omega + (r_c ^ impulse) * (1.0 / (0.4 * radius * radius))


def simulate_full(start, velocity=None, wind=None, radius=3.7, ground_y=0.0,
                  restitution=0.45, mu_slide=0.6, mu_roll=0.15,
                  rest_speed=30.0, dt=1.0 / 240.0, max_time=15.0):
    floor = ground_y + radius
    body = orange_physics.Body(start, velocity=velocity, radius=radius, wind=wind)
    omega = om.MVector(0, 0, 0)
    mode = 'air'
    t = 0.0
    samples = [(t, om.MVector(body.pos), om.MVector(body.vel), om.MVector(omega), mode)]
    events = []
    r_c = UP * (-radius)

    while t < max_time:
        if mode == 'air':
            prev_pos = om.MVector(body.pos)
            prev_vel = om.MVector(body.vel)
            body.step(dt)
            t += dt
            if body.pos.y <= floor and body.vel.y < 0:
                frac = (prev_pos.y - floor) / (prev_pos.y - body.pos.y)
                hit = prev_pos + (body.pos - prev_pos) * frac
                body.pos = om.MVector(hit.x, floor, hit.z)
                body.vel = prev_vel + (body.vel - prev_vel) * frac
                impact_speed = -body.vel.y
                omega = _impact(body, omega, radius, restitution, mu_slide)
                events.append((t - dt * (1.0 - frac), 'impact', impact_speed))
                if body.vel.y < rest_speed:
                    body.vel = om.MVector(body.vel.x, 0, body.vel.z)
                    mode = 'ground'
                    events.append((t, 'rolling', 0.0))
        else:
            v = om.MVector(body.vel.x, 0, body.vel.z)
            v_c = v + (omega ^ r_c)
            slip = om.MVector(v_c.x, 0, v_c.z)
            slip_len = slip.length()
            if slip_len > 0.5:
                t_hat = slip * (-1.0 / slip_len)
                jt = min(mu_slide * G * dt, slip_len / 3.5)
                v = v + t_hat * jt
                omega = omega + (r_c ^ (t_hat * jt)) * (1.0 / (0.4 * radius * radius))
            else:
                speed = v.length()
                if speed > 0:
                    v = v * (max(0.0, speed - mu_roll * G * dt) / speed)
                omega = (UP ^ v) * (1.0 / radius) + om.MVector(0, omega.y * (1.0 - 4.0 * dt), 0)
            body.vel = v
            body.pos = om.MVector(body.pos.x + v.x * dt, floor, body.pos.z + v.z * dt)
            t += dt
            if v.length() < 2.0 and slip_len <= 0.5:
                body.vel = om.MVector(0, 0, 0)
                omega = om.MVector(0, 0, 0)
                events.append((t, 'at rest', 0.0))
                samples.append((t, om.MVector(body.pos), om.MVector(body.vel), om.MVector(omega), 'rest'))
                break
        samples.append((t, om.MVector(body.pos), om.MVector(body.vel), om.MVector(omega), mode))
    return samples, events
