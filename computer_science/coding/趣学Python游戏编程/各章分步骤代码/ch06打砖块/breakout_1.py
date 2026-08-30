# -*- coding:gb18030 -*-
# 打砖块游戏分步骤代码1：创建场景及角色

import random
WIDTH = 640        # 屏幕宽度
HEIGHT = 400       # 屏幕高度
BRICK_W = 80       # 砖块宽度
BRICK_H = 20       # 砖块高度

# 创建挡板
pad = Actor("breakout_paddle", (WIDTH // 2, HEIGHT - 30))

# 创建小球
ball = Actor("breakout_ball", (WIDTH // 2, HEIGHT - 47))

# 创建砖块列表
bricks = []

# 创建砖块
for i in range(5):
    for j in range(WIDTH // BRICK_W):
        brick = Actor("breakout_brick")
        brick.left = j * BRICK_W
        brick.top = 30 + i * BRICK_H
        bricks.append(brick)


# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))
    ball.draw()
    pad.draw()
    for brick in bricks:
        brick.draw()
