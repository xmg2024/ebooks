# -*- coding:gb18030 -*-
# 贪食蛇分步骤代码1：创建场景和角色

import random
SIZE = 15              # 贪食蛇及食物的尺寸
WIDTH = SIZE * 30      # 屏幕宽度
HEIGHT = SIZE * 30     # 屏幕高度


# 创建贪食蛇头
snake_head = Actor("snake_head", (30 , 30))


# 绘制游戏角色
def draw():
    screen.fill((255, 255, 255))
    snake_head.draw()
