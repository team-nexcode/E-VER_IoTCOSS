#!/bin/bash
# ============================================================
#  IoTCOSS_NEXCODE - 자동 배포 스크립트
#  사용법: bash fetch.sh
# ============================================================

set -e

# ─── 설정 ───
GITHUB_TOKEN="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"
REPO_URL="https://secuho:${GITHUB_TOKEN}@github.com/team-nexcode/AIoT.git"
PROJECT_DIR="/IoTCOSS_NEXCODE"
FRONTEND_DIR="${PROJECT_DIR}/Frontend"
BACKEND_DIR="${PROJECT_DIR}/Backend"
BRANCH="main"

# ─── 색상 출력 ───
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[>>]${NC} $1"; }
err()  { echo -e "${RED}[!!]${NC} $1"; }

echo ""
echo "========================================"
echo "  IoTCOSS_NEXCODE 자동 배포"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# ─── 토큰 확인 ───
if [ "$GITHUB_TOKEN" = "[여기에_토큰_입력]" ]; then
    err "GitHub 토큰이 설정되지 않았습니다."
    err "fetch.sh 상단의 GITHUB_TOKEN 값을 수정하세요."
    exit 1
fi

# ─── 1. 프로젝트 클론 또는 풀 ───
if [ ! -d "${PROJECT_DIR}/.git" ]; then
    warn "프로젝트가 없습니다. git clone 실행..."
    git clone "${REPO_URL}" "${PROJECT_DIR}"
    log "git clone 완료"
else
    warn "git pull 실행..."
    cd "${PROJECT_DIR}"
    git pull origin "${BRANCH}"
    log "git pull 완료"
fi

# ─── 2. Backend .env 확인 ───
if [ ! -f "${BACKEND_DIR}/.env" ]; then
    warn ".env 파일이 없습니다. 기본 템플릿 생성..."
    cat > "${BACKEND_DIR}/.env" << 'ENVEOF'
# IoTCOSS 백엔드 환경 변수 설정
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/iotcoss
REDIS_URL=redis://localhost:6379
MQTT_BROKER=onem2m.iotcoss.ac.kr
MQTT_PORT=11883
SECRET_KEY=your-secret-key-change-in-production

X-API-KEY=tBaM6UH8VnlS9bIi4zdEwJAjLdT9vaQL
X-AUTH-CUSTOM-LECTURE=LCT_20250007
X-AUTH-CUSTOM-CREATOR=dgu2025112456

mp_url=https://onem2m.iotcoss.ac.kr
cb=Mobius
ENVEOF
    log ".env 파일 생성 완료 (필요시 비밀번호 수정)"
else
    log ".env 파일 확인 완료"
    # MQTT 브로커 설정이 localhost면 실제 브로커로 업데이트
    if grep -q "MQTT_BROKER=localhost" "${BACKEND_DIR}/.env"; then
        sed -i 's|MQTT_BROKER=localhost|MQTT_BROKER=onem2m.iotcoss.ac.kr|' "${BACKEND_DIR}/.env"
        sed -i 's|MQTT_PORT=1883|MQTT_PORT=11883|' "${BACKEND_DIR}/.env"
        log "MQTT 브로커 설정 업데이트: onem2m.iotcoss.ac.kr:11883"
    fi
fi

# ─── 3. Backend 가상환경 및 의존성 설치 ───
warn "Backend 의존성 확인..."
cd "${BACKEND_DIR}"

if [ ! -d "venv" ]; then
    warn "가상환경 생성 중..."
    python3 -m venv venv
    log "가상환경 생성 완료"
fi

source venv/bin/activate
pip install -q -r requirements.txt
deactivate
log "Backend 의존성 설치 완료"

# ─── 4. Frontend 빌드 ───
warn "Frontend 빌드 중..."
cd "${FRONTEND_DIR}"
npm install --silent
npm run build
log "Frontend 빌드 완료"

# ─── 5. 서비스 재시작 ───
warn "서비스 재시작 중..."

sudo systemctl restart iotcoss-backend 2>/dev/null && \
    log "Backend (FastAPI) 재시작 완료" || \
    warn "Backend 서비스가 아직 등록되지 않음 (method.txt STEP 7 참고)"

sudo systemctl restart nginx 2>/dev/null && \
    log "Nginx 재시작 완료" || \
    warn "Nginx가 설치되지 않음"

# ─── 6. 상태 확인 ───
echo ""
echo "========================================"
echo "  배포 완료 - 서비스 상태"
echo "========================================"
echo ""

for svc in nginx iotcoss-backend postgresql redis-server mosquitto; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        log "$svc: 실행 중"
    else
        warn "$svc: 비활성"
    fi
done

echo ""
log "배포 완료! $(date '+%H:%M:%S')"
echo ""
