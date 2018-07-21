#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
import socket
import time
import os
import thread
import string
import math
import serial
import serial.tools.list_ports
import pickle
import random
from flask import Flask
import flask
import cv2
from enum import Enum
import matplotlib.pyplot as plt
from pylab import *
import matplotlib
matplotlib.use('Agg')
mpl.rcParams['font.sans-serif'] = ['monospace']

#definations
moodtexts = (u'''狗狗运动量较大，目前处于活跃状态，适合与之玩耍，但要小心安全哦！''' , u'''小狗运动量适中，但未达到高标准。考虑下班后与狗狗玩耍5分钟吧！''' , u'''狗狗运动量较低，是不是心情不好或者身体不舒服？敬请下翻，看看究竟:)''')
foodtexts = (u'''食物充足，狗狗再也不用担心饿到啦！''',u'''食物较充足，余粮充分，狗狗3~4天内不会被饿到了！''',u'''食物告急，只能支撑1~2天，请尽快补充！''',u'''食物不够啦！''')
foodValues = (u'''略有超出''', u'''基本持平''', u'''略有下降''')

shootTryout = 0
lastShootTime = 0
ballHistory=[]
todayMomentum=[8,8,9,9.5,9.2,20,21,25.5,27.5,31.5,40.5,62.5,64.5,61.8,59.1,44.7,50.5,30.2,10.2,8.5,8.5,12,1,2]#1-24h
avgMomentum=[7.5,7.8,8,8.2,8.9,16.0,17.2,18.2,19.3,25.2,32.0,44.0,69.0,65.0,54.0,52.5,43.7,21.2,10.0,8,5,3,3,3]#21.0:11
uMomentum=0.0
hMomentum=0.0
dMomentum=0.0
for i in todayMomentum:
    dMomentum=dMomentum+i
print("fake dmomentum = %d"%(dMomentum))

hLastEntry=-1#last time update todayMomentum

minShootTime = 60
foodAmount = 0;#TODO
waterAmount = 0;
motion = 0;
foodKg = 0.75
avgFoodKg = 0.65
foodValue = u'''略有超出'''
normalSpeed = 40;
batteryLife = 87.0;
NULL = 424242#MAGIC NUM
FRAME_INTERVAL = 0.25
MAX_BALLLENGTH = 10#FIXME
TURN_THRESHOLD = 0.2
GO_THRESHOLD = 20
sportScore = 35.0;
avgSport = 45;

dock_state = 0
lObstacle = 0
rObstacle = 0

app = Flask("Petty")

iBest = -1.0
String = ""

screenx = 320#camera resolution / 2
screeny = 240

arduinoLoc = "/dev/ttyACM1"#volatile
blunoLoc = "/dev/ttyACM0"#volatile
unoLoc = "/dev/ttyACM2"#volatile

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0',55555))#volatile,32768-61000;(maybe?)

lastReceiveBluno = time.time()


print "step 1 of 6:perform arduino detection"
arduino = serial.Serial(arduinoLoc,9600,timeout=1.5,rtscts=True,dsrdtr=True)#FIX
print("using ",arduino.name," for arduino")
bluno = serial.Serial(blunoLoc,115200,timeout=1.5)
print("using",bluno.name," for bluno")

class Command(Enum):
    STOP = 0
    FORWARD = 1
    BACK = 2
    TURNLEFT = 3
    TURNRIGHT = 4
    SHOOT = 5
    RETRIEVE_STATION = 6
    QUERY = 7
class systemState(Enum):
    loading = 1
    handmode = 2
    automode_normal = 3
    automode_shooting = 4
    automode_retrieving_station = 5
    automode_stop = 8
class userPreference(Enum):
    PlayDog = 0
    RandomShoot = 1
    TimelyShoot = 2

state = systemState.loading
#-------------HTTP response part
@app.route('/')
def hello_world():
	return 'server run success on port 80'
@app.route('/stop')
def haltit():
    callUno(Command.STOP)
    return 'stopped'
@app.route('/l')
def left():
    print "from flask:begin write left"
    if state==systemState.handmode:
        callUno(Command.LEFT)
    print "from flask:end writing left"
    return 'left done'
@app.route('/r')
def right():
    print "from flask:begin write right"
    if state==systemState.handmode:
        callUno(Command.RIGHT)
    print "from flask:begin write right"
    return 'right done'
@app.route('/f')
def forward():
    print "from flask:begin write forward"
    if state==systemState.handmode:
        callUno(Command.FORWARD)
    print "from flask:begin write forward"
    return 'forward done'
@app.route('/d')
def down():
    print "from flask:begin write down"
    if state==systemState.handmode:
        callUno(Command.BACK)
    print "from flask:begin write down"
    return 'back done'
@app.route('/turnleft')
def turnleft():
    print "from flask:begin write turnleft"
    if state==systemState.handmode:
        callUno(Command.TURNLEFT,normalSpeed)
    print "from flask:end write turnleft"
    return 'left done'
@app.route('/turnright')
def turnright():
    print "from flask:begin write turnright"
    if state==systemState.handmode:
        callUno(Command.TURNRIGHT,normalSpeed)
    print "from flask:begin write turnright"
    return 'right done'
@app.route('/up')
def upAuto():
    global state
    state=systemState.automode_retrieving_station
    time.sleep(0.5)
    print('now state=',state)
    return 'auto up'
@app.route('/down')
def downAuto():
    global state
    state=systemState.handmode
    os.system("killall apriltags_demo")
    time.sleep(0.5)
    print('now state=',state)
    return 'auto down'
@app.route('/shoot')
def shoot():
    if state==systemState.handmode:
        callUno(Command.SHOOT)
    return 'shoot done'
@app.route('/pick')
def pick():
    if state==systemState.handmode:
        callUno(Command.PICK)
    return 'pick done'
@app.route('/statistics')#the statistics.
def showStatistics():
    global uMomentum,foodAmount,foodtext,foodKg,foodValue,foodtexts,moodtexts
    if uMomentum*2.0>100:
        moodtext = moodtexts[0]
    elif uMomentum*2.0>50:
        moodtext = moodtexts[1]
    else:
        moodtext = moodtexts[2]

    if foodAmount>80:
        foodtext = foodtexts[0]
    elif foodAmount>30:
        foodtext = foodtexts[1]
    elif foodAmount>10:
        foodtext = foodtexts[2]
    else:
        foodtext = foodtexts[3]
    if foodKg>avgFoodKg and math.fabs(foodKg-avgFoodKg)>=0.1:
        foodValue = foodValues[0]
    elif math.fabs(foodKg-avgFoodKg)<=0.1:
        foodValue = foodValues[1]
    else:
        foodValue = foodValues[2]

    if sportScore >= avgSport:
        sportState = u'''高'''
    else:
        sportState = u'''低'''
    return flask.render_template('index.html',motion=uMomentum*2.0, \
    food=foodAmount,water = waterAmount,moodtext = moodtext,\
    foodtext=foodtext,foodKg=foodKg,avgFoodKg=avgFoodKg,\
    foodValue=foodValue,batteryLife=batteryLife,\
    sportScore=sportScore,sportState=sportState)

#EOF---------------------
def start_http_handler():
	app.run(host='0.0.0.0',port=5000)
def acquire_info():
    tot = arduino.read_until("\n");
    if len(tot) != 3:
        print "acquire info error."
    else:
        print tot
    arduino.flushInput();

# def april():
#     a = os.popen("./apriltags -d -D 1")
#     while c=a.readLines():
#         d,x,y,z = c.split(" ")

def ReadRawFile(filepath):
    file = open(filepath)
    try:
        tempa = file.read()
    finally:
        file.close()
        tempa = tempa.replace(" ","").replace("\n","")
    return tempa
def callUno(action,parameter=normalSpeed):
    if not arduino.writable():
        print("E:arduino not writable")
    else:
        if parameter>=10  and parameter<=99:
            arduino.write(str(action)+str(parameter))
        else:
            arduino.write(str(action)+"0"+str(parameter))
def dist(x1,y1,x2,y2):
    return math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2))
def isFineToShoot():#judge 1.if is night 2. if too frequent (3.if danger)
    dt = math.fabs(time.time()-lastShootTime)
    #1.judge freq
    if (dt>=minShootTime):#if
        pass
    else:
        return False
    #2.judge night
    if (time.localtime(time.time()).tm_hour>6 and time.localtime(time.time()).tm_hour<21):
        return True
    else:
        return False;

def extractDigit(word):
    res = ''
    for alp in word:
        if alp.isdigit():
            res = res+str(alp)

    if res!='':
        return int(res)
    else:
        return None

def mood():#TODO:return dog mood based on recently acceleration count,1to100,integer/float
    global uMomentum,hMomentum,hLastEntry,lastReceiveBluno
    time.sleep(0.5)

    while True:
        raw=bluno.read_until('\r\n')
        # print "raw=%s"%(raw)
        if hasThing(raw) and hasThing(extractDigit(raw)):
            # print "raw=%s,"%(extractDigit(raw))

            if extractDigit(raw)>0 :#good
                lastReceiveBluno = time.time()
                # x,y,z = raw.split(",")
                #print("x=",x,",y=",y,",z=",z)
                uMomentum = extractDigit(raw)
                hMomentum = hMomentum
                if time.localtime(time.time()).tm_hour!=hLastEntry:
                    pass;#TODO
                    # uMomentum=math.fabs(int(x))+math.fabs(int(y))+math.fabs(int(z)) #update current
                    # hMomentum=hMomentum+uMomentum/3600.0 #add a small bonus
                    # if time.localtime(time.time()).tm_hour!=hLastEntry:#if a new hour occours
                    #     hLastEntry=time.localtime(time.time()).tm_hour
                    #     todayMomentum[hLastEntry-1]=hMomentum
                    #     hMomentum=0.0#clear the temp momentum
                raw=''
            # except BaseException as b:
            #     pass;

def dogAlarm():#thread
    while True:
        if math.fabs(time.time()-lastReceiveBluno)>=5:
            #callUno(Command.RING)
            print "狗狗不见了！"
            time.sleep(1)

def fetchFoodWater():
    global foodAmount
    while True:
        foodAmount2,addr = s.recvfrom(1024)
        if round(float(foodAmount2))>0:#fixed:in case of flush
            foodAmount = round(float(foodAmount2))#update
            foodKg = foodAmount*0.01*3

def hasThing(obj):
    if obj is None:
        return False
    else:
        return True
def updateGraph():
    names = range(1,25)
    x = range(len(names))
    y = todayMomentum
    y1 = avgMomentum
    plt.plot(x,y,)
    plt.plot(x, y, marker='o', mec='r', mfc='w',label=u'curret dog mood')
    plt.plot(x, y1, marker='*', ms=10,label=u'average dog mood')
    plt.legend()  # 让图例生效
    plt.xticks(x, names, rotation=45)
    plt.margins(0)
    plt.subplots_adjust(bottom=0.15)
    plt.xlabel(u"Time of The Day(h)") #X轴标签
    plt.ylabel("Movement") #Y轴标签
    plt.title("Dog movement picture") #标题
    savefig("test.jpg")

def getLastLine(file):
    while True:
        try:
            ll=file.next()
        except StopIteration:
            return ll;

#---------------------------------------------------------------------------------
state = systemState.loading
with open("UserPreferences.pk","rb") as usf:
    strategy = pickle.load(usf)
    print("strategy=",strategy)
print "step 4 of 6:start user respond service"
thread.start_new_thread(start_http_handler,())
print "step 6 of 6:start dog mood processing service"
_ = bluno.read_all()#flush the pool
thread.start_new_thread(mood,())
time.sleep(3)
thread.start_new_thread(dogAlarm,())
time.sleep(3)
thread.start_new_thread(fetchFoodWater,())
print "step 7 of 6:start autoretrieve service"
while True:

    #print "R:state=<SystemState>",state
    if math.fabs(uMomentum*2.0)<=0.5:
        print "--"
    else:
        print "心情"+str(uMomentum*2.0)

    if (state==systemState.loading):
        print "handmode started."
        state=systemState.handmode
    elif (state==systemState.automode_normal ):#fixed #or state==systemState.automode_shooting
        dogmood = uMomentum*2.0
        print "uDogmood=",dogmood
        if dogmood>50:
            #state=systemState.automode_shooting
                if isFineToShoot(): #HACK
                    callUno(Command.SHOOT)
                print "right to shoot:shoot performed."
                shootTryout = 0;
                time.sleep(random.randint(5,20))
                state=systemState.automode_normal
    elif (state==systemState.automode_retrieving_station):
        callUno(Command.TURNLEFT)
        flag = True;done = False;
        f = os.popen("./apriltags_demo -d -D 1")
        line = f.readline()
        while not done:
            try:
                d,x,y,z = line.split(" ")
            except ValueError:
                print "catched"
                if line.find("Terminated"):
                    print "termed."
                    print "attempt to reboot..."
                    f = os.popen("./apriltags_demo -d -D 1")
                    line = f.readline()
            print "y=%f"%(float(y))
            yf = float(y);
            if (yf>TURN_THRESHOLD):
                callUno(Command.TURNRIGHT)
            elif -yf>TURN_THRESHOLD:
                callUno(Command.TURNLEFT)
            else:
                callUno(Command.FORWARD)
                time.sleep(0.1)
                print "(temply)located."
                #os.system('killall apriltags_demo')

            line = f.readline()
        callUno(Command.STOP)
        os.system("killall apriltags_demo")

        print "navigated."
        batteryLife =100.0

        state = systemState.automode_normal
    else:
        print "since in a brand-new mode , system halts.\n"
    print "foodAmount="+str(foodAmount)
    time.sleep(0.5)
    batteryLife = batteryLife-0.02#HACK
    if batteryLife<=0:
        systemState = systemState.automode_retrieving_station

    time.sleep(FRAME_INTERVAL)
