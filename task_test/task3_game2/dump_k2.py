# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
c=open('pvz_demo.py',encoding='utf-8').read()
for name in ['_kill_zombie','_spawn_zombie','_draw_zombie']:
    i=c.find('def '+name)
    print(name, i)
i=c.find('def _kill_zombie')
j=c.find('def _draw_zombie_hp')
open('kill.txt','w',encoding='utf-8').write(c[i:j])
print('kill written', j-i)
