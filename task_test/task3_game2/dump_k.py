# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
c=open('pvz_demo.py',encoding='utf-8').read()
i=c.find('def _kill_zombie')
j=c.find('def _spawn_zombie')
src=c[i:j]
print(src)
print('=== LEN', j-i)
