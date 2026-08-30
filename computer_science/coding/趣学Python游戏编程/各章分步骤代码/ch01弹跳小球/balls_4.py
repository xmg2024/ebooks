# -*- coding:gb18030 -*-
# 弹跳小球分步骤代码4：移动小球

WIDTH = 800                    # 屏幕宽度
HEIGHT = 600                   # 屏幕高度

ball = Actor("breakout_ball", (200, 100))   # 创建小球角色


# 更新游戏逻辑
def update():
    ball.x += 1           # 更新小球水平坐标
    ball.y += 1           # 更新小球垂直坐标


# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))    # 清空屏幕
    ball.draw()                     # 绘制小球
