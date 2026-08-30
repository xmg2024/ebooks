# -*- coding:gb18030 -*-
# 打砖块游戏分步骤代码3：处理角色间的碰撞

import random
WIDTH = 640        # 屏幕宽度
HEIGHT = 400       # 屏幕高度
BRICK_W = 80       # 砖块宽度
BRICK_H = 20       # 砖块高度
started = False    # 小球发射标记


# 创建挡板
pad = Actor("breakout_paddle", (WIDTH // 2, HEIGHT - 30))
pad.speed = 5      # 挡板移动速度

# 创建小球
ball = Actor("breakout_ball", (WIDTH // 2, HEIGHT - 47))

# 创建砖块列表
bricks = []
for i in range(5):
    for j in range(WIDTH // BRICK_W):
        brick = Actor("breakout_brick")
        brick.left = j * BRICK_W
        brick.top = 30 + i * BRICK_H
        bricks.append(brick)


# 更新游戏逻辑
def update():
    pad_move()
    ball_move()
    collision_ball_bricks()
    collision_ball_pad()


# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))
    ball.draw()
    pad.draw()
    for brick in bricks:
        brick.draw()


# 移动挡板
def pad_move():
    # 用键盘控制挡板移动
    if keyboard.right:
        pad.x += pad.speed
    elif keyboard.left:
        pad.x -= pad.speed
    # 将挡板限制在窗口范围内
    if pad.left < 0:
        pad.left = 0
    elif pad.right > WIDTH :
        pad.right = WIDTH


# 移动小球
def ball_move():
    global started
    # 检测是否发射小球
    if not started:
        if keyboard.space:
            dir = 1 if random.randint(0, 1) else -1
            ball.vx = 3 * dir
            ball.vy = -3
            started = True
        else:
            ball.x = pad.x
            ball.bottom = pad.top
            return
    # 更新小球坐标
    ball.x += ball.vx
    ball.y += ball.vy
    # 检测及处理小球与窗口四周的碰撞
    if ball.left < 0:
        ball.vx = abs(ball.vx)
    elif ball.right > WIDTH:
        ball.vx = -abs(ball.vx)
    if ball.top < 0:
        ball.vy = abs(ball.vy)
    elif ball.top > HEIGHT:
        started = False
        sounds.miss.play()


# 检测并处理小球与砖块的碰撞
def collision_ball_bricks():
    # 检测小球是否碰到砖块，若没有则返回
    n = ball.collidelist(bricks)
    if n == -1:
        return
    # 移除碰到的方块
    brick = bricks[n]
    bricks.remove(brick)
    sounds.collide.play()
    # 设置小球反弹方向
    if  brick.left < ball.x < brick.right:     # 碰到砖块中部的反弹
        ball.vy *= -1
    elif ball.x <= brick.left:                 # 碰到砖块左部的反弹
        if ball.vx > 0:
            ball.vx *= -1
        else:
            ball.vy *= -1
    elif ball.x >= brick.right:                # 碰到砖块右部的反弹
        if ball.vx < 0:
            ball.vx *= -1
        else:
            ball.vy *= -1


# 检测并处理小球与挡板的碰撞
def collision_ball_pad():
    # 检测小球是否碰到挡板，若没有则返回
    if not ball.colliderect(pad):
        return
    # 垂直方向反弹
    if ball.y < pad.y:
        ball.vy = -abs(ball.vy)
        sounds.bounce.play()
    # 水平方向反弹
    if ball.x < pad.x:
        ball.vx = -abs(ball.vx)
    else:
        ball.vx = abs(ball.vx)
