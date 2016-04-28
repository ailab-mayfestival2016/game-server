# -*- coding: utf-8 -*-

import csv
import random
import threading
import time

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
    file_dir = 'C:\document\map'
    difficulty = raw_input('Please input difficulty.\n')
    file_dir = file_dir + '\block_' + difficulty + '.csv'
    fh1 = open(file_dir,'rb')
    reader1 = csv.reader(fh1)
    lst_block = []
    for i in reader1:
        tmp = Block(i[0],i[1],i[2],i[3],i[4])
        lst_block.append(tmp)
    fh1.close()
    file_dir = file_dir + '\item_' + difficulty + '.csv'
    fh2 = open(file_dir,'rb')
    reader2 = csv.reader(fh2)
    lst_item = []
    for i in reader2:
        tmp = Item(i[0],i[1])
        lst_item.append(tmp)
    fh2.close()
    return lst_block,lst_item

def first_vector(): #初期ベクトルを生成する函数
    vector = [random.random()*45.0+45.0,(random.random()-0.5)*180.0]
    return vector

def hit_judge(position,block_lst): #ブロックに当たったかどうかを判定する関数
    return True

def is_exist(block_lst): #ブロックがまだあるかどうか判定する函数
    judge = False
    for i in xrange(len(block_lst)):
        judge = judge or block_lst[i].exist
    return judge

def gameover_judge(position): #ゲームオーバーかどうかを判別する函数
    if position[0] > 300.0: #x座標が300以上でゲームオーバー
        return True
    else:
        return False

def append_block(data,block_lst): #ブロックを追加する函数
    tmp = Block(data[0],data[1],data[2],data[3],data[4])
    block_lst.append(tmp)

def append_item(data,item_lst): #アイテムを追加する函数
    tmp = Item(data[0],data[1])
    item_lst.append(tmp)

def func_communication(): #通信スレッド用の函数
    pass

class Timer_thread(threading.Thread): #タイマースレッドのクラス
    def __init__(self):
        super(Timer_thread,self).__init__()
        self.timeup = False
    def run(self):
        time.sleep(300.0) #制限時間は300秒
        self.timeup = True

class Communication_thread(threading.Thread): #通信スレッドのクラス
    def __init__(self):
        super(Communication_thread,self).__init__()
        self.receive = [] #メインスレッドが受信するコマンドを格納
        self.send = [] #メインスレッドが送信するコマンドを格納
    def run(self):
        func_communication()

class Item_thread(threading.Thread): #アイテムを取った時にその持続時間を計っておくスレッド
    def __init__(self):
        super(Item_thread,self).__init__()
        self.ready = True #スレッドが待機状態かどうかを示す
    def run(self): #アイテムを取ったら呼び出す(is_aliveメソッドがTrueならアイテムの効果中)
        time.sleep(20.0) #アイテムの持続時間
        self.ready = False #スレッドが待機状態でない(アイテムを取り終わった後)

if __name__ == '__main__':
    thread_Communication = Communication_thread()
    thread_Timer = Timer_thread()
    thread_Item = Item_thread()
    block_lst,item_lst = map_setup()
    initial_vector = first_vector()
    #ここにマップデータと初期ベクトルの送信プログラムが入る
    thread_Communication.start() #スレッド開始
    thread_Timer.start()
    while True(): #メインループ
        if thread_Timer.timeup == True: #タイムアップの時
            send_command = (6,None)
            thread_Communication.send.append(send_command)
            break
        if thread_Item.ready == False: #アイテムの持続時間が終わったとき
            thread_Item.join()
            send_command = (2,False)
            thread_Communication.send.append(send_command)
            thread_Item = Item_thread() #アイテムのスレッドを待機状態にしておく
        elif len(thread_Communication.receive) > 0: #コマンドが送られてきているとき
            receive_command = thread_Communication.receive[0]
            del thread_Communication.receive[0] #コマンドを受け取って消す
            if receive_command[0] == 1: #座標が送られてきたとき
                position = receive_command[1]
                if hit_judge(position,block_lst) != False: #当たっていた場合法線ベクトルを送信し、クリア判定
                    if is_exist(block_lst) == False: #クリアの場合(ブロックが全部消された)
                        send_command = (4,None)
                        thread_Communication.send.append(send_command)
                        break
                elif gameover_judge(position) == True: #ゲームオーバーの時
                    send_command = (5,None)
                    thread_Communication.send.append(send_command)
                    break
            elif receive_command[0] == 2: #ブロックの追加命令が送られてきたとき
                append_block(receive_command[1],block_lst)
                send_command = (3,(block_lst,item_lst)) #マップ情報送信
                thread_Communication.send.append(send_command)
            elif receive_command[0] == 3: #アイテムの追加命令が送られてきたとき
                append_item(receive_command[1],item_lst)
                send_command = (3,(block_lst,item_lst)) #マップ情報送信
                thread_Communication.send.append(send_command)
