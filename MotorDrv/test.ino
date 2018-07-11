//#include <PID_v1.h>
#include <Servo.h>
#include <assert.h>
#define FRAME_DURATION 50000
int SpeedToPWM[256];
double lSpeed,rSpeed;
double lPWM=30,rPWM=30;

const int TargetSpeed = 70;//FIXME
double Kp=0.4, Ki=5.5, Kd=0;

const int shootPort = 26;//volatile
const int lSpeedPort = 2;//checked
const int lControlPortA = 22;
const int lControlPortB = 23;
const int lReturnPort = 18;
const int rSpeedPort = 3;
const int rControlPortA = 24;
const int rControlPortB = 25;
const int rReturnPort = 19;
unsigned long currentMillis,previousMillis;

const bool left = true;
const bool right = false;
int mode=0;
int argument=100;//input speed (if have any)

// PID PID_L(&lSpeed, &lPWM, &TargetSpeed, Kp, Ki, Kd, DIRECT);
// PID PID_R(&rSpeed, &rPWM, &TargetSpeed, Kp, Ki, Kd, DIRECT);

void letForward(bool isLeftPort){
  if (isLeftPort){
    digitalWrite(lControlPortA,HIGH);
    digitalWrite(lControlPortB,LOW);
  }
  else{
    digitalWrite(rControlPortA,HIGH);
    digitalWrite(rControlPortB,LOW);
  }
}

void letBackward(bool isLeftPort){
  if (isLeftPort){
    digitalWrite(lControlPortB,HIGH);
    digitalWrite(lControlPortA,LOW);
  }
  else{
    digitalWrite(rControlPortB,HIGH);
    digitalWrite(rControlPortA,LOW);
  }
}

void letHalt(bool isLeftPort){
  if (isLeftPort){
    digitalWrite(lControlPortA,HIGH);
    digitalWrite(lControlPortB,HIGH);
  }
  else{
    digitalWrite(rControlPortA,HIGH);
    digitalWrite(rControlPortB,HIGH);
  }
}

void changeSpeed(bool isLeftPort,int speed){
  assert((speed>0) && (speed<255));
  if (isLeftPort) analogWrite(lSpeedPort,speed);
  else analogWrite(rSpeedPort,speed);
}



void accumulateLSpeed(){lSpeed++;}
void accumulateRSpeed(){rSpeed++;}




void setup()
{
    Serial.begin(9600);
    Serial.setTimeout(100);
    while(Serial.read()>= 0) {} //clear serial port
    pinMode(shootPort,OUTPUT);//init()
    pinMode(lControlPortA,OUTPUT);
    pinMode(lControlPortB,OUTPUT);
    pinMode(rControlPortA,OUTPUT);
    pinMode(rControlPortB,OUTPUT);
    pinMode(lSpeedPort,OUTPUT);
    pinMode(rSpeedPort,OUTPUT);
    pinMode(lReturnPort,INPUT);
    pinMode(rReturnPort,INPUT);
    attachInterrupt(digitalPinToInterrupt(lReturnPort) , accumulateLSpeed, CHANGE);
    attachInterrupt(digitalPinToInterrupt(rReturnPort) , accumulateRSpeed, CHANGE);
    delay(1000);
    TURNRIGHT();
    // PID_L.SetMode(AUTOMATIC);
    // PID_L.SetSampleTime(50);
    // PID_R.SetMode(AUTOMATIC);
    // PID_R.SetSampleTime(50);
  }

void parseArguments(){
  char* str;
  if (Serial.readBytes(str,Serial.available())){
    mode = (char)str[0]-'0';
    argument = ((char)str[1]-'0')*10+((char)str[2]-'0');
  }
  else{
    mode = -1;
  }
}
void loop()
{
  parseArguments();
  if (mode==9){
    STOP();
    Serial.println(lSpeed);
    Serial.printf("||");
    Serial.println(rSpeed);
  }
}

void STOP(){
  letHalt(left);
  letHalt(right);
  mode=0;
}
void FORWARD(){
  letForward(left);
  letForward(right);
  analogWrite(lSpeedPort,lPWM);
  analogWrite(rSpeedPort,rPWM);
}
void BACKWARD(){
  letBackward(left);
  letBackward(right);
  analogWrite(lSpeedPort,lPWM);
  analogWrite(rSpeedPort,rPWM);
}
void TURNLEFT(){
  letHalt(left);
  letForward(right);
  analogWrite(lSpeedPort,lPWM);
  analogWrite(rSpeedPort,rPWM);
}
void TURNRIGHT(){
  letHalt(right);
  letForward(left);
  analogWrite(lSpeedPort,lPWM);
  analogWrite(rSpeedPort,rPWM);
}
void SHOOT(){
  digitalWrite(shootPort,HIGH);
  delay(600);//WITHOUT PID;
  digitalWrite(shootPort,LOW);
  delay(40);
  mode = 0;
}
