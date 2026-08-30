# -*- coding:gb18030 -*-
# 贪食蛇分步骤代码2：移动蛇头

import random
SIZE = 15              # 贪食蛇及食物的尺寸
WIDTH = SIZE * 30      # 屏幕宽度
HEIGHT = SIZE * 30     # 屏幕高度

counter = 0            # 延迟变量，控制贪食蛇移动速度
direction = "east"     # 移动方向
dirs = {"east":(1, 0), "west":(-1, 0),
"north":(0, -1), "south":(0, 1)}

# 创建贪食蛇头
snake_head = Actor("snake_head", (30 , 30))


# 更新游戏逻辑
def update():
    check_keys()
    update_snake()


# 绘制游戏角色
def draw():
    screen.fill((255, 255, 255))
    snake_head.draw()


# 检查方向键的按下事件，来设置蛇头移动方向
def check_keys():
    global direction
    #根据所按下的键来设置方向值，并设置蛇头的正确朝向
    if keyboard.right and direction != "west":
        direction = "east"
        snake_head.angle = 0
    elif keyboard.left and direction != "east":
        direction = "west"
        snake_head.angle = 180
    elif keyboard.up and direction != "south":
        direction = "north"
        snake_head.angle = 90
    elif keyboard.down and direction != "north":
        direction = "south"
        snake_head.angle = -90


# 更新贪食蛇
def update_snake():
    # 延缓贪食蛇移动速度
    global counter
    counter += 1
    if counter < 10:
        return
    else:
        counter = 0
	# 更新蛇头的坐标
    dx, dy = dirs[direction]
    snake_head.x += dx * SIZE
    snake_head.y += dy * SIZE
