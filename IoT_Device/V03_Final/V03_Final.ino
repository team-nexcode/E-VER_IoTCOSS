#include <Arduino_JSON.h>
#include <WiFiS3.h>
#include <WiFiSSLClient.h>
#include <DHT11.h>

// ----------------------------------------------------------------
// [설정] 네트워크 및 oneM2M
// ----------------------------------------------------------------
const char ssid[] = "CSE-3173_2.4G";
const char pass[] = "CSE3173@";

const char server[] = "onem2m.iotcoss.ac.kr";
const int port = 443;

const String cse = "Mobius";
const String ae = "ae_nexcode";
const String cnt_monitor = "monitor";
const String cnt_cmd = "switch";

const String apiKey = "gscrrHKE0ugczEJaG2wJy1wUJodNu3Ft";
const String lectureId = "LCT_20250007";
const String creatorId = "dgunexcode";
const String origin = "SOrigin_nexcode";

// ----------------------------------------------------------------
// [하드웨어]
// ----------------------------------------------------------------
DHT11 dht(A1);
const int sensorIn = A0;
const int relay = 3;

WiFiSSLClient client;

String myMacAddress = "";
String relayStatus = "on"; 
int mVperAmp = 450; 

// [최적화 1] 타이머 변수
unsigned long lastSendTime = 0;
unsigned long lastCheckTime = 0;
const long uploadInterval = 1000;  // 1초마다 센서 전송
const long commandInterval = 500;  // 0.5초마다 명령 확인

// [최적화 2] 연결 재사용 카운터
int connectionReuseCount = 0;
const int maxReuse = 10; 

// ----------------------------------------------------------------
// [SETUP]
// ----------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    // while(!Serial);

    pinMode(relay, OUTPUT);
    digitalWrite(relay, LOW); 
    relayStatus = "on";

    if (WiFi.status() == WL_NO_MODULE) while (true);

    if (WiFi.firmwareVersion() < "0.3.0") {
        Serial.println(F("[Warn] Firmware Update Recommended!"));
    }

    connectWiFi();
    myMacAddress = getMacAddressStr();
    Serial.println("\n[System] Ready. MAC: " + myMacAddress);
}

// ----------------------------------------------------------------
// [LOOP]
// ----------------------------------------------------------------
void loop() {
    unsigned long currentMillis = millis();

    // 1. WiFi 끊기면 복구
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    // 2. 시리얼 제어
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        controlRelay(input);
    }

    // 3. 서버 명령 확인 (GET)
    if (currentMillis - lastCheckTime >= commandInterval) {
        lastCheckTime = currentMillis;
        getCommandFromServer();
    }

    // 4. 센서 데이터 업로드 (POST)
    if (currentMillis - lastSendTime >= uploadInterval) {
        lastSendTime = currentMillis;
        processAndUploadSensorData();
    }
}

// ----------------------------------------------------------------
// [통신 핵심] 요청 전송 (Keep-Alive)
// ----------------------------------------------------------------
void sendRequest(String method, String url, String body) {
    if (!client.connected()) {
        if (!client.connect(server, port)) {
            Serial.println(F("[Err] Conn Fail"));
            return;
        }
        connectionReuseCount = 0;
    }

    // [수정된 부분] F() 매크로는 순수 문자열에만 사용해야 함
    // 변수와 + 연산자가 섞인 곳에서는 F()를 제거했습니다.
    client.print(method + " " + url + " HTTP/1.1\r\n");
    client.print("Host: " + String(server) + "\r\n");
    
    if (connectionReuseCount > maxReuse) {
        client.print(F("Connection: close\r\n"));
    } else {
        client.print(F("Connection: keep-alive\r\n"));
    }
    
    client.print(F("Accept: application/json\r\n"));
    client.print(F("X-M2M-RI: 12345\r\n"));
    
    // [수정] 아래 줄들은 변수(apiKey 등)가 포함되어 있어 F()를 빼야 합니다.
    client.print("X-M2M-Origin: " + origin + "\r\n");
    client.print("X-API-KEY: " + apiKey + "\r\n");
    client.print("X-AUTH-CUSTOM-LECTURE: " + lectureId + "\r\n");
    client.print("X-AUTH-CUSTOM-CREATOR: " + creatorId + "\r\n");

    if (method == "POST") {
        client.print(F("Content-Type: application/json;ty=4\r\n"));
        client.print("Content-Length: " + String(body.length()) + "\r\n");
        client.print("\r\n");
        client.print(body);
    } else {
        client.print("\r\n");
    }

    unsigned long timeout = millis();
    while (client.available() == 0) {
        if (millis() - timeout > 1000) {
            Serial.println(F(">>> Timeout!"));
            client.stop();
            return;
        }
    }
    
    processResponse(method);

    connectionReuseCount++;
    if (connectionReuseCount > maxReuse) {
        client.stop();
        connectionReuseCount = 0;
    }
}

// ----------------------------------------------------------------
// [응답 처리] 파싱 및 로그 출력
// ----------------------------------------------------------------
void processResponse(String method) {
    bool headerEnded = false;
    String responseBody = "";
    
    while(client.available()) {
        String line = client.readStringUntil('\n');
        if (line == "\r") {
            headerEnded = true;
            continue;
        }
        if (headerEnded) {
            responseBody += line;
        }
    }

    if (method == "GET" && responseBody.length() > 0) {
        JSONVar doc = JSON.parse(responseBody);
        if (JSON.typeof(doc) != "undefined" && doc.hasOwnProperty("m2m:cin")) {
            JSONVar conObj = doc["m2m:cin"]["con"];
            
            if (conObj.hasOwnProperty(myMacAddress)) {
                String cmd = (const char*) conObj[myMacAddress];
                
                Serial.print(F("[CMD] Found: "));
                Serial.println(cmd);

                controlRelay(cmd);
            }
        }
    }
}

// ----------------------------------------------------------------
// [기능 함수]
// ----------------------------------------------------------------
void getCommandFromServer() {
    String url = "/" + cse + "/" + ae + "/" + cnt_cmd + "/la";
    sendRequest("GET", url, "");
}

void processAndUploadSensorData() {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    if (isnan(t)) t = 0; if (isnan(h)) h = 0;

    double amps = readCurrentFast();

    Serial.print(F("[Data] ")); Serial.print(amps, 3); Serial.print(F("A, "));
    Serial.print(relayStatus); Serial.println(F(" sent."));

    String payload = "{\\\"temp\\\":" + String(t, 1) + 
                     ", \\\"humi\\\":" + String(h, 0) + 
                     ", \\\"energy\\\":" + String(amps, 3) + 
                     ", \\\"status\\\":\\\"" + relayStatus + "\\\"}";
                     
    String body = "{\"m2m:cin\": {\"con\": \"" + payload + "\", \"lbl\": [\"smart_plug\", \"" + myMacAddress + "\"]}}";
    String url = "/" + cse + "/" + ae + "/" + cnt_monitor;
    
    sendRequest("POST", url, body);
}

float readCurrentFast() {
    int maxValue = 0;          
    int minValue = 1024;          
    unsigned long start_time = millis();
    
    while((millis() - start_time) < 100) {
        int readValue = analogRead(sensorIn); 
        if (readValue > maxValue) maxValue = readValue;
        if (readValue < minValue) minValue = readValue;
    }
    
    float resultVoltage = ((maxValue - minValue) * 5.0) / 1024.0;
    float vrms = (resultVoltage / 2.0) * 0.707;
    float amps = ((vrms * 1000) / mVperAmp) - 0.03;
    if (amps < 0) amps = 0;
    return amps;
}

void controlRelay(String cmd) {
    if (cmd == "on" && relayStatus != "on") {
        digitalWrite(relay, LOW); 
        relayStatus = "on";
        Serial.println(F(">>> RELAY TURNED ON (Action Taken)"));
    } else if (cmd == "off" && relayStatus != "off") {
        digitalWrite(relay, HIGH); 
        relayStatus = "off";
        Serial.println(F(">>> RELAY TURNED OFF (Action Taken)"));
    }
}

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;
    Serial.print(F("[WiFi] Conn.."));
    while (WiFi.status() != WL_CONNECTED) {
        WiFi.begin(ssid, pass);
        delay(3000);
    }
    Serial.println(F("OK"));
    client.stop();
}

String getMacAddressStr() {
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