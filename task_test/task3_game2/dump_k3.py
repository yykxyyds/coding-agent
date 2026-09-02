# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
c=open('pvz_demo.py',encoding='utf-8').read()
i=c.find('def _kill_zombie')
# 截取到下一个 def（在i之后搜索）
j=c.find('\n    def ', i+10)
open('kill.txt','w',encoding='utf-8').write(c[i:j])
print('kill written', j-i, c[i:j][:50])
