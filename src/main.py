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

NULL = 424242#MAGIC NUM
FRAME_INTERVAL = 0.25
MAX_BALLLENGTH = 10#FIXME
TURN_THRESHOLD = 40
GO_THRESHOLD = 20

dock_state = 0
lObstacle = 0
rObstacle = 0

app = Flask("Petty")

iBest = -1.0
String = ""

screenx = 320#camera resolution / 2
screeny = 240

systemDevice = "/dev/video1"#volatile
directPlayDevice = "/dev/video2"#volatile

arduinoLoc = "/dev/ttyACM1"#volatile
blunoLoc = "/dev/ttyACM0"#volatile
unoLoc = "/dev/ttyACM2"#volatile

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('192.168.1.157',2018))#volatile
lastReceiveBluno = time.time()

shootTryout = 0
lastShootTime = 0
ballHistory=[]
todayMomentum=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#1-24h
uMomentum=0.0
hMomentum=0.0
hLastEntry=-1#last time update todayMomentum

foodAmount = 0;#TODO
waterAmount = 0;
motion = 0;

normalSpeed = 40;

print "step 1 of 6:perform arduino detection"
arduino = serial.Serial(arduinoLoc,9600,timeout=1.5,rtscts=True,dsrdtr=True)#FIX
print("using ",arduino.name," for arduino")
bluno = serial.Serial(blunoLoc,115200,timeout=1.5)
print("using",bluno.name," for bluno")
# uno = serial.Serial(unoLoc,9600,timeout=1.5)
# print("using",uno.name," for uno")


# print "Now running the Serial check."
# print "please put your hand before the ultrasound detector"


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
print "Step 2 of 6 : test navigate camera..."
currentPhoto=takePhoto()#test if the cam is success

class Command(Enum):
                 # 0->STOP  1->FORWARD  2->BACK   3->LEFT   4->RIGHT   5->TURNLEFT  6->TURNRIGHT
    STOP = 0
    FORWARD = 1
    BACK = 2
    TURNLEFT = 3
    TURNRIGHT = 4
    SHOOT = 5
    QUERY = 6

class systemState(Enum):
#    empty = 0 #useless , it's impossible
    loading = 1
    handmode = 2
    automode_normal = 3
    automode_shooting = 4
    automode_retrieving_station = 5
    automode_moving_obstacle = 6

    automode_navigate = 7
    automode_stop = 8

class userPreference(Enum):
    PlayDog = 0
    RandomShoot = 1
    TimelyShoot = 2

state = systemState.loading
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
def showStatistics():
    return flask.render_template('index.html',motion=uMomentum*2.0,food=foodAmount,water = waterAmount)

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

def acquire_info():
    tot = arduino.read_until("\n");
    if len(tot) != 3:
        print "acquire info error."
    else:
        print tot
    arduino.flushInput();
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
    arduino.write(str(action))
    # if (parameter==-1):
    #     if action==Command.STOP:
    #         arduino.write('111')
    #         # time.sleep(0.5)
    #         print('writed 111')
    #     else:
    #         arduino.write(str(action)+" "+str(normalSpeed))
    #         # time.sleep(0.5)
    #         print('writed ',str(action)+" "+str(normalSpeed))
    # else:
    #     if action==Command.STOP:
    #         arduino.write('111')
    #         #time.sleep(0.5)
    #         print('writed 111')
    #     else:
    #         if parameter>0 and parameter<=99:
    #             arduino.write(str(action)+" "+str(parameter))
    #             time.sleep(0.5)
    #             print('writed ',str(action)+" "+str(normalSpeed))
    #         else:
    #             print("E:callUno parameter fail")

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
    time.sleep(2)

    while True:
        raw=bluno.read_until('\r\n')
        # print raw
        # print "the type of raw is:"
        # print type(raw)
        # print('the len is ',len(raw))
        if hasThing(raw):
            if len(raw)<=15:#HACK
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
            # except BaseException as b:
            #     pass;
        time.sleep(0.2)
def dogAlarm():#thread
    while True:
        if math.fabs(time.time()-lastReceiveBluno)>=5:
            #callUno(Command.RING)
            print "狗狗不见了！"
            time.sleep(1)
def fetchFoodWater():
    while True:
        foodAmount,addr = s.recvfrom(1024)

def hasThing(obj):
    if obj is None:
        return False
    else:
        return True


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

# def getDirection():#get the base 's direction
#     dot = None;cnt=1
#     while dot==None:
#         print("%d trying..\n" %(cnt))
#         cnt=cnt+1
#         pic = takePhoto();dot = getBlueDot(pic)
#         if cnt>10:
#             print "E:返回基站错误::找不到基站"
#             #sys.exit("sorry,goodbye!")
#             return None;
#     print("X:%f Y:%f\n" %( (dot[0]-screenx/2) , (screeny/2-dot[1]) ));
#     # angle = math.atan((dot[0]-screenx/2)/(screeny/2-dot[1]))#in rads
#     print("angle:%f\n" %( angle ) )
#     return angle;


#---------------------------------------------------------------------------------
state = systemState.loading
print "step 3 of 6:read user preferences"
with open("UserPreferences.pk","rb") as usf:
    strategy = pickle.load(usf)
    print("strategy=",strategy)
print "step 4 of 6:start user respond service"
thread.start_new_thread(start_http_handler,())
print "step 5 of 6:start direct play service"
thread.start_new_thread(start_service,())
print "step 6 of 6:start dog mood processing service"
_ = bluno.read_all()#flush the pool
thread.start_new_thread(mood,())
time.sleep(3)
thread.start_new_thread(dogAlarm,())
time.sleep(3)
thread.start_new_thread(fetchFoodWater,())
# print "step 6.5 of 6:start car info acquire service"
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
            p1 = takePhoto();time.sleep(1); p2 = takePhoto();
            if not isDangerous(p1,p2,320,240) and isFineToShoot(): #HACK
                callUno(Command.SHOOT)
                print "right to shoot:shoot performed."
                shootTryout = 0;
                time.sleep(random.randint(5,20))
                state=systemState.automode_normal
    elif (state==systemState.automode_retrieving_station):
        pic = takePhoto()
        p = getBlueDot(pic);
        if (hasThing(p)):
            print "home detected@(%d,%d).rel.p is (%d,%d).\n" % (p[0],p[1],p[0]-screenx,screeny-p[1])
            if (math.fabs(p[0]-screenx)>TURN_THRESHOLD):

                print "now turning "+ str(math.fabs(p[0]-screenx)) +"pixel-steps..."

                while (math.fabs(p[0]-screenx)>TURN_THRESHOLD):
                    if p[0]<screenx:
                        callUno(Command.TURNRIGHT)
                        time.sleep(0.3)
                        callUno(Command.STOP)
                        time.sleep(1)
                        pic = takePhoto()
                        pp = getBlueDot(pic);
                        while not hasThing(pp):
                            pic = takePhoto()
                            pp = getBlueDot(pic);
                            time.sleep(0.5)
                            print "base lost while attempting turn"
                        print "base found."
                        p = pp#update the direction

                    else:
                        callUno(Command.TURNLEFT)
                        time.sleep(0.5)
                        callUno(Command.STOP)
                        time.sleep(1)
                        pic = takePhoto()
                        pp = getBlueDot(pic);
                        while not hasThing(pp):
                            pic = takePhoto()
                            pp = getBlueDot(pic);
                            print "base lost while attempting turn"
                        print "base found."
                        p = pp#update the direction
                callUno(Command.STOP)
                time.sleep(0.5)
                print "turn done."
            else:
                print "turn has done."
                print "now going "+ str(math.fabs(p[1]-screeny)) +"pixel-steps..."
                if (math.fabs(p[1]-screeny)>GO_THRESHOLD):
                    if p[1]<screeny:
                        callUno(Command.FORWARD)
                        time.sleep(0.3)
                        callUno(Command.STOP)
                        time.sleep(0.8)
                    else:
                        callUno(Command.BACK)
                        time.sleep(0.3)
                        callUno(Command.STOP)
                        time.sleep(0.8)
                else:
                    print "go done!"
                    state = systemState.automode_navigate;
        else:
            print "unable to find base station."
    else:
        print "new mode.do nothing."
    time.sleep(FRAME_INTERVAL)
