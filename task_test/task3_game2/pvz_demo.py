# -*- coding: utf-8 -*-
"""
植物大战僵尸 Demo（tkinter 版）
经典玩法精简复刻：
- 5行 x 9列草地
- 植物：向日葵、豌豆射手、寒冰射手、坚果墙、樱桃炸弹
- 僵尸：普通僵尸、路障僵尸、铁桶僵尸
- 阳光系统、卡片选择、铲子、胜负判定

运行方式: python pvz_demo.py
"""
import tkinter as tk
import random
import math

# ===================== 常量配置 =====================
ROWS = 5                # 行数
COLS = 9                # 列数
CELL = 90               # 每个格子像素
MARGIN_X = 120          # 左侧留白（卡片栏/阳光区）
TOP = 90                # 顶部工具栏高度
WIDTH = MARGIN_X + COLS * CELL
HEIGHT = TOP + ROWS * CELL

GRID_X = MARGIN_X       # 网格起始x
GRID_Y = TOP            # 网格起始y

FPS = 60                # 刷新率（帧/秒）

# 阳光
SUN_INITIAL = 150       # 初始阳光
SUN_VALUE = 25          # 每颗阳光价值
SUN_DROP_INTERVAL = 300 # 每5秒随机掉落一颗阳光(帧数)

# ===================== 植物配置 =====================
PLANTS = {
    "向日葵": {
        "cost": 50, "hp": 80, "cool": 20,
        "sun_interval": 90,     # 每1.5秒产一颗阳光
        "color": "#FFD700", "desc": "生产阳光",
        "key": "1",
    },
    "豌豆射手": {
        "cost": 100, "hp": 100, "cool": 30,
        "shoot_interval": 30,   # 每0.5秒
        "damage": 20,
        "peas": [], "color": "#4CAF50", "desc": "发射豌豆",
        "key": "2",
    },
    "寒冰射手": {
        "cost": 175, "hp": 100, "cool": 30,
        "shoot_interval": 35,
        "damage": 20, "slow": True, # 带减速
        "peas": [], "color": "#00BCD4", "desc": "冰冻+减速",
        "key": "3",
    },
    "坚果墙": {
        "cost": 50, "hp": 600, "cool": 20,
        "color": "#8D6E63", "desc": "高血量阻挡",
        "key": "4",
    },
    "樱桃炸弹": {
        "cost": 150, "hp": 100, "cool": 40,
        "fuse": 30,             # 延时后爆炸
        "color": "#E53935", "desc": "范围爆炸",
        "key": "5",
    },
}

# ===================== 僵尸配置 =====================
ZOMBIES = {
    "普通僵尸": {
        "hp": 100, "speed": 0.35, "damage": 25,
        "color": "#795548", "reward": 0,
    },
    "路障僵尸": {
        "hp": 250, "speed": 0.28, "damage": 25,
        "color": "#00695C", "reward": 25,
    },
    "铁桶僵尸": {
        "hp": 450, "speed": 0.22, "damage": 25,
        "color": "#37474F", "reward": 50,
    },
}
ZOMBIE_TYPES = ["普通僵尸", "普通僵尸", "普通僵尸", "路障僵尸", "铁桶僵尸"]

# 波次配置：(间隔帧数, 每波僵尸数)
WAVES = [
    (400, 2),   # 波1
    (700, 3),   # 波2
    (700, 4),   # 波3
    (800, 5),   # 波4
    (800, 6),   # 最终波
]

# ===================== 矢量图形绘制工具 =====================
def draw_sun_icon(c, x, y, r=14, tag="sun"):
    """绘制一个阳光（金色圆+光芒），所有图元共享tag，返回tag名"""
    c.create_oval(x - r, y - r, x + r, y + r,
                  fill="#FFD600", outline="#F9A825", width=2, tags=tag)
    for i in range(8):
        ang = math.radians(i * 45)
        c.create_line(x + (r+2) * math.cos(ang), y + (r+2) * math.sin(ang),
                      x + (r+8) * math.cos(ang), y + (r+8) * math.sin(ang),
                      fill="#FFD600", width=3, tags=tag)
    return tag

def draw_plant_shape(c, x, y, ptype, scale=1.0):
    """绘制植物形象（矢量，可在草地和卡片使用）"""
    s = scale
    if ptype == "向日葵":
        # 茎
        c.create_line(x, y + 25*s, x, y + 45*s, fill="#4E8E1E", width=4)
        # 叶
        c.create_oval(x - 18*s, y + 30*s, x - 4*s, y + 44*s, fill="#7CB342", outline="")
        c.create_oval(x + 4*s, y + 28*s, x + 18*s, y + 42*s, fill="#7CB342", outline="")
        # 外圈花瓣
        c.create_oval(x - 18*s, y - 18*s, x + 18*s, y + 18*s, fill="#FFC107", outline="")
        # 花心
        c.create_oval(x - 9*s, y - 9*s, x + 9*s, y + 9*s, fill="#8D5A1B", outline="#5D3A0D")

    elif ptype in ("豌豆射手", "寒冰射手"):
        color = "#4CAF50" if ptype == "豌豆射手" else "#00BCD4"
        dark = "#2E7D32" if ptype == "豌豆射手" else "#0097A7"
        # 茎
        c.create_line(x, y + 22*s, x, y + 45*s, fill="#4E8E1E", width=4)
        c.create_oval(x - 18*s, y + 28*s, x - 3*s, y + 44*s, fill="#7CB342", outline="")
        # 炮管（向前伸）
        c.create_rectangle(x + 6*s, y - 7*s, x + 32*s, y + 7*s,
                           fill=color, outline=dark, width=2)
        c.create_oval(x + 28*s, y - 9*s, x + 36*s, y + 9*s,
                      fill=color, outline=dark, width=2)
        # 头
        c.create_oval(x - 16*s, y - 16*s, x + 14*s, y + 16*s,
                      fill=color, outline=dark, width=2)
        # 眼睛
        c.create_oval(x + 8*s, y - 6*s, x + 12*s, y - 2*s, fill="#00251A")
        c.create_oval(x - 4*s, y + 8*s, x + 8*s, y + 18*s, fill="#A5D6A7", outline="")
        if ptype == "寒冰射手":
            c.create_oval(x - 5*s, y - 24*s, x + 3*s, y - 14*s,
                          fill="#E0F7FA", outline="#80DEEA")

    elif ptype == "坚果墙":
        c.create_oval(x - 20*s, y - 18*s, x + 20*s, y + 24*s,
                      fill="#A1887F", outline="#6D4C41", width=2)
        c.create_oval(x - 12*s, y - 12*s, x - 2*s, y - 4*s, fill="#D7CCC8", outline="")
        # 无奈表情
        c.create_line(x - 9*s, y + 1*s, x - 3*s, y + 1*s, fill="#3E2723", width=2)
        c.create_line(x + 3*s, y + 1*s, x + 9*s, y + 1*s, fill="#3E2723", width=2)
        c.create_arc(x - 8*s, y + 3*s, x + 8*s, y + 14*s,
                     start=0, extent=180, style="arc", outline="#3E2723", width=2)

    elif ptype == "樱桃炸弹":
        c.create_line(x + 2*s, y - 4*s, x + 2*s, y - 16*s, fill="#4E8E1E", width=3)
        c.create_oval(x - 2*s, y - 22*s, x + 12*s, y - 14*s, fill="#7CB342", outline="")
        c.create_oval(x - 10*s, y - 18*s, x + 0*s, y - 10*s, fill="#7CB342", outline="")
        c.create_oval(x - 20*s, y - 2*s, x + 0*s, y + 18*s, fill="#D32F2F", outline="#7F0000", width=2)
        c.create_oval(x + 0*s, y - 2*s, x + 20*s, y + 18*s, fill="#D32F2F", outline="#7F0000", width=2)
        c.create_oval(x - 16*s, y + 3*s, x - 10*s, y + 9*s, fill="#FF8A80", outline="")
        c.create_oval(x + 4*s, y + 3*s, x + 10*s, y + 9*s, fill="#FF8A80", outline="")

def draw_zombie_shape(c, x, y, ztype, scale=1.0, tag=None, speed=0.3):
    """绘制僵尸形象（矢量），所有图元共享tag便于整组移动"""
    Zbody = "#8E7A63"
    Zface = "#6D9B6A"
    s = scale
    kw = {}
    if tag is not None:
        kw = {"tags": tag}
    # 身体（旧衣服）
    c.create_oval(x - 14*s, y + 8*s, x + 16*s, y + 32*s,
                  fill=Zbody, outline="#3E2723", width=2, **kw)
    # 腿部
    c.create_rectangle(x - 10*s, y + 28*s, x - 2*s, y + 42*s,
                       fill="#5D4037", outline="#3E2723", width=1, **kw)
    c.create_rectangle(x + 4*s, y + 28*s, x + 12*s, y + 42*s,
                       fill="#5D4037", outline="#3E2723", width=1, **kw)
    # 前伸双臂
    c.create_line(x - 16*s, y + 12*s, x - 38*s, y + 22*s,
                  fill=Zbody, width=6, **kw)
    c.create_line(x + 16*s, y + 12*s, x + 38*s, y + 22*s,
                  fill=Zbody, width=6, **kw)
    # 手
    c.create_oval(x - 42*s, y + 18*s, x - 34*s, y + 26*s,
                  fill=Zface, outline="#2E5D2E", width=1, **kw)
    c.create_oval(x + 34*s, y + 18*s, x + 42*s, y + 26*s,
                  fill=Zface, outline="#2E5D2E", width=1, **kw)
    # 头
    c.create_oval(x - 15*s, y - 24*s, x + 15*s, y + 6*s,
                  fill=Zface, outline="#2E5D2E", width=2, **kw)
    # 眼睛
    c.create_oval(x - 9*s, y - 14*s, x - 3*s, y - 8*s, fill="#FFEB3B", **kw)
    c.create_oval(x + 3*s, y - 14*s, x + 9*s, y - 8*s, fill="#FFEB3B", **kw)
    c.create_oval(x - 8*s, y - 13*s, x - 5*s, y - 10*s, fill="#000", **kw)
    c.create_oval(x + 5*s, y - 13*s, x + 8*s, y - 10*s, fill="#000", **kw)
    # 嘴（烂牙线）
    c.create_line(x - 6*s, y - 2*s, x + 6*s, y - 2*s,
                  fill="#1B5E20", width=3, **kw)
    # 领带（破旧）
    c.create_polygon(x - 3*s, y + 6*s, x + 3*s, y + 6*s,
                     x + 1*s, y + 22*s, x - 1*s, y + 22*s,
                     fill="#B71C1C", outline="#7F0000", width=1, **kw)

    if ztype == "路障僵尸":
        # 橙色锥形路障帽
        c.create_polygon(x - 10*s, y - 38*s, x - 6*s, y - 58*s,
                         x + 8*s, y - 58*s, x + 12*s, y - 38*s,
                         x + 4*s, y - 42*s, x - 4*s, y - 42*s,
                         fill="#FF6F00", outline="#E65100", width=2, **kw)
    elif ztype == "铁桶僵尸":
        # 灰色铁桶帽
        c.create_rectangle(x - 14*s, y - 42*s, x + 12*s, y - 22*s,
                           fill="#90A4AE", outline="#607D8B", width=2, **kw)
        c.create_line(x - 14*s, y - 34*s, x + 12*s, y - 34*s,
                      fill="#607D8B", width=2, **kw)
        c.create_rectangle(x - 14*s, y - 30*s, x + 12*s, y - 26*s,
                           fill="#B0BEC5", outline="#607D8B", width=1, **kw)
    return tag
def draw_shovel_shape(c, x, y, scale=1.0):
    """绘制铲子"""
    s = scale
    c.create_line(x - 28*s, y + 40*s, x - 10*s, y - 20*s, fill="#8D6E63", width=6)
    c.create_oval(x - 36*s, y + 34*s, x - 22*s, y + 48*s,
                  fill="#5D4037", outline="#3E2723", width=2)
    c.create_polygon(x - 14*s, y - 22*s, x + 2*s, y + 6*s,
                     x + 18*s, y + 10*s, x - 6*s, y - 28*s,
                     fill="#78909C", outline="#455A64", width=2)


# ===================== 游戏主类 =====================
class PvZGame:
    def __init__(self, root):
        self.root = root
        root.title("植物大战僵尸 Demo")
        root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#7EC850")
        self.canvas.pack()

        # 游戏状态
        self.sun = SUN_INITIAL
        self.selected = None       # 当前选中卡片/铲子
        self.wave = 0
        self.frame = 0
        self.game_over = False
        self.victory = False
        self.paused = False

        # 动态对象
        self.plants = []           # {type,row,col,x,y,hp,frame,shoot_cd,sun_cd,...}
        self.zombies = []          # {type,row,x,y,hp,speed,frame,slow_frame}
        self.peas = []             # {x,y,row,damage,slow,color}
        self.suns = []             # 掉落的阳光 {x,y,row,col,value,life}
        self.sun_fall = []         # 向日葵产出的阳光（带目标点）
        self.explosions = []       # 爆炸动画 {x,y,row,col,frame}

        # 卡冷却
        self.cool = {}             # 植物名 -> 当前剩余冷却帧
        for name in PLANTS:
            self.cool[name] = 0

        self.sun_drop_timer = 0

        self._draw_board()
        self._draw_ui()
        self._bind_events()

        # 下一波按钮
        self.next_wave_btn = tk.Button(root, text="▶ 开始", command=self.advance_wave,
                                      bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                                      activebackground="#66BB6A", relief="raised", bd=2)
        self.next_wave_btn.place(x=MARGIN_X, y=8, width=100, height=30)

        self.pause_btn = tk.Button(root, text="暂停", command=self.toggle_pause,
                                   bg="#FFA726", fg="white", font=("Arial", 9, "bold"),
                                   activebackground="#FFB74D", relief="raised", bd=2)
        self.pause_btn.place(x=MARGIN_X + 105, y=8, width=60, height=30)

        self._spawn_wave()
        self._tick()

    # ---------- 界面绘制 ----------
    def _draw_board(self):
        """绘制草地网格"""
        for r in range(ROWS):
            for c in range(COLS):
                x = GRID_X + c * CELL
                y = GRID_Y + r * CELL
                if (r + c) % 2 == 0:
                    color = "#7EC850"
                else:
                    color = "#86D05A"
                self.canvas.create_rectangle(x, y, x + CELL, y + CELL,
                                             fill=color, outline="#6BB843")
        # 房子（左侧，僵尸到达即失败）
        self.canvas.create_rectangle(10, GRID_Y, GRID_X, HEIGHT,
                                     fill="#C78A57", outline="#A06A3C")
        # 门
        self.canvas.create_rectangle(15, GRID_Y + 45, 45, GRID_Y + 130,
                                     fill="#A06A3C", outline="#6D4C41", width=2)
        # 窗
        for wy in (GRID_Y + 18, GRID_Y + 160, GRID_Y + 300, GRID_Y + 440):
            self.canvas.create_rectangle(40, wy, 78, wy + 50,
                                         fill="#E0C08C", outline="#A06A3C", width=2)
            self.canvas.create_line(59, wy, 59, wy + 50, fill="#A06A3C", width=2)
        self.canvas.create_text(98, GRID_Y + ROWS * CELL // 2 - 20,
                                text="僵尸到达此线\n即失败!\n\n保护房子!", 
                                font=("Arial", 9), fill="#5D4037", justify="center")

    def _draw_ui(self):
        """绘制顶部工具栏 + 卡片 + 阳光（矢量图标）"""
        self.canvas.create_rectangle(0, 0, WIDTH, TOP, fill="#8E5B3E", outline="")
        # 左侧竖排标题
        self.canvas.create_text(12, TOP // 2 - 10, text="植\n物\n大\n战\n僵\n尸",
                                font=("Arial", 8, "bold"), fill="#FFF3E0")
        # 阳光显示（矢量图标 + 数字）
        draw_sun_icon(self.canvas, GRID_X + 20, TOP // 2 - 4, r=12)
        self.sun_text = self.canvas.create_text(
            GRID_X + 42, TOP // 2, text=f"{self.sun}",
            font=("Arial", 18, "bold"), fill="#FFF176", anchor="w")

        # 卡片栏
        self.card_items = {}
        card_x = GRID_X + 190
        for name in PLANTS:
            p = PLANTS[name]
            self.card_items[name] = {"x": card_x, "y": 13, "w": 68, "h": 68}
            x0, y0 = card_x, 13
            self.canvas.create_rectangle(x0, y0, x0 + 68, y0 + 68,
                                         fill="#E0E6EA", outline="#78909C", width=2)
            # 快捷键角标
            self.canvas.create_rectangle(x0 + 48, y0, x0 + 68, y0 + 20,
                                         fill="#90A4AE", outline="#78909C")
            self.canvas.create_text(x0 + 58, y0 + 10, text=p["key"],
                                    font=("Arial", 10, "bold"), fill="white")
            # 图标底色 + 植物矢量小图标
            self.canvas.create_oval(x0 + 9, y0 + 22, x0 + 59, y0 + 58,
                                    fill="#C8E6C9", outline="")
            draw_plant_shape(self.canvas, x0 + 34, y0 + 42, name, scale=0.9)
            # 费用（用矢量太阳点代替字符）
            self.canvas.create_text(x0 + 34, y0 + 62, text=f"{p['cost']}",
                                    font=("Arial", 8, "bold"), fill="#E65100")
            card_x += 74

        # 铲子
        self.shovel_item = {"x": GRID_X + 190 + 74 * len(PLANTS) + 8, "y": 13, "w": 68, "h": 68}
        sx, sy = self.shovel_item["x"], self.shovel_item["y"]
        self.canvas.create_rectangle(sx, sy, sx + 68, sy + 68,
                                     fill="#FFE0B2", outline="#D84315", width=2)
        draw_shovel_shape(self.canvas, sx + 34, sy + 40, scale=0.7)
        self.canvas.create_text(sx + 34, sy + 64, text="铲子", 
                                font=("Arial", 7), fill="#BF360C")

        # 波次提示
        self.wave_text = self.canvas.create_text(
            WIDTH // 2, 45, text=f"第 {self.wave}/{len(WAVES)} 波",
            font=("Arial", 14, "bold"), fill="white")
        # 开局引导提示（wave=0时显示）
        self.hint_id = self.canvas.create_text(
            WIDTH // 2, GRID_Y + ROWS * CELL // 2 - 40,
            text="先在草地上种植物布置防线\n点击左上角〔开始〕按钮开始第一波\n之后每波僵尸会自动来袭，坚持到全部消灭！",
            font=("Arial", 13, "bold"), fill="#FFF176",
            justify="center")

    def _update_ui(self):
        """刷新阳光数字、卡片冷却"""
        self.canvas.itemconfig(self.sun_text, text=f"☀ {self.sun}")
        # 游戏开始后（wave>0）隐藏引导提示
        if self.wave > 0 and hasattr(self, "hint_id") and self.hint_id is not None:
            self.canvas.delete(self.hint_id)
            self.hint_id = None

        # 卡片冷却遮罩
        for name, ci in self.card_items.items():
            # 找这块区域的现有对象（简易处理：直接重绘遮罩矩形）
            pass
        # 简化：清掉旧的遮罩
        self.canvas.delete("coolmask")
        for name, ci in self.card_items.items():
            cd = self.cool[name]
            if cd > 0:
                # 冷却过半屏遮罩
                h = int(ci["h"] * cd / PLANTS[name]["cool"])
                self.canvas.create_rectangle(
                    ci["x"], ci["y"], ci["x"] + ci["w"], ci["y"] + h,
                    fill="#37474F", stipple="gray50", tags="coolmask"
                )

    # ---------- 事件 ----------
    def _bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Key>", self.on_key)

    def on_key(self, event):
        key = event.char
        for name, p in PLANTS.items():
            if p["key"] == key:
                self.select_card(name)
                return

    def select_card(self, name):
        if name in PLANTS:
            self.selected = name
            self._flash_selected()

    def _flash_selected(self):
        # 简单提示当前选择
        self.root.title(f"植物大战僵尸 Demo - 已选择: {self.selected}")

    def on_click(self, event):
        x, y = event.x, event.y
        if self.game_over:
            return

        # 铲子点击
        sx, sy = self.shovel_item["x"], self.shovel_item["y"]
        if sx <= x <= sx + 60 and sy <= y <= sy + 60:
            self.selected = "铲子"
            self.root.title("植物大战僵尸 Demo - 铲子（点击植物铲除）")
            return

        # 卡片点击
        for name, ci in self.card_items.items():
            if ci["x"] <= x <= ci["x"] + ci["w"] and ci["y"] <= y <= ci["y"] + ci["h"]:
                self.select_card(name)
                return

        # 点击收集阳光
        for s in self.suns[:]:
            if abs(s["x"] - x) < 22 and abs(s["y"] - y) < 22:
                self.sun += s["value"]
                self.suns.remove(s)
                self.canvas.delete(s["id"])
                return
        for s in self.sun_fall[:]:
            if abs(s["x"] - x) < 22 and abs(s["y"] - y) < 22:
                self.sun += s["value"]
                self.sun_fall.remove(s)
                self.canvas.delete(s["id"])
                return

        # 种植 / 铲除
        col = int((x - GRID_X) // CELL)
        row = int((y - GRID_Y) // CELL)
        if not (0 <= row < ROWS and 0 <= col < COLS):
            # 点击"开始下一波"
            return

        if self.selected == "铲子":
            self.remove_plant_at(row, col)
            return

        if self.selected and self.selected in PLANTS:
            self.plant_at(row, col, self.selected)

    def on_right_click(self, event):
        """右键铲除植物"""
        x, y = event.x, event.y
        col = int((x - GRID_X) // CELL)
        row = int((y - GRID_Y) // CELL)
        if 0 <= row < ROWS and 0 <= col < COLS:
            self.remove_plant_at(row, col)

    # ---------- 种植 ----------
    def plant_at(self, row, col, name):
        p = PLANTS[name]
        # 检查格子是否已有植物
        for pl in self.plants:
            if pl["row"] == row and pl["col"] == col:
                return
        # 检查阳光和冷却
        if self.sun < p["cost"]:
            return
        if self.cool[name] > 0:
            return

        self.sun -= p["cost"]
        self.cool[name] = PLANTS[name]["cool"]

        plant = {
            "type": name, "row": row, "col": col,
            "hp": p["hp"],
            "frame": 0,
            "shoot_cd": 0,
            "sun_cd": 0,
            "fuse": 0,
            "id": None,
            "hp_id": None,
        }
        self.plants.append(plant)
        self._draw_plant(plant)

    def remove_plant_at(self, row, col):
        for pl in self.plants[:]:
            if pl["row"] == row and pl["col"] == col:
                self.canvas.delete(pl["id"])
                self.canvas.delete(pl["hp_id"])
                self.plants.remove(pl)
                return

    def _draw_plant(self, pl):
        x = GRID_X + pl["col"] * CELL + CELL // 2
        y = GRID_Y + pl["row"] * CELL + CELL // 2
        pl["id"] = draw_plant_shape(self.canvas, x, y, pl["type"])
        self._draw_plant_hp(pl)

    def _draw_plant_hp(self, pl):
        p = PLANTS[pl["type"]]
        x = GRID_X + pl["col"] * CELL + CELL // 2
        y = GRID_Y + pl["row"] * CELL + 8
        if pl.get("hp_id"):
            self.canvas.delete(pl["hp_id"])
        ratio = max(0, pl["hp"] / p["hp"])
        pl["hp_id"] = self.canvas.create_rectangle(
            x - 20, y - 4, x - 20 + int(40 * ratio), y - 1,
            fill="#4CAF50" if ratio > 0.5 else "#F44336",
            outline="#333", width=1
        )

    # ---------- 僵尸 ----------
    def _spawn_wave(self):
        if self.wave >= len(WAVES):
            return
        interval, count = WAVES[self.wave]
        self.pending_zombies = count
        self.zombie_timer = interval // count  # 间隔
        self.zombie_frame = 0

    def advance_wave(self):
        """手动进入下一波"""
        if self.wave < len(WAVES):
            self.wave += 1
            self.canvas.itemconfig(self.wave_text,
                text=f"第 {self.wave}/{len(WAVES)} 波")
        if self.wave < len(WAVES):
            interval, count = WAVES[self.wave - 1]
            self.pending_zombies = count
            self.zombie_timer = interval // count
            self.zombie_frame = 0
        elif len(self.zombies) == 0:
            self.win()

    def _spawn_zombie(self):
        ztype = random.choice(ZOMBIE_TYPES)
        z = ZOMBIES[ztype]
        row = random.randrange(ROWS)
        x = WIDTH + random.randint(10, 30)
        tagname = "z_%d_%d" % (self.frame, len(self.zombies))
        zombie = {
            "type": ztype, "row": row,
            "x": x, "y": GRID_Y + row * CELL + CELL // 2,
            "hp": z["hp"], "speed": z["speed"],
            "frame": 0, "slow_frame": 0,
            "id": tagname, "hp_id": None,
        }
        self.zombies.append(zombie)
        self._draw_zombie(zombie)

    def _draw_zombie(self, z):
        draw_zombie_shape(self.canvas, z["x"], z["y"], z["type"],
                          tag=z["id"])
        self._draw_zombie_hp(z)

    def _draw_zombie_hp(self, z):
        if z.get("hp_id"):
            self.canvas.delete(z["hp_id"])
        ratio = max(0, z["hp"] / ZOMBIES[z["type"]]["hp"])
        z["hp_id"] = self.canvas.create_rectangle(
            z["x"] - 20, z["y"] - 32, z["x"] - 20 + int(40 * ratio), z["y"] - 29,
            fill="#F44336", outline="#333", width=1
        )

    # ---------- 豌豆 ----------
    def _shoot_pea(self, plant):
        p = PLANTS[plant["type"]]
        pea = {
            "x": GRID_X + plant["col"] * CELL + CELL // 2 + 15,
            "y": GRID_Y + plant["row"] * CELL + CELL // 2,
            "row": plant["row"],
            "damage": p["damage"],
            "slow": p.get("slow", False),
            "color": ("#81D4FA" if p.get("slow") else "#9CCC65"),
            "id": None,
        }
        pea["id"] = self.canvas.create_oval(
            pea["x"] - 8, pea["y"] - 8, pea["x"] + 8, pea["y"] + 8,
            fill=pea["color"], outline="#33691E"
        )
        self.peas.append(pea)

    def _hit_zombie_row(self, row, x_min):
        """找某行中x在给定列之后最靠前的僵尸"""
        candidates = [z for z in self.zombies if z["row"] == row and z["x"] >= x_min]
        if not candidates:
            return None
        return min(candidates, key=lambda z: z["x"])

    # ---------- 樱桃炸弹 ----------
    def _explode(self, plant):
        row, col = plant["row"], plant["col"]
        cx = GRID_X + col * CELL + CELL // 2
        cy = GRID_Y + row * CELL + CELL // 2
        self.explosions.append({"x": cx, "y": cy, "row": row, "col": col, "frame": 0})
        # 伤害范围内僵尸
        for z in self.zombies[:]:
            if abs(z["row"] - row) <= 1 and abs(z["x"] - cx) < CELL * 2.2:
                z["hp"] -= 1800
                if z["hp"] <= 0:
                    self._kill_zombie(z)
        self.canvas.delete(plant["id"])
        self.canvas.delete(plant["hp_id"])
        self.plants.remove(plant)

    def _kill_zombie(self, z):
        if z in self.zombies:
            self.zombies.remove(z)
            self.canvas.delete(z["id"])
            self.canvas.delete(z["hp_id"])

    # ---------- 主循环 ----------
    def _tick(self):
        if not self.paused and not self.game_over:
            self.frame += 1
            self._update_cool()
            self._update_plants()
            self._update_peas()
            self._update_zombies()
            self._update_suns()
            self._update_explosions()
            self._update_ui()
            self._check_win()
        self.root.after(int(1000 / FPS), self._tick)

    def _update_cool(self):
        for name in self.cool:
            if self.cool[name] > 0:
                self.cool[name] -= 1

    def _update_plants(self):
        # 生成掉落阳光
        if self.frame % SUN_DROP_INTERVAL == 0:
            row = random.randrange(ROWS)
            col = random.randrange(COLS)
            self.drop_sun(GRID_X + col * CELL + CELL // 2,
                          GRID_Y + row * CELL + CELL // 2, SUN_VALUE)

        for pl in self.plants[:]:
            pl["frame"] += 1
            t = pl["type"]

            if t == "向日葵":
                pl["sun_cd"] += 1
                if pl["sun_cd"] >= PLANTS[t]["sun_interval"]:
                    pl["sun_cd"] = 0
                    x = GRID_X + pl["col"] * CELL + CELL // 2
                    y = GRID_Y + pl["row"] * CELL + CELL // 2
                    self.drop_sun(x + 15, y, SUN_VALUE, from_plant=True)

            elif t in ("豌豆射手", "寒冰射手"):
                pl["shoot_cd"] += 1
                target = self._hit_zombie_row(pl["row"], GRID_X + (pl["col"] + 1) * CELL)
                if target and pl["shoot_cd"] >= PLANTS[t]["shoot_interval"]:
                    pl["shoot_cd"] = 0
                    self._shoot_pea(pl)

            elif t == "樱桃炸弹":
                pl["fuse"] += 1
                if pl["fuse"] >= PLANTS[t]["fuse"]:
                    self._explode(pl)

    def drop_sun(self, x, y, value, from_plant=False):
        obj = {"x": x, "y": y - 40, "tx": x, "ty": y + 30, "value": value,
               "life": 600, "from_plant": from_plant, "id": None}
        tagname = "sun_%d_%d" % (self.frame, len(self.suns) + len(self.sun_fall))
        draw_sun_icon(self.canvas, x, y - 40, r=13, tag=tagname)
        obj["id"] = tagname
        if from_plant:
            self.sun_fall.append(obj)
        else:
            self.suns.append(obj)

    def _update_suns(self):
        # 天空掉落的阳光，向地面移动
        for s in self.suns[:]:
            if s["y"] < s["ty"]:
                self.canvas.move(s["id"], 0, 1.2)
                s["y"] += 1.2
            s["life"] -= 1
            if s["life"] < 0:
                self.suns.remove(s)
                self.canvas.delete(s["id"])

        # 向日葵产出的阳光，向地面落
        for s in self.sun_fall[:]:
            if s["y"] < s["ty"]:
                self.canvas.move(s["id"], 0, 1.0)
                s["y"] += 1.0
            s["life"] -= 1
            if s["life"] < 0:
                self.sun_fall.remove(s)
                self.canvas.delete(s["id"])

    def _update_peas(self):
        for pea in self.peas[:]:
            pea["x"] += 12
            self.canvas.coords(pea["id"], pea["x"] - 8, pea["y"] - 8,
                               pea["x"] + 8, pea["y"] + 8)
            if pea["x"] > WIDTH + 20:
                self.peas.remove(pea)
                self.canvas.delete(pea["id"])
                continue
            # 命中僵尸
            for z in self.zombies:
                if z["row"] == pea["row"] and abs(z["x"] - pea["x"]) < 26:
                    z["hp"] -= pea["damage"]
                    if pea["slow"]:
                        z["slow_frame"] = 120   # 减速2秒
                    if z["hp"] <= 0:
                        self._kill_zombie(z)
                    self.peas.remove(pea)
                    self.canvas.delete(pea["id"])
                    break

    def _update_zombies(self):
        # 生成待出僵尸
        if self.wave > 0 and self.pending_zombies > 0:
            self.zombie_frame += 1
            if self.zombie_frame >= self.zombie_timer:
                self.zombie_frame = 0
                self.pending_zombies -= 1
                self._spawn_zombie()

        for z in self.zombies[:]:
            z["frame"] += 1
            # 减速
            speed = z["speed"]
            if z["slow_frame"] > 0:
                z["slow_frame"] -= 1
                speed *= 0.4

            # 检查面前是否有植物阻挡
            blocking = False
            front_x = z["x"] - 20
            for pl in self.plants:
                plx = GRID_X + pl["col"] * CELL + CELL // 2
                if pl["row"] == z["row"] and plx <= front_x and abs(plx - front_x) < 70:
                    blocking = True
                    # 啃食该植物
                    pl["hp"] -= ZOMBIES[z["type"]]["damage"] / 2.0
                    self._draw_plant_hp(pl)
                    if pl["hp"] <= 0:
                        self.canvas.delete(pl["id"])
                        self.canvas.delete(pl["hp_id"])
                        self.plants.remove(pl)
                    break
            if not blocking:
                z["x"] -= speed
                self.canvas.move(z["id"], -speed, 0)
                self._draw_zombie_hp(z)

            # 僵尸到达左边 -> 游戏失败
            if z["x"] < GRID_X - 10:
                self.game_over = True
                self._show_message("僵尸进了房子！游戏失败 😢")
                return

    def _update_explosions(self):
        for e in self.explosions[:]:
            e["frame"] += 1
            if e["frame"] == 1:
                r = 45
                self.canvas.create_oval(
                    e["x"] - r, e["y"] - r, e["x"] + r, e["y"] + r,
                    fill="#FF7043", outline="#E64A19", width=4,
                    tags="boom")
                self.canvas.create_text(e["x"], e["y"], text="💥",
                                        font=("Arial", 40), tags="boom")
            if e["frame"] > 20:
                self.canvas.delete("boom")
                self.explosions.remove(e)

    # ---------- 胜负 ----------
    def _check_win(self):
        # 每波僵尸(已放出+战场上)全部清空后，自动进入下一波
        if self.wave > 0 and self.pending_zombies == 0 and len(self.zombies) == 0:
            if self.wave < len(WAVES):
                self.advance_wave()          # 自动开始下一波
            else:
                self.win()                   # 全部波次打完，胜利

    def win(self):
        if not self.game_over and not self.victory:
            self.victory = True
            self.game_over = True
            self._show_message("胜利！所有僵尸被消灭 🎉")

    def _show_message(self, msg):
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text=msg, font=("Arial", 26, "bold"), fill="#FF1744"
        )
        # 重新开始按钮
        self.restart_btn = tk.Button(self.root, text="重新开始", command=self.restart)
        self.restart_btn.place(x=WIDTH // 2 - 50, y=HEIGHT // 2 + 30, width=100, height=35)

    def restart(self):
        # 清除全部对象
        self.canvas.delete("all")
        self.plants = []
        self.zombies = []
        self.peas = []
        self.suns = []
        self.sun_fall = []
        self.explosions = []
        self.sun = SUN_INITIAL
        self.wave = 0
        self.frame = 0
        self.game_over = False
        self.victory = False
        self.pending_zombies = 0
        for name in PLANTS:
            self.cool[name] = 0
        self.selected = None
        if hasattr(self, "restart_btn"):
            self.restart_btn.destroy()
        self._draw_board()
        self._draw_ui()
        self._spawn_wave()
        self.root.title("植物大战僵尸 Demo")

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="继续" if self.paused else "暂停")


# ===================== 启动 =====================
if __name__ == "__main__":
    root = tk.Tk()
    game = PvZGame(root)
    root.mainloop()
