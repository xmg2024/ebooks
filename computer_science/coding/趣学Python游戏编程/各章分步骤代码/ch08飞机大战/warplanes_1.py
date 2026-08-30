# -*- coding:gb18030 -*-
#飞机大战游戏分步骤代码1：创建游戏场景

import random, time, math
WIDTH = 480                 # 屏幕宽度
HEIGHT = 680                # 屏幕高度
backgrounds = []            # 背景图像列表
backgrounds.append(Actor("warplanes_background", topleft=(0, 0)))
backgrounds.append(Actor("warplanes_background", bottomleft=(0, 0)))


# 更新游戏逻辑
def update():
    update_background()


# 绘制游戏场景和角色
def draw():
    for backimgae in backgrounds:
        backimgae.draw()


# 更新游戏场景
def update_background():
    for backimage in backgrounds:
        backimage.y += 2
        if backimage.top > HEIGHT:
            backimage.bottom = 0
