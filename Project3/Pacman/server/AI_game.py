from distutils.log import error
import os
import STcpServer
import gameUI
import threading
from gameUI import *
import pygame as pg
import random
import time
MAX_STEP = 2000
EPISODE = 550
def main():
    team_id = []
    with open('../path.txt', 'r', encoding="utf-8") as f:
        for line in f.readlines():
            if line[-1] == '\n':
                team_id.append(line[:-1])
            else:
                team_id.append(line)
    idTeam1 = int(team_id[0])
    pathExe1 = team_id[1]

    idTeam2 = int(team_id[2])
    pathExe2 = team_id[3]

    idTeam3 = int(team_id[4])
    pathExe3 = team_id[5]

    idTeam4 = int(team_id[6])
    pathExe4 = team_id[7]

    for i in range(EPISODE):
        print("This time is : ",EPISODE)
        (success, failId) = STcpServer.StartMatch(idTeam1, pathExe1, idTeam2, pathExe2, idTeam3, pathExe3, idTeam4, pathExe4)

        if(not success):
            print("connection fail, teamId:", failId)
        else:
            print("connect success, init game")
            # 16*16 16*16
            p_wall, v_wall = gameUI.createMap()

            for playerid in range(4):
                success = STcpServer.SendMap(playerid, p_wall, v_wall)
                if success != 0:
                    print("init fail")
            gamestart(p_wall, v_wall)
            # time.sleep(15)

def gamestart(p_wall, v_wall):
    screen = initialize()
    wall_positions = drawWall(p_wall, v_wall)
    level = Game(wall_positions)
    clock = pg.time.Clock()
    SCORE = 0
    wall_sprites, safe_place = level.setupWalls(SKYBLUE)

    hero_sprites = level.setPlayer(PAC_MAN)
    ghost_sprites = level.setGhost(GHOST)
    landmine_sprites = level.setLandmines(YELLOW, BLACK)
    power_sprites = level.setPower(RED, BLACK)
    pellet_sprites = level.setPellet(GREEN, BLACK)
    bomb_sprites = level.setBomb()
    leave = False

    gameScore = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                leave = True
                pg.quit()
        if (len(landmine_sprites) == 0 and len(power_sprites) == 0 and len(pellet_sprites) == 0 and leave == False) or STcpServer.idPackage > MAX_STEP:
            leave = True
            pg.quit()
        if leave == True: break
        STcpServer.idPackage += 1
        # get status
        ghosts= []
        for ghost in ghost_sprites:
            ghosts.append((ghost.rect.left, ghost.rect.top))
        heros = []
        for hero in hero_sprites:
            heros.append((hero.rect.left, hero.rect.top, hero.landmine, hero.super_time, hero.score))
        foods = []
        # 0 = landmine, 1 = power, 2 = pellet, 3 = bomb
        for landmine in landmine_sprites:
            foods.append((0, landmine.rect.left, landmine.rect.top))
        for power in power_sprites:
            foods.append((1, power.rect.left, power.rect.top))
        for pellet in pellet_sprites:
            foods.append((2, pellet.rect.left, pellet.rect.top))
        for bomb in bomb_sprites:
            foods.append((3, bomb.rect.left, bomb.rect.top))
        #

        #send
        player_action = [(0, True) for i in range(4)]
        threads = []
        def sendstatus(playerID, ghost, hero, food):
            success, action = STcpServer.Sendstatus(playerID, ghosts, heros, foods)
            if success == 0:
                player_action[playerID] = action
            if success > 0 :
                print("random for player:", playerID)
                player_action[playerID] = (random.choice([0, 1, 2, 3]), random.choice([True, False]))

        # creat thread for each player
        for playerid in range(4):
            threads.append(threading.Thread(target = sendstatus, args = (playerid, ghosts, heros, foods)))
            threads[playerid].start()
            #threads[playerid].join()

        # wait for each thread end
        for playerid in range(4):
            threads[playerid].join()

        # receive control
        direction = [[-1, 0],[1, 0],[0, -1],[0, 1]]
        playerid = 0
        for hero in hero_sprites:
            if player_action[playerid][0] != 4:
                hero.changedirection(direction[player_action[playerid][0]], wall_sprites)
            hero.is_move = True
            if hero.landmine > 0 and player_action[playerid][1] and not (151 <= hero.rect.left <= 201 and 151 <= hero.rect.top <= 201):
                hero.superman_time = 10
                bomb_sprites.add(Food(hero.rect.left+8, hero.rect.top+8, 11, 11, BOMB_COLOR, BLACK))
                hero.landmine -= 1
            playerid += 1
        screen.fill(BLACK)  # black

        # update position and condition check
        for ghost in ghost_sprites:
            ghost.update(wall_sprites)
        for hero in hero_sprites:
            hero.update(wall_sprites)
            eat_pellet = pg.sprite.spritecollide(hero, pellet_sprites, True)
            eat_landmine = pg.sprite.spritecollide(hero, landmine_sprites, True)
            eat_power = pg.sprite.spritecollide(hero, power_sprites, True)
            if eat_pellet:
                level.Pellet_num -= len(eat_pellet)
                hero.score += 10
            if eat_landmine:
                level.Landmines_num -= len(eat_landmine)
                hero.landmine += 1
            if eat_power:
                hero.clock = pg.time.Clock()
                hero.super = True
                hero.super_time = 10000
                hero.speed = [speed * 8 / 5 for speed in hero.speed]
                hero.base_speed = [8, 8]
            if hero.super:
                dead_list = pg.sprite.spritecollide(hero, ghost_sprites, False)
                hero.clock.tick()
                hero.super_time -= hero.clock.get_time()
                if hero.super_time < 0:
                    hero.super = False
                    hero.speed = [speed * 5 / 8 for speed in hero.speed]
                    hero.base_speed = [5, 5]
                if dead_list:
                    for ghost in dead_list:
                        if (151 <= hero.rect.left <= 201 and 151 <= hero.rect.top <= 201): continue
                        # ghost eaten by hero
                        hero.score += 200
                        ghost_sprites.remove(ghost)
                        x=random.choice([176,201])
                        y=random.choice([176,201])
                        new_ghost = Ghost(x, y, GHOST + "blueGhost.png")
                        new_ghost.dead_time = 100
                        ghost_sprites.add(new_ghost)
        
        # condition check ( bomb )
        for bomb in bomb_sprites:
            dead_list = pg.sprite.spritecollide(bomb, hero_sprites, False)
            for hero in dead_list:
                if hero.superman_time == 0:
                    # hero dead by bomb
                    hero.dead_time = 100
                    hero.movePosition()
                    bomb_sprites.remove(bomb)
            dead_list = pg.sprite.spritecollide(bomb, ghost_sprites, False)
            if dead_list:
                bomb_sprites.remove(bomb)
                for ghost in dead_list:
                    # ghost dead by bomb
                    ghost_sprites.remove(ghost)
                    x = random.choice([176, 201])
                    y = random.choice([176, 201])
                    new_ghost = Ghost(x, y, GHOST + "blueGhost.png")
                    new_ghost.dead_time = 100
                    ghost_sprites.add(new_ghost)
        
        # condition check ( ghost )
        for ghost in ghost_sprites:
            if 151 <= ghost.rect.left <= 201 and 151 <= ghost.rect.top <= 201 : continue
            dead_list = pg.sprite.spritecollide(ghost, hero_sprites, False)
            for hero in dead_list:
                if 151 <= hero.rect.left <= 201 and 151 <= hero.rect.top <= 201:continue
                if hero.superman_time == 0:
                    # hero eaten by ghost
                    hero.dead_time = 100
                    hero.movePosition()
                            
        safe_place.draw(screen)
        hero_sprites.draw(screen)
        ghost_sprites.draw(screen)
        wall_sprites.draw(screen)
        pellet_sprites.draw(screen)
        landmine_sprites.draw(screen)
        power_sprites.draw(screen)
        bomb_sprites.draw(screen)
        
        color = ["yellow", "pink", "orange", "purple"]
        idx = 0
        text_height = 10
        for hero in hero_sprites:
            text_to_screen(screen, '{:6}: {}'.format(color[idx], hero.score), x=410, y=text_height)
            idx += 1
            text_height += 20
        text_to_screen(screen, 'time: {}'.format(STcpServer.idPackage), x=410, y=text_height)

        pg.display.flip()
        clock.tick(20)

    for i in range(4):
        status = STcpServer.Sendend(i)
    for hero in hero_sprites:
        print("{} : {}".format(hero.role_name, hero.score))


if __name__ == "__main__":
    main()
    os.system('pause')