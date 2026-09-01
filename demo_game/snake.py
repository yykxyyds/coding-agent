# -*- coding: utf-8 -*-
"""经典贪吃蛇游戏 — 基于 tkinter 实现，无需额外依赖。"""

import random
import tkinter as tk
from tkinter import messagebox

# 游戏参数
CELL = 20                # 每个格子像素大小
ROWS, COLS = 25, 30      # 网格行列数
WIDTH = CELL * COLS
HEIGHT = CELL * ROWS
BASE_SPEED = 150         # 基础帧间隔(毫秒)，数值越小越快
MIN_SPEED = 70           # 最快速度

# 颜色
COLOR_BG = "#1e1e1e"
COLOR_SNAKE = "#4caf50"
COLOR_SNAKE_HEAD = "#81c784"
COLOR_FOOD = "#f44336"
COLOR_TEXT = "#eeeeee"


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("贪吃蛇 🐍")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        # 分数显示
        self.score_label = tk.Label(root, text="分数: 0    速度: 1x",
                                    font=("Consolas", 12, "bold"),
                                    bg=COLOR_BG, fg=COLOR_TEXT)
        self.score_label.pack(pady=5)

        self._init_game()
        self._bind_keys()

        # 开始游戏
        self.root.after(BASE_SPEED, self._game_loop)

    def _init_game(self):
        """初始化游戏状态。"""
        # 蛇：每个元素是 (row, col)，初始在中间，向右走
        mid_r, mid_c = ROWS // 2, COLS // 2
        self.snake = [(mid_r, mid_c - 2), (mid_r, mid_c - 1), (mid_r, mid_c)]
        self.direction = (0, 1)          # 移动方向 (dr, dc)
        self.next_direction = (0, 1)
        self.food = None
        self.score = 0
        self.game_over = False
        self.paused = False
        self._spawn_food()

    def _spawn_food(self):
        """在空白位置随机生成一个食物。"""
        occupied = set(self.snake)
        free = [(r, c) for r in range(ROWS) for c in range(COLS)
                if (r, c) not in occupied]
        if not free:
            # 蛇占满了整个屏幕，胜利！
            self._win()
            return
        self.food = random.choice(free)

    def _bind_keys(self):
        """绑定键盘事件。"""
        self.root.bind("<Up>", lambda e: self._set_dir(-1, 0))
        self.root.bind("<Down>", lambda e: self._set_dir(1, 0))
        self.root.bind("<Left>", lambda e: self._set_dir(0, -1))
        self.root.bind("<Right>", lambda e: self._set_dir(0, 1))
        self.root.bind("<space>", lambda e: self._toggle_pause())
        self.root.bind("<r>", lambda e: self._restart())
        self.root.bind("<Escape>", lambda e: self._toggle_pause())

    def _set_dir(self, dr, dc):
        """更新移动方向（不允许直接反向）。"""
        if (dr, dc) == (-self.direction[0], -self.direction[1]):
            return
        self.next_direction = (dr, dc)

    def _toggle_pause(self):
        if self.game_over:
            return
        self.paused = not self.paused

    def _restart(self):
        self._init_game()
        self._draw()
        self._update_score_text()

    def _game_loop(self):
        """主循环。"""
        if not self.game_over and not self.paused:
            self._step()
        # 根据分数调整速度（每 5 分加一档速度）
        speed = max(BASE_SPEED - (self.score // 5) * 15, MIN_SPEED)
        self.root.after(speed, self._game_loop)

    def _step(self):
        """执行一次移动逻辑。"""
        self.direction = self.next_direction
        dr, dc = self.direction
        head_r, head_c = self.snake[-1]
        new_head = (head_r + dr, head_c + dc)

        # 检查撞墙
        if not (0 <= new_head[0] < ROWS and 0 <= new_head[1] < COLS):
            self._game_over("撞墙了！")
            return

        # 检查撞到自己（吃到食物时尾巴会移动，不会立刻撞到）
        eating = (new_head == self.food)
        body_to_check = self.snake[:-1] if eating else self.snake
        if new_head in body_to_check:
            self._game_over("撞到自己了！")
            return

        # 移动蛇
        self.snake.append(new_head)
        if eating:
            self.score += 1
            self._spawn_food()
        else:
            self.snake.pop(0)

        self._draw()
        self._update_score_text()

    def _draw(self):
        """绘制画面。"""
        self.canvas.delete("all")

        # 绘制网格线（轻量背景）
        for i in range(ROWS):
            self.canvas.create_line(0, i * CELL, WIDTH, i * CELL,
                                    fill="#2a2a2a")
        for j in range(COLS):
            self.canvas.create_line(j * CELL, 0, j * CELL, HEIGHT,
                                    fill="#2a2a2a")

        # 绘制蛇
        for i, (r, c) in enumerate(self.snake):
            x1, y1 = c * CELL, r * CELL
            x2, y2 = x1 + CELL, y1 + CELL
            color = COLOR_SNAKE_HEAD if i == len(self.snake) - 1 else COLOR_SNAKE
            self.canvas.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                                         fill=color, outline="")

        # 绘制食物
        if self.food:
            r, c = self.food
            x1, y1 = c * CELL, r * CELL
            x2, y2 = x1 + CELL, y1 + CELL
            self.canvas.create_oval(x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                                    fill=COLOR_FOOD, outline="")

        # 暂停/结束提示
        if self.paused:
            self._draw_overlay("暂停中...\n按空格继续")
        if self.game_over:
            self._draw_overlay(f"游戏结束！得分：{self.score}\n按 R 重新开始")

    def _draw_overlay(self, text):
        self.canvas.create_rectangle(0, HEIGHT // 2 - 40, WIDTH,
                                     HEIGHT // 2 + 40, fill="#00000088",
                                     outline="")
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text=text,
                                fill=COLOR_TEXT, font=("Consolas", 16, "bold"))

    def _update_score_text(self):
        level = max(self.score // 5 + 1, 1)
        self.score_label.config(text=f"分数: {self.score}    速度: {level}x")

    def _game_over(self, reason):
        self.game_over = True
        messagebox.showinfo("游戏结束", f"{reason}\n最终得分：{self.score}\n按 R 重新开始")
        self._draw()

    def _win(self):
        self.game_over = True
        messagebox.showinfo("恭喜！", "你填满了整个屏幕，太厉害了！")
        self._draw()


def main():
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
