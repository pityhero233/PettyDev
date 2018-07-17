int x,y,z;
void setup()

{
  Serial.begin(115200);

} 
int mapper(int x,int y,int z){
  if (x>=255||y>=255||z>=255){
    return 100.0;
  }
  else{
    return (x+y+z);
  }
}


void loop()

{
    x=abs(analogRead(A0)-414);
    y=abs(analogRead(A1)-321);
    z=abs(analogRead(A2)-327);
    Serial.print(mapper(x,y,z));
   //Serial.write((int)mapper(x,y,z));
   delay(500);
}
