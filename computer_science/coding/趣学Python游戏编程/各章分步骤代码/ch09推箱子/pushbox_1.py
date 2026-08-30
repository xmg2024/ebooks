# -*- coding:gb18030 -*-
#推箱子游戏分步骤代码1：创建场景和角色

TILESIZE = 48                            # 箱子尺寸
WIDTH = TILESIZE * 6                     # 屏幕宽度
HEIGHT = TILESIZE * 6                    # 屏幕高度

map =   [ ['-1',  '1',	'1',	'1',	'-1',	'-1'],
          ['1',	  '1',	'4',	'1',	'1',	'1'],
          ['1',	  '4',	'0',	'2',	'0',	'1'],
          ['1',	  '1',	'2',	'0',	'3',	'1'],
          ['-1',  '1',	'0',	'0',	'1',	'1'],
          ['-1',  '1',	'1',	'1',	'1',	'-1'] ]


# 初始化地图，生成游戏角色
def initlevel(mapdata):
    global walls, floors, boxes, targets, player
    walls = []                           # 墙壁列表
    floors= []                           # 地板列表
    boxes = []                           # 箱子列表
    targets = []                         # 目标点列表
    for row in range(len(mapdata)):
        for col in range(len(mapdata[row])):
            x = col * TILESIZE
            y = row * TILESIZE
            if mapdata[row][col] >= "0" and mapdata[row][col] != "1":
                floors.append(Actor("pushbox_floor", topleft=(x, y)))
            if mapdata[row][col] == "1":
                walls.append(Actor("pushbox_wall", topleft=(x, y)))
            elif mapdata[row][col] == "2":
                box = Actor("pushbox_box", topleft=(x, y))
                box.placed = False
                boxes.append(box)
            elif mapdata[row][col] == "4":
                targets.append(Actor("pushbox_target", topleft=(x, y)))
            elif mapdata[row][col] == "6":
                targets.append(Actor("pushbox_target", topleft=(x, y)))
                box = Actor("pushbox_box_hit", topleft=(x, y))
                box.placed = True
                boxes.append(box)
            elif mapdata[row][col] == "3":
                player = Actor("pushbox_right", topleft=(x, y))

initlevel(map)


# 绘制游戏图像
def draw():
    screen.fill((200, 255, 255))
    for floor in floors:
        floor.draw()
    for wall in walls:
        wall.draw()
    for target in targets:
        target.draw()
    for box in boxes:
        box.draw()
    player.draw()
