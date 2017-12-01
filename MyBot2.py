"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
from hlt import helper
# Then let's import the logging module so we can print out information
import logging
import time

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Bot2")
# Then we print our start message to the logs
logging.info("Starting my Settler bot!")

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
    # For every ship that I control

    numPlanets = 0
    max_calculations = 2500

    unfilled_planets = helper.unfilled_planets(game_map)
    enemy_planets = helper.enemy_planets(game_map)
    unowned_planets = helper.unowned_planets(game_map)
    my_ships = helper.my_ships(game_map)
    remaining_ships = [ship for ship in my_ships if ship.docking_status == ship.DockingStatus.UNDOCKED]

    logging.info("Total Ships: " + str(len(my_ships)))
    logging.info("Undocked Ships: " + str(len(remaining_ships)))


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

    unowned_table = {p:helper.num_docking_spots(p) for p in unowned_planets}

    logging.info("Remaining Ships: " + str(len(remaining_ships)))
    logging.info("Number Unowned: " + str(len(unowned_planets)))
    logging.info("Number Enemy: " +  str(len(enemy_planets)))

    for ship in remaining_ships:

        targPlanet = None
        enemy = False

        # for planet in emptyPlanets:
        #     if targPlanet == None or ship.calculate_distance_between(ship.closest_point_to(targPlanet)) > ship.calculate_distance_between(ship.closest_point_to(planet)):
        #         targPlanet = planet

        # if targPlanet == None:
        #     for planet in theirPlanets:
        #         if targPlanet == None or ship.calculate_distance_between(ship.closest_point_to(targPlanet)) > ship.calculate_distance_between(ship.closest_point_to(planet)):
        #             targPlanet = planet
        #             enemy = True

        for planet in enemy_planets + unowned_planets:
            enemy_planet = not (planet.owner == game_map.get_me() or planet.owner == None)
            if targPlanet == None:
                targPlanet = planet
                enemy = enemy_planet
            else: 
                curDist = ship.calculate_distance_between(ship.closest_point_to(targPlanet))
                newDist = ship.calculate_distance_between(ship.closest_point_to(planet))
                if not enemy_planet and curDist > newDist and unowned_table[planet] > 0:
                    targPlanet = planet
                    enemy = enemy_planet
                    unowned_table[planet] = unowned_table[planet] - 1
                elif enemy_planet and helper.dist_to_turns(curDist) > helper.dist_to_turns(newDist) + 2*len(planet.all_docked_ships()):
                    if not targPlanet.is_owned():
                        unowned_table[targPlanet] = unowned_table[targPlanet] + 1
                    targPlanet = planet
                    enemy = enemy_planet


        if targPlanet == None:
            break

        if not enemy:
            if ship.can_dock(targPlanet):
                # We add the command by appending it to the command_queue
                command_queue.append(ship.dock(targPlanet))
            else:
                navigate_command = helper.navigate(ship,ship.closest_point_to(targPlanet),game_map,speed=int(hlt.constants.MAX_SPEED),ignore_ships=True)
                if navigate_command:
                    command_queue.append(navigate_command)
        else:
            targShip = None
            for docked_ship in targPlanet.all_docked_ships():
                if targShip == None or ship.calculate_distance_between(ship.closest_point_to(targShip)) > ship.calculate_distance_between(ship.closest_point_to(docked_ship)):
                    targShip = docked_ship

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

