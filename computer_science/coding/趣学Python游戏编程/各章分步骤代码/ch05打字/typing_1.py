# -*- coding:gb18030 -*-
# 打字游戏分步骤代码1：创建一个字母气球

WIDTH = 640                       # 屏幕宽度
HEIGHT = 400                      # 屏幕高度

balloon = Actor("typing_balloon", (WIDTH // 2, HEIGHT))
balloon.char = "A"

# 更新游戏逻辑
def update():
    balloon.y += -1


# 绘制游戏图像
def draw():
    screen.fill((255, 255, 255))
    balloon.draw()
    # 绘制气球上的字母
    screen.draw.text(balloon.char,center=balloon.center,color="black")
