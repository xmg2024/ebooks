# -*- coding:gb18030 -*-
# 弹跳小球分步骤代码5：实现小球反弹

WIDTH = 800                    # 屏幕宽度
HEIGHT = 600                   # 屏幕高度

ball = Actor("breakout_ball", (200, 100))   # 创建小球角色
ball.dx = 5                                 # 设置小球水平速度
ball.dy = 5                                 # 设置小球垂直速度


# 更新游戏逻辑
def update():
    ball.x += ball.dx           # 更新小球水平坐标
    ball.y += ball.dy           # 更新小球垂直坐标
    # 若小球碰到屏幕左右边界，则水平反向
    if ball.right > WIDTH or ball.left < 0:
        ball.dx = -ball.dx
    # 若小球碰到屏幕上下边界，则垂直反向
    if ball.bottom > HEIGHT or ball.top < 0:
        ball.dy = -ball.dy


# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))    # 清空屏幕
    ball.draw()                 # 绘制小球
