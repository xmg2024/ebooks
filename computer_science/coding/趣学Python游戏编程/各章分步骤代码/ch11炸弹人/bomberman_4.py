# -*- coding:gb18030 -*-
# 炸弹人分步骤代码4: 设置道具功能

import random

HEIGHT=850
WIDTH=850
TITLE="Bomberman"
objs = []

# 方块类，炸弹可以炸开
class Block(Actor):
    def update(self):
        pass

# 砖块类，炸弹不能炸开
class Brick(Actor):
    def update(self):
        pass

# 玩家角色类
class Player(Actor):
    def __init__(self, img, pos):
        super().__init__(img, pos)
        self.health = 3         # 生命值
        self.clock = 0          # 动画帧计时
        self.lastbombtime = 0   # 放置炸弹计时
        self.nbomb = 1          # 炸弹数量
        self.bombs=[]           # 炸弹列表
        self.radius = 1         # 爆炸半径
        self.speed = 2.5        # 移动速度
    # 更新角色
    def update(self):
        # 更新计时
        self.clock=(self.clock+1)%60
        self.lastbombtime += 1
        # 更新炸弹
        for bomb in self.bombs:
            bomb.update()
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
            if self.colliderect(obj) and obj.image in ["block.png","brick.png"]:
                self.x=self.x-dx
                self.y=self.y-dy
                break
    # 放置炸弹
    def plantbomb(self):
        x=int(self.x/50)*50                 # 炸弹横坐标
        y=int(self.y/50)*50                 # 炸弹纵坐标
        #若炸弹数未达上限，且距上次放置炸弹相隔二十帧，则重新放置一枚炸弹
        if len(self.bombs) < self.nbomb and self.lastbombtime>20:
            bomb = Bomb("bomb0.png", self)
            bomb.topleft = (x, y)
            self.bombs.append(bomb)         # 加入玩家的炸弹列表
            self.lastbombtime = 0           # 更新放置炸弹时间

# 炸弹类
class Bomb(Actor):
    def __init__(self, img, player):
        super().__init__(img)
        self.clock = 5      # 爆炸计时
        self.player = player
    # 更新炸弹
    def update(self):
        self.clock=self.clock-0.07      # 更新爆炸计时
        if int(self.clock)>=0:         # 更新炸弹图像
            self.image="bomb"+str(int(self.clock)) +".png"
            for obj in objs:            # 若炸弹碰到火焰则立即引爆
                if self.collidepoint(obj.pos) and obj.image in ["fire0.png","fire1.png","fire2.png"]:
                    self.detonate()
                    break
        else:
            self.detonate()             # 若计时减为零则引爆
    # 引爆炸弹
    def detonate(self):
        fire = Fire("fire0.png")
        fire.topleft=self.topleft
        objs.append(fire)
        for k in [[0,1],[0,-1],[1,0],[-1,0]]:         # 朝上下左右四个方向分别生成火焰
            for i in range(1,self.player.radius+1):   # 根据爆炸半径决定各方向的炸弹数
                fire = Fire("fire0.png")
                fire.left = self.left + 50 * i * k[0]
                fire.top = self.top + 50 * i * k[1]
                objs.append(fire)
                done = False
                for obj in objs:        # 检查火焰是否与砖块或方块碰撞
                    if fire.colliderect(obj) and obj.image in ["block.png","brick.png"]:
                        done = True
                if done:                # 若火焰碰到障碍物则停止朝该方向蔓延
                    break
        self.player.bombs.remove(self)  # 从玩家的炸弹列表中移除

# 火焰类
class Fire(Actor):
    def __init__(self, img):
        super().__init__(img)
        self.clock = 3      # 燃烧计时
    # 更新火焰
    def update(self):
        self.clock=self.clock-0.1       # 更新燃烧计时
        if int(self.clock)>=0:         # 更新火焰图像
            self.image="fire"+str(int(self.clock)) +".png"
        else:
            if self.colliderect(p1):    # 检测是否碰到玩家1
                p1.center=(75,75)
                p1.health=p1.health-1
            for obj in objs:            # 若碰到方块则有3%几率生成道具
                if self.colliderect(obj) and obj.image == "block.png":
                    if random.random()<0.03 :
                        objs.append(Bonus1("powerup.png",topleft=obj.topleft))
                    elif random.random()<0.03 :
                        objs.append(Bonus2("p1hearth.png",topleft=obj.topleft))
                    elif random.random()<0.03 :
                        objs.append(Bonus3("addone.png",topleft=obj.topleft))
                    objs.remove(obj)
                    break
            objs.remove(self)

# 道具一，增加爆炸半径，上限为5
class Bonus1(Actor):
    def update(self):
        if p1.colliderect(self):
            p1.radius=p1.radius+1
            if p1.radius > 5:
                p1.radius = 5
            objs.remove(self)

# 道具二，增加生命值，上限为7
class Bonus2(Actor):
    def update(self):
        if p1.colliderect(self):
            p1.health=p1.health+1
            if p1.health > 7:
                p1.health = 7
            objs.remove(self)

# 道具三，增加炸弹数量，上限为5
class Bonus3(Actor):
    def update(self):
        if p1.colliderect(self):
            p1.nbomb=p1.nbomb+1
            if p1.nbomb > 5:
                p1.nbomb = 5
            objs.remove(self)

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
    if p1.health>0:
        for obj in objs:
            obj.draw()
        p1.draw()
        for bomb in p1.bombs:
            bomb.draw()
        # 绘制生命值图像
        for i in range(p1.health):
            screen.blit("p1hearth.png",(i*50,HEIGHT-50))

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
    if keyboard.space:
        p1.plantbomb()

# 更新游戏逻辑
def update():
    check_keys()
    # 更新游戏角色
    for obj in objs:
        obj.update()
    p1.update()

newgame()
p1 = Player("1player1down.png", (75,75))
