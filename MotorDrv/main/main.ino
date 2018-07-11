//#include <PID_v1.h>
#include <Servo.h>
#include <assert.h>
#define FRAME_DURATION 50
int SpeedToPWM[256];
double lPulse,rPulse;
double lPWM=50,rPWM=50;

//const int TargetSpeed = 70;//FIXME
double Kp=0.4, Ki=5.5, Kd=0;
const int fullcycle = 15700;

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

// bool handmode = false;//默认是专业人员的耐心模式（automode）

const bool left = true;
const bool right = false;
int mode=0;
int argument=100;//input speed (if have any)

//signed int beginRotatePulse = 0;//- means left , + means right
signed int pulseLeftToDo = 0;
//bool directionLeftToDo = left;

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



void accumulateLPulse(){lPulse++;}
void accumulateRPulse(){rPulse++;}




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
    attachInterrupt(digitalPinToInterrupt(lReturnPort) , accumulateLPulse, CHANGE);
    attachInterrupt(digitalPinToInterrupt(rReturnPort) , accumulateRPulse, CHANGE);
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
    currentMillis = millis ();
    if(Serial.available()>0)
    {
        parseArguments();//TODO
                if( currentMillis - previousMillis >= FRAME_DURATION )
        {
            previousMillis = currentMillis ;
            // PID_L.Compute();PID_R.Compute();
            if (true)
            {
                switch(mode)
                {
                case 0:
                    STOP();
                    break;
                case 1:
                    FORWARD();
                    break;
                case 2:
                    BACKWARD();;
                    break;
                case 3:
                    TURNLEFT();
                    delay(FRAME_DURATION-5);
                    break;
                case 4:
                    TURNRIGHT();
                    delay(FRAME_DURATION-5);
                    break;
                case 5:
                    SHOOT();
                    break;
                // case 6:
                //     handmode = true;//用户
                //     break;
                // case 7:
                //     handmode = false;//专业人员 maintain mode
                //     break;
                default :
                    STOP();
                    break;
                }
                // 0->STOP  1->FORWARD  2->BACK   3->LEFT   4->RIGHT   5->TURNLEFT  6->TURNRIGHT
                lPulse = 0;
                rPulse = 0;
            Serial.println("FIN");

    }
        }
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
  letHalt(left);.
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
