#include <PID_v1.h>
#include <Servo.h>
#include <assert.h>
#include <string.h>
#define FRAME_DURATION 50
#define COLOR_THRESHOLD 500
#define DANGER_THRESHOLD 15
int SpeedToPWM[256];
double lPulse,rPulse;
double lPWM=73,rPWM=70;
int totMode=0 ;// 0 - no detection 1 - fore detection 2 - both detection
double TargetSpeed = 70;//FIXME
double Kp=0.4, Ki=0.2, Kd=0.06;
double befmode = 0;
//double  Kp=0, Ki=0,Kd=0;
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
const int lUltraSoundTrigPort = 29;
const int rUltraSoundTrigPort = 31;
const int lUltraSoundEchoPort = 28;
const int rUltraSoundEchoPort = 30;
unsigned long currentMillis,previousMillis;

bool handmode = true;//默认是专业人员的耐心模式（automode）

const bool left = true;
const bool right = false;
int mode=0;
int argument=100;//input speed (if have any)
int lDanger = 0;
int rDanger = 0;
//signed int beginRotatePulse = 0;//- means left , + means right
signed int pulseLeftToDo = 0;
//bool directionLeftToDo = left;

PID PID_L(&lPulse, &lPWM, &TargetSpeed, Kp, Ki, Kd, DIRECT);
PID PID_R(&rPulse, &rPWM, &TargetSpeed, Kp, Ki, Kd, DIRECT);

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
    pinMode(lUltraSoundTrigPort,OUTPUT);
    pinMode(rUltraSoundTrigPort,OUTPUT);
    pinMode(lUltraSoundEchoPort,INPUT);
    pinMode(rUltraSoundEchoPort,INPUT);
    attachInterrupt(digitalPinToInterrupt(lReturnPort) , accumulateLPulse, CHANGE);
    attachInterrupt(digitalPinToInterrupt(rReturnPort) , accumulateRPulse, CHANGE);
 //   PID_L.SetMode(AUTOMATIC);
//    PID_L.SetSampleTime(50);
 //   PID_R.SetMode(AUTOMATIC);
//    PID_R.SetSampleTime(50);
  }

// void parseArguments(){
//   string str;
//   if (Serial.available()>0){
//     str = Serial.readString();
//     if (str[0]=='6') befmode = mode;
//     mode = (char)str-'0'
//     argument = ((char)str[1]-'0')*10+((char)str[2]-'0');
//   }
//   else{
//     mode = -1;
//   }
// }

void parseArguments(){
   char s1,s2,s3;
   if (Serial.available()>0){
     delay(10);//wait for finish
     s1 = Serial.read();
     s2 = Serial.read();
     s3 = Serial.read();
     if (s1=='6') befmode = mode;
     mode = s1 - '0';
     argument = ((char)s2-'0')*10+((char)s3-'0');
     Serial.println("Rcvd:");
     Serial.println(argument);
   }
}

// void parseOneArguments(){
//   char str;
//   if (Serial.available()>0){
//     Serial.readBytes(str,sizeof(str))
//     if (str=='6') befmode = mode;
//     mode = (char)str-'0'
// //    argument = ((char)str[1]-'0')*10+((char)str[2]-'0');
//   }
//   else{
//     mode = -1;
//   }
// }

void updateDetectors(){
  //1.color detectors
  int raw1,raw2;
  raw1 = analogRead(0);
  raw2 = analogRead(1);
  if ((raw1>COLOR_THRESHOLD)&&(raw2>COLOR_THRESHOLD)){
    totMode = 0;
  }
  else if ((raw1<COLOR_THRESHOLD)&&(raw2>COLOR_THRESHOLD)){
    totMode = 1;
  }
  else if ((raw1<COLOR_THRESHOLD)&&(raw2<COLOR_THRESHOLD)){
    totMode=2;
  }
  else{
    totMode = 3;
  }
  //2.ultra detectors
  static float d1,d2;
  digitalWrite(lUltraSoundTrigPort,LOW);
  delayMicroseconds(2);
  digitalWrite(lUltraSoundTrigPort,HIGH);
  delayMicroseconds(10);
  digitalWrite(lUltraSoundTrigPort,LOW);
  d1=pulseIn(lUltraSoundEchoPort,HIGH)/58.00;     //检测脉冲宽度，并计算出距离
   digitalWrite(rUltraSoundTrigPort,LOW);
  delayMicroseconds(2);
  digitalWrite(rUltraSoundTrigPort,HIGH);
  delayMicroseconds(10);
  digitalWrite(rUltraSoundTrigPort,LOW);
  d2=pulseIn(rUltraSoundEchoPort,HIGH)/58.00;     //检测脉冲宽度，并计算出距离
  Serial.println(d1);
  Serial.println(d2);
  Serial.println(raw1);
  Serial.println(raw2);
  lDanger = (d1>DANGER_THRESHOLD)?0:1;
  rDanger = (d2>DANGER_THRESHOLD)?0:1;
}


void loop()
{
    int b1,b2,p;
    int bef,aft,realPulse;
    currentMillis = millis ();
    if(Serial.available()>0)
    {
        parseArguments();
    }
        if( currentMillis - previousMillis >= FRAME_DURATION )
        {
            previousMillis = currentMillis ;
 //           PID_L.Compute();PID_R.Compute();
            // Serial.print("lPWM=");Serial.print(lPulse);Serial.print(",rPWM=");Serial.println(rPulse);
              if (handmode)//normal mode
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
                case 6:
                    updateDetectors();
                    Serial.print(lDanger);
                    Serial.print(rDanger);
                    Serial.println(totMode);
                    mode = befmode;
                    break;
                 case 7:
                     handmode = false;//专业人员 maintain mode
                     break;
                 case 8:
                     handmode = true;
                     break;
                default :
                    STOP();
                    break;
                }
                // 0->STOP  1->FORWARD  2->BACK   3->LEFT   4->RIGHT   5->TURNLEFT  6->TURNRIGHT
                lPulse = 0;
                rPulse = 0;
            // Serial.print()

          }else{//auto good mode
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
                  realPulse = fullcycle*(argument/360.0);
//                  Serial.println("now turning left...");

                  bef  = aft = rPulse;
                  aft = bef + realPulse;
//                  Serial.print(bef);Serial.print(" "); Serial.println(aft);
                  TURNLEFT();
                  while (rPulse<=aft){
//                    Serial.println(rPulse);
                    delay(10);
                  }
                  STOP();
                  break;
              case 4:
              realPulse = fullcycle*(argument/360.0);
              bef  = aft = lPulse;
              aft = bef + realPulse;
              TURNRIGHT();
              while (lPulse<=aft){
//                realPulse++;realPulse--;
              delay(10);
              }
              STOP();
                  break;
              case 5:
                  SHOOT();
                  break;
              case 6:
                  updateDetectors();
                  Serial.print(lDanger);
                  Serial.print(rDanger);
                  Serial.println(totMode);
                  mode = befmode;
                  break;
               case 7:
                   handmode = false;//专业人员 maintain mode
                   break;
              case 8:
                  handmode = true;
                  break;
              default :
                  STOP();
                  break;
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
