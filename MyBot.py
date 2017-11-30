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
# Then let's import the logging module so we can print out information
import logging

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("Bot2")
# Then we print our start message to the logs
logging.info("Starting my Settler bot!")

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control

    emptyPlanets = []
    theirPlanets = []

    numPlanets = 0
    docking_spots = 0
    max_calculations = 2500

    for planet in game_map.all_planets():
        if planet.owner == game_map.get_me() and not planet.is_full() or not planet.is_owned():
            emptyPlanets = emptyPlanets + [planet]
        elif planet.owner != game_map.get_me():
            logging.info("Planet Owner" + str(planet.owner))
            theirPlanets = theirPlanets + [planet]
        numPlanets = numPlanets + 1
        docking_spots = docking_spots + planet.num_docking_spots

    logging.info("Number of Empty Planets: " + str(len(emptyPlanets)))
    logging.info("Number of Enemy Planets: " + str(len(theirPlanets)))

    max_ships = int(max_calculations/numPlanets)

    ship_counter = 0;

    for ship in game_map.get_me().all_ships():
        # If the ship is docked

        if ship_counter < max_ships:
            ship_counter = ship_counter + 1
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship
                continue

            targPlanet = None
            enemy = False

            for planet in emptyPlanets:
                if targPlanet == None or ship.calculate_distance_between(ship.closest_point_to(targPlanet)) > ship.calculate_distance_between(ship.closest_point_to(planet)):
                    targPlanet = planet

            if targPlanet == None:
                logging.info("ENEMY!")
                for planet in theirPlanets:
                    if targPlanet == None or ship.calculate_distance_between(ship.closest_point_to(targPlanet)) > ship.calculate_distance_between(ship.closest_point_to(planet)):
                        targPlanet = planet
                        enemy = True

            if targPlanet == None:
                break

            if not enemy:
                logging.info("ITS NOT AN ENEMY")
                if ship.can_dock(targPlanet):
                    # We add the command by appending it to the command_queue
                    command_queue.append(ship.dock(targPlanet))
                else:
                    # If we can't dock, we move towards the closest empty point near this planet (by using closest_point_to)
                    # with constant speed. Don't worry about pathfinding for now, as the command will do it for you.
                    # We run this navigate command each turn until we arrive to get the latest move.
                    # Here we move at half our maximum speed to better control the ships
                    # In order to execute faster we also choose to ignore ship collision calculations during navigation.
                    # This will mean that you have a higher probability of crashing into ships, but it also means you will
                    # make move decisions much quicker. As your skill progresses and your moves turn more optimal you may
                    # wish to turn that option off.
                    navigate_command = ship.navigate(ship.closest_point_to(targPlanet),game_map,speed=int(hlt.constants.MAX_SPEED),ignore_ships=False)
                    # If the move is possible, add it to the command_queue (if there are too many obstacles on the way
                    # or we are trapped (or we reached our destination!), navigate_command will return null;
                    # don't fret though, we can run the command again the next turn)
                    if navigate_command:
                        command_queue.append(navigate_command)
            else:
                logging.info("ITS AN ENEMY")
                targShip = None
                for docked_ship in targPlanet.all_docked_ships():
                    if targShip == None or ship.calculate_distance_between(ship.closest_point_to(targShip)) > ship.calculate_distance_between(ship.closest_point_to(docked_ship)):
                        targShip = docked_ship

                navigate_command = ship.navigate(ship.closest_point_to(targShip), game_map, speed = int(hlt.constants.MAX_SPEED))
                if navigate_command:
                    command_queue.append(navigate_command)

    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
