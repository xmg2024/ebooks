# -*- coding:gb18030 -*-
# 扫雷分步骤代码2：给方块插上旗子

import random
BOMBS = 20               # 炸弹数量
ROWS = 15                # 方块行数
COLS = 15                # 方块列数
SIZE = 25                # 方块尺寸
WIDTH = SIZE * COLS      # 屏幕宽度
HEIGHT = SIZE * ROWS     # 屏幕高度
blocks = []              # 方块列表

# 将所有方块添加到场景中
for i in range(ROWS):
    for j in range(COLS):
        block = Actor("minesweep_block")
        block.left = j * SIZE       # 设置方块的水平位置
        block.top = i * SIZE        # 设置方块的垂直位置
        block.isbomb = False        # 标记方块是否埋设地雷
        block.isflag = False        # 标记方块是否插上棋子
        blocks.append(block)

# 随机打乱方块列表的次序
random.shuffle(blocks)

# 埋设地雷
for i in range(BOMBS):
    blocks[i].isbomb = True


# 绘制游戏图像
def draw():
    for block in blocks:
        block.draw()


# 处理鼠标点击事件
def on_mouse_down(pos, button):
    for block in blocks:
        # 若方块被鼠标点击，且该方块未曾打开
        if block.collidepoint(pos):
            # 若鼠标右键点击方块
            if button == mouse.RIGHT:
                set_flag(block)


# 为方块插上棋子
def set_flag(block):
    if not block.isflag:
        block.image = "minesweep_flag"
        block.isflag = True
    else:
        block.image = "minesweep_block"
        block.isflag = False
