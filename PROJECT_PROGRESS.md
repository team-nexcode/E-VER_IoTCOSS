# IoTCOSS_NEXCODE - 프로젝트 진행상황

## 프로젝트 개요
- **프로젝트명**: IoTCOSS_NEXCODE (IoT 기반 전력소비절감 시스템)
- **목적**: 아두이노 기반 스마트 플러그 디바이스를 통한 가정 내 전력 소비 모니터링 및 절감
- **서버 환경**: AWS EC2 (Ubuntu)
- **시작일**: 2026-01-27

---

## 의사결정 기록

### 1. 웹 서버 선택: Apache vs Nginx
- **결정**: **Nginx** 채택
- **근거**:
  - WebSocket 지원이 뛰어남 (IoT 실시간 데이터 전송에 필수)
  - FastAPI(Uvicorn)와의 리버스 프록시 연동이 간편
  - 메모리 사용량이 적고 동시 접속 처리 성능이 우수
  - Vue 빌드 정적 파일 서빙에 최적화
  - 현대 웹 서비스의 사실상 표준

### 2. Backend 프레임워크: Flask vs FastAPI
- **결정**: **FastAPI** 채택
- **근거**:
  - 비동기(async/await) 네이티브 지원 → IoT 실시간 데이터 처리에 적합
  - WebSocket 내장 지원 → 별도 라이브러리 불필요
  - Pydantic 기반 자동 데이터 검증 및 API 문서 생성
  - Flask와 문법이 유사하여 팀 적응 비용이 낮음
  - 성능이 Flask 대비 월등히 우수 (비동기 처리)

### 3. Frontend 프레임워크: React → Vue 3 전환
- **초기 결정**: React + TypeScript
- **전환 결정**: **Vue 3 + TypeScript (Composition API)** 채택 (2026-01-31)
- **전환 근거**:
  - `<script setup>` 문법으로 보일러플레이트 대폭 감소
  - Composition API의 `ref`/`computed`/`watch`가 React Hooks보다 직관적
  - ECharts(vue-echarts)로 IoT 센서 데이터 시각화에 더 적합
  - Pinia 상태관리가 Zustand 대비 Vue DevTools 통합 우수
  - WebSocket 컴포저블로 실시간 IoT 데이터 처리 구조화

### 4. 프론트-백엔드 아키텍처
- **결정**: **완전 분리형 아키텍처**
- **구조**: Frontend(Vue 3) ↔ REST API / WebSocket ↔ Backend(FastAPI)
- **장점**:
  - Frontend 교체 시 Backend 코드 수정 불필요
  - 독립적 개발/배포 가능
  - API 규격만 맞추면 어떤 클라이언트든 연동 가능 (모바일 앱 등)

---

## 기술 스택

### Backend
| 기술 | 용도 | 비고 |
|------|------|------|
| **Python 3.11+** | 메인 언어 | |
| **FastAPI** | API 프레임워크 | 비동기, WebSocket 내장 지원 |
| **Uvicorn** | ASGI 서버 | FastAPI 구동용 |
| **SQLAlchemy 2.0** | ORM | 비동기 지원 |
| **Alembic** | DB 마이그레이션 | |
| **PostgreSQL** | 메인 데이터베이스 | 디바이스/사용자/설정 데이터 |
| **Redis** | 캐시 / Pub-Sub | 실시간 데이터 브로커 |
| **aiomqtt** | MQTT 클라이언트 | IoT 디바이스 통신 |
| **Pydantic** | 데이터 검증 | FastAPI 내장 |
| **python-jose** | JWT 인증 | |
| **passlib** | 비밀번호 해싱 | |

### Frontend
| 기술 | 용도 | 비고 |
|------|------|------|
| **Vue 3.5** | UI 프레임워크 | Composition API + `<script setup>` |
| **TypeScript 5.9** | 타입 안전성 | |
| **Vite 7** | 빌드 도구 | 빠른 HMR |
| **Tailwind CSS v4** | 스타일링 | 유틸리티 퍼스트 |
| **Vue Router 4** | 라우팅 | 레이지 로딩 |
| **ECharts 5 + vue-echarts 7** | 차트/그래프 | 전력 데이터 시각화 |
| **Lucide Vue Next** | 아이콘 | |
| **Pinia 2** | 상태관리 | Vue DevTools 통합 |

### 인프라 / 배포
| 기술 | 용도 | 비고 |
|------|------|------|
| **Nginx** | 리버스 프록시 / 정적 파일 서빙 | |
| **Docker + Docker Compose** | 컨테이너화 | 배포 일관성 |
| **Mosquitto** | MQTT 브로커 | IoT 디바이스 통신 |
| **Certbot** | SSL 인증서 | Let's Encrypt |

### IoT 디바이스
| 기술 | 용도 | 비고 |
|------|------|------|
| **Arduino (ESP32)** | 메인 MCU | WiFi 내장 |
| **PZEM-004T** | 전력 측정 센서 | 전압/전류/전력/전력량 |
| **릴레이 모듈** | 가전제품 On/Off | |
| **DS18B20 / NTC** | 내부 온도 센서 | |
| **MQTT** | 서버 통신 프로토콜 | 경량 IoT 프로토콜 |

---

## AWS EC2 Ubuntu 필수 패키지 설치 가이드

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Python 3.11+ 설치
sudo apt install -y python3.11 python3.11-venv python3-pip

# 3. Node.js 20 LTS 설치 (Frontend 빌드용)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 4. PostgreSQL 설치
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql

# 5. Redis 설치
sudo apt install -y redis-server
sudo systemctl enable redis-server

# 6. Nginx 설치
sudo apt install -y nginx
sudo systemctl enable nginx

# 7. MQTT 브로커 (Mosquitto) 설치
sudo apt install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto

# 8. Docker & Docker Compose 설치 (선택)
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker $USER

# 9. Git 설치
sudo apt install -y git

# 10. Certbot (SSL) 설치
sudo apt install -y certbot python3-certbot-nginx

# 11. 기타 유틸리티
sudo apt install -y curl wget vim htop
```

---

## 프로젝트 폴더 구조

```
IoTCOSS_NEXCODE/
├── Backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI 앱 진입점
│   │   ├── config.py            # 환경 설정
│   │   ├── database.py          # DB 연결 설정
│   │   ├── models/              # SQLAlchemy 모델
│   │   │   ├── __init__.py
│   │   │   ├── device.py
│   │   │   ├── power_log.py
│   │   │   └── user.py
│   │   ├── schemas/             # Pydantic 스키마
│   │   │   ├── __init__.py
│   │   │   ├── device.py
│   │   │   └── power.py
│   │   ├── api/                 # API 라우터
│   │   │   ├── __init__.py
│   │   │   ├── devices.py
│   │   │   ├── power.py
│   │   │   ├── auth.py
│   │   │   └── websocket.py
│   │   ├── services/            # 비즈니스 로직
│   │   │   ├── __init__.py
│   │   │   ├── mqtt_service.py
│   │   │   ├── device_service.py
│   │   │   └── power_service.py
│   │   └── utils/               # 유틸리티
│   │       └── __init__.py
│   ├── alembic/                 # DB 마이그레이션
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env
├── Frontend/
│   ├── public/
│   │   └── vite.svg
│   ├── src/
│   │   ├── main.ts                      # Vue 앱 진입점
│   │   ├── App.vue                      # 루트 컴포넌트
│   │   ├── env.d.ts                     # Vue SFC 타입 선언
│   │   ├── index.css                    # Tailwind + CSS 변수
│   │   ├── router/
│   │   │   └── index.ts                 # Vue Router 설정 (7개 라우트)
│   │   ├── stores/
│   │   │   └── device.ts                # Pinia 스토어
│   │   ├── composables/
│   │   │   └── useWebSocket.ts          # WebSocket 컴포저블
│   │   ├── types/
│   │   │   ├── device.ts                # 디바이스 관련 타입
│   │   │   └── apiLog.ts                # API 로그 타입
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Layout.vue
│   │   │   │   ├── TopBar.vue
│   │   │   │   └── Sidebar.vue
│   │   │   └── Dashboard/
│   │   │       ├── StatusCard.vue
│   │   │       ├── PowerChart.vue
│   │   │       ├── DevicePanel.vue
│   │   │       ├── FloorPlan.vue
│   │   │       └── OutletPopup.vue
│   │   └── pages/
│   │       ├── Dashboard.vue
│   │       ├── Devices.vue
│   │       ├── PowerAnalysis.vue
│   │       ├── Schedule.vue
│   │       ├── Alerts.vue
│   │       ├── ApiLogs.vue
│   │       └── Settings.vue
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   └── eslint.config.js
├── IoT_Device/                  # 아두이노 펌웨어
├── Documents/                   # 참고 자료
├── fetch.sh                     # 자동 배포 스크립트
├── reload.sh                    # 서비스 재시작 스크립트
├── method.txt                   # 서버 셋업 가이드
├── PROJECT_PROGRESS.md          # 이 파일
└── .gitignore
```

---

## 대시보드 탭 구성

### 상단 바 (Top Bar)
- 좌측: 로고 + 시스템 이름
- 우측: 알림 벨, 사용자 프로필

### 좌측 사이드바 (Sidebar) 탭 구성
| 탭 | 아이콘 | 설명 |
|----|--------|------|
| **대시보드** | LayoutDashboard | 메인 모니터링 - 집 구조도 + 콘센트 실시간 상태 |
| **디바이스** | Plug | 디바이스 목록, 상태, 개별 제어 (On/Off) |
| **전력 분석** | BarChart3 | 전력 소비 통계, 일별/주별/월별 차트, 절감률 |
| **스케줄** | Clock | 자동 On/Off 스케줄 설정 |
| **알림** | Bell | 과전력 경고, 이상 온도 감지, 디바이스 오프라인 알림 |
| **API 로그** | FileText | Mobius 서버 API 통신 로그 조회/필터/삭제 |
| **설정** | Settings | 시스템 설정, 사용자 관리, MQTT 설정 |

---

## 진행 상황

### Phase 1: 프로젝트 초기 설정 - 완료
- [x] 프로젝트 구조 설계
- [x] 기술 스택 결정 (의사결정 기록 참고)
- [x] 진행상황 문서 생성
- [x] Node.js 설치
- [x] Frontend 프로젝트 생성 (Vite)
- [x] Frontend 패키지 설치 (Tailwind CSS, Vue Router, ECharts, Lucide, Pinia)
- [x] Vite 설정 완료 (Tailwind, API Proxy → iotcoss.nexcode.kr:8000)
- [x] Backend FastAPI 프로젝트 초기화 (전체 구조 완성)
- [x] 대시보드 레이아웃 구축 (상단바 + 좌측 사이드바 7개 탭)
- [x] 메인 대시보드 페이지 (5개 방 집 구조도 + 5개 디바이스 콘센트 모니터링)
- [x] 더미 데이터 5개 디바이스: 거실TV, 주방 전자레인지, 침실 에어컨, 서재 컴퓨터, 욕실 온풍기
- [x] Frontend 개발 서버 실행 확인 (http://localhost:5173/)
- [x] React → Vue 3 마이그레이션 완료 (2026-01-31)
- [x] API 로그 페이지 구현 (필터, 검색, 페이지네이션, 행 확장)
- [x] WebSocket 컴포저블 준비 (useWebSocket.ts)

### Phase 2: Backend API 개발 - 완료 (골격)
- [x] 데이터베이스 모델 설계 (Device, PowerLog, User)
- [x] 디바이스 CRUD API (/api/devices)
- [x] 전력 데이터 API (/api/power)
- [x] WebSocket 실시간 데이터 전송 (/ws/devices)
- [x] 인증/인가 시스템 (/api/auth - JWT 기반)
- [ ] DB 마이그레이션 (Alembic 설정)
- [ ] 실제 DB 연동 테스트 (PostgreSQL 필요)

### Phase 3: IoT 디바이스 연동
- [ ] MQTT 브로커 설정
- [ ] MQTT 서비스 구현
- [ ] 아두이노 펌웨어 개발
- [ ] 디바이스-서버 통신 테스트

### Phase 4: 배포
- [ ] Docker 컨테이너화
- [ ] Nginx 설정
- [ ] AWS EC2 배포
- [ ] SSL 인증서 설정

---

*마지막 업데이트: 2026-01-31*
