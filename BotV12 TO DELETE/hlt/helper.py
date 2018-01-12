from . import entity, game_map, constants, geom
from hlt.entity import Position, Ship
from .geom import Point, Seg, min_dist, ps_dist, pp_dist
import math
import logging
from collections import OrderedDict
from .constants import *

def to_turns(dist, speed = constants.MAX_SPEED):
    return dist/speed

def view_angle(ship, targ):
    dist = ship.dist_to(targ)
    radius = ship.radius + targ.radius +.0001
    return math.degrees(math.asin(radius/dist))


def nav(ship, targ, gmap, obs, moves, speed = MAX_SPEED, max_view = 90):
    dist = ship.dist_to(targ)
    angle = ship.angle_to(targ)
    speed = speed if (dist >= speed) else int(dist)
    good_angs = set(range(0,360))

    if obs == None:
        obs = [e for e in gmap.all_planets() + gmap.my_dships() 
                if ship.dist_to(e)-ship.radius-e.radius <= min(dist,MAX_SPEED*5)]
        obs.extend([e for e in gmap.my_uships() if e != ship and e not in moves
            and ship.dist_to(e)-ship.radius-e.radius <= MAX_SPEED + speed])

    for e in obs:
        obs_ang = ship.angle_to(e)
        d_ang = view_angle(ship,e)
        min_ang = math.floor(obs_ang-d_ang)
        max_ang = math.ceil(obs_ang+d_ang)
        for i in range(min_ang+1, max_ang):
            good_angs.discard(i%360)

    if angle - round(angle) <0:
        angs = [int(n/2) if n%2 == 0 else -int(n/2) for n in range(1,max_view*2+2)]
    else:
        angs = [int(n/2) if n%2 == 1 else -int(n/2) for n in range(1,max_view*2+2)]

    angle = round(angle)
    for d_ang in angs:
        move_ang = (angle+d_ang) % 360
        if move_ang not in good_angs:
            continue

        d = Point.polar(speed, move_ang)
        move = Seg(ship.loc, ship.loc+d)

        for e in moves:
            if min_dist(move,moves[e]) <= ship.radius + e.radius + .0001:
                break
        else:
            return ship.thrust(speed, move_ang), move
    return None, None

def cent_of_mass(entities):
    return Position(geom.cent_of_mass([e.loc for e in entities]))

def est_hits(ship):
    return math.ceil(ship.hp/WEAPON_DAMAGE)

def total_hits(ships):
    return sum([est_hits(s) for s in ships])

def max_killed(ships, num_hits):
    ships = sorted(ships, key = lambda t: t.hp)
    num_killed = 0
    for s in ships:
        if num_hits >= est_hits(s):
            num_hits -= est_hits(s)
            num_killed += 1
        else:
            break

    return num_killed



