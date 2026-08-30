# -*- coding:gb18030 -*-
# 打字游戏分步骤代码3：实现打字功能

import random, time
WIDTH = 640                       # 屏幕宽度
HEIGHT = 400                      # 屏幕高度
MAX_NUM = 5                       # 窗口中气球的最大数量
balloons = []                     # 气球列表
balloon_queue = []                # 命中的气球队列


# 更新游戏逻辑
def update():
    if len(balloons) < MAX_NUM:
        add_balloon()
    update_balloon()


# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))
    for balloon in balloons:
        balloon.draw()
        # 绘制气球上的字母，若命中显示白色，否则为黑色
        if balloon.typed:
            screen.draw.text(balloon.char,center=balloon.center,color="white")
        else:
            screen.draw.text(balloon.char,center=balloon.center,color="black")


# 处理键盘按键事件
def on_key_down(key):
    # 检测按键是否和气球的字符相对应
    for balloon in balloons:
        if balloon.y > 0 and str(key) == "keys." + balloon.char:
            balloon.typed = True
            balloon_queue.append(balloon)
            # 延迟消除气球
            clock.schedule(remove_balloon, 0.3)
            break


# 从窗口中删除气球
def remove_balloon():
    sounds.eat.play()
    balloon = balloon_queue.pop(0)
    if balloon in balloons:
        balloons.remove(balloon)


# 向窗口中添加气球
def add_balloon():
    balloon = Actor("typing_balloon", (WIDTH // 2, HEIGHT))
    balloon.x = random_location()
    balloon.vy = random_velocity()
    balloon.char = random_char()
    balloon.typed = False
    balloons.append(balloon)


# 随机生成气球的初始位置
def random_location():
    min_dx = 0
    while min_dx < 50:
        min_dx = WIDTH
        x = random.randint(20, WIDTH - 20)
        for balloon in balloons:
            dx = abs(balloon.x - x)
            min_dx = min(min_dx, dx)
    return x


# 随机生成气球的移动速度
def random_velocity():
    n = random.randint(1, 100)
    if n <= 5:
        velocity = -5
    elif n <= 25:
        velocity = -4
    elif n <= 75:
        velocity = -3
    elif n <= 95:
        velocity = -2
    else:
        velocity = -1
    return velocity


# 随机生成气球上的字母
def random_char():
    charset = set()
    for balloon in balloons:
        charset.add(balloon.char)
    ch = chr(random.randint(65, 90))
    while ch in charset:
        ch = chr(random.randint(65, 90))
    return ch


# 更新气球的位置
def update_balloon():
    for balloon in balloons:
        balloon.y += balloon.vy
        if balloon.bottom < 0:
            balloons.remove(balloon)
