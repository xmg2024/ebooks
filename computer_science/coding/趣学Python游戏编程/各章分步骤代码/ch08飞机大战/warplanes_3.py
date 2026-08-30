# -*- coding:gb18030 -*-
#飞机大战游戏分步骤代码3：添加子弹

import random, time, math
WIDTH = 480                 # 屏幕宽度
HEIGHT = 680                # 屏幕高度
backgrounds = []            # 背景图像列表
backgrounds.append(Actor("warplanes_background", topleft=(0, 0)))
backgrounds.append(Actor("warplanes_background", bottomleft=(0, 0)))
hero = Actor("warplanes_hero1", midbottom=(WIDTH // 2, HEIGHT - 50))
hero.speed = 5              # 战机移动速度
hero.animcount = 0          # 战机动画计数
hero.power = False          # 子弹增强标记

bullets = []                # 子弹列表
powers = []                 # 增强道具列表


# 更新游戏逻辑
def update():
    update_background()
    update_hero()
    update_bullets()
    update_powerup()


# 绘制游戏场景和角色
def draw():
    for backimgae in backgrounds:
        backimgae.draw()
    for powerup in powers:
        powerup.draw()
    for bullet in bullets:
        bullet.draw()
    hero.draw()


# 更新游戏场景
def update_background():
    for backimage in backgrounds:
        backimage.y += 2
        if backimage.top > HEIGHT:
            backimage.bottom = 0


# 更新战机
def update_hero():
    move_hero()
    # 播放战机飞行动画
    hero.animcount = (hero.animcount + 1) % 20
    if hero.animcount == 0:
        hero.image = "warplanes_hero1"
    elif hero.animcount == 10:
        hero.image = "warplanes_hero2"


# 移动战机
def move_hero():
    if keyboard.right:
        hero.x += hero.speed
    elif keyboard.left:
        hero.x -= hero.speed
    if keyboard.down:
        hero.y += hero.speed
    elif keyboard.up:
        hero.y -= hero.speed
    if keyboard.space:
        clock.schedule_unique(shoot, 0.1)    # 射击冻结时间为0.1秒
    if hero.left < 0:
        hero.left = 0
    elif hero.right > WIDTH:
        hero.right = WIDTH
    if hero.top < 0:
        hero.top = 0
    elif hero.bottom > HEIGHT:
        hero.bottom = HEIGHT


# 子弹射击
def shoot():
    sounds.bullet.play()
    bullets.append(Actor("warplanes_bullet", midbottom=(hero.x, hero.top)))
    # 如果获得增强道具则额外添加两枚子弹
    if hero.power:
        leftbullet = Actor("warplanes_bullet", midbottom=(hero.x, hero.top))
        leftbullet.angle = 15
        bullets.append(leftbullet)
        rightbullet = Actor("warplanes_bullet", midbottom=(hero.x, hero.top))
        rightbullet.angle = -15
        bullets.append(rightbullet)


# 更新子弹
def update_bullets():
    for bullet in bullets:
        theta = math.radians(bullet.angle + 90)
        bullet.x += 10 * math.cos(theta)
        bullet.y -= 10 * math.sin(theta)
        if bullet.bottom < 0:
            bullets.remove(bullet)


# 更新增强道具
def update_powerup():
    for powerup in powers:
        powerup.y += 2
        if powerup.top > HEIGHT:
            powers.remove(powerup)
        elif powerup.colliderect(hero):
            powers.remove(powerup)
            hero.power = True
            clock.schedule(powerdown, 5.0)      # 5秒钟后取消增强效果
    if hero.power or len(powers) != 0:
        return
    # 随机生成增强道具
    if random.randint(1, 1000) < 5:
            x = random.randint(50, WIDTH)
            powerup = Actor("warplanes_powerup", bottomright=(x, 0))
            powers.append(powerup)


# 取消子弹增强效果
def powerdown():
    hero.power = False

