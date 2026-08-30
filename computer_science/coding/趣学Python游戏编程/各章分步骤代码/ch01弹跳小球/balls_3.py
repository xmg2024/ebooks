# -*- coding:gb18030 -*-
# 弹跳小球分步骤代码3：建立游戏世界

WIDTH = 800                    # 屏幕宽度
HEIGHT = 600                   # 屏幕高度

ball = Actor("breakout_ball", (200, 100))   # 创建小球角色

# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))    # 清空屏幕
    ball.draw()                     # 绘制小球
