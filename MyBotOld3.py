
import hlt
from hlt import helper
import logging
import time

# GAME START
game = hlt.Game("CurrentBot")
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


    logging.info("Total Ships: " + str(len(my_ships)))
    logging.info("Undocked Ships: " + str(len(remaining_ships)))

    threat_ships = []
    for s in enemy_undocked_ships:
        for docked in my_docked_ships:
            if helper.dist_to_turns(s.calculate_distance_between(docked)) <= 2:
                threat_ships.append(s)
                break

    for p in unfilled_planets:

        num_ships = helper.num_docking_spots(p)
        ship_dict = helper.nearby_entities_by_distance(p, remaining_ships)
        dist_list = sorted(ship_dict, reverse = True)

        i = 0
        while i < num_ships and len(dist_list) > 0:
            dist = dist_list.pop()
            if helper.dist_to_turns(dist) > p.remaining_resources/(len(p.all_docked_ships())*hlt.constants.BASE_PRODUCTIVITY):
                break
            for s in ship_dict[dist]:
                if s.can_dock(p):
                    command_queue.append(s.dock(p))
                else:
                    navigate_command = helper.navigate(s,s.closest_point_to(p),game_map,speed=int(hlt.constants.MAX_SPEED),ignore_ships=True)
                    if navigate_command:
                        command_queue.append(navigate_command)

                remaining_ships.remove(s)
                i = i+1

    

    logging.info("Remaining Ships: " + str(len(remaining_ships)))
    logging.info("Number Unowned: " + str(len(unowned_planets)))
    logging.info("Number Enemy: " +  str(len(enemy_planets)))

    unowned_table = {p:helper.num_docking_spots(p) for p in unowned_planets}

    for ship in remaining_ships:

        targ = None
        enemy = False

        for entity in enemy_planets + unowned_planets + threat_ships:
            if type(entity) == hlt.entity.Planet:
                if targ == None:
                    targ = entity
                    enemy = helper.is_enemy(game_map, entity)
                else: 
                    curDist = ship.calculate_distance_between(ship.closest_point_to(targ))
                    newDist = ship.calculate_distance_between(ship.closest_point_to(entity))
                    if not helper.is_enemy(game_map, entity) and curDist > newDist and unowned_table[entity] > 0:
                        targ = entity
                        enemy = helper.is_enemy(game_map, entity)
                        unowned_table[entity] = unowned_table[entity] - 1
                    elif helper.is_enemy(game_map, entity) and helper.dist_to_turns(curDist) > helper.dist_to_turns(newDist) + 2*len(entity.all_docked_ships()):
                        if not targ.is_owned():
                            unowned_table[targ] = unowned_table[targ] + 1
                        targ = entity
                        enemy = helper.is_enemy(game_map, entity)
            else:
                curDist = ship.calculate_distance_between(ship.closest_point_to(targ))
                newDist = ship.calculate_distance_between(ship.closest_point_to(entity))
                if curDist > newDist:
                    targ = entity
                    enemy = helper.is_enemy(game_map, entity)



        if targ == None:
            break

        if not enemy:
            if ship.can_dock(targ):
                # We add the command by appending it to the command_queue
                command_queue.append(ship.dock(targ))
            else:
                navigate_command = helper.navigate(ship,ship.closest_point_to(targ),game_map,speed=int(hlt.constants.MAX_SPEED),ignore_ships=True)
                if navigate_command:
                    command_queue.append(navigate_command)
        else:
            targShip = None
            if type(targ) == hlt.entity.Planet:
                for docked_ship in targ.all_docked_ships():
                    if targShip == None or ship.calculate_distance_between(ship.closest_point_to(targShip)) > ship.calculate_distance_between(ship.closest_point_to(docked_ship)):
                        targShip = docked_ship
            else:
                targShip = targ

            navigate_command = helper.navigate(ship,ship.closest_point_to(targShip),game_map,speed=int(hlt.constants.MAX_SPEED),ignore_ships=True)
            if navigate_command:
                command_queue.append(navigate_command)

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)

    end_time = time.process_time()
    elapsed_time = end_time - start_time
    if elapsed_time >= 1:
        logging.critical("Time Elapsed: " + str(end_time - start_time))
    else:
        logging.info("Time Elapsed: " + str(end_time - start_time))
    # TURN END
# GAME END

