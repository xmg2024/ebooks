# -*- coding:gb18030 -*-
# 拼图分步骤代码3：移动图片块

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


# 检测鼠标按下事件
def on_mouse_down(pos):
    grid_x = pos[0] // SIZE
    grid_y = pos[1] // SIZE
    # 获取当前鼠标点击的图片块
    thispic = get_pic(grid_x, grid_y)
    if thispic == None:
        return
    # 判断图片块是否可以向上移动
    if grid_y > 0 and get_pic(grid_x, grid_y - 1) == None:
        thispic.y -= SIZE
        return
    # 判断图片块是否可以向下移动
    if grid_y < 2 and get_pic(grid_x, grid_y + 1) == None:
        thispic.y += SIZE
        return
    # 判断图片块是否可以向左移动
    if grid_x > 0 and get_pic(grid_x - 1, grid_y) == None:
        thispic.x -= SIZE
        return
    # 判断图片块是否可以向右移动
    if grid_x < 2 and get_pic(grid_x + 1, grid_y) == None:
        thispic.x += SIZE
        return


# 获取某个方格处的图片块，参数为方格的水平与垂直索引值
def get_pic(grid_x, grid_y):
    for pic in pics:
        if pic.x // SIZE == grid_x and pic.y // SIZE == grid_y:
            return pic
    return None
