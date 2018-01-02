from . import collision, entity, game_map, constants
from hlt.entity import Position, Ship
from .geom import Point, Seg, min_dist, ps_dist
import math
import logging

def my_ships(map):
    return map.get_me().all_ships()

def my_docked_ships(map):
    return [ship for ship in my_ships(map) if ship.docking_status != ship.DockingStatus.UNDOCKED]

def my_undocked_ships(map):
    return [ship for ship in my_ships(map) if ship.docking_status == ship.DockingStatus.UNDOCKED]

def enemy_ships(map):
    ships = []
    for player in map.all_players():
        if player != map.get_me():
            ships = ships + player.all_ships()
    return ships

def enemy_undocked_ships(map):
    return [ship for ship in enemy_ships(map) if ship.docking_status == ship.DockingStatus.UNDOCKED]

def enemy_docked_ships(map):
    return [ship for ship in enemy_ships(map) if ship.docking_status != ship.DockingStatus.UNDOCKED]

def my_planets(map):
    return [planet for planet in map.all_planets() if planet.owner == map.get_me()]

def unfilled_planets(map):
    return [planet for planet in map.all_planets() if planet.owner == map.get_me() and not planet.is_full()]

def unowned_planets(map):
    return [planet for planet in map.all_planets() if not planet.is_owned()]

def enemy_planets(map):
    return [planet for planet in map.all_planets() if planet.owner != map.get_me() and planet.is_owned()]

def dist_to_turns(dist, speed = constants.MAX_SPEED, round = False):
    return math.ceil(dist/speed) if round else dist/speed

def nearby_entities_by_distance(entity, entity_list):
    result = {}
    for foreign_entity in entity_list:
        if entity == foreign_entity:
            continue
        result.setdefault(entity.calculate_distance_between(foreign_entity), []).append(foreign_entity)
    return result

def num_docking_spots(planet):
    return planet.num_docking_spots - len(planet.all_docked_ships())

def is_enemy(map, target):
    return not (target.owner == map.get_me() or target.owner == None)

def navigate(ship, target, map, speed, move_table, 
    obs=None, max_corrections=180, d_ang = 1, ang_step=1):

    distance = ship.calculate_distance_between(target)
    angle = round(ship.calculate_angle_between(target))

    if obs == None:
        obs = [e for e in map.all_planets() + my_docked_ships(map) if e != target and e != ship 
                and ship.calculate_distance_between(e)-ship.radius-e.radius <= distance]

    move_table_upd = move_table
    for e in move_table:
        if ship.calculate_distance_between(e) <= constants.MAX_SPEED*2 + ship.radius + e.radius:
            move_table_upd[e] = move_table[e]

    move_table = move_table_upd

    if max_corrections <= 0:
        return None, None

    if obstacles_between(ship, target, map, speed, obs, move_table):
        new_target_dx = math.cos(math.radians(angle + d_ang)) * distance
        new_target_dy = math.sin(math.radians(angle + d_ang)) * distance
        new_target = Position(ship.x + new_target_dx, ship.y + new_target_dy)
        return navigate(ship, new_target, map, speed, move_table, obs, 
            max_corrections - 1, -(d_ang+ang_step) if d_ang > 0 else -(d_ang-ang_step))

    speed = speed if (distance >= speed) else int(distance)
    pos = Point(ship.x, ship.y)
    d = Point(speed*math.cos(math.radians(angle)),speed*math.sin(math.radians(angle)))
    move = Seg(pos, pos+d)

    return ship.thrust(speed, angle), move

def obstacles_between(ship, target, map, speed, obs, move_table):
    move = Seg(Point(ship.x,ship.y), Point(target.x,target.y))
    #logging.info("Angle: " + str(round(ship.calculate_angle_between(target))))
    
    for e in obs:
        if e == ship or e == target:
            continue
        p = Point(e.x,e.y)
        if ps_dist(p,move) <= ship.radius + e.radius:
            #logging.info("PS_Dist: " + str(ps_dist(p,move)-e.radius) + ", Collides with: " 
            #    + str(e) + ", " + str(ps_dist(p,move)))
            return True


    distance = ship.calculate_distance_between(target)
    speed = speed if (distance >= speed) else int(distance)
    angle = round(ship.calculate_angle_between(target))
    pos = Point(ship.x, ship.y)
    d = Point(speed*math.cos(math.radians(angle)),speed*math.sin(math.radians(angle)))
    move = Seg(pos, pos+d)

    #logging.info("Test Move: " + str(move))

    for ship_oth, move_oth in move_table.items():
        if move_oth == None:
            move_oth = Seg(Point(ship_oth.x,ship_oth.y),Point(ship_oth.x,ship_oth.y)) 
        if ship_oth == ship:
            continue
        
        if min_dist(move, move_oth) <= ship.radius + ship_oth.radius:
            #logging.info("Min_Dist: " + str(min_dist(move, move_oth)) + ", Collides with: " 
            #    + str(ship_oth) + " With Seg " + str(move_oth))
            return True

    return False