#include <DHT11.h>

DHT11 dht(A1);

const int sensorIn = A0;
const int relay = 3;
int mVperAmp = 450; // use 100 for 20A Module and 66 for 30A Module
double Voltage = 0;
double VRMS = 0;
double AmpsRMS = 0;

void setup(){ 
    Serial.begin(115200);
    pinMode(relay, OUTPUT);
    digitalWrite(relay, HIGH);
}

void loop(){
    if(Serial.available()) {
        String data = Serial.readStringUntil('\n');
        data.trim();

        if(data == "off") {
            digitalWrite(relay, HIGH);
        }
        else if(data == "on") {
            digitalWrite(relay, LOW);
        }
    }

    float t, h;
    t = dht.readTemperature();
    h = dht.readHumidity();

    Voltage = getVPP();
    VRMS = (Voltage/2.0) *0.707; 
    AmpsRMS = ((VRMS * 1000)/mVperAmp) - 0.03;

    if (AmpsRMS < 0) {
        AmpsRMS = -AmpsRMS;
    }

    Serial.print(AmpsRMS, 3);
    Serial.print(" Amps RMS / ");
    Serial.print(AmpsRMS*220);
    Serial.print("W / ");
    Serial.print("T: ");
    Serial.print(t);
    Serial.print(" H: ");
    Serial.println(h);
}

float getVPP()
{
  float result;
  
  int readValue;             //value read from the sensor
  int maxValue = 0;          // store max value here

    int minValue = 1024;          // store min value here
  
   uint32_t start_time = millis();
   while((millis()-start_time) < 100) //sample for 1 Sec
   {
       readValue = analogRead(sensorIn); 
       // see if you have a new maxValue
       if (readValue > maxValue) 
       {
           /*record the maximum sensor value*/
           maxValue = readValue;
       }
       if (readValue < minValue) 
       {
           /*record the maximum sensor value*/
           minValue = readValue;
       }
   }
   
   // Subtract min from max
   result = ((maxValue - minValue) * 5.0)/1024.0;
      
   return result;
 }