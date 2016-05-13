# -*- coding: utf-8 -*-

import csv
import random
import threading
import time
import math
from sioclient import SioClient

class Block(object):  #ブロックのクラス
    def __init__(self,x,y,xlength,ylength):
        self.x = x #x座標
        self.y = y #y座標
        self.xlength = xlength #x方向の長さ(単位はcm)
        self.ylength = ylength #y方向の長さ
        self.rgb = (0.,0.,0.) #色
    def to_data(self):
        data = (self.x,self.y,self.xlength,self.ylength,self.rgb)
        return data

class Controller(object):
    def __init__(self):
        self.width = 60.0 #バーの幅[cm]
        self.position = 100.0 #バーの位置(x座標)[cm]
        self.velocity = 0.0 #バーの移動速度[cm/s]
        self.time = time.time()
    def calculate(self,slope): #コントローラーの傾きのデータ(-1～1)からバーの位置と速度を計算する
        global send_all
        if slope != None: #データが来ているときは速度を更新
            self.velocity = slope*150.0 #最大150cm/s
            time_old = self.time #経過時間を計算
            self.time = time.time()
            tmp = self.position + self.velocity*(self.time-time_old)
        if tmp < self.width/2.0: #左端
            tmp = self.width/2.0
        elif tmp > 300.0 - self.width/2.0: #右端
            tmp = 300.0 - self.width/2.0
        self.position = tmp
        send_all.append(('bar_position',['Client'],tmp))

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

def collision(ph_position,ph_vector,dict_block): #当たり判定函数
    phex,phey = ph_position[0],ph_position[1]
    vx,vy = ph_vector[0],ph_vector[1]
    phesize = 18.0 #フェノックス当たり判定範囲(縦,横)
    answer_id = []
    normalx,normaly = 0,0
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
                bt = posy+sizey/2.0
                br = posx+sizex/2.0
                bb = posy-sizey/2.0
                bl = posx-sizex/2.0
                pt = phey+phesize/2.0
                pr = phex+phesize/2.0
                pb = phey-phesize/2.0
                pl = phex-phesize/2.0
                if pl<bl<pr<br: #左から衝突
                    normalx -= 1
                if bl<pl<br<pr: #右から
                    normalx += 1
                if bb<pb<bt<pt: #下から
                    normaly -= 1
                if pb<bb<pt<bt: #上から
                    normaly += 1
                answer_id.append(i) #ブロックのID,法線ベクトル
    if normalx != 0:
        vx = -vx
    if normaly != 0:
        vy = -vy
    answer = (answer_id,(vx,vy))
    return answer

def bounce(bar,vector,position): #バーの当たり判定函数
    phesize = 18.0 #width and height of phenox
    ppx,ppy = position[0],position[1]
    vpx,vpy = vector[0],vector[1]
    if ppy <= phesize/2.0:
        if abs(ppx-bar.position) <= (bar.width/2.0+phesize/2.0):
            theta = math.atan(vpx/vpy)
            limit = max(abs(theta),math.pi/4.0)
            k = math.pi/4.0
            thetap = theta - k*bar.velocity
            if thetap >= limit:
                thetap = limit
            if thetap <= -limit:
                thetap = -limit
            vpyp = math.cos(thetap)
            vpxp = -math.sin(thetap)
            answer = (vpxp,vpyp)
            return answer
    return None

def gameover_judge(position): #ゲームオーバーかどうかを判別する函数
    if position[1] < -20.0: #y座標が-20以下でゲームオーバー
        return True
    else:
        return False

def to_send_map(dict_block):
    tmp = {}
    for i in dict_block:
        tmp[str(i)] = dict_block[i].to_data()
    return tmp

class Timer_thread(threading.Thread): #タイマースレッドのクラス
    def __init__(self):
        super(Timer_thread,self).__init__()
        self.timeup = False
    def run(self):
        global block_dict,send_all
        for i in xrange(30):
            time.sleep(5.0) #制限時間(5×30秒)
            tmp = to_send_map(block_dict)
            send_all.append(('map',['Client'],tmp))
        self.timeup = True

class Simulator(threading.Thread): #シミュレータ用スレッド
    def __init__(self):
        super(Simulator,self).__init__()
        self.vector = [0.0,0.0] #方向ベクトル
        self.position = [50.0,50.0] #座標
        self.speed = 30.0 #速度[cm/s]
        self.dlt = 0.033
    def run(self):
        global receive_other,send_all
        while True:
            self.position[0] = self.position[0] + self.vector[0]*self.speed*self.dlt
            self.position[1] = self.position[1] + self.vector[1]*self.speed*self.dlt
            if self.position[0] < -150.0 or self.position[0] > 150.0: #x座標が枠に当たった
                self.vector[0] = self.vector[0]*-1.0
                send_all.append(('reflect',['Client'],None))
            elif self.position[1] < 0.0 or self.position[1] > 400.0: #y座標が枠に当たった
                self.vector[1] = self.vector[1]*-1.0
                send_all.append(('reflect',['Client'],None))
            receive_other.append(('px_position',self.position)) #座標と速度送信
            time.sleep(self.dlt)

class Communication_thread(threading.Thread): #通信スレッドのクラス
    def __init__(self):
        super(Communication_thread,self).__init__()
        self.loop = True #ループをするかどうかを示すbool値
    def run(self):
        global receive_controller,send_all,bar
        while self.loop: #通信のループ
            while(len(receive_controller)>0): #コントローラからのデータがあるとき
                data = receive_controller[0][1]
                del receive_controller[0]
                bar.calculate(data)
            while(len(send_all)>0): #送信するデータがあるとき
                data = send_all[0]
                del send_all[0]
                #print 'send',data
                client.sendData(data[0],data[1],data[2])

if __name__ == '__main__':
    receive_controller = [] #コントローラから受信したデータを格納
    receive_other = [] #コントローラ以外からのデータを格納
    send_all = [] #送信するデータを格納
    block_dict,block_id = map_setup()
    velocity = first_vector() #Phenoxの速度ベクトルを保持
    bar = Controller()
    thread_Timer = Timer_thread()
    thread_Timer.setDaemon(True)
    thread_Communication = Communication_thread() #通信開始
    simulator = Simulator()
    #thread_Communication.setDaemon(True) #メインが終わったら終了するようにdaemonにしておく
    simulator.setDaemon(True)
    client = SioClient()
    event_lst = ['px_position','px_velocity','px_start','px_bounce','controller'] #受信するイベントの一覧
    client.setEventList(event_lst)
    client.setMyRoom('Game')
    client.setDataQueue(receive_controller,['controller'])
    client.setDataQueue(receive_other)
    client.start('http://192.168.1.58:8000',True) #通信開始
    tmp = to_send_map(block_dict)
    client.sendData('map',['Client'],tmp) #マップ情報送信
    #thread_Communication.client.sendData('takeoff',['Phenox'],None) #Phenoxを離陸させる
    event = 'hoge'
    """
    while True: #Phenoxの離陸を待つ
        #time.sleep(1.0)
        while(len(receive_other)>0):
            event = receive_other[0][0]
            print event
            del receive_other[0]
            if event == 'px_start':
                break
        if event == 'px_start':
            break
            """
    client.sendData('direction',['Phenox'],velocity) #初期ベクトル送信
    time.sleep(0.05)
    simulator.vector = list(velocity)
    simulator.start()
    thread_Communication.start() #通信ループ開始
    thread_Timer.start()
    while True: #メインループ
        if thread_Timer.timeup == True: #タイムアップの時
            send_all.append(('timeup',['Client'],None))
            break
        elif len(receive_other) > 0: #コマンドが送られてきているとき
            receive_command = receive_other[0] #コマンドを受け取って消す
            del receive_other[0]
            if receive_command[0] == 'px_position': #座標が送られてきたとき
                position = receive_command[1]
                send_all.append(('px_position',['Client'],position))
                answer_block = collision(position,velocity,block_dict)
                answer_bar = bounce(bar,velocity,position)
                if len(answer_block[0]) > 0: #ブロックに当たっていた場合法線ベクトルを送信し、クリア判定
                    send_all.append(('direction',['Phenox'],answer_block[1]))
                    send_all.append(('reflect',['Client'],None))
                    velocity = answer_block[1]
                    simulator.vector = list(velocity)
                    for i in answer_block[0]: #ブロックを消す
                        send_all.append(('hit',['Client'],i))
                        print 'hit',i
                        del block_dict[i]
                    if len(block_dict) == 0: #クリアの場合
                        send_all.append(('complete',['Client'],None))
                        break
                elif answer_bar != None: #バーに当たった場合
                    send_all.append(('direction',['Phenox'],answer_bar))
                #elif gameover_judge(position) == True: #ゲームオーバーの時
                    #send_all.append(('gameover',['Client'],None))
                    #break
            elif receive_command[0] == 'px_velocity': #Phenoxの速度ベクトルが送られてきたとき
                velocity = receive_command[1]
            elif receive_command[0] == 'px_bounce': #Phenoxが反射したとき
                send_all.append(('reflect',['Client'],None))
                print 'recieve',receive_command
            elif receive_command[0] == 'px_start':
                break
    time.sleep(0.15) #コマンド送信のために少し待機
    thread_Communication.loop = False #通信ループ終了
    thread_Communication.join() #ループ終了まで待つ
    client.sendData('direction',['Phenox'],(0.,0.))
    client.sendData('landing',['Phenox'],True) #ゲームが終了したらPhenoxを着陸させる
    time.sleep(0.05) #コマンド送信のために少し待機