# -*- coding: utf-8 -*-

import numpy as np
import csv
import random
import multiprocessing as multi
import time

class Block(object): #ブロックのクラス
    def __init__(self,x,y,xlength,ylength,stock):
        self.x = x
        self.y = y
        self.xlength = xlength
        self.ylength = ylength
        self.stock = stock
        self.exist = True

def block_setup(): #ブロックを生成する函数
    file_dir = 'C:\document\map'
    difficulty = raw_input('Please input difficulty.\n')
    file_dir = file_dir + '\_' + difficulty + '.csv'
    fh = open(file_dir,'rb')
    reader = csv.reader(fh)
    tmp_lst = []
    for i in reader:
        tmp = Block(i[0],i[1],i[2],i[3],i[4])
        tmp_lst.append(tmp)
    return tmp_lst

def first_vector(): #初期ベクトルを生成する函数
    vector = [random.random()*45.0+45.0,(random.random()-0.5)*180.0]
    return vector

def is_completed(block_lst): #ブロックが全部消されたかどうか判定する函数
    judge = False
    for i in xrange(len(block_lst)):
        judge = judge or block_lst[i].exist
    return judge

def func_Timer(conn): #タイマープロセス用の函数(Pipeで通信)
    time.sleep(300.0)
    conn.send('time_up!')
