# -*- coding: utf-8 -*-

import csv
import random
import threading
import time
import math
from sioclient import SioClient

class Block(object): #ブロックのクラス
    def __init__(self,x,y,xlength,ylength):
        self.x = x #x座標
        self.y = y #y座標
        self.xlength = xlength #x方向の長さ(単位はcm)
        self.ylength = ylength #y方向の長さ

class Controller(object):
    def __init__(self):
        self.width = 60.0 #バーの幅[cm]
        self.position = 100.0 #バーの位置(x座標)[cm]
        self.velocity = 0.0 #バーの移動速度[cm/s]
    def calculate(self,slope): #コントローラーの傾きのデータ(-1～1)からバーの位置と速度を計算する
        global thread_Communication
        if slope != None: #データが来ているときは速度を更新
            self.velocity = slope*150.0 #最大150cm/s
        tmp = self.position + self.velocity*1.0/30.0 #30fps
        if tmp < self.width/2.0: #左端
            tmp = self.width/2.0
        elif tmp > 300.0 - self.width/2.0: #右端
            tmp = 300.0 - self.width/2.0
        self.position = tmp
        thread_Communication.send.append({'room':['Client'],'event':'bar_position','data':tmp})

def map_setup(): #ブロックとアイテムのcsvからマップを生成する函数
    block_id = 0
    color_lst = [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255)] #RGB256段階
    file_dir = 'C:\python27'
    difficulty = str(raw_input('Please input difficulty (easy or hard) .\n'))
    file_dir ='_block_' + difficulty + '.csv'
    fh1 = open(file_dir,'rb')
    reader1 = csv.reader(fh1)
    dict_block = {}
    for i in reader1:
        i = map(float,i)
        tmp1 = Block(i[0],i[1],i[2],i[3])
        tmp1.rgb = random.choice(color_lst)
        dict_block[block_id] = tmp1
        block_id += 1
    fh1.close()
    return dict_block,block_id

def first_vector(): #初期ベクトルを生成する函数
    arg = (random.random()*90.0 + 45.0)*math.pi/180.0
    vector = [math.cos(arg),math.sin(arg)]
    return vector

def collision(ph_position,dict_block): #当たり判定函数
    phex,phey = ph_position[0],ph_position[1]
    phesize = 15.0 #フェノックス当たり判定範囲(縦,横)
    answer = []
    for i in dict_block:
        block = dict_block[i]
        posx = block.x
        posy = block.y
        sizex = block.xlength
        sizey = block.ylength
        distx = abs(posx-phex)
        disty = abs(posy-phey)
        sizesumx = sizex/2.0+phesize/2.0
        sizesumy = sizey/2.0+phesize/2.0
        if (distx<=sizesumx):
            if (disty<=sizesumy):
                bt = posx-sizex/2.0
                br = posy+sizey/2.0
                bb = posx+sizex/2.0
                bl = posy-sizey/2.0
                pt = phex-phesize/2.0
                pr = phey+phesize/2.0
                pb = phex+phesize/2.0
                pl = phey-phesize/2.0
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

def bounce(bar,vector,position): #バーの当たり判定函数
    phesize = 15.0 #width and height of phenox
    ppx,ppy = position[0],position[1]
    vpx,vpy = vector[0],vector[1]
    if ppy <= phesize/2.0:
        if abs(ppx-bar.position) <= (bar.width/2.0+phesize/2.0):
            theta = math.atan(vpy/vpx)
            limit = min(abs(theta),math.pi/3.0)
            k = math.pi/3.0
            thetap = theta - k*bar.velocity
            if thetap >= limit:
                thetap = limit
            if thetap <= -limit:
                thetap = -limit
            vpxp = math.cos(thetap)
            vpyp = -math.sin(thetap)
            answer = (vpxp,vpyp)
        return answer
    else:
        return None

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
        global thread_Communication
        for i in xrange(30):
            time.sleep(5.0) #制限時間(5×30秒)
            thread_Communication.send.append({'room':['Client'],'event':'map','data':block_dict})
        self.timeup = True

class Simulator(threading.Thread): #シミュレーター用スレッド
    def __init__(self):
        super(Simulator,self).__init__()
        self.vector = [0.0,0.0] #方向ベクトル
        self.position = [50.0,50.0] #座標
        self.speed = 30.0 #速度[cm/s]
        self.dlt = 0.033
    def run(self):
        global thread_Communication
        while True:
            self.position[0] = self.position[0] + self.vector[0]*self.speed*self.dlt
            self.position[1] = self.position[1] + self.vector[1]*self.speed*self.dlt
            if self.position[0] < 0.0 or self.position[0] > 350.0: #x座標が枠に当たった
                self.vector[0] = self.vector[0]*-1.0
            elif self.position[1] < 0.0 or self.position[1] > 250.0: #y座標が枠に当たった
                self.vector[1] = self.vector[1]*-1.0
            thread_Communication.receive_other.append((0,(self.position,self.vector))) #座標と速度送信
            time.sleep(self.dlt)

class Communication_thread(threading.Thread): #通信スレッドのクラス
    def __init__(self):
        super(Communication_thread,self).__init__()
        self.receive_controller = [] #コントローラから受信したデータを格納
        self.receive_other = [] #メインスレッドが受信するコマンドを格納
        self.send = [] #メインスレッドが送信するコマンドを格納
        self.client = SioClient()
        event_lst = ['Phenox','controller','append_block']
        self.client.setEventList(event_lst)
        self.client.setMyRoom('Game')
        self.client.setDataQueue(self.receive_controller,['controller'])
        self.client.setDataQueue(self.receive_other)
    def run(self):
        self.client.start('http://192.168.1.39:8000') #通信開始
        while True:
            while(len(self.receive_controller)>0):
                pass

if __name__ == '__main__':
    thread_Communication = Communication_thread()
    thread_Timer = Timer_thread()
    simulator = Simulator()
    thread_Communication.setDaemon(True) #メインが終わったら終了するようにdaemonにしておく
    thread_Timer.setDaemon(True)
    simulator.setDaemon(True)
    block_dict,block_id = map_setup()
    initial_vector = first_vector()
    thread_Communication.start() #通信開始
    thread_Communication.send.append({'room':['Client'],'event':'map','data':block_dict}) #マップ情報送信
    thread_Communication.send.append({'room':['Phenox'],'event':'takeoff','data':None}) #Phenoxを離陸させる
    thread_Communication.send.append({'room':['Phenox'],'event':'vector','data':initial_vector})
    simulator.vector = initial_vector
    simulator.start()
    bar = Controller()
    thread_Timer.start()
    while True: #メインループ
        if thread_Timer.timeup == True: #タイムアップの時
            thread_Communication.send.append({'room':['Client'],'event':'timeup','data':None})
            break
        elif len(thread_Communication.receive_other) > 0: #コマンドが送られてきているとき
            receive_command = thread_Communication.receive_other[0]
            del thread_Communication.receive[0] #コマンドを受け取って消す
            if receive_command[0] == 0: #座標が送られてきたとき
                position,vector = receive_command[1][0],receive_command[1][1]
                thread_Communication.send.append({'room':['Client'],'event':'position','data':position})
                answer_block = collision(position,block_dict)
                answer_bar = bounce(bar,vector,position)
                if len(answer_block) > 0: #当たっていた場合法線ベクトルを送信し、クリア判定
                    thread_Communication.send.append({'room':['Phenox'],'event':'n_vector','data':answer_block[0][1]})
                    thread_Communication.send.append({'room':['Client'],'event':'reflect','data':None})
                    if answer_block[0][1][0] == 0.0: #法線ベクトルがy方向
                        simulator.vector[1] = simulator.vector[1]*-1.0
                    else:
                        simulator.vector[0] = simulator.vector[0]*-1.0
                    for i in answer_block: #ブロックを消す
                        thread_Communication.send.append({'room':['Client'],'event':'hit','data':i[0]})
                        del block_dict[i[0]]
                    if len(block_dict) == 0: #クリアの場合
                        thread_Communication.send.append({'room':['Client'],'event':'complete','data':None})
                        break
                elif answer_bar != None: #バーに当たった場合
                    thread_Communication.send.append({'room':['Phenox'],'event':'vector','data':answer_bar})
                elif gameover_judge(position) == True: #ゲームオーバーの時
                    thread_Communication.send.append({'room':['Client'],'event':'gameover','data':None})
                    break
            elif receive_command[0] == 1: #ブロックの追加命令が送られてきたとき
                append_block = receive_command[1]
                block_dict[block_id] = append_block
                block_id += 1
                thread_Communication.send.append({'room':['Client'],'event':'append_block','data':append_block})
    time.sleep(0.15) #コマンド送信のために少し待機
    thread_Communication.send = [{'room':['Phenox'],'event':'vector','data':(0.,0.)},
                                 {'room':['Phenox'],'event':'landing','data':None}] #ゲームが終了したらPhenoxを着陸させる
    time.sleep(0.05) #コマンド送信のために少し待機
