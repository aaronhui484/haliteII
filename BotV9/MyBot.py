import hlt
from hlt import helper
import logging
import time
import math
from hlt.geom import Point, Seg

# GAME START
game = hlt.Game("Bot V9")
turn = 0

while True:
    # TURN START
    logging.info("TURN " + str(turn))
    start_time = time.process_time()
    turn = turn + 1

    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []

    #Gather Game Information
    unfilled_planets = helper.unfilled_planets(game_map)
    enemy_planets = helper.enemy_planets(game_map)
    unowned_planets = helper.unowned_planets(game_map)
    my_ships = helper.my_ships(game_map)
    remaining_ships = helper.my_undocked_ships(game_map)
    my_docked_ships = helper.my_docked_ships(game_map)
    enemy_undocked_ships = helper.enemy_undocked_ships(game_map)
    enemy_docked_ships = helper.enemy_docked_ships(game_map)
    enemy_ships = helper.enemy_ships(game_map)

    logging.info("Total Ships: " + str(len(my_ships)))
    logging.info("Undocked Ships: " + str(len(remaining_ships)))

    ship_dists = {}
    threat_level = {}
    planet_rem_dock_spot = {p:helper.num_docking_spots(p) for p in unfilled_planets + unowned_planets}
    enemy_ship_assigned = {s:int(s.health/hlt.constants.WEAPON_DAMAGE) for s in enemy_ships}

    targs = unfilled_planets + unowned_planets + helper.enemy_ships(game_map)

    for s in remaining_ships:
        info = {}
        for e in targs:
            if s == e:
                continue
            #TEMP CODE TO PREVENT INSTAKILLS
            if type(e) == hlt.entity.Planet:
                info[e] = helper.dist_to_turns(s.calculate_distance_between(s.closest_point_to(e)), round = False)
                info[e] += 2
                if e.owner != game_map.get_me():
                    info[e] += .5
                #logging.info("PLANET: " + str(info[e]))
            elif type(e) == hlt.entity.Ship:
                info[e] = helper.dist_to_turns(s.calculate_distance_between(e) - hlt.constants.WEAPON_RADIUS, round = False)
                #logging.info("SHIP: " + str(info[e]))

        ship_dists[s] = info

    for s in my_docked_ships:
        info = {}
        for e in enemy_undocked_ships:
            if not e in threat_level:
                threat_level[e] = int(helper.dist_to_turns(s.calculate_distance_between(e)-hlt.constants.WEAPON_RADIUS, round = False))
            else:
                threat_level[e] = min(threat_level[e], int(helper.dist_to_turns(s.calculate_distance_between(e)-hlt.constants.WEAPON_RADIUS, round = False)))


    for e in threat_level:
        for s in ship_dists:
            if threat_level[e] < 1:
                ship_dists[s][e] -= 1-threat_level[e]

    for s in ship_dists:
        ship_dists[s] = sorted(ship_dists[s], key = ship_dists[s].get, reverse = True)

    assigned_ships = []

    if len(ship_dists) < 300:
        move_table = {s:Seg(Point(s.x,s.y),Point(s.x,s.y)) for s in ship_dists}
    else:
        move_table = {}
    
    #Ship Commands
    for s in ship_dists:
        logging.info("Routing " + str(s))
        targs = ship_dists[s]
        first_targ = None
        assigned = False
        nav_cmd = None
        move = None

        while len(targs) > 0 and assigned == False:
            targ = targs.pop()
            if first_targ == None and type(targ) == hlt.entity.Ship:
                first_targ = targ

            if type(targ) == hlt.entity.Planet and planet_rem_dock_spot[targ] > 0:
                if s.can_dock(targ):
                    logging.info("Dock at: " + str(targ))
                    nav_cmd = s.dock(targ)
                    move = Seg(Point(s.x,s.y), Point(s.x,s.y))
                    planet_rem_dock_spot[targ] -= 1
                    assigned = True
                else:
                    logging.info("Go To: " + str(targ))
                    nav_cmd, move = helper.navigate(s,s.closest_point_to(targ),game_map,int(hlt.constants.MAX_SPEED), move_table)
                    assigned = True
                    if nav_cmd:
                        planet_rem_dock_spot[targ] -= 1
            elif type(targ) == hlt.entity.Ship:
                if enemy_ship_assigned[targ] > 0 or helper.dist_to_turns(s.calculate_distance_between(targ)) < 2:
                    logging.info("Attack: " + str(targ))
                    nav_cmd, move = helper.navigate(s,s.closest_point_to(targ),game_map,int(hlt.constants.MAX_SPEED), move_table)
                    assigned = True
                    if nav_cmd:
                        enemy_ship_assigned[targ] -= 1

        if assigned and nav_cmd:
            command_queue.append(nav_cmd)
            move_table[s] = move

        if not assigned and first_targ != None:
            nav_cmd, move = helper.navigate(s,s.closest_point_to(first_targ),game_map,int(hlt.constants.MAX_SPEED), move_table)
            if nav_cmd:
                command_queue.append(nav_cmd)
                move_table[s] = move

        logging.info("Make Move: " + str(move))

        if nav_cmd == None:
            logging.info("NULL NAV_CMD")

        logging.info("END ROUTING FOR SHIP " + str(s.id))

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

