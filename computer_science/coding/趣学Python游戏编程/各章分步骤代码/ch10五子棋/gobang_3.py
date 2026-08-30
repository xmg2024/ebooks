# -*- coding:gb18030 -*-
# 五子棋游戏分步骤代码3：完善游戏规则

import random
SIZE = 40                       # 棋盘方格尺寸
WIDTH = SIZE * 15               # 屏幕宽度
HEIGHT = SIZE * 15              # 屏幕高度

# 棋盘信息列表
board = [[" "for i in range(15)]for j in range(15)]
chesses = []                    # 棋子列表
turn = "b"                      # 当前走棋方
last_turn = "w"                 # 上一步走棋方
gameover = False                # 游戏结束标记


# 处理鼠标点击事件
def on_mouse_down(pos, button):
    if gameover:
        return
    if button == mouse.LEFT:             # 点击鼠标左键下棋
        play(pos)
    elif button == mouse.RIGHT:          # 点击鼠标右键悔棋
        retract()


# 更新游戏逻辑
def update():
    global gameover
    if gameover:
        return
    if check_win():
         gameover = True
         if last_turn == "b":
             sounds.win.play()
         else:
             sounds.fail.play()
         return


# 绘制游戏图像
def draw():
    screen.fill((210, 180, 140))
    draw_board()
    draw_chess()
    draw_text()


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


# 玩家悔棋操作
def retract():
    if len(chesses) == 0:
        return
    for i in range(2):                       # 连续撤回两枚棋子
        chess = chesses.pop()
        col = int(chess.x - 20) // SIZE
        row = int(chess.y - 20) // SIZE
        board[col][row] = " "


# 检查走棋某一方是否获胜
def check_win( ):
    a = last_turn
    # 从左到右判断是否形成五子连珠
    for i in range(11):
        for j in range(15):
            if board[i][j] == a and board[i+1][j] == a and board[i+2][j] == a \
               and board[i+3][j] == a and board[i+4][j] == a :
                return True
    # 从上到下判断是否形成五子连珠
    for i in range(15):
        for j in range(11):
            if board[i][j] == a and board[i][j+1] == a and board[i][j+2] == a \
               and board[i][j+3] == a and board[i][j+4] == a :
                return True
    # 从左上到右下判断是否形成五子连珠
    for i in range(11):
        for j in range(11):
            if board[i][j] == a \
            and board[i+1][j+1] == a and board[i+2][j+2] == a \
            and board[i+3][j+3] == a and board[i+4][j+4] == a :
                return True
    # 从左下到右上判断是否形成五子连珠
    for i in range(11):
        for j in range(4, 15):
            if board[i][j] == a \
            and board[i+1][j-1] == a and board[i+2][j-2] == a \
            and board[i+3][j-3] == a and board[i+4][j-4] == a :
                return True
    return False


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


#  绘制文字提示
def draw_text():
    if not gameover:
        return
    if last_turn == "b":
        text = "You Win"
    else:
        text = "You Lost"
    screen.draw.text(text, center=(WIDTH // 2, HEIGHT // 2), fontsize=100, color="red")
