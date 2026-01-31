#include <WiFiS3.h>
#include <WiFiSSLClient.h>
#include <DHT11.h>

DHT11 dht(A1);

byte mac[6];

char ssid[] = "CSE-3173_2.4G";
char pass[] = "CSE3173@";

// 1. 서버 주소
char server[] = "onem2m.iotcoss.ac.kr"; 
int port = 443;

// 2. oneM2M 리소스 이름
String cse = "Mobius";
String ae = "ae_nexcode";

// 3. 인증 헤더
String apiKey = "gscrrHKE0ugczEJaG2wJy1wUJodNu3Ft";
String lectureId = "LCT_20250007";
String creatorId = "dgunexcode";
String origin = "SOrigin_nexcode";

WiFiSSLClient client;

const int sensorIn = A0;
const int relay = 3;
int mVperAmp = 450; // use 100 for 20A Module and 66 for 30A Module
double Voltage = 0;
double VRMS = 0;
double AmpsRMS = 0;

void setup(){ 
    Serial.begin(115200);
    pinMode(relay, OUTPUT);
    digitalWrite(relay, LOW);

    if(WiFi.status() == WL_NO_MODULE) {
        Serial.println("WiFi Module Fail");
        while(true);
    }

    WiFi.macAddress(mac);

    Serial.print("Connecting to WiFi");
    while (WiFi.status() != WL_CONNECTED) {
        WiFi.begin(ssid, pass);
        Serial.print(".");
        delay(5000);
    }
    Serial.println("\nConnected!");
    printWifiStatus();
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

    sendData(String(t), "temp");
    sendData(String(h), "humi");
    sendData(String(AmpsRMS), "energy");
}

float getVPP()
{
    float result;

    int readValue;             //value read from the sensor
    int maxValue = 0;          // store max value here

    int minValue = 1024;          // store min value here

    uint32_t start_time = millis();
    while((millis()-start_time) < 500) //sample for 1 Sec
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

void sendData(String value, String cnt) {
    Serial.println("Connecting to Server (HTTPS)...");
    
    // HTTPS(443) 연결 시도
    if(client.connect(server, port)) {
        Serial.println("Connected!");

        // oneM2M ContentInstance 생성 Body
        String myMac = getMacAddress();
        String body = "{\"m2m:cin\": {\"con\": \"" + value + "\", \"lbl\": [\"smart_plug\", \"" + myMac + "\"]}}"; 

        // HTTP POST 요청 헤더 작성
        // URL 구조: https://onem2m.iotcoss.ac.kr/Mobius/{AE}/{CNT}
        client.println("POST /" + cse + "/" + ae + "/" + cnt + " HTTP/1.1"); 
        client.println("Host: " + String(server));
        
        // [Postman 파일에서 확인한 필수 헤더들]
        client.println("Content-Type: application/json;ty=4");
        client.println("Accept: application/json");
        client.println("X-M2M-RI: 12345");
        client.println("X-M2M-Origin: " + origin);
        
        // IoT COSS 전용 인증 헤더 (이게 없으면 401 에러)
        client.println("X-API-KEY: " + apiKey);
        client.println("X-AUTH-CUSTOM-LECTURE: " + lectureId);
        client.println("X-AUTH-CUSTOM-CREATOR: " + creatorId);
        
        client.println("Connection: close");
        client.print("Content-Length: ");
        client.println(body.length());
        client.println(); // 빈 줄 (헤더 끝)
        client.println(body); // 본문 전송

        Serial.println("Data Sent: " + body);
    } else {
        Serial.println("Server Connection Failed! (Check WiFi or SSL)");
    }
    client.stop();
}

void printWifiStatus() {
    Serial.print("SSID: ");
    Serial.println(WiFi.SSID());
    IPAddress ip = WiFi.localIP();
    Serial.print("IP Address: ");
    Serial.println(ip);
}

String getMacAddress() {
    byte mac[6];
    WiFi.macAddress(mac);
    String s = "";
    for (int i = 0; i < 6; i++) {
        if (mac[i] < 16) s += "0";
        s += String(mac[i], HEX);
        if (i < 5) s += ":";
    }
    s.toUpperCase();
    return s;
}