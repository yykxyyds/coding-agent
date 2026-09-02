# -*- coding: utf-8 -*-
"""完整游玩模拟：模拟 _tick 每帧调用，捕捉异常，检查各阶段"""
import os, sys, traceback
sys.stdout.reconfigure(encoding='utf-8')
OUT=[]; ERR=[]
def w(s=""): OUT.append(str(s))
try:
    import tkinter as tk
    import pvz_demo
    root=tk.Tk()
    game=pvz_demo.PvZGame(root)

    # 布置防线（充足的阳光植物）
    game.sun=99999
    for n in pvz_demo.PLANTS: game.cool[n]=0
    for r in range(pvz_demo.ROWS):
        for col,name in [(7,"向日葵"),(6,"向日葵"),(5,"豌豆射手"),
                         (4,"豌豆射手"),(3,"寒冰射手"),(1,"坚果墙")]:
            game.plant_at(r,col,name)
            game.cool[name]=0
    w("=== 布防完成, 植物=%d, 阳光=%d ===" % (len(game.plants), game.sun))

    # 模拟 _tick 每帧逻辑
    def tick():
        game.frame+=1
        game._update_cool(); game._update_plants(); game._update_peas()
        game._update_zombies(); game._update_suns(); game._update_explosions()
        game._update_ui(); game._check_win()

    # 点击一次开始 → 波1
    game.advance_wave()
    w("点击 [开始] 后 wave=%d 提示=%s" % (game.wave, game.canvas.itemcget(game.wave_text,'text')))

    peak_zombies=0; peak_peas=0; peak_suns=0; peaks=[]
    auto=0; last_w=1
    max_frame=120*60
    for f in range(max_frame):
        tick()
        peak_zombies=max(peak_zombies,len(game.zombies))
        peak_peas=max(peak_peas,len(game.peas))
        peak_suns=max(peak_suns,len(game.suns))
        if game.wave!=last_w and game.wave>1:
            auto+=1; peaks.append("进%d波前僵尸峰值=%d"%(game.wave,peak_zombies_prev if 'peak_zombies_prev' in dir() else 0)); last_w=game.wave; peak_zombies_prev=peak_zombies
        if not hasattr(game,'__probe') and f%1800==1799:
            w("  %d秒: 波%d, 场上僵尸%d 豌豆%d 阳光%s" % (f//60, game.wave, len(game.zombies), len(game.peas), game.sun))
        if game.game_over or game.victory:
            w("  在第%d秒结束 (victory=%s game_over=%s), 最后一波=%d/5, 自动推进%d次" % (f//60, game.victory, game.game_over, game.wave, auto))
            break
    w("峰值: 僵尸=%d, 豌豆=%d, 阳光=%d" % (peak_zombies, peak_peas, peak_suns))
    w("自动推进次数=%d" % auto)
    if game.victory:
        w(">>> 全自动通过5波, 胜利!")
    else:
        w(">>> 未胜利, 原因: 僵尸突破防线.")

    # 检查画布上无孤儿图元（之前渲染bug相关）
    allc=game.canvas.find_all()
    w("画布活动图元总数=%d" % len(allc))
    root.destroy()
except Exception:
    ERR.append(traceback.format_exc())
open('play_log.txt','w',encoding='utf-8').write('\n'.join(OUT+['---ERROR---']+ERR))
