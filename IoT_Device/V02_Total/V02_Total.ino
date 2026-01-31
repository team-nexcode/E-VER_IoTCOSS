#include <WiFiS3.h>
#include <WiFiSSLClient.h>
#include <DHT11.h>

DHT11 dht(A1);

byte mac[6];

char ssid[] = "CSE-3173_2.4G";
char pass[] = "[WIFI_PASSWORD]";

// 1. 서버 주소
char server[] = "onem2m.iotcoss.ac.kr"; 
int port = 443;

// 2. oneM2M 리소스 설정
String cse = "Mobius";
String ae = "ae_nexcode";
String cnt_name = "monitor"; 

// 3. 인증 헤더
String apiKey = "[MOBIUS_API_KEY]";
String lectureId = "[LECTURE_ID]";
String creatorId = "dgunexcode";
String origin = "SOrigin_nexcode";

WiFiSSLClient client;

const int sensorIn = A0;
const int relay = 3;
int mVperAmp = 450; 
double Voltage = 0;
double VRMS = 0;
double AmpsRMS = 0;

// [추가] 릴레이 상태를 저장할 변수 (초기값: setup에서 LOW로 켜므로 "on")
String relayStatus = "on"; 

// 마지막 전송 시간을 저장할 변수 (비차단 지연)
unsigned long lastSendTime = 0;
const long interval = 2000; 

void setup(){ 
    Serial.begin(115200);
    pinMode(relay, OUTPUT);
    
    // 초기 상태 설정 (Active Low 기준: LOW가 켜짐)
    digitalWrite(relay, LOW); 
    relayStatus = "on"; // 변수도 상태 맞춤

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
    // 시리얼 제어 로직
    if(Serial.available()) {
        String data = Serial.readStringUntil('\n');
        data.trim();
        
        // [수정] 릴레이 동작 시 상태 변수도 함께 업데이트
        if(data == "off") {
            digitalWrite(relay, HIGH);
            relayStatus = "off";
        }
        else if(data == "on") {
            digitalWrite(relay, LOW);
            relayStatus = "on";
        }
    }

    // 센서 데이터 읽기
    float t = dht.readTemperature();
    float h = dht.readHumidity();

    Voltage = getVPP();
    VRMS = (Voltage/2.0) * 0.707; 
    AmpsRMS = ((VRMS * 1000)/mVperAmp) - 0.03;
    if (AmpsRMS < 0) AmpsRMS = -AmpsRMS;

    // 시리얼 모니터 출력 [수정: 상태 표시 추가]
    Serial.print(AmpsRMS, 3);
    Serial.print(" A / ");
    Serial.print(AmpsRMS*220);
    Serial.print(" W / T ");
    Serial.print(t);
    Serial.print(" / H: ");
    Serial.print(h);
    Serial.print(" / Status: "); // 상태 출력 추가
    Serial.println(relayStatus);

    // [최적화] 일정 간격으로 데이터 통합 전송
    if (millis() - lastSendTime >= interval) {
        lastSendTime = millis();
        
        // JSON 형태 생성: {"temp":24.0, "humi":60.0, "energy":0.123, "status":"on"}
        // 문자열 값("on"/"off")을 넣으려면 이스케이프(\")가 앞뒤로 더 필요합니다.
        String dataPayload = "{\\\"temp\\\":" + String(t, 2) + 
                             ", \\\"humi\\\":" + String(h, 2) + 
                             ", \\\"energy\\\":" + String(AmpsRMS, 3) + 
                             ", \\\"status\\\":\\\"" + relayStatus + "\\\"}";

        sendData(dataPayload, cnt_name);
    }
}

float getVPP()
{
    float result;
    int readValue;             
    int maxValue = 0;          
    int minValue = 1024;          
    uint32_t start_time = millis();
    
    while((millis()-start_time) < 500) 
    {
        readValue = analogRead(sensorIn); 
        if (readValue > maxValue) maxValue = readValue;
        if (readValue < minValue) minValue = readValue;
    }
    result = ((maxValue - minValue) * 5.0)/1024.0;
    return result;
}

void sendData(String value, String cnt) {
    
    if (!client.connected()) {
        Serial.println("Connection lost. Reconnecting...");
        client.stop(); 
        if (client.connect(server, port)) {
            Serial.println("Reconnected!");
        } else {
            Serial.println("Connection Failed!");
            return; 
        }
    }

    String myMac = getMacAddress();
    String body = "{\"m2m:cin\": {\"con\": \"" + value + "\", \"lbl\": [\"smart_plug\", \"" + myMac + "\"]}}"; 

    client.println("POST /" + cse + "/" + ae + "/" + cnt + " HTTP/1.1"); 
    client.println("Host: " + String(server));
    
    client.println("Connection: keep-alive"); 
    client.println("Keep-Alive: timeout=15, max=100");
    
    client.println("Content-Type: application/json;ty=4");
    client.println("Accept: application/json");
    client.println("X-M2M-RI: 12345");
    client.println("X-M2M-Origin: " + origin);
    client.println("X-API-KEY: " + apiKey);
    client.println("X-AUTH-CUSTOM-LECTURE: " + lectureId);
    client.println("X-AUTH-CUSTOM-CREATOR: " + creatorId);
    
    client.print("Content-Length: ");
    client.println(body.length());
    client.println(); 
    client.println(body);

    unsigned long timeout = millis();
    while (client.available() == 0) {
        if (millis() - timeout > 1000) { 
            Serial.println(">>> Client Timeout !");
            client.stop(); 
            return;
        }
    }

    while(client.available()){
        char c = client.read();
    }
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