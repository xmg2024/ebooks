# -*- coding:gb18030 -*-
# 五子棋游戏分步骤代码1：创建棋盘和棋子

import random
SIZE = 40                       # 棋盘方格尺寸
WIDTH = SIZE * 15               # 屏幕宽度
HEIGHT = SIZE * 15              # 屏幕高度


# 绘制游戏图像
def draw():
    screen.fill((210, 180, 140))
    draw_board()


# 绘制棋盘
def draw_board():
    for i in range(15):
        screen.draw.line((20, SIZE * i + 20), (580, SIZE * i + 20), (0, 0, 0))
    for i in range(15):
        screen.draw.line((SIZE * i + 20, 20), (SIZE * i + 20, 580), (0, 0, 0))
