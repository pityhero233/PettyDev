#include <PID_v1.h>
#include <Servo.h>
#include <assert.h>
#include <string.h>
#define FRAME_DURATION 50
#define COLOR_THRESHOLD 500
#define DANGER_THRESHOLD 15
int SpeedToPWM[256];
double lPulse, rPulse;
double lPWM = 73, rPWM = 70;
int totMode = 0 ; // 0 - no detection 1 - fore detection 2 - both detection
double TargetSpeed = 70;//FIXME
double Kp = 0.4, Ki = 0.2, Kd = 0.06;
double befmode = 0;
int val11;
//double  Kp=0, Ki=0,Kd=0;
const int fullcycle = 13700;

const int shootPort = 48;//volatile
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
int homeDirection = 0.0;
//const int directionPort = 32;
//const int controlPort = 33;
const int redPort = 27;
unsigned long currentMillis, previousMillis;

bool needToTurn = false;
bool handmode = true;//默认是专业人员的耐心模式（automode）
bool synced = false;
const bool left = true;
const bool right = false;
int mode = 0;
int argument = 100; //input speed (if have any)
int lDanger = 0;
int rDanger = 0;
int foreDetector, backDetector;
bool rights;
Servo leftServo,rightServo;
int lPWMPinPort=8,rPWMPinPort=9;
//signed int beginRotatePulse = 0;//- means left , + means right
signed int pulseLeftToDo = 0;
//bool directionLeftToDo = left;

PID PID_L(&lPulse, &lPWM, &TargetSpeed, Kp, Ki, Kd, DIRECT);
PID PID_R(&rPulse, &rPWM, &TargetSpeed, Kp, Ki, Kd, DIRECT);

void letForward(bool isLeftPort) {
  if (isLeftPort) {
    leftServo.write(88);

  }
  else {
    rightServo.write(100);
  }
}

void letBackward(bool isLeftPort) {
  if (isLeftPort) {
    leftServo.write(100);
  }
  else {
    rightServo.write(88);
  }
}

void letHalt(bool isLeftPort) {
  if (isLeftPort) {
    leftServo.write(94);
  }
  else {
    rightServo.write(94);
  }
}

void changeSpeed(bool isLeftPort, int speed) {
  assert((speed > 0) && (speed < 255));
  if (isLeftPort) analogWrite(lSpeedPort, speed);
  else analogWrite(rSpeedPort, speed);
}



void accumulateLPulse() {
  lPulse++;
}
void accumulateRPulse() {
  rPulse++;
}




void setup()
{
  leftServo.attach(lPWMPinPort);
  rightServo.attach(rPWMPinPort);

  Serial.begin(9600);
  Serial.setTimeout(100);
  Serial3.begin(19200);//the mv
  while (Serial.read() >= 0) {} //clear serial port
  pinMode(shootPort, OUTPUT); //init()
  pinMode(lControlPortA, OUTPUT);
  pinMode(lControlPortB, OUTPUT);
  pinMode(rControlPortA, OUTPUT);
  pinMode(rControlPortB, OUTPUT);
  pinMode(lSpeedPort, OUTPUT);
  pinMode(rSpeedPort, OUTPUT);
  pinMode(lReturnPort, INPUT);
  pinMode(rReturnPort, INPUT);
  pinMode(lUltraSoundTrigPort, OUTPUT);
  pinMode(rUltraSoundTrigPort, OUTPUT);
  pinMode(lUltraSoundEchoPort, INPUT);
  pinMode(rUltraSoundEchoPort, INPUT);
  pinMode(redPort, OUTPUT);
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

void parseArguments() {
  char s1, s2, s3;
  if (Serial.available() > 0) {
    delay(10);//wait for finish
    s1 = Serial.read();
    s2 = Serial.read();
    s3 = Serial.read();
    if (s1 == '6') befmode = mode;
    mode = s1 - '0';
    argument = ((char)s2 - '0') * 10 + ((char)s3 - '0');
    //     Serial.println("Rcvd:");
    //     Serial.println(argument);
  }




}


void updateDetectors() {
  //1.color detectors
  int raw1, raw2;
  raw1 = analogRead(0);
  raw2 = analogRead(1);
      Serial.println("raw1="); //volatile
    Serial.println(raw1);
    Serial.println("raw2="); //volatile
    Serial.println(raw2);
  if ((raw1 > COLOR_THRESHOLD) && (raw2 > COLOR_THRESHOLD+20)) {
    totMode = 0;
  }
  else if ((raw1 < COLOR_THRESHOLD) && (raw2 > COLOR_THRESHOLD+20)) {
    totMode = 1;
  }
  else if ((raw1 < COLOR_THRESHOLD) && (raw2 < COLOR_THRESHOLD+20)) {
    totMode = 2;
  }
  else {
    totMode = 3;
  }
}

float mapVoltage(float x) {
  return 117.785 - 0.14375 * x;
}

int mapPercent(float voltage) { //10.2 0   12.5 100   11.1 70
  return (int)(-24.4997 * voltage * voltage + 599.62 * voltage - 3567.18);
}

void loop()
{
  int b1, b2, p;
  int bef, aft, realPulse;
  char s1, s2, s3;
  if (Serial3.available() > 0) {
    delay(10);//wait for finish
    s1 = Serial3.read();
    s2 = Serial3.read();
    s3 = Serial3.read();
    homeDirection = (s1 - '0') * 100 + (s2 - '0') * 10 + (s3 - '0');
//    Serial.print("homeDirection="); Serial.println(homeDirection);
  }

  currentMillis = millis ();
  lPWM = 73; rPWM = 70;
  if (Serial.available() > 0)
  {
    parseArguments();
  }
  if ( currentMillis - previousMillis >= FRAME_DURATION )
  {
    previousMillis = currentMillis ;
    if (handmode)//normal mode == true
    {
      if (mode != 6) {
        synced = false;
      }
      switch (mode)
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
          delay(FRAME_DURATION - 5);
          break;
        case 4:
          TURNRIGHT();
          delay(FRAME_DURATION - 5);
          break;
        case 5:
          digitalWrite(redPort, HIGH);
          delay(500);
          digitalWrite(redPort, LOW);
          delay(500);
          digitalWrite(redPort, HIGH);
          delay(500);
          digitalWrite(redPort, LOW);
          delay(500);
          digitalWrite(redPort, HIGH);
          SHOOT();
          digitalWrite(redPort, LOW);
          break;
        case 6:
          if (homeDirection < 10 || homeDirection > 355) {
            needToTurn = false;
          }
          else {
            needToTurn = true;
          }
          if (homeDirection < 180) {
            rights = true;
          }
          else {
            rights = false;
          }
          // Serial.print(needToTurn);
          lPWM = 77; rPWM = 74;
          if (needToTurn && !synced) {
            if (rights) {
              TURNRIGHT();
              delay(10);
            }
            else {
              TURNLEFT();
              delay(10);
            }
          } else {

//                                      Serial.print("totmode=");
//                                      Serial.println(totMode);
            updateDetectors();

            if (totMode == 0 && (!synced)) {
              synced = true;
              FORWARD();
            }
            if (totMode == 1 && (synced)) {
              TURNLEFT(); //Serial.println("ohsihit");
            }
            if (totMode == 2) {
               
              FORWARD();
              delay(1500);
//              TURNRIGHT();
//              delay(100);
              FORWARD();
              delay(2000);
   

              STOP();
              mode = 0;
              delay(10);
              Serial.print("E");
            }
          }
          break;
        case 7:
            Serial.println(76);
          // val11 = (int)(analogRead(1)/4.092);
//          Serial.println(analogRead(A1)); //hacked.
//          Serial.println(mapVoltage(analogRead(A1)));
//          Serial.println(mapPercent(mapVoltage(analogRead(A1))));
        case 8://show
            BACKWARD();
            delay(1500);
            TURNRIGHT();
            delay(500);
            FORWARD();
            delay(500);
            TURNRIGHT();
            delay(500);
            FORWARD();
            delay(500);
            TURNRIGHT();
            delay(500);
            FORWARD();
            delay(500);
            TURNRIGHT();
            delay(500);
            FORWARD();
            delay(500);
            TURNRIGHT();
            delay(500);
            FORWARD();
            delay(500);
            STOP();
        default :
          STOP();
          break;
      }
      lPulse = 0;
      rPulse = 0;
    }
  }
}

void STOP() {
  letHalt(left);
  letHalt(right);
  mode = 0;
}
void FORWARD() {
  letForward(left);
  letForward(right);
  analogWrite(lSpeedPort, lPWM);
  analogWrite(rSpeedPort, rPWM);
}
void BACKWARD() {
  letBackward(left);
  letBackward(right);
  analogWrite(lSpeedPort, lPWM);
  analogWrite(rSpeedPort, rPWM);
}
void TURNLEFT() {
  letBackward(left);
  letForward(right);
  analogWrite(lSpeedPort, lPWM);
  analogWrite(rSpeedPort, rPWM);
}
void TURNRIGHT() {
  letBackward(right);
  letForward(left);
  analogWrite(lSpeedPort, lPWM);
  analogWrite(rSpeedPort, rPWM);
}
void SHOOT() {
  digitalWrite(shootPort, HIGH);
  delay(600);//WITHOUT PID;
  digitalWrite(shootPort, LOW);
  delay(40);
  mode = 0;
}

