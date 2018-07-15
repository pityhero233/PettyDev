#!/usr/bin/python
# -*- coding: utf-8 -*-

import flask
from flask import Flask
app = Flask("Petty")

uMomentum = 12.0
foodAmount = 63.7
waterAmount = 35.5
moodtexts = (u'''狗狗运动量较大，目前处于活跃状态，适合与之玩耍，但要小心安全哦！''' , u'''小狗运动量适中，但未达到高标准。考虑下班后与狗狗玩耍5分钟吧！''' , u'''狗狗运动量较低，是不是心情不好或者身体不舒服？敬请下翻，看看究竟:)''')
foodtexts = (u'''食物充足，狗狗再也不用担心饿到啦！''',u'''食物较充足，余粮充分，狗狗3~4天内不会被饿到了！''',u'''食物告急，只能支撑1~2天，请尽快补充！''',u'''食物不够啦！''')
@app.route('/statistics')#the statistics.
def showStatistics():
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
        moodtext = moodtexts[3]
    return flask.render_template('index.html',motion=uMomentum*2.0,food=foodAmount,water = waterAmount,moodtext = moodtext,foodtext=foodtext)

app.run(host='0.0.0.0',port=5000)
