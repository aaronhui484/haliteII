import hlt
from hlt import helper
import logging
import time
import math
from hlt.geom import Point, Seg
from collections import OrderedDict

# GAME START
game = hlt.Game("Bot V10")
turn = 0

while True:
    # TURN START
    
    start_time = time.process_time()

    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    logging.info("TURN " + str(turn))
    turn = turn + 1

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []

    #Gather Game Information
    unfilled_planets = helper.unfilled_planets(game_map)
    enemy_planets = helper.enemy_planets(game_map)
    unowned_planets = helper.unowned_planets(game_map)
    my_ships = helper.my_ships(game_map)
    my_undocked_ships = helper.my_undocked_ships(game_map)
    my_docked_ships = helper.my_docked_ships(game_map)
    enemy_undocked_ships = helper.enemy_undocked_ships(game_map)
    enemy_docked_ships = helper.enemy_docked_ships(game_map)
    enemy_ships = helper.enemy_ships(game_map)

    logging.info("Total Ships: " + str(len(my_ships)))
    logging.info("Undocked Ships: " + str(len(my_undocked_ships)))

    threat_level = {}
    planet_rem_dock_spot = {p:helper.num_docking_spots(p) for p in unfilled_planets + unowned_planets}
    enemy_ship_assigned = {s:int(s.health/hlt.constants.WEAPON_DAMAGE) for s in enemy_ships}

    targs = unfilled_planets + unowned_planets + helper.enemy_ships(game_map)

    dists = {}
    has_attacked = set()

    for s in my_undocked_ships + enemy_undocked_ships:
        atks = []
        for t in my_ships + enemy_ships:
            if s.owner != t.owner and s.calculate_distance_between(t) <= hlt.constants.WEAPON_RADIUS:
                atks.append(t)

        if atks:
            has_attacked.add(s)
            for t in atks:
                t.health -= int(hlt.constants.WEAPON_DAMAGE/len(atks))

    for s in my_docked_ships:
        for e in enemy_undocked_ships:
            if not e in threat_level:
                threat_level[e] = int(helper.dist_to_turns(s.calculate_distance_between(e)-hlt.constants.WEAPON_RADIUS))
            else:
                threat_level[e] = min(threat_level[e], int(helper.dist_to_turns(s.calculate_distance_between(e)-hlt.constants.WEAPON_RADIUS)))

    for s in my_undocked_ships:
        for e in targs:
            if type(e) == hlt.entity.Planet:
                d = helper.dist_to_turns(s.calculate_distance_between(s.closest_point_to(e))) + 2
                if e.owner != game_map.get_me():
                    d += .5
            elif type(e) == hlt.entity.Ship:
                d = helper.dist_to_turns(s.calculate_distance_between(e) - hlt.constants.WEAPON_RADIUS)
                if e in threat_level:
                    if threat_level[e] < 1:
                        d -= 1-threat_level[e]
            dists[(s,e)] = d 


    dists = OrderedDict(sorted(dists.items(), key = lambda t:t[1]))


    first_targ = {s:None for s in my_undocked_ships}
    move_table = {s:None for s in my_undocked_ships}

    for (s,e), d in dists.items():
        if time.process_time() - start_time > 1.95:
            logging.info("RUNNING OUT OF TIME, BREAK")
            break
        if move_table[s] != None:
            continue

        if first_targ[s] == None:
            first_targ[s] = e

        assigned = False
        nav_cmd = None
        move = None
        if type(e) == hlt.entity.Planet and planet_rem_dock_spot[e] > 0:
            if s.can_dock(e):
                logging.info("Dock at: " + str(e))
                nav_cmd = s.dock(e)
                move = Seg(Point(s.x,s.y), Point(s.x,s.y))
                planet_rem_dock_spot[e] -= 1
                assigned = True
            else:
                logging.info("Go To: " + str(e))
                nav_cmd, move = helper.navigate(s,s.closest_point_to(e),game_map,int(hlt.constants.MAX_SPEED), move_table)
                assigned = True
                if nav_cmd:
                    planet_rem_dock_spot[e] -= 1
        elif type(e) == hlt.entity.Ship:
            if enemy_ship_assigned[e] > 0 or helper.dist_to_turns(s.calculate_distance_between(e)) < 2:
                logging.info("Attack: " + str(e))
                if s in has_attacked and e in has_attacked:
                    angle = s.calculate_angle_between(e)
                    pos = hlt.entity.Position(s.x+hlt.constants.MAX_SPEED*math.cos(angle), s.y + hlt.constants.MAX_SPEED*math.sin(angle))
                    nav_cmd,move = helper.navigate(s,s.closest_point_to(e,s.calculate_distance_between(e) + hlt.constants.MAX_SPEED),game_map,int(hlt.constants.MAX_SPEED), move_table)
                else:
                    nav_cmd, move = helper.navigate(s,s.closest_point_to(e),game_map,int(hlt.constants.MAX_SPEED), move_table)
                assigned = True
                if nav_cmd:
                    enemy_ship_assigned[e] -= 1

        if assigned and nav_cmd:
            command_queue.append(nav_cmd)
            move_table[s] = move

    for s in move_table:
        if time.process_time() - start_time > 1.95:
            logging.info("RUNNING OUT OF TIME, BREAK")
            break
        if move_table[s] == None:
            nav_cmd, move = helper.navigate(s,s.closest_point_to(first_targ[s]),game_map,int(hlt.constants.MAX_SPEED), move_table)
            if nav_cmd:
                command_queue.append(nav_cmd)
                move_table[s] = move

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)

    end_time = time.process_time()
    elapsed_time = end_time - start_time
    if elapsed_time >= .5:
        logging.critical("Time Elapsed: " + str(end_time - start_time))
    else:
        logging.info("Time Elapsed: " + str(end_time - start_time))
    # TURN END
# GAME END

