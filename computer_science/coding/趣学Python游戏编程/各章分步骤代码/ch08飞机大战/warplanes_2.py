# -*- coding:gb18030 -*-
#飞机大战游戏分步骤代码2：添加英雄战机

import random, time, math
WIDTH = 480                 # 屏幕宽度
HEIGHT = 680                # 屏幕高度
backgrounds = []            # 背景图像列表
backgrounds.append(Actor("warplanes_background", topleft=(0, 0)))
backgrounds.append(Actor("warplanes_background", bottomleft=(0, 0)))
hero = Actor("warplanes_hero1", midbottom=(WIDTH // 2, HEIGHT - 50))
hero.speed = 5              # 战机移动速度
hero.animcount = 0          # 战机动画计数


# 更新游戏逻辑
def update():
    update_background()
    update_hero()


# 绘制游戏场景和角色
def draw():
    for backimgae in backgrounds:
        backimgae.draw()
    hero.draw()


# 更新游戏场景
def update_background():
    for backimage in backgrounds:
        backimage.y += 2
        if backimage.top > HEIGHT:
            backimage.bottom = 0


# 更新战机
def update_hero():
    move_hero()
    # 播放战机飞行动画
    hero.animcount = (hero.animcount + 1) % 20
    if hero.animcount == 0:
        hero.image = "warplanes_hero1"
    elif hero.animcount == 10:
        hero.image = "warplanes_hero2"


# 移动战机
def move_hero():
    if keyboard.right:
        hero.x += hero.speed
    elif keyboard.left:
        hero.x -= hero.speed
    if keyboard.down:
        hero.y += hero.speed
    elif keyboard.up:
        hero.y -= hero.speed

    if hero.left < 0:
        hero.left = 0
    elif hero.right > WIDTH:
        hero.right = WIDTH
    if hero.top < 0:
        hero.top = 0
    elif hero.bottom > HEIGHT:
        hero.bottom = HEIGHT
