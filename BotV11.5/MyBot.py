import hlt
from hlt import helper
import logging
import time
import math
from hlt.geom import Point, Seg, cent_of_mass
from collections import OrderedDict
from hlt.constants import *
from hlt.entity import Position

# GAME START
game = hlt.Game("Bot V11.5")
turn = 0

while True:
    start_time = time.process_time()
    gmap = game.update_map()

    logging.info("TURN {}".format(turn))
    turn = turn + 1

    #HANDLE ATKS AT T=0
    has_atked = set()
    for s in gmap.all_uships():
        atks = []
        for t in gmap.all_ships():
            if s.owner != t.owner and s.dist_to(t) < WEAPON_RADIUS:
                atks.append(t)

        if atks:
            has_atked.add(s)
            for t in atks:
                t.hp -= WEAPON_DAMAGE/len(atks)
                if t.hp <= 0:
                    gmap.remove_ship(t)


    #THREAT LEVEL CODE
    threat_level = {}
    if gmap.my_dships():
        for e in gmap.en_uships():
            min_turns = helper.to_turns(min(map(lambda t:e.dist_to(s),gmap.my_dships()))-WEAPON_RADIUS)
            min_turns = max([0,min_turns])
            if min_turns < 1:
                threat_level[e] = 1


    #OTHER INFO
    rem_dock = {p:p.rem_spots() for p in gmap.unowned_planets() + gmap.my_uplanets()}
    en_ship_assigned = {s:math.ceil(s.hp/WEAPON_DAMAGE) for s in gmap.en_ships()}

    #MOVE LIST WITH PRIORITIES
    move_list = {}
    for s in gmap.my_uships():
        for e in gmap.unowned_planets() + gmap.my_uplanets() + gmap.en_ships():
            if type(e) == hlt.entity.Planet:
                d = helper.to_turns(s.dist_to(s.closest_pt_to(e))) + 2
                if e.owner != gmap.get_me():
                    d += .5
            elif type(e) == hlt.entity.Ship:
                d = helper.to_turns(s.dist_to(e) - WEAPON_RADIUS)
                if e in threat_level:
                    d -= threat_level[e]
                elif not e.can_atk():
                    d -= 1

            move_list[(s,e)] = d

    move_list = OrderedDict(sorted(move_list.items(), key=lambda t:t[1]))

    #ITERATE THROUGH MOVES
    move_table = {s:None for s in gmap.my_uships()}
    first_targ = OrderedDict()
    unassigned = set(gmap.my_uships())

    logging.info("HALFWAY TIME: {}".format(time.process_time() - start_time))

    cmds = []
    for (s,e), d in move_list.items():
        if time.process_time() - start_time > 1.9:
            logging.info("TOOK WAY TOO MUCH TIME")
            break

        nav_cmd = None
        move = None
        assigned = False

        if s not in unassigned or len(unassigned) == 0:
            continue

        if s not in first_targ:
            first_targ[s] = e

        if type(e) == hlt.entity.Planet and rem_dock[e] > 0:
            assigned = True
            if s.can_dock(e):
                nav_cmd = s.dock(e)
                rem_dock[e] -= 1
            else:
                nav_cmd, move = helper.nav(s,s.closest_pt_to(e), gmap, MAX_SPEED,move_table)
                if nav_cmd:
                    rem_dock[e] -= 1
        elif type(e) == hlt.entity.Ship:

            if s.dist_to(e) <= WEAPON_RADIUS + 2*MAX_SPEED:
                assigned = True
                enemies = [t for t in gmap.en_uships() if s.dist_to(t) <= WEAPON_RADIUS + 2*MAX_SPEED]
                friends = [t for t in gmap.my_ships() if e.dist_to(t) <= WEAPON_RADIUS + 2*MAX_SPEED]

                if len(enemies) >= len(friends):
                    dv = Point.polar(MAX_SPEED, s.angle_to(helper.cent_of_mass(enemies)))
                    pos = Position(s.loc - dv)
                    nav_cmd, move = helper.nav(s,pos,gmap,MAX_SPEED,move_table)
                elif len(friends) > len(enemies) and s in has_atked:
                    pos = helper.cent_of_mass(friends)
                    nav_cmd, move = helper.nav(s,pos,gmap,MAX_SPEED,move_table)
                else:
                    nav_cmd, move = helper.nav(s,s.closest_pt_to(e),gmap,MAX_SPEED,move_table)
                    if nav_cmd:
                        en_ship_assigned[e] -= 1

            elif en_ship_assigned[e] > 0:
                assigned = True
                nav_cmd, move = helper.nav(s,s.closest_pt_to(e),gmap,MAX_SPEED,move_table)
                if nav_cmd:
                        en_ship_assigned[e] -= 1

        if assigned:
            unassigned.remove(s)
        if nav_cmd:
            cmds.append(nav_cmd)
            move_table[s] = move

    for s in first_targ:
        if time.process_time() - start_time > 1.9:
            logging.info("TOOK WAY TOO MUCH TIME")
            break
        if s in unassigned:
            nav_cmd, move = helper.nav(s,s.closest_pt_to(first_targ[s]),gmap, MAX_SPEED, move_table)
            if nav_cmd:
                cmds.append(nav_cmd)
                move_table[s] = move

    game.send_command_queue(cmds)

    elapsed_time = time.process_time() - start_time
    if elapsed_time >= .5:
        logging.info("Time Elapsed CRITICAL: {}".format(elapsed_time))
    else:
        logging.info("Time Elapsed: {}".format(elapsed_time))
    # TURN END
# GAME END

