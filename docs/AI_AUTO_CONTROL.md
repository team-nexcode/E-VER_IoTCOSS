# AI 스마트 대기전력 자동 차단 기능

## 개요
profiles.json의 사용 패턴 데이터를 기반으로 **사용자가 사용하는 시간 전에 미리 릴레이를 켜고**, **사용하지 않는 시간에는 대기전력을 차단**하는 AI 자동 제어 기능입니다.

## 아키텍처

```
Frontend (Sidebar.vue)
    ↓ 토글 ON/OFF
Backend API (/api/device_mac/{id}/ai-control)
    ↓ DB 저장 (device_mac.ai_auto_control)
AI Auto Control Service (60분 주기)
    ↓ AI 활성화된 디바이스 조회
AI Server (/devices/{mac}/auto-control-recommendation)
    ↓ profiles.json 기반 추천
    → on_rate >= 0.7: ON (사용 예정)
    → on_rate <= 0.3: OFF (미사용, 대기전력 차단)
    → else: KEEP (현재 상태 유지)
Mobius Service (send_relay_command)
    ↓ 릴레이 실제 제어
```

## 주요 컴포넌트

### 1. 프론트엔드 (Sidebar.vue)
- **AI 자동 차단** 패널에서 디바이스별 토글
- 토글 변경 시 `PATCH /api/device_mac/{id}/ai-control` 호출
- DB에서 초기 상태 로드 (localStorage fallback)

### 2. 백엔드 API (device_mac.py)
**새로운 엔드포인트:**
- `PATCH /api/device_mac/{device_id}/ai-control?enabled=true|false`
  - AI 자동 제어 활성화/비활성화
- `GET /api/device_mac/ai-enabled`
  - AI 자동 제어가 활성화된 디바이스 목록

### 3. AI Server (ai_server.py)
**profiles.json 로딩:**
```python
# ModelStore에 profiles 추가
self.profiles: Dict[str, Dict[str, Any]] = {}

# profiles.json 구조:
{
  "device_mac": {
    "device_name": "TV",
    "on_rate": [
      [0.0, 0.0, ..., 1.0, 1.0, ..., 0.0],  # 월요일 24시간
      [0.0, 0.0, ..., 1.0, 1.0, ..., 0.0],  # 화요일 24시간
      ...
    ]
  }
}
```

**자동 제어 추천 엔드포인트:**
- `GET /devices/{device_mac}/auto-control-recommendation`
  - 현재 시간 기준 on_rate 확인
  - on_rate >= 0.7 → ON (사용 예정)
  - on_rate <= 0.3 → OFF (미사용)
  - else → KEEP (유지)

- `GET /auto-control/recommendations`
  - 모든 디바이스의 추천 목록

### 4. AI Auto Control Service (ai_auto_control_service.py)
**주기적 실행 (60분):**
1. DB에서 `ai_auto_control = True`인 디바이스 조회
2. 각 디바이스별로 AI 추천 받기
3. 추천에 따라 `send_relay_command(mac, "on"|"off")` 실행
4. 로그 기록

**실행 방식:**
- main.py의 lifespan에서 백그라운드 태스크로 시작
- 60분마다 자동 실행 (설정 가능)

## 사용 시나리오

### 예시: 사무실 PC
```
profiles.json:
- 평일 09:00~18:00: on_rate = 1.0 (항상 사용)
- 평일 00:00~08:00: on_rate = 0.0 (미사용)
- 주말: on_rate = 0.0 (미사용)

자동 제어:
- 08:00 ~ 09:00 사이에 AI가 실행되면 → on_rate >= 0.7 → ON 명령 (사용 준비)
- 18:00 ~ 19:00 사이에 AI가 실행되면 → on_rate <= 0.3 → OFF 명령 (대기전력 차단)
- 주말에 실행되면 → on_rate = 0.0 → OFF 명령 (대기전력 차단)
```

## 데이터베이스 마이그레이션

```sql
-- migrations/add_ai_auto_control.sql
ALTER TABLE device_mac 
ADD COLUMN IF NOT EXISTS ai_auto_control BOOLEAN DEFAULT FALSE NOT NULL;

CREATE INDEX IF NOT EXISTS idx_device_mac_ai_auto_control 
ON device_mac(ai_auto_control) 
WHERE ai_auto_control = TRUE;
```

**실행:**
```bash
psql -h iotcoss.nexcode.kr -U postgres -d aiot -f Backend/migrations/add_ai_auto_control.sql
```

## API 테스트

### 1. AI 자동 제어 활성화
```bash
curl -X PATCH "http://iotcoss.nexcode.kr:8000/api/device_mac/1/ai-control?enabled=true"
```

### 2. AI 활성화된 디바이스 목록
```bash
curl "http://iotcoss.nexcode.kr:8000/api/device_mac/ai-enabled"
```

### 3. AI 추천 조회 (AI Server)
```bash
curl "http://127.0.0.1:8001/devices/F4:12:FA:9C:7F:9C/auto-control-recommendation"

# 응답 예시:
{
  "device_mac": "F4:12:FA:9C:7F:9C",
  "device_name": "멀티탭",
  "current_hour": 14,
  "on_rate": 1.0,
  "action": "ON",
  "reason": "사용률 100% - 사용 예정 시간"
}
```

### 4. 전체 디바이스 추천
```bash
curl "http://127.0.0.1:8001/auto-control/recommendations"
```

## 수동 실행 (테스트용)

```bash
# AI 자동 제어 서비스 단독 실행 (10분 주기)
cd Backend
python -m app.services.ai_auto_control_service 10
```

## 로그 확인

```python
# AI 추천 로그
[AI_CONTROL] TV (48:27:E2:E0:53:DC) -> ON | 사유: 사용률 100% - 사용 예정 시간

# 제어 실행 로그
[AI_CONTROL] 멀티탭 (F4:12:FA:9C:7F:9C) -> OFF | 사유: 사용률 0% - 미사용 시간 (대기전력 차단)

# 사이클 완료
[AI_CONTROL] 제어 대상: 3개 디바이스
[AI_CONTROL] 사이클 완료
```

## 주의사항

1. **profiles.json 필수**: 해당 디바이스의 프로파일이 없으면 KEEP (현재 상태 유지)
2. **AI Server 실행**: AI Server (port 8001)가 실행 중이어야 함
3. **주기 설정**: 기본 60분, 너무 짧게 설정하면 불필요한 ON/OFF 반복
4. **Mobius 연동**: 실제 릴레이 제어는 Mobius를 통해 실행

## 향후 개선 방안

- [ ] 프론트엔드에 AI 제어 상태 실시간 표시
- [ ] AI 제어 히스토리 로그 저장
- [ ] 사용자별 선호 설정 (예: 출근 시간 조정)
- [ ] 기상청 API 연동 (날씨 기반 제어)
- [ ] 전력 요금 절감 금액 계산 및 대시보드 표시
