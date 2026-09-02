# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
c=open('pvz_demo.py',encoding='utf-8').read()
for kw in ['进房子','game_over = True','lose','LOSE','失败','game_over']:
    idx=c.find(kw)
    if idx>=0:
        print('== %s @%d ==' % (kw,idx))
        print(c[max(0,idx-150):idx+150].replace('\n','\\n'))
        print()
    else:
        print('NOT FOUND:', kw)
