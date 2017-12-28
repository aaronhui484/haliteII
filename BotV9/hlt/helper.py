from . import collision, entity, game_map, constants
from hlt.entity import Position, Ship
import math

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

def dist_to_turns(dist, speed = constants.MAX_SPEED, round = True):
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

def navigate(ship, target, game_map, speed, avoid_obstacles=True, max_corrections=60, angular_step=1,
             ignore_ships=False, ignore_planets=False):
    """
    Move a ship to a specific target position (Entity). It is recommended to place the position
    itself here, else navigate will crash into the target. If avoid_obstacles is set to True (default)
    will avoid obstacles on the way, with up to max_corrections corrections. Note that each correction accounts
    for angular_step degrees difference, meaning that the algorithm will naively try max_correction degrees before giving
    up (and returning None). The navigation will only consist of up to one command; call this method again
    in the next turn to continue navigating to the position.

    :param Entity target: The entity to which you will navigate
    :param game_map.Map game_map: The map of the game, from which obstacles will be extracted
    :param int speed: The (max) speed to navigate. If the obstacle is nearer, will adjust accordingly.
    :param bool avoid_obstacles: Whether to avoid the obstacles in the way (simple pathfinding).
    :param int max_corrections: The maximum number of degrees to deviate per turn while trying to pathfind. If exceeded returns None.
    :param int angular_step: The degree difference to deviate if the original destination has obstacles
    :param bool ignore_ships: Whether to ignore ships in calculations (this will make your movement faster, but more precarious)
    :param bool ignore_planets: Whether to ignore planets in calculations (useful if you want to crash onto planets)
    :return string: The command trying to be passed to the Halite engine or None if movement is not possible within max_corrections degrees.
    :rtype: str
    """
    # Assumes a position, not planet (as it would go to the center of the planet otherwise)
    if max_corrections <= 0:
        return None
    distance = ship.calculate_distance_between(target)
    angle = ship.calculate_angle_between(target)
    ignore = () if not (ignore_ships or ignore_planets) \
        else Ship if (ignore_ships and not ignore_planets) \
        else Planet if (ignore_planets and not ignore_ships) \
        else Entity
    if avoid_obstacles and obstacles_between(ship, target, game_map, ignore):
        new_target_dx = math.cos(math.radians(angle + angular_step)) * distance
        new_target_dy = math.sin(math.radians(angle + angular_step)) * distance
        new_target = Position(ship.x + new_target_dx, ship.y + new_target_dy)
        return navigate(ship, new_target, game_map, speed, True, max_corrections - 1, -(angular_step+3))
    speed = speed if (distance >= speed) else distance
    return ship.thrust(speed, angle)

def obstacles_between(ship, target, map, ignore=()):
    """
    Check whether there is a straight-line path to the given point, without planetary obstacles in between.

    :param entity.Ship ship: Source entity
    :param entity.Entity target: Target entity
    :param entity.Entity ignore: Which entity type to ignore
    :return: The list of obstacles between the ship and target
    :rtype: list[entity.Entity]
    """
    obstacles = []
    entities = ([] if issubclass(entity.Planet, ignore) else map.all_planets()) \
        + ([] if issubclass(entity.Ship, ignore) else enemy_ships(map)) \
        + (my_undocked_ships(map) if len(my_undocked_ships(map)) < 50 else []) \
        + (my_docked_ships(map))
    for foreign_entity in entities:
        if foreign_entity == ship or foreign_entity == target:
            continue
        if collision.intersect_segment_circle(ship, target, foreign_entity, fudge=ship.radius + 0.1):
            obstacles.append(foreign_entity)
    return obstacles

def point_line_dist(p, seg):
    line_dist = (seg.y2 - seg.y1) * p.x - (seg.x2 - seg.x1)*p.y + seg.x2*seg.y1 - seg.y2*seg.x1
    e1_dist = sqrt((p.x-seg.x1)**2 + (p.y - seg.y1)**2)
    e2_dist = sqrt((p.x-seg.x2)**2 + (p.y - seg.y2)**2)
    return min(line_dist, e1_dist, e2_dist)