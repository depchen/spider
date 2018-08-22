# encoding: utf-8
'''
@author: depchen

@file: zheye_test.py.py

@time: 2017/11/25 15:19

@desc:
'''


from zheye import zheye
z = zheye()
positions = z.Recognize('e.gif')
print(positions)