# -*- coding:gb18030 -*-
# 五子棋游戏分步骤代码2：执行走棋操作

import random
SIZE = 40                       # 棋盘方格尺寸
WIDTH = SIZE * 15               # 屏幕宽度
HEIGHT = SIZE * 15              # 屏幕高度

# 棋盘信息列表
board = [[" "for i in range(15)]for j in range(15)]
chesses = []                    # 棋子列表
turn = "b"                      # 当前走棋方
last_turn = "w"                 # 上一步走棋方


# 处理鼠标点击事件
def on_mouse_down(pos, button):
    if button == mouse.LEFT:             # 点击鼠标左键下棋
        play(pos)


# 绘制游戏图像
def draw():
    screen.fill((210, 180, 140))
    draw_board()
    draw_chess()


# 玩家下棋操作
def play(pos):
    col = pos[0] // SIZE
    row = pos[1] // SIZE
    if board[col][row] != " ":
        return
    if turn == "b":
        chess = Actor("gobang_black", (col * SIZE + 20, row * SIZE + 20))
    else:
        chess = Actor("gobang_white", (col * SIZE + 20, row * SIZE + 20))
    chesses.append(chess)
    board[col][row] = turn
    change_side()


# 交换下棋双方
def change_side():
    global turn, last_turn
    last_turn = turn
    if turn == "b":
        turn = "w"
    else:
        turn = "b"


# 绘制棋子
def draw_chess():
    for chess in chesses:
        chess.draw()
    # 为上一步走的棋子绘制提示框
    if len(chesses) > 0:
        chess = chesses[-1]
        rect = Rect(chess.topleft, (36, 36))
        screen.draw.rect(rect, (255, 255, 255))


# 绘制棋盘
def draw_board():
    for i in range(15):
        screen.draw.line((20, SIZE * i + 20), (580, SIZE * i + 20), (0, 0, 0))
    for i in range(15):
        screen.draw.line((SIZE * i + 20, 20), (SIZE * i + 20, 580), (0, 0, 0))
