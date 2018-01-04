from . import entity, game_map, constants, geom
from hlt.entity import Position, Ship
from .geom import Point, Seg, min_dist, ps_dist
import math
import logging
from collections import OrderedDict

def to_turns(dist, speed = constants.MAX_SPEED):
    return dist/speed

def nav(ship, targ, gmap, speed, move_table, 
    obs=None, max_corrections=180, d_ang = 1, ang_step=1):

    dist = ship.dist_to(targ)
    angle = round(ship.angle_to(targ))
    speed = speed if (dist >= speed) else int(dist)
    d = Point.polar(speed, angle)
    move = Seg(ship.loc, ship.loc+d)

    if obs == None:
        obs = [e for e in gmap.all_planets() + gmap.my_dships() if e != targ and e != ship 
                and ship.dist_to(e)-ship.radius-e.radius <= dist]
    obs = sorted(obs, key = lambda t:ship.dist_to(t))

    move_table_upd = {}
    for e in move_table:
        if ship.dist_to(e) <= constants.MAX_SPEED*2 + ship.radius + e.radius:
            move_table_upd[e] = move_table[e]
    move_table = OrderedDict(sorted(move_table_upd.items(), key=lambda t:ship.dist_to(t[0])))

    if max_corrections <= 0:
        return None, None

    if not gmap.contains_pt(ship.loc+d) or obs_between(ship, targ, gmap, speed, obs, move_table) != None:
        dv = Point.polar(dist, angle+d_ang)
        new_target = Position(ship.loc + dv)
        return nav(ship, new_target, gmap, speed, move_table, obs, 
            max_corrections - 1, -(d_ang+ang_step) if d_ang > 0 else -(d_ang-ang_step))

    return ship.thrust(speed, angle), move

def obs_between(ship, targ, gmap, speed, obs, move_table):
    move = Seg(ship.loc,targ.loc)
    
    for e in obs:
        if e == ship or e == targ:
            continue
        if ps_dist(e.loc,move) <= ship.radius + e.radius:
            return e

    dist = ship.dist_to(targ)
    speed = speed if (dist >= speed) else int(dist)
    angle = round(ship.angle_to(targ))

    d = Point.polar(speed, angle)
    move = Seg(ship.loc, ship.loc+d)

    for ship_oth, move_oth in move_table.items():
        if ship_oth == ship:
            continue
        if move_oth == None:
            move_oth = Seg(ship_oth.loc,ship_oth.loc) 
        
        if min_dist(move, move_oth) <= ship.radius + ship_oth.radius:
            return ship_oth

    return None

def cent_of_mass(entities):
    return Position(geom.cent_of_mass([e.loc for e in entities]))