# E-VER - IoT 기반 스마트 전력 관리 시스템

<div align="center">

**Arduino 기반 스마트 플러그를 활용한 가정 내 전력 소비 모니터링 및 AI 기반 대기전력 자동 절감 시스템**

</div>

---

## 📌 프로젝트 개요

E-VER는 ESP32 기반 스마트 플러그 디바이스를 통해 가정 내 전기 기기의 실시간 전력 소비를 모니터링하고, AI가 사용 패턴을 학습하여 대기전력을 자동으로 차단하는 전력 절감 시스템입니다.

### 핵심 가치
- 🔌 **실시간 전력 모니터링**: ACS712 센서를 통한 정확한 전압/전류/전력/전력량 측정
- 🤖 **AI 기반 자동 제어**: 사용 패턴 학습을 통한 스마트한 대기전력 차단
- 📊 **직관적인 대시보드**: 실시간 데이터 시각화 및 원격 제어
- ⚡ **즉각적인 WebSocket 통신**: 1초 단위 실시간 데이터 업데이트
- 📱 **스케줄 관리**: 시간대별 자동 On/Off 예약 기능

---

## 🎯 주요 기능

### 1. 실시간 전력 모니터링
- ESP32 + ACS712 센서를 통한 1초 간격 데이터 수집
- 전압(V), 전류(A), 전력(W), 전력량(Wh), 온도 실시간 측정
- WebSocket을 통한 지연 없는 대시보드 업데이트
- ECharts 기반 실시간 그래프 시각화

### 2. AI 스마트 대기전력 자동 차단
- **사용 패턴 학습**: 요일별/시간대별 기기 사용 패턴 분석
- **예측 제어**: 사용 전 미리 켜고, 미사용 시간에 자동 차단
- **profiles.json 기반 추천**:
  - `on_rate >= 0.5`: 사용 예정 → 자동 ON
  - `on_rate < 0.5`: 미사용 시간 → 자동 OFF (대기전력 차단)
- 10초 주기 백그라운드 자동 실행

### 3. 이상 감지 및 알림
- Robust Z-Score 기반 전력 이상치 탐지
- 대기전력 낭비 추정 (Standby Waste)
- 실시간 알림 시스템

### 4. 스케줄 관리
- 시간대별 자동 On/Off 예약
- 반복 스케줄 설정 (요일별)
- 스케줄 우선순위 관리

### 5. 원격 제어
- 웹 대시보드를 통한 기기 On/Off 제어
- oneM2M 표준 기반 IoT 통신
- MQTT를 통한 즉각적인 명령 전달

---

## 🛠 기술 스택

### Backend
| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.11+ | 메인 언어 |
| **FastAPI** | latest | 비동기 REST API 프레임워크 |
| **SQLAlchemy** | 2.0 | ORM (비동기 지원) |
| **PostgreSQL** | latest | 메인 데이터베이스 |
| **Redis** | latest | 캐시 및 Pub-Sub |
| **aiomqtt** | latest | MQTT 클라이언트 (IoT 통신) |
| **Uvicorn** | latest | ASGI 서버 |
| **Pydantic** | latest | 데이터 검증 |
| **python-jose** | latest | JWT 인증 |

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| **Vue 3** | 3.5+ | UI 프레임워크 (Composition API) |
| **TypeScript** | 5.9+ | 타입 안전성 |
| **Vite** | 7 | 빌드 도구 |
| **Tailwind CSS** | v4 | 유틸리티 기반 스타일링 |
| **Vue Router** | 4 | 라우팅 |
| **Pinia** | 2 | 상태 관리 |
| **ECharts 5** | 5 + vue-echarts 7 | 차트 시각화 |
| **Axios** | latest | HTTP 클라이언트 |
| **Lucide Vue Next** | latest | 아이콘 |

### IoT Device
| 기술 | 버전 | 용도 |
|------|------|------|
| **Arduino (ESP32)** | - | 메인 MCU (WiFi 내장) |
| **ACS712** | - | 전류 측정 센서 |
| **릴레이 모듈** | - | 가전제품 On/Off 제어 |
| **DHT11 / DS18B20** | - | 온도 센서 |
| **MQTT** | - | 서버 통신 프로토콜 |

### Infrastructure
| 기술 | 용도 |
|------|------|
| **Nginx** | 리버스 프록시 / 정적 파일 서빙 |
| **Docker** | 컨테이너화 |
| **Mosquitto** | MQTT 브로커 |
| **AWS EC2** | 서버 호스팅 (Ubuntu) |

---

## 🏗 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                         │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────────┐  │
│  │Dashboard │  │   Devices │  │  Power   │  │   Schedule   │  │
│  │  (실시간) │  │  (제어)   │  │ (분석)   │  │   (예약)     │  │
│  └──────────┘  └───────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
           │                                           │
           │ REST API / WebSocket                     │
           ▼                                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────┐    │
│  │   REST API   │  │  WebSocket  │  │   MQTT Service     │    │
│  │  (제어/조회)  │  │ (실시간 전송)│  │   (IoT 통신)       │    │
│  └──────────────┘  └─────────────┘  └────────────────────┘    │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────────┐    │
│  │Schedule Svc  │  │ AI Control  │  │  Mobius Service    │    │
│  │ (자동예약)    │  │ (AI 자동화) │  │  (oneM2M)          │    │
│  └──────────────┘  └─────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
           │                          │                  │
           ▼                          ▼                  ▼
┌──────────────────┐      ┌───────────────────┐   ┌──────────┐
│   PostgreSQL     │      │   AI Server       │   │  Redis   │
│  (메인 DB)       │      │  (패턴 분석/추천)  │   │ (캐시)   │
└──────────────────┘      └───────────────────┘   └──────────┘
                                     │
                                     ▼
                          ┌───────────────────┐
                          │  profiles.json    │
                          │  thresholds.json  │
                          │  baselines.json   │
                          └───────────────────┘
                                     ▲
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           │                    MQTT Broker                     │
           │                   (Mosquitto)                      │
           └─────────────────────────────────────────────────────┘
                          ▲                    ▲
                          │ Publish            │ Subscribe
                          │                    │
           ┌──────────────┴────────┐    ┌─────┴──────────────┐
           │   IoT Device #1       │    │   IoT Device #2    │
           │  ┌─────────────────┐  │    │  ┌──────────────┐  │
           │  │   ESP32 + WiFi  │  │    │  │ ESP32 + WiFi │  │
           │  │   ACS712        │  │    │  │  ACS712      │  │
           │  │   릴레이 모듈    │  │    │  │  릴레이 모듈  │  │
           │  │   온도 센서      │  │    │  │  온도 센서    │  │
           │  └─────────────────┘  │    │  └──────────────┘  │
           │         ↕             │    │        ↕           │
           │    [가전제품]         │    │   [가전제품]        │
           └───────────────────────┘    └────────────────────┘
```

### 데이터 흐름

1. **센서 → 서버**:
   ```
   IoT Device (ESP32) → MQTT Publish → Backend MQTT Service → 
   WebSocket Broadcast → Frontend 실시간 업데이트
   ```

2. **제어 명령**:
   ```
   Frontend → REST API → Mobius Service (oneM2M) → 
   MQTT → IoT Device → 릴레이 제어
   ```

3. **AI 자동 제어**:
   ```
   AI Service (60분 주기) → DB 조회 (ai_auto_control=true) →
   AI Server (패턴 분석) → 추천 결정 → Mobius Service → 
   MQTT → IoT Device
   ```

---

## 📦 프로젝트 구조

```
AIoT/
├── Backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py            # 앱 진입점
│   │   ├── config.py          # 환경 설정
│   │   ├── database.py        # DB 연결
│   │   ├── __init__.py
│   │   ├── api/               # REST API 엔드포인트
│   │   │   ├── __init__.py
│   │   │   ├── ai_analysis.py
│   │   │   ├── api_logs.py
│   │   │   ├── auth.py
│   │   │   ├── devices.py
│   │   │   ├── device_mac.py
│   │   │   ├── mobius.py
│   │   │   ├── power.py
│   │   │   ├── schedules.py
│   │   │   ├── system_logs.py
│   │   │   └── websocket.py
│   │   ├── models/            # SQLAlchemy 모델
│   │   │   ├── __init__.py
│   │   │   ├── api_log.py
│   │   │   ├── dashboard.py
│   │   │   ├── device.py
│   │   │   ├── device_mac.py
│   │   │   ├── device_switch.py
│   │   │   ├── power_log.py
│   │   │   ├── schedule.py
│   │   │   ├── system_log.py
│   │   │   └── user.py
│   │   ├── schemas/           # Pydantic 스키마
│   │   │   ├── __init__.py
│   │   │   ├── api_log.py
│   │   │   ├── device.py
│   │   │   ├── device_mac.py
│   │   │   ├── device_switch.py
│   │   │   ├── power.py
│   │   │   ├── schedule.py
│   │   │   └── system_log.py
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── ai_auto_control_service.py
│   │   │   ├── device_service.py
│   │   │   ├── mobius_service.py
│   │   │   ├── mqtt_service.py
│   │   │   └── schedule_service.py
│   │   ├── ai/                # AI 서버
│   │   │   ├── ai_server.py
│   │   │   ├── train_models.py
│   │   │   ├── train_profiles.py
│   │   │   ├── export_devices.py
│   │   │   ├── test.py
│   │   │   ├── devices.csv
│   │   │   ├── dummy_devices.csv
│   │   │   └── models/
│   │   │       ├── profiles.json
│   │   │       ├── thresholds.json
│   │   │       └── baselines.json
│   │   └── utils/
│   ├── requirements.txt
│   └── migrations/
│       └── add_ai_auto_control.sql
│
├── Frontend/                   # Vue 3 프론트엔드
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── index.css
│   │   ├── env.d.ts
│   │   ├── pages/             # 페이지 컴포넌트
│   │   │   ├── Dashboard.vue
│   │   │   ├── Devices.vue
│   │   │   ├── PowerAnalysis.vue
│   │   │   ├── Schedule.vue
│   │   │   ├── Alerts.vue
│   │   │   ├── SystemLog.vue
│   │   │   └── Settings.vue
│   │   ├── components/        # 재사용 컴포넌트
│   │   │   ├── Dashboard/
│   │   │   │   ├── DevicePanel.vue
│   │   │   │   ├── FloorPlan.vue
│   │   │   │   ├── OutletPopup.vue
│   │   │   │   ├── PowerChart.vue
│   │   │   │   └── StatusCard.vue
│   │   │   └── Layout/
│   │   ├── stores/            # Pinia 스토어
│   │   │   ├── device.ts
│   │   │   ├── deviceMac.ts
│   │   │   ├── power.ts
│   │   │   ├── schedule.ts
│   │   │   └── systemLog.ts
│   │   ├── composables/       # Vue Composables
│   │   │   └── useWebSocket.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   └── types/
│   │       ├── device.ts
│   │       ├── deviceMac.ts
│   │       ├── schedule.ts
│   │       └── systemLog.ts
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── eslint.config.js
│   ├── index.html
│   └── team.txt
│
├── IoT_Device/                 # Arduino 펌웨어
│   ├── V03_Final/
│   │   └── V03_Final.ino      # 최종 펌웨어
│   ├── V02_Total/
│   │   └── V02_Total.ino
│   ├── V01/
│   │   └── V01.ino
│   └── device/
│       └── device.ino
│
├── docs/                       # 문서
│   └── AI_AUTO_CONTROL.md
│
├── Documents/
│   └── Mobius_API_Release2.postman_collection.json
│
├── .gitignore
├── PROJECT_PROGRESS.md         # 개발 진행 기록
├── README.md
├── method.txt
├── fetch.sh
└── reload.sh
```

---

## 📡 API 문서

### Backend API (Port 8000)

#### 인증 (Auth)
```
POST   /api/auth/register          # 회원가입
POST   /api/auth/login             # 로그인
GET    /api/auth/me                # 내 정보 조회
```

#### 디바이스 관리 (Device MAC)
```
GET    /api/device_mac/            # 디바이스 MAC 전체 목록 조회
POST   /api/device_mac/            # 디바이스 MAC 등록
PUT    /api/device_mac/{device_id} # 디바이스 MAC 수정
DELETE /api/device_mac/{device_id} # 디바이스 MAC 삭제
PATCH  /api/device_mac/{device_id}/ai-control  # AI 자동 제어 토글
GET    /api/device_mac/ai-enabled  # AI 활성화 디바이스 목록
```

#### 디바이스 센서 데이터
```
GET    /api/devices/               # 디바이스 센서 데이터 목록 조회
POST   /api/devices/power/control  # 디바이스 전원 제어 (릴레이 ON/OFF)
GET    /api/devices/power/status   # 모든 디바이스의 전원 상태 조회
```

#### 전력 데이터
```
GET    /api/power/{device_id}/current  # 현재 전력 조회 (최신)
GET    /api/power/{device_id}/history  # 전력 사용 이력 조회
GET    /api/power/summary              # 전체 전력 요약 조회
GET    /api/power/daily                # 일별 총 전력량 조회
```

#### 스케줄
```
GET    /api/schedules              # 전체 스케줄 조회
POST   /api/schedules              # 스케줄 생성
GET    /api/schedules/{schedule_id}  # 스케줄 상세 조회
PATCH  /api/schedules/{schedule_id}  # 스케줄 수정
DELETE /api/schedules/{schedule_id}  # 스케줄 삭제
```

#### AI 분석
```
GET    /api/ai/report              # AI 전력 분석 리포트 데이터 조회
GET    /api/ai/analyze             # OpenAI 전력 분석
GET    /api/ai/full-report         # 전체 분석 리포트 (데이터 + AI 분석)
GET    /api/ai/analyze-ai-server   # AI 서버 리포트를 OpenAI로 분석
```

#### Mobius (oneM2M)
```
GET    /api/mobius/cse                           # CSE 정보 조회
GET    /api/mobius/ae/{ae}                       # AE 조회
POST   /api/mobius/ae                            # AE 생성
PUT    /api/mobius/ae/{ae}                       # AE 수정
DELETE /api/mobius/ae/{ae}                       # AE 삭제
GET    /api/mobius/ae/{ae}/container/{cnt}      # Container 조회
POST   /api/mobius/ae/{ae}/container            # Container 생성
PUT    /api/mobius/ae/{ae}/container/{cnt}      # Container 수정
DELETE /api/mobius/ae/{ae}/container/{cnt}      # Container 삭제
GET    /api/mobius/ae/{ae}/container/{cnt}/cin/{cin}  # CIN 조회
GET    /api/mobius/ae/{ae}/container/{cnt}/cin       # 최신 CIN 조회
POST   /api/mobius/ae/{ae}/container/{cnt}/cin       # CIN 생성
```

#### 시스템 로그
```
GET    /api/system_logs/           # 시스템 로그 목록 조회
DELETE /api/system_logs/           # 시스템 로그 전체 삭제
```

#### API 로그
```
GET    /api/api_logs/              # API 로그 목록 조회
GET    /api/api_logs/{log_id}      # API 로그 상세 조회
DELETE /api/api_logs/              # API 로그 전체 삭제
```

#### WebSocket
```
WS     /api/ws/devices             # 실시간 디바이스 데이터 스트리밍
```

---

### AI Server API (Port 8001 - 독립 실행)

```
GET    /health                               # AI 서버 상태 확인
POST   /models/reload                        # 모델 리로드
GET    /devices                              # 디바이스 목록 조회
GET    /devices/{device_mac}/state           # 디바이스 상태 분류 (IDLE/STANDBY/LOAD)
GET    /devices/{device_mac}/anomalies       # 이상치 탐지
GET    /devices/{device_mac}/waste           # 대기전력 낭비 추정
GET    /devices/{device_mac}/report          # 디바이스 분석 리포트
GET    /devices/{device_mac}/auto-control-recommendation  # AI 자동 제어 추천
GET    /auto-control/recommendations         # 전체 디바이스 AI 추천
```

---

## 🤖 AI 자동 제어 동작 원리

### 1. 데이터 수집 및 학습
```python
# train_profiles.py - 사용 패턴 학습
- 디바이스별 전력 데이터 분석
- 요일별(0-6) × 시간대별(0-23) ON 비율 계산
- profiles.json에 저장
```

### 2. 실시간 추천
```python
# ai_server.py - 자동 제어 추천
현재 시간의 on_rate 확인:
- on_rate >= 0.5 → "ON"  (사용 예정, 미리 켜기)
- on_rate < 0.5 → "OFF" (미사용, 대기전력 차단)
```

### 3. 자동 실행
```python
# ai_auto_control_service.py - 60분 주기 실행
1. DB에서 ai_auto_control=True인 디바이스 조회
2. AI 서버에 추천 요청
3. 추천에 따라 릴레이 제어
4. 로그 기록
```

### 사용 예시: 사무실 PC
```
학습된 패턴 (profiles.json):
- 평일 09:00~18:00: on_rate = 1.0 (항상 사용)
- 평일 00:00~08:00: on_rate = 0.0 (미사용)
- 주말: on_rate = 0.0 (미사용)

자동 제어:
✅ 08:00에 AI 실행 → on_rate 0.5 이상 → ON (출근 전 미리 켜기)
✅ 18:00에 AI 실행 → on_rate 0.5 미만 → OFF (퇴근 후 대기전력 차단)
✅ 주말에 AI 실행 → on_rate 0.0 → OFF (대기전력 차단)
```

---

## 📊 주요 화면

### Dashboard
- 실시간 전력 소비 현황
- 디바이스별 상태 모니터링
- 실시간 차트 (전력, 전압, 전류)
- 원격 On/Off 제어

### Devices
- 디바이스 목록 및 상세 정보
- 디바이스 등록/수정/삭제

### Power Analysis
- 전력 사용 통계 및 그래프
- 시간대별 분석
- 대기전력 낭비 분석
- 생성형 인공지능을 활용한 피드백

### Schedule
- 시간대별 자동 제어 설정
- 반복 스케줄 관리

### AI Auto Control
- 디바이스별 AI 자동 제어 토글
- 학습된 패턴 시각화
- 자동 제어 로그

---

## 🌟 주요 특징

### 1. 실시간 성능
- **WebSocket**: 1초 간격 실시간 데이터 업데이트
- **비동기 처리**: FastAPI의 async/await로 높은 동시성
- **Redis 캐싱**: 자주 조회되는 데이터 캐싱으로 응답 속도 향상

### 2. 확장 가능한 아키텍처
- **모듈화된 서비스**: 각 기능별 독립적인 서비스 모듈
- **oneM2M 표준**: 표준 IoT 플랫폼 연동
- **RESTful API**: 어떤 클라이언트든 연동 가능

### 3. 안정성
- **재연결 로직**: MQTT/DB 연결 끊김 시 자동 재연결
- **로깅**: 상세한 로그 기록으로 디버깅 용이

### 4. 사용자 경험
- **직관적인 UI**: Tailwind CSS 기반 모던한 디자인
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **즉각적인 피드백**: WebSocket을 통한 즉시 UI 업데이트

---

## 📝 개발 과정

프로젝트 개발 과정 및 의사결정 기록은 [PROJECT_PROGRESS.md](PROJECT_PROGRESS.md)를 참고하세요.

### 주요 의사결정
1. **웹 서버**: Apache → **Nginx** (WebSocket 지원, 성능 우수)
2. **Backend**: Flask → **FastAPI** (비동기, WebSocket 내장)
3. **Frontend**: React → **Vue 3** (Composition API, 직관적, ECharts 통합)
4. **아키텍처**: 완전 분리형 (Frontend ↔ API ↔ Backend)

---

## 🤝 팀 구성

- **Backend**: FastAPI, AI 서버, MQTT 통신
- **Frontend**: Vue 3, 대시보드, 실시간 차트
- **IoT Device**: ESP32 펌웨어, 센서 통합

---

## 🔗 관련 링크

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [oneM2M Standard](https://www.onem2m.org/)
- [MQTT Protocol](https://mqtt.org/)
- [ECharts Documentation](https://echarts.apache.org/)

---

<div align="center">

**Made by NEXCODE**

</div>
