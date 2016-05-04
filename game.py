# -*- coding: utf-8 -*-

import csv
import random
import threading
import time
import math

class Block(object): #ブロックのクラス
    def __init__(self,x,y,xlength,ylength,stock):
        self.x = x #x座標
        self.y = y #y座標
        self.xlength = xlength #x方向の長さ(単位はcm)
        self.ylength = ylength #y方向の長さ
        self.stock = stock #ボックスの残機
        self.exist = True #ボックスが存在するかどうか
    def delete(self): #ボックスの残機を減らすメソッド
        self.stock = self.stock - 1
        if self.stock == 0:
            self.exist = False

class Item(object): #アイテムのクラス
    def __init__(self,x,y):
        self.x = x #x座標
        self.y = y #y座標
        self.xlength = 20.0 #大きさは20×20cm
        self.ylength = 20.0
        self.exist = True
    def delete(self):
        self.exist = False

def map_setup(): #ブロックとアイテムのcsvからマップを生成する函数
    block_id = 0
    item_id = 0
    file_dir = 'C:\python27'
    difficulty = str(raw_input('Please input difficulty (easy or hard) .\n'))
    file_dir ='_block_' + difficulty + '.csv'
    fh1 = open(file_dir,'rb')
    reader1 = csv.reader(fh1)
    dict_block = {}
    for i in reader1:
        i = map(float,i)
        tmp1 = Block(i[0],i[1],i[2],i[3],int(i[4]))
        dict_block[block_id] = tmp1
        block_id += 1
    fh1.close()
    file_dir ='_item_' + difficulty + '.csv'
    fh2 = open(file_dir,'rb')
    reader2 = csv.reader(fh2)
    dict_item = {}
    for i in reader2:
        i = map(float,i)
        tmp2 = Item(i[0],i[1])
        dict_item[item_id] = tmp2
        item_id += 1
    fh2.close()
    return dict_block,dict_item,block_id,item_id

def first_vector(): #初期ベクトルを生成する函数
    arg = (random.random()*90.0 + 45.0)*math.pi
    vector = [math.cos(arg),math.sin(arg)]
    return vector

def collision(ph_position,dict_block): #当たり判定函数
    phex,phey = ph_position[0],ph_position[1]
    phesizex,phesizey = 15,15 #フェノックス当たり判定範囲(奥行き方向[cm],左右方向)
    answer = []
    for i in dict_block:
        block = dict_block[i]
        posx = block.x
        posy = block.y
        sizex = block.xlength
        sizey = block.ylength
        distx = abs(posx-phex)
        disty = abs(posy-phey)
        sizesumx = sizex/2.0+phesizex/2.0
        sizesumy = sizey/2.0+phesizey/2.0
        if (distx<=sizesumx):
            if (disty<=sizesumy):
                bt = posx-sizex/2.0
                br = posy+sizey/2.0
                bb = posx+sizex/2.0
                bl = posy-sizey/2.0
                pt = phex-phesizex/2.0
                pr = phey+phesizey/2.0
                pb = phex+phesizex/2.0
                pl = phey-phesizey/2.0
                cx = 0.
                cy = 0.
                if pl<bl<pr<br:
					cy -= 1.
                if bl<pl<br<pr:
					cy += 1.
                if pt<bt<pb<bb:
					cx += 1.
                if bt<pt<bb<pb:
					cx -= 1.
                answer.append((i,(cx,cy))) #ブロックのID,法線ベクトル
    return answer

"""
def is_exist(block_dict): #ブロックがまだあるかどうか判定する函数
    judge = False
    for i in xrange(len(block_lst)):
        judge = judge or block_lst[i].exist
    return judge
"""

def gameover_judge(position): #ゲームオーバーかどうかを判別する函数
    if position[1] < -10.0: #y座標が-10以下でゲームオーバー
        return True
    else:
        return False

class Timer_thread(threading.Thread): #タイマースレッドのクラス
    def __init__(self):
        super(Timer_thread,self).__init__()
        self.timeup = False
    def run(self):
        time.sleep(150.0) #制限時間
        self.timeup = True

class Communication_thread(threading.Thread): #通信スレッドのクラス
    def __init__(self):
        super(Communication_thread,self).__init__()
        self.receive = [] #メインスレッドが受信するコマンドを格納
        self.send = [] #メインスレッドが送信するコマンドを格納
    def run(self):
        while True:
            if len(self.send) > 0:
                send_command = self.send[0]
                del self.send[0]
                print send_command

class Item_thread(threading.Thread): #アイテムを取った時にその持続時間を計っておくスレッド
    def __init__(self):
        super(Item_thread,self).__init__()
        self.ready = True #スレッドが待機状態かどうかを示す
    def run(self): #アイテムを取ったら呼び出す(is_aliveメソッドがTrueならアイテムの効果中)
        time.sleep(20.0) #アイテムの持続時間
        self.ready = False #スレッドが待機状態でない(アイテムを取り終わった後)

class Simulator(threading.Thread): #シミュレーター用スレッド
    def __init__(self):
        super(Simulator,self).__init__()
        self.vector = [0.0,0.0] #方向ベクトル
        self.position = [50.0,50.0] #座標
        self.speed = 30.0 #速度[cm/s]
        self.dlt = 0.033
    def run(self):
        while True:
            self.position[0] = self.position[0] + self.vector[0]*self.speed*self.dlt
            self.position[1] = self.position[1] + self.vector[1]*self.speed*self.dlt
            if self.position[0] < 0.0 or self.position[0] > 350.0: #x座標が枠に当たった
                self.vector[0] = self.vector[0]*-1.0
            elif self.position[1] < 0.0 or self.position[1] >250.0: #y座標が枠に当たった
                self.vector[1] = self.vector[1]*-1.0
            thread_Communication.receive.append((0,(self.position,self.vector))) #座標と速度送信
            time.sleep(self.dlt)

if __name__ == '__main__':
    thread_Communication = Communication_thread()
    thread_Timer = Timer_thread()
    thread_Item = Item_thread()
    simulator = Simulator()
    thread_Communication.setDaemon(True) #メインが終わったら終了するようにdaemonにしておく
    thread_Timer.setDaemon(True)
    thread_Item.setDaemon(True)
    simulator.setDaemon(True)
    block_dict,item_dict,block_id,item_id = map_setup()
    initial_vector = first_vector()
    thread_Communication.start() #通信開始
    thread_Communication.send.append((0,10,block_dict)) #マップ情報送信
    thread_Communication.send.append((1,1,None)) #Phenoxを離陸させる
    thread_Communication.send.append((1,0,initial_vector))
    simulator.vector = initial_vector
    simulator.start()
    thread_Timer.start()
    while True: #メインループ
        if thread_Timer.timeup == True: #タイムアップの時
            thread_Communication.send.append((0,9,None))
            break
        if thread_Item.ready == False: #アイテムの持続時間が終わったとき
            thread_Communication.send.append((0,4,None))
            thread_Item = Item_thread() #アイテムのスレッドを待機状態にしておく
        elif len(thread_Communication.receive) > 0: #コマンドが送られてきているとき
            receive_command = thread_Communication.receive[0]
            del thread_Communication.receive[0] #コマンドを受け取って消す
            if receive_command[0] == 0: #座標が送られてきたとき
                position,vector = receive_command[1][0],receive_command[1][1]
                thread_Communication.send.append((0,0,position))
                answer = collision(position,block_dict)
                if len(answer) > 0: #当たっていた場合法線ベクトルを送信し、クリア判定
                    thread_Communication.send.append((1,0,answer[0][1]))
                    thread_Communication.send.append((0,1,None))
                    if answer[0][1][0] == 0.0: #法線ベクトルがy方向
                        simulator.vector[1] = simulator.vector[1]*-1.0
                    else:
                        simulator.vector[0] = simulator.vector[0]*-1.0
                    for i in answer: #ブロックを消す
                        del block_dict[i[0]]
                    if len(block_dict) == 0: #クリアの場合
                        thread_Communication.send.append((0,7,None))
                        break
                elif gameover_judge(position) == True: #ゲームオーバーの時
                    thread_Communication.send.append((0,8,None))
                    break
            elif receive_command[0] == 1: #ブロックの追加命令が送られてきたとき
                append_block = receive_command[1]
                block_dict[block_id] = append_block
                block_id += 1
                thread_Communication.send.append((0,3,append_block))
            elif receive_command[0] == 2: #アイテムの追加命令が送られてきたとき
                append_item = receive_command[1]
                item_dict[item_id] = append_item
                item_id += 1
                thread_Communication.send.append((0,4,append_item))
    thread_Communication.send = [(1,0,(0.,0.)),(1,1,None)] #ゲームが終了したらPhenoxを着陸させる
    time.sleep(1.0) #コマンド送信のために少し待機
