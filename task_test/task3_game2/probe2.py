# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
OUT=[]
def w(s): OUT.append(str(s))
import tkinter as tk, pvz_demo
root=tk.Tk(); game=pvz_demo.PvZGame(root)
baseline=len(game.canvas.find_all())
w("初始画布图元=%d" % baseline)
game.sun=99999
for n in pvz_demo.PLANTS: game.cool[n]=0
game.advance_wave()
w("波1 pending=%d" % game.pending_zombies)
for fr in range(30):
    game.frame+=1; game._update_cool(); game._update_plants(); game._update_peas()
    game._update_zombies(); game._update_suns(); game._update_explosions()
    game._update_ui(); game._check_win()
w("僵尸出场后: 僵尸列表=%d, 画布图元=%d (增加=%d)" % (
    len(game.zombies), len(game.canvas.find_all()), len(game.canvas.find_all())-baseline))
root.destroy()
open('probe2_log.txt','w',encoding='utf-8').write('\n'.join(OUT))
