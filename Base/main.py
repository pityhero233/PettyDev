#! /usr/bin/python
# -*- coding:utf-8 -*-

import RPi.GPIO as GPIO
import time
import socket
sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fullbucket = 14.5
def checkdist():
        GPIO.output(2,GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(2,GPIO.LOW)
        while not GPIO.input(3):
                pass
        t1 = time.time()
        while GPIO.input(3):
                pass
        t2 = time.time()
        #返回距离，单位为cm
        return (t2-t1)*34000/2
def init():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2,GPIO.OUT,initial=GPIO.LOW)
    GPIO.setup(3,GPIO.IN)
    time.sleep(1)

def clean():
    GPIO.cleanup()

init()

while True:
    d = checkdist()
    percent = (100-d/fullbucket*100)
    sck.sendto(str(percent),('192.168.1.194',2018))#volatile
    time.sleep(0.5)
clean()
