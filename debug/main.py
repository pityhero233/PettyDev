#!/usr/bin/python
# -*- coding: utf-8 -*-
import numpy as np
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
import cv2
from enum import Enum
normalSpeed = 11
NULL = 424242#MAGIC NUM

app = Flask("Petty")

iBest = -1.0
String = ""

screenx = 640#camera resolution
screeny = 320

systemDevice = "/dev/video2"
directPlayDevice = "/dev/video1"

arduinoLoc = "/dev/ttyACM0"#volatile
blunoLoc = "/dev/ttyACM1"#volatile

lastReceiveBluno = time.time()

shootTryout = 0
lastShootTime = 0
ballHistory=[]
todayMomentum=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#1-24h
uMomentum=0.0
hMomentum=0.0
hLastEntry=-1#last time update todayMomentum
#print "step 0 of 6:perform arduino detection"
arduino = serial.Serial(arduinoLoc,9600,timeout=1.5,rtscts=True,dsrdtr=True)#FIX
#print("using ",arduino.name," for arduino")
#bluno = serial.Serial(blunoLoc,115200,timeout=1.5)
#print("using",bluno.name," for bluno")

def scanUno():
    port_list = list(serial.tools.list_ports.comports())
    if len(port_list)<=0:
        print("E:arduino base not found.")
        return NULL
    else:
        pl1 =list(port_list[0])
        port_using = pl1[0]
        arduino = serial.Serial(port_using,57600,timeout = 1.5)
        print("using ",arduino.name)
        print("current arduino=",arduino)
        return arduino

def takePhoto():#take a photo using outside func
    try:
        os.system("fswebcam -d "+systemDevice+" -r 640x480 --no-banner tot.jpg")
        pic = cv2.imread("tot.jpg")
        return pic
    except:
        print "takePhoto Error"

#currentPhoto=takePhoto()#test if the cam is success

class Command(Enum):
                 # 0->STOP  1->FORWARD  2->BACK   3->LEFT   4->RIGHT   5->TURNLEFT  6->TURNRIGHT
    STOP = 0
    FORWARD = 1
    BACK = 2
    TURNLEFT = 3
    TURNRIGHT = 4
    SHOOT = 8

class systemState(Enum):
    empty = 0
    loading = 1
    handmode = 2
    automode_normal = 3
    automode_shooting = 4
    automode_retrieving_station = 5
    automode_moving_obstacle = 6

class userPreference(Enum):
    PlayDog = 0
    RandomShoot = 1
    TimelyShoot = 2

state = systemState.handmode
strategy = userPreference.PlayDog#TODO
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
        callUno(Command.TURNLEFT,150)
    print "from flask:end write turnleft"
    return 'left done'
@app.route('/turnright')
def turnright():
    print "from flask:begin write turnright"
    if state==systemState.handmode:
        callUno(Command.TURNRIGHT,150)
    print "from flask:begin write turnright"
    return 'right done'
@app.route('/up')
def upAuto():
    global state
    state=systemState.automode_normal
    print('now state=',state)
    return 'auto up'
@app.route('/down')
def downAuto():
    global state
    state=systemState.handmode
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
@app.route('/prefer_playdog')
def chg_prf_pd():
    strategy = userPreference.PlayDog
    with open("UserPreferences.pk","wb") as filea:
        pickle.dump(strategy,filea)
@app.route('/prefer_random')
def chg_prf_rd():
    strategy = userPreference.RandomShoot
    with open("UserPreferences.pk","wb") as filea:
        pickle.dump(strategy,filea)
#@app.route('/prefer_timelyshoot') TODO
@app.route('/statistics')#the statistics.
def debug_print():#print today's momentum.
    dst = '''{'''

    tot = 0;
    while (tot<=23):
        dst.join(todayMomentum[tot])
        if tot!=23:
            dst.join(",")
    dst.join('''}''')
    print dst

@app.route('/statisticsB')#magic
def debug_printB():#MAGIC HACK FIXME
    print '''{8, 10, 12, 13, 15, 13, 31, 35, 45, 46, 42, 52, 71, 67, 70, 41, 35, \
36, 27, 25, 25, 31, 10, 8}'''

#EOF---------------------

def start_http_handler():
	app.run(host='0.0.0.0',port=5000)

def start_service():
    res=os.system('''mjpg_streamer -i "input_uvc.so -d '''+directPlayDevice+''' -f 10 -y" -o "output_http.so -w www -p 8888"''')#dont forget to change video n

def ReadRawFile(filepath):
    file = open(filepath)
    try:
        tempa = file.read()
    finally:
        file.close()
        tempa = tempa.replace(" ","").replace("\n","")
    return tempa

def callUno(action,parameter=-1):
    if not arduino.writable():
        print("E:arduino not writable")
    if (parameter==-1):
        if action==Command.STOP:
            arduino.write('111')
            time.sleep(0.5)
            print('writed 111')
        else:
            arduino.write(str(action)+" "+str(normalSpeed))
            time.sleep(0.5)
            print('writed ',str(action)+" "+str(normalSpeed))
    else:
        if action==Command.STOP:
            arduino.write('1 000')
            time.sleep(0.5)
            print('writed 1 000')
        else:
            if parameter>0 and parameter<=999:
                arduino.write(str(action)+" "+str(parameter))
                time.sleep(0.5)
                print('writed ',str(action)+" "+str(normalSpeed))
            else:
                print("E:callUno parameter fail")

def dist(x1,y1,x2,y2):
    return math.sqrt((x1-x2)*(x1-x2)+(y1-y2)*(y1-y2))

def isDangerous(frame1,frame2,px,py):#detect if point(px,py) is in "the moving area of frame"(dog) PASSED
    gray1 = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)#FIXED 1
    gray2 = cv2.cvtColor(frame2,cv2.COLOR_BGR2GRAY)#FIXED 2
    diff = cv2.absdiff(gray1,gray2)
    _,thr = cv2.threshold(diff,15,255,cv2.THRESH_BINARY)#FIXED 3&4
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(15,15))
    thr = cv2.erode(thr,erode_kernel)
    thr = cv2.dilate(thr,dilate_kernel)
    contours,_ = cv2.findContours(thr,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

    for tot in contours:
        ((x,y),radius) = cv2.minEnclosingCircle(tot)
        if dist(x,y,px,py)<=radius:
            return True
    return False

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

def mood():#TODO:return dog mood based on recently acceleration count,1to100,integer/float
    global uMomentum,hMomentum,hLastEntry,lastReceiveBluno
    while True:
        raw=bluno.read_until('\r\n')

        while raw!='':
            lastReceiveBluno = time.time()
            x,y,z = raw.split(",")
            #print("x=",x,",y=",y,",z=",z)
            if x!='' and y!='' and z!='':
                uMomentum=math.fabs(int(x))+math.fabs(int(y))+math.fabs(int(z)) #update current
                hMomentum=hMomentum+uMomentum/3600.0 #add a small bonus
                if time.localtime(time.time()).tm_hour!=hLastEntry:#if a new hour occours
                    hLastEntry=time.localtime(time.time()).tm_hour
                    todayMomentum[hLastEntry-1]=hMomentum
                    hMomentum=0.0#clear the temp momentum
                raw=''

def dogAlarm():#thread
    while True:
        if math.fabs(time.time()-lastReceiveBluno)>=5:
            #callUno(Command.RING)
            print "狗狗不见了！"
            time.sleep(2)
def getBlueDot(frame2):#returns a num[] contains [x,y,r]
    lower = (25,85,6)
    upper = (64,255,255)
    LowerBlue = np.array([100, 0, 0])
    UpperBlue = np.array([130, 255, 255])
    if True:
        element = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))

        HSV =  cv2.cvtColor(frame2,cv2.COLOR_BGR2HSV)
        #H,S,V = cv2.split(HSV)
        mask = cv2.inRange(HSV,lower,upper)
        mask = cv2.erode(mask,None,iterations=2)
        mask = cv2.dilate(mask,None,iterations=2)
        contours = cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2]
        center = None

        maxPercentage = 0
        maxPercentageContour = None
        for contour in contours:
        	((x,y),radius) = cv2.minEnclosingCircle(contour)
        	contourArea = cv2.contourArea(contour)
        	if contourArea < 100:
        		continue
        	pass;
        	percentage = contourArea / (radius * radius * 3.1415926)
        	if percentage>maxPercentage and percentage>0.50:#requires DEBUG
        		maxPercentageContour = contour

        if (maxPercentageContour!=None):
            M=cv2.moments(maxPercentageContour)
            center = (int(M["m10"]/M["m00"]), int(M["m01"] / M["m00"]))
            ((x,y),radius) = cv2.minEnclosingCircle(contour)
            cv2.circle(frame2,(int(x),int(y)),int(radius),(0,255,255),2)
            cv2.circle(frame2,center,5,(0,0,255),-1)
            datatorep = [int(x),int(y),int(radius)]
            return datatorep
        # if len(contours)>0:
        #     c = max(contours,key=cv2.contourArea
        #     ((x,y),radius) = cv2.minEnclosingCircle(c)
        #     M=cv2.moments(c)
        #     center = (int(M["m10"]/M["m00"]), int(M["m01"] / M["m00"]))
        #     if radius > 10: #confirm it is a ball
        #         datatorep = [int(x),int(y),int(radius)]
        #         cv2.circle(frame2,(int(x),int(y)),int(radius),(0,255,255),2)
        #         cv2.circle(frame2,center,5,(0,0,255),-1)
        #         return datatorep



def gotoHome():
    pass
    #while (distance):
    #   while (obstacle) right;
    #   angle = calc()
    #   gotoAngle()

def TennisDetect(frame2):#capture a picture and perform a tennis detect
    global lower,upper,LowerBlue,UpperBlue,iBest
    #cv2.namedWindow("splitter",cv2.WINDOW_AUTOSIZE)
    #cv2.namedWindow("debug",cv2.WINDOW_AUTOSIZE)

    diff=getCircle(frame2)
    #cv2.imshow("splitter",frame2)
    #cv2.waitKey(1)
    print diff #show the data containing [x,y,r]
    #cv2.destroyAllWindows();
    if diff!=-1:
        return diff
    else:
        return [0,0,0]


#---------------------------------------------------------------------------------
print "step 2 of 6:start user respond service"
thread.start_new_thread(start_http_handler,())
while True:
	print "i am running!"
	time.sleep(1)
