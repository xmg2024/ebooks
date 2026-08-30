# -*- coding:gb18030 -*-
#推箱子游戏分步骤代码2：实现角色的交互

TILESIZE = 48                            # 箱子尺寸
WIDTH = TILESIZE * 6                     # 屏幕宽度
HEIGHT = TILESIZE * 6                    # 屏幕高度
# 方向字典，存储各方向对应的坐标偏移值
dirs = {"east":(1, 0), "west":(-1, 0),
        "north":(0, -1), "south":(0, 1), "none":(0, 0)}

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


# 处理键盘按下事件
def on_key_down(key):
    if key == keys.RIGHT:
        player.direction = "east"
        player.image = "pushbox_right"
    elif key == keys.LEFT:
        player.direction = "west"
        player.image = "pushbox_left"
    elif key == keys.DOWN:
        player.direction = "south"
        player.image = "pushbox_down"
    elif key == keys.UP:
        player.direction = "north"
        player.image = "pushbox_up"
    else:
        player.direction = "none"
    player_move()
    player_collision()


# 移动玩家角色
def player_move():
    player.oldx = player.x
    player.oldy = player.y
    dx, dy = dirs[player.direction]
    player.x += dx * TILESIZE
    player.y += dy * TILESIZE


# 玩家角色的碰撞检测与处理
def player_collision():
    # 玩家与墙壁的碰撞
    if player.collidelist(walls) != -1:
        player.x = player.oldx
        player.y = player.oldy
        return
    # 玩家与箱子的碰撞
    index = player.collidelist(boxes)
    if index == -1:
        return
    box = boxes[index]
    if box_collision(box) == True:
        box.x = box.oldx
        box.y = box.oldy
        player.x = player.oldx
        player.y = player.oldy
        return
    sounds.fall.play()


# 箱子角色的碰撞检测与处理
def box_collision(box):
    box.oldx = box.x
    box.oldy = box.y
    dx, dy = dirs[player.direction]
    box.x += dx * TILESIZE
    box.y += dy * TILESIZE
    # 箱子与墙壁的碰撞
    if box.collidelist(walls) != -1:
        return True
    # 箱子与其他箱子的碰撞
    for bx in boxes:
        if box == bx:
            continue
        if box.colliderect(bx):
            return True
    check_target(box)
    return False


# 检测箱子是否放置在目标点上
def check_target(box):
    if box.collidelist(targets) != -1:
        box.image = "pushbox_box_hit"
        box.placed = True
    else:
        box.image = "pushbox_box"
        box.placed = False


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
