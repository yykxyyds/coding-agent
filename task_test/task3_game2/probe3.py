# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
OUT=[]
def w(s): OUT.append(str(s))
import tkinter as tk, pvz_demo
root=tk.Tk(); game=pvz_demo.PvZGame(root)
baseline=len(game.canvas.find_all())
w("初始基线图元=%d" % baseline)
game.sun=99999
for n in pvz_demo.PLANTS: game.cool[n]=0
# 只放豌豆射手打僵尸
game.plant_at(0,5,"豌豆射手"); game.cool["豌豆射手"]=0
game.advance_wave()
# 记录僵尸出场瞬间的图元与死亡后的图元
z_prev=0
peak_items=baseline
for fr in range(400):
    game.frame+=1; game._update_cool(); game._update_plants(); game._update_peas()
    game._update_zombies(); game._update_suns(); game._update_explosions()
    game._update_ui(); game._check_win()
    n=len(game.zombies)
    # 僵尸在场时记录最大图元
    if n>0:
        peak_items=max(peak_items, len(game.canvas.find_all()))
    if z_prev>0 and n==0 and z_prev!=1:
        w("帧%d: 僵尸 %d->%d 被消灭" % (fr, z_prev, n))
    # 记录死亡前瞬间图元
    z_prev=n
    if game.game_over or game.victory:
        break
end_items=len(game.canvas.find_all())
w("僵尸峰值在场图元≈%d(基线%d→增加%d), 结束后图元=%d" % (
    peak_items, baseline, peak_items-baseline, end_items))
# 僵尸在场时，2个僵尸约17*2=34图元+豌豆等。结束后若残留则end>baseline
w("结束后相对基线残留=%d (若>0说明僵尸/豌豆图元残留未清理)" % (end_items-baseline))
root.destroy()
open('probe3_log.txt','w',encoding='utf-8').write('\n'.join(OUT))
