# -*- coding:gb18030 -*-
# Flappy Bird游戏分步骤代码2：添加障碍物

import random
WIDTH = 138 * 4             # 窗口宽度（由四张背景图片组成）
HEIGHT = 396                # 窗口高度
GAP = 150                   # 上下水管间的缺口大小
SPEED = 3                   # 场景滚动速度

backgrounds = []            # 背景图像列表

# 创建五张背景图像角色，用于循环滚动游戏场景
for i in range(5):
    backimage = Actor("flappybird_background", topleft=(i * 138, 0))
    backgrounds.append(backimage)

# 创建地面角色
ground = Actor("flappybird_ground", bottomleft=(0, HEIGHT))

# 创建上下水管角色
pipe_top = Actor("flappybird_top_pipe")
pipe_bottom = Actor("flappybird_bottom_pipe")


# 游戏逻辑更新
def update():
    update_background()
    update_ground()
    update_pipes()


# 绘制游戏角色
def draw():
    screen.fill((255, 255, 255))
    for backimage in backgrounds:
        backimage.draw()
    pipe_top.draw()
    pipe_bottom.draw()
    ground.draw()


# 更新游戏场景，循环滚动背景图像
def update_background():
    for backimage in backgrounds:
        backimage.x -= SPEED
        if backimage.right <= 0:
            backimage.left = WIDTH


# 更新地面角色
def update_ground():
    ground.x -= SPEED
    if ground.right < WIDTH:
        ground.left = 0


# 更新水管角色
def update_pipes():
    pipe_top.x -= SPEED
    pipe_bottom.x -= SPEED
    if pipe_top.right < 0:
        reset_pipes()


# 重新设置上下水管出现的位置
def reset_pipes():
    # 随机生成上方水管的垂直位置
    pipe_top.bottom = random.randint(50, 150)
    # 根据上方水管的垂直位置来设置下方水管的垂直位置
    pipe_bottom.top = pipe_top.bottom + GAP
    # 设置上下水管的水平位置
    pipe_top.left = WIDTH
    pipe_bottom.left = WIDTH
reset_pipes()
