# -*- coding:gb18030 -*-
# 炸弹人分步骤代码1: 创建游戏场景

import random

HEIGHT=850
WIDTH=850
TITLE="Bomberman"
objs = []

# 方块类，炸弹可以炸开
class Block(Actor):
    pass

# 砖块类，炸弹不能炸开
class Brick(Actor):
    pass

# 初始化游戏
def newgame():
    # 在游戏场景四周添加砖块边界
    for i in range(17):
        objs.append(Brick("brick.png",topleft=(i*50,0)))
        objs.append(Brick("brick.png",topleft=(i*50,HEIGHT-50)))
    for i in range(15):
        objs.append(Brick("brick.png",topleft=(0,i*50+50)))
        objs.append(Brick("brick.png",topleft=(WIDTH-50,i*50+50)))
    # 读取地图文件，并根据文件中的标记添加方块
    with open('maps/map1.txt') as file:
        i=1
        for line in file:
            for j in range(len(line)):
                if line[j]=="#":
                    objs.append(Block("block.png",topleft=(j*50+50, i*50)))
            i=i+1

# 绘制游戏图像
def draw():
    screen.fill((148, 146, 255))
    for obj in objs:
        obj.draw()

# 更新游戏逻辑
def update():
    pass

newgame()
