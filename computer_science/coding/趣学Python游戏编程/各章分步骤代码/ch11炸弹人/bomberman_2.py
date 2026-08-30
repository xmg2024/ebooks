# -*- coding:gb18030 -*-
# 炸弹人分步骤代码2: 创建玩家角色

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

# 玩家角色类
class Player(Actor):
    def __init__(self, img, pos):
        super().__init__(img, pos)
        self.clock = 0          # 动画帧计时
        self.speed = 2.5        # 移动速度
    # 更新角色
    def update(self):
        # 更新计时
        self.clock=(self.clock+1)%60
    # 移动角色
    def move(self,dx,dy):
        self.x=self.x+dx     # 水平位移
        self.y=self.y+dy     # 垂直位移
        # 更新角色图片
        if dy>0 and dx==0:    # 向下
            self.image = str(self.clock//20)+"player1down.png"
        if dy<0 and dx==0:    # 向上
            self.image = str(self.clock//20)+"player1up.png"
        if dy==0 and dx>0:    # 向右
            self.image = str(self.clock//20)+"player1right.png"
        if dy==0 and dx<0:    # 向左
            self.image = str(self.clock//20)+"player1left.png"
        # 碰撞检测，若角色碰到方块或砖块则回退
        for obj in objs:
            if self.colliderect(obj):
                self.x=self.x-dx
                self.y=self.y-dy
                break

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
    p1.draw()

# 按键事件处理
def check_keys():
    # 玩家1的键盘按键处理
    if keyboard.w:
        p1.move(0,-p1.speed)
    if keyboard.s:
        p1.move(0,p1.speed)
    if keyboard.a:
        p1.move(-p1.speed,0)
    if keyboard.d:
        p1.move(p1.speed,0)

# 更新游戏逻辑
def update():
    check_keys()
    p1.update()

newgame()
p1 = Player("1player1down.png", (75,75))
