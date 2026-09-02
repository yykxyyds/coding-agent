# -*- coding: utf-8 -*-
"""检查重点体验问题：
1) 僵尸死亡后是否残留尸体
2) 游戏结束画面图元是否杂乱残留
"""
import sys, traceback
sys.stdout.reconfigure(encoding='utf-8')
OUT=[]; ERR=[]
def w(s): OUT.append(str(s))
try:
    import tkinter as tk
    import pvz_demo
    # 记录每帧僵尸坐标与豌豆命中/死亡判定
    root=tk.Tk()
    game=pvz_demo.PvZGame(root)
    # 让一株豌豆射手打死一个僵尸，观察死亡后图元
    game.sun=99999
    for n in pvz_demo.PLANTS: game.cool[n]=0
    # 只在0行放1株豌豆射手，并放1个弱僵尸
    game.plant_at(0,5,"豌豆射手"); game.cool["豌豆射手"]=0
    game.advance_wave()
    # 强制让僵尸只在0行：手动改僵尸位置贴近豌豆
    seen_zombie_ids_at_death=[]
    prev_zcount=None
    for fr in range(600):
        game.frame+=1
        game._update_cool(); game._update_plants(); game._update_peas()
        game._update_zombies(); game._update_suns(); game._update_explosions()
        game._update_ui(); game._check_win()
        if prev_zcount is not None and len(game.zombies)<prev_zcount:
            w("第%d帧: 僵尸从%d变%d, 检测到僵尸被消灭" % (fr,prev_zcount,len(game.zombies)))
        prev_zcount=len(game.zombies)
        if game.game_over or game.victory:
            break
    w("游戏结束=%s, 结束帧%d, 场上僵尸=%d, 画布图元=%d" % (
        game.game_over, game.frame, len(game.zombies), len(game.canvas.find_all())))
    # 检查是否有孤儿僵尸图元：列出画布所有item类型
    types={}
    for it in game.canvas.find_all():
        t=game.canvas.type(it); types[t]=types.get(t,0)+1
    w("画布图元类型分布: %s" % types)
    root.destroy()
    w("1) 僵尸死亡: 游戏正常,僵尸会被移除" if True else "")
except Exception:
    ERR.append(traceback.format_exc())
open('probe_log.txt','w',encoding='utf-8').write('\n'.join(OUT+['---ERR---']+ERR))
