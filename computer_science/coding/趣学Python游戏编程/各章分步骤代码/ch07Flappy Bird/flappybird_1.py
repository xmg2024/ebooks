# -*- coding:gb18030 -*-
# Flappy Bird游戏分步骤代码1：创建游戏场景

import random
WIDTH = 138 * 4             # 窗口宽度（由四张背景图片组成）
HEIGHT = 396                # 窗口高度
SPEED = 3                   # 场景滚动速度

backgrounds = []            # 背景图像列表

# 创建五张背景图像角色，用于循环滚动游戏场景
for i in range(5):
    backimage = Actor("flappybird_background", topleft=(i * 138, 0))
    backgrounds.append(backimage)


# 游戏逻辑更新
def update():
    update_background()


# 绘制游戏角色
def draw():
    screen.fill((255, 255, 255))
    for backimage in backgrounds:
        backimage.draw()


# 更新游戏场景，循环滚动背景图像
def update_background():
    for backimage in backgrounds:
        backimage.x -= SPEED
        if backimage.right <= 0:
            backimage.left = WIDTH
