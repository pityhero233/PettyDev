import flask
from flask import Flask
app = Flask("Petty")

uMomentum = 12.0
foodAmount = 63.7
waterAmount = 35.5
@app.route('/statistics')#the statistics.
def showStatistics():
    return flask.render_template('index.html',motion=uMomentum*2.0,food=foodAmount,water = waterAmount)

app.run(host='0.0.0.0',port=5000)
