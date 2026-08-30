# -*- coding:gb18030 -*-
# 拼图分步骤代码2：打乱图片块

import random
SIZE = 96             # 图片块尺寸为96
WIDTH = SIZE * 3      # 屏幕宽度
HEIGHT = SIZE * 3     # 屏幕高度
pics = []             # 图片块列表

# 循环生成前8个图片块，并加入列表
for i in range(8):
    pic = Actor("puzzle_pic" + str(i))
    pic.index = i     # 图片块索引值
    pics.append(pic)

# 随机打乱列表中的图片块次序
random.shuffle(pics)

# 为列表中的图片设置初始位置
for i in range(8):
    pics[i].left = i % 3 * SIZE
    pics[i].top = i // 3 * SIZE


# 绘制游戏角色
def draw():
    screen.fill((255, 255, 255))
    # 绘制前8个图片块
    for pic in pics:
        pic.draw()
