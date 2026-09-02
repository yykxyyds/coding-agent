# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
c=open('pvz_demo.py',encoding='utf-8').read()
i=c.find('def _update_peas')
j=c.find('def _update_zombies')
open('peas.txt','w',encoding='utf-8').write(c[i:j])
print('written', j-i)
