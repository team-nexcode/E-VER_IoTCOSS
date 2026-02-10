#include <Arduino_JSON.h>
#include <WiFiS3.h>
#include <WiFiSSLClient.h>
#include <DHT11.h>

DHT11 dht(A1);

byte mac[6];

char ssid[] = "[WIFI_SSID]";
char pass[] = "[WIFI_PASSWORD]";

char server[] = "onem2m.iotcoss.ac.kr"; 
int port = 443;

// oneM2M 리소스 설정
String cse = "Mobius";
String ae = "ae_nexcode";
String cnt_name = "monitor"; 

// 인증 헤더
String apiKey = "[MOBIUS_API_KEY]";
String lectureId = "[LECTURE_ID]";
String creatorId = "[CREATOR_ID]";
String origin = "SOrigin_nexcode";

WiFiSSLClient client;

const int sensorIn = A0;
const int relay = 3;
int mVperAmp = 450; 
double Voltage = 0;
double VRMS = 0;
double AmpsRMS = 0;

String relayStatus = "on"; 

unsigned long lastSendTime = 0;
const long interval = 2000; 

void setup(){ 
    Serial.begin(115200);
    pinMode(relay, OUTPUT);
    
    digitalWrite(relay, LOW); 
    relayStatus = "on";

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
    // 1. 시리얼 제어 (비차단성 유지)
    if(Serial.available()) {
        String data = Serial.readStringUntil('\n');
        data.trim();
        
        if(data == "off") {
            digitalWrite(relay, HIGH);
            relayStatus = "off";
        }
        else if(data == "on") {
            digitalWrite(relay, LOW);
            relayStatus = "on";
        }
    }

    // 2. 센서 읽기 및 데이터 전송
    // 중요: getVPP()가 딜레이를 유발하므로, 전송 타이밍에만 실행합니다.
    if (millis() - lastSendTime >= interval) {
        lastSendTime = millis();
        
        // --- 센서 데이터 읽기 시작 ---
        float t = dht.readTemperature();
        float h = dht.readHumidity();

        // 전류 측정 (여기서 0.5초 소요됨)
        Voltage = getVPP();
        VRMS = (Voltage/2.0) * 0.707; 
        AmpsRMS = ((VRMS * 1000)/mVperAmp) - 0.03;
        if (AmpsRMS < 0) AmpsRMS = 0; // 0 이하 보정

        // 시리얼 모니터 출력
        Serial.print(AmpsRMS, 3);
        Serial.print(" A / ");
        Serial.print(AmpsRMS*220);
        Serial.print(" W / T ");
        Serial.print(t);
        Serial.print(" / H: ");
        Serial.print(h);
        Serial.print(" / Status: ");
        Serial.println(relayStatus);

        // --- 데이터 전송 ---
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
    
    // 500ms 동안 샘플링 (블로킹 구간)
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
    
    // 연결 상태 확인 및 재연결 로직 강화
    if (!client.connected()) {
        Serial.println("Connecting to server...");
        // 중요: 연결 시도 전 기존 소켓 정리
        client.stop(); 
        
        if (client.connect(server, port)) {
            Serial.println("Connected!");
        } else {
            Serial.println("Connection Failed!");
            return; 
        }
    }

    String myMac = getMacAddress();
    String body = "{\"m2m:cin\": {\"con\": \"" + value + "\", \"lbl\": [\"smart_plug\", \"" + myMac + "\"]}}"; 

    client.println("POST /" + cse + "/" + ae + "/" + cnt + " HTTP/1.1"); 
    client.println("Host: " + String(server));
    
    // 수정: 안정성을 위해 close 사용 (매번 끊고 다시 연결)
    client.println("Connection: close"); 
    
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

    // 응답 대기 (타임아웃 2초로 증가)
    unsigned long timeout = millis();
    while (client.available() == 0) {
        if (millis() - timeout > 2000) { 
            Serial.println(">>> Client Timeout !");
            client.stop(); 
            return;
        }
    }

    // 응답 비우기
    while(client.available()){
        char c = client.read();
        // Serial.write(c); // 디버깅 필요시에만 주석 해제
    }
    
    // 트랜잭션 종료 후 소켓 닫기 (Connection: close 사용 시 필수)
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