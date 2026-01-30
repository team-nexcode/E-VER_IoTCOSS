#!/bin/bash
# ============================================================
#  IoTCOSS_NEXCODE - 서비스 재시작 스크립트
#  사용법: bash reload.sh [frontend|backend|all]
#  인자 없으면 all (둘 다 재시작)
# ============================================================

PROJECT_DIR="/IoTCOSS_NEXCODE"
FRONTEND_DIR="${PROJECT_DIR}/Frontend"
BACKEND_DIR="${PROJECT_DIR}/Backend"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[>>]${NC} $1"; }
err()  { echo -e "${RED}[!!]${NC} $1"; }

TARGET="${1:-all}"

reload_backend() {
    warn "Backend 재시작 중..."

    # 기존 uvicorn 프로세스 종료
    pkill -f "uvicorn app.main:app" 2>/dev/null && \
        log "기존 Backend 프로세스 종료" || \
        warn "실행 중인 Backend 없음"

    sleep 1

    cd "${BACKEND_DIR}"

    if [ ! -d "venv" ]; then
        warn "가상환경 생성 중..."
        python3 -m venv venv
    fi

    source venv/bin/activate
    pip install -q -r requirements.txt

    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/iotcoss-backend.log 2>&1 &
    log "Backend 시작 완료 (PID: $!, 로그: /tmp/iotcoss-backend.log)"
}

reload_frontend() {
    warn "Frontend 빌드 중..."
    cd "${FRONTEND_DIR}"
    npm install --silent
    npm run build
    log "Frontend 빌드 완료"

    sudo systemctl reload nginx 2>/dev/null && \
        log "Nginx 리로드 완료" || \
        warn "Nginx 리로드 실패"
}

echo ""
echo "========================================"
echo "  IoTCOSS 서비스 재시작 [${TARGET}]"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

case "$TARGET" in
    backend)
        reload_backend
        ;;
    frontend)
        reload_frontend
        ;;
    all)
        reload_backend
        reload_frontend
        ;;
    *)
        err "사용법: bash reload.sh [frontend|backend|all]"
        exit 1
        ;;
esac

echo ""
log "완료! $(date '+%H:%M:%S')"
echo ""
