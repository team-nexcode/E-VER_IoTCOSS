"""
AI 전력 분석 API 라우터
외부 AI API에서 이상치/대기전력 데이터를 받아 OpenAI로 분석합니다.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import httpx

from app.database import get_db
from app.models.device import Device
from app.config import get_settings

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

router = APIRouter(prefix="/api/ai", tags=["AI 분석"])
logger = logging.getLogger(__name__)
settings = get_settings()


# ==================== Schemas ====================

class AnomalyDevice(BaseModel):
    """이상치 디바이스 정보"""
    device_mac: str
    device_name: str
    timestamp: datetime
    current_amp: float
    expected_amp: float
    deviation_percent: float
    severity: str  # "low", "medium", "high"


class StandbyPowerDevice(BaseModel):
    """대기전력 낭비 디바이스 정보"""
    device_mac: str
    device_name: str
    avg_standby_power_watts: float
    daily_waste_kwh: float
    monthly_waste_kwh: float
    monthly_waste_cost: int  # 원


class AIReportData(BaseModel):
    """AI 분석 원본 데이터"""
    anomalies: List[AnomalyDevice]
    standby_power_devices: List[StandbyPowerDevice]
    total_anomaly_count: int
    total_standby_waste_kwh: float
    total_standby_waste_cost: int


class OpenAIAnalysisResponse(BaseModel):
    """OpenAI 분석 결과"""
    summary: str
    recommendations: List[str]
    anomaly_insights: str
    standby_insights: str
    estimated_savings: str


# ==================== AI Report Data 생성 ====================

async def get_ai_report_data(db: AsyncSession) -> AIReportData:
    """
    전력 데이터를 분석하여 이상치와 대기전력 낭비를 탐지합니다.
    실제 AI 서버가 있다면 해당 API를 호출하고, 없으면 로컬 분석을 수행합니다.
    """
    
    # 1. 외부 AI 서버 호출 시도
    if settings.AI_REPORT_URL and settings.AI_REPORT_URL != "http://localhost:5000":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.AI_REPORT_URL}/api/report")
                if response.status_code == 200:
                    data = response.json()
                    return AIReportData(**data)
        except Exception as e:
            logger.warning(f"외부 AI 서버 호출 실패, 로컬 분석으로 전환: {e}")
    
    # 2. 로컬 분석 (외부 AI 서버가 없거나 실패한 경우)
    anomalies = await detect_anomalies(db)
    standby_devices = await analyze_standby_power(db)
    
    total_standby_waste_kwh = sum(d.monthly_waste_kwh for d in standby_devices)
    total_standby_waste_cost = sum(d.monthly_waste_cost for d in standby_devices)
    
    return AIReportData(
        anomalies=anomalies,
        standby_power_devices=standby_devices,
        total_anomaly_count=len(anomalies),
        total_standby_waste_kwh=round(total_standby_waste_kwh, 2),
        total_standby_waste_cost=total_standby_waste_cost
    )


async def detect_anomalies(db: AsyncSession) -> List[AnomalyDevice]:
    """이상치 탐지: 최근 24시간 데이터에서 급격한 전류 변화 감지"""
    anomalies = []
    
    # 최근 24시간 데이터 조회
    since = datetime.now() - timedelta(hours=24)
    
    # 디바이스별 평균 전류 계산
    result = await db.execute(
        select(
            Device.device_mac,
            func.avg(Device.energy_amp).label('avg_amp'),
            func.stddev(Device.energy_amp).label('stddev_amp'),
            func.max(Device.energy_amp).label('max_amp'),
        )
        .where(
            Device.timestamp >= since,
            Device.energy_amp.isnot(None),
            Device.energy_amp > 0
        )
        .group_by(Device.device_mac)
    )
    
    device_stats = result.all()
    
    # 각 디바이스에서 이상치 찾기
    for mac, avg_amp, stddev_amp, max_amp in device_stats:
        if not stddev_amp or stddev_amp == 0:
            continue
        
        # 최근 데이터에서 3σ 이상 벗어난 값 찾기
        threshold = avg_amp + (3 * stddev_amp)
        
        anomaly_result = await db.execute(
            select(Device)
            .where(
                Device.device_mac == mac,
                Device.timestamp >= since,
                Device.energy_amp > threshold
            )
            .order_by(Device.timestamp.desc())
            .limit(5)
        )
        
        anomaly_records = anomaly_result.scalars().all()
        
        for record in anomaly_records:
            deviation = ((record.energy_amp - avg_amp) / avg_amp) * 100
            
            # 심각도 판단
            if deviation > 200:
                severity = "high"
            elif deviation > 100:
                severity = "medium"
            else:
                severity = "low"
            
            anomalies.append(AnomalyDevice(
                device_mac=record.device_mac,
                device_name=record.device_name or "Unknown",
                timestamp=record.timestamp,
                current_amp=round(record.energy_amp, 2),
                expected_amp=round(avg_amp, 2),
                deviation_percent=round(deviation, 1),
                severity=severity
            ))
    
    return anomalies[:10]  # 상위 10개만 반환


async def analyze_standby_power(db: AsyncSession) -> List[StandbyPowerDevice]:
    """대기전력 분석: OFF 상태에서 소비되는 전력 계산"""
    standby_devices = []
    
    # 최근 7일간 데이터 조회
    since = datetime.now() - timedelta(days=7)
    
    # 디바이스별로 OFF 상태 전력 소비 분석
    result = await db.execute(
        select(
            Device.device_mac,
            Device.device_name,
            func.avg(Device.energy_amp).label('avg_amp')
        )
        .where(
            Device.timestamp >= since,
            Device.relay_status == "off",  # OFF 상태
            Device.energy_amp.isnot(None),
            Device.energy_amp > 0.01  # 최소 대기전력 기준
        )
        .group_by(Device.device_mac, Device.device_name)
        .having(func.avg(Device.energy_amp) > 0.05)  # 평균 50mA 이상
    )
    
    standby_data = result.all()
    
    for mac, name, avg_amp in standby_data:
        # 대기 전력 계산 (W = V × A)
        avg_standby_watts = avg_amp * 220.0
        
        # 일일 낭비량 (kWh) = W × 24h / 1000
        daily_waste_kwh = (avg_standby_watts * 24) / 1000
        
        # 월간 낭비량
        monthly_waste_kwh = daily_waste_kwh * 30
        
        # 월간 낭비 비용 (원) - 전기요금 약 300원/kWh 가정
        monthly_waste_cost = int(monthly_waste_kwh * 300)
        
        standby_devices.append(StandbyPowerDevice(
            device_mac=mac,
            device_name=name or "Unknown",
            avg_standby_power_watts=round(avg_standby_watts, 2),
            daily_waste_kwh=round(daily_waste_kwh, 3),
            monthly_waste_kwh=round(monthly_waste_kwh, 2),
            monthly_waste_cost=monthly_waste_cost
        ))
    
    # 낭비량 많은 순으로 정렬
    standby_devices.sort(key=lambda x: x.monthly_waste_kwh, reverse=True)
    
    return standby_devices[:10]  # 상위 10개만 반환


# ==================== OpenAI 분석 ====================

async def analyze_with_openai(report_data: AIReportData) -> OpenAIAnalysisResponse:
    """OpenAI를 사용하여 전력 분석 리포트 생성"""
    
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        )
    
    if not AsyncOpenAI:
        raise HTTPException(
            status_code=500,
            detail="openai 패키지가 설치되지 않았습니다. pip install openai를 실행하세요."
        )
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # 프롬프트 생성
    prompt = f"""IoT 스마트 콘센트 전력 모니터링 데이터를 분석하여 사용자가 이해하기 쉬운 리포트를 작성해주세요.

## 분석 데이터

### 이상치 감지
- 감지된 이상치: {report_data.total_anomaly_count}건
{_format_anomalies(report_data.anomalies[:5])}

### 대기전력 낭비
- 월간 낭비량: {report_data.total_standby_waste_kwh} kWh
- 월간 낭비 비용: {report_data.total_standby_waste_cost:,}원
{_format_standby_devices(report_data.standby_power_devices[:5])}

## 작성 가이드

다음 형식으로 **구조화된 분석**을 작성하세요:

### 1. 전체 요약 (2-3문장)
현재 전력 사용 상황을 한눈에 파악할 수 있도록 핵심만 간결하게 요약하세요.
예시: "최근 24시간 동안 4건의 이상 전류가 감지되었으며, 대기전력으로 월 58Wh(약 17원)가 낭비되고 있습니다. 전반적으로 양호하나 일부 기기의 점검이 필요합니다."

### 2. 이상치 인사이트
- 이상치가 발생한 기기와 시간대
- 예상 원인 (센서 오류, 부하 급등, 릴레이 문제 등)
- 심각도 판단 (정상 범위 vs 즉시 조치 필요)

### 3. 대기전력 인사이트
- 대기전력이 높은 기기 목록
- 실제 낭비되는 금액의 의미 (커피 한 잔 값, 월 전기요금의 X% 등)
- 패턴 분석 (항상 켜진 상태, 간헐적 사용 등)

### 4. 개선 권장사항 (3-5개)
**실행 가능한 구체적인 조치**를 제시하세요. 각 항목은 명령형으로 시작하세요.
예시:
- "온풍기는 사용 후 반드시 전원을 차단하세요"
- "대기전력이 높은 TV는 멀티탭 스위치로 완전 차단하세요"
- "이상 전류가 반복되는 전기히터는 전문가 점검을 받으세요"

### 5. 예상 절감 효과
권장사항을 실행했을 때의 구체적인 절감 효과를 숫자로 제시하세요.
예시: "대기전력을 모두 차단하면 월 최대 17원, 연간 약 200원을 절약할 수 있습니다."

## 작성 시 주의사항
- 전문 용어는 쉬운 말로 풀어쓰세요 (예: "정격 전류 초과" → "전기를 너무 많이 사용")
- 숫자는 구체적으로 제시하되, 비유를 섞어 이해를 도우세요
- 부정적인 표현보다 개선 가능성을 강조하세요
- 기술적 설명보다 행동 지침에 집중하세요"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 IoT 전력 관리 전문가이자 친절한 AI 어시스턴트입니다. "
                        "복잡한 전력 데이터를 일반 사용자가 이해하기 쉽게 설명하고, "
                        "실행 가능한 절약 방법을 제안합니다. 항상 긍정적이고 도움이 되는 톤으로 작성하세요."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # 응답 파싱 (구조화된 형태로 변환)
        return _parse_openai_response(analysis_text, report_data)
        
    except Exception as e:
        logger.error(f"OpenAI API 호출 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"OpenAI 분석 중 오류가 발생했습니다: {str(e)}"
        )


def _format_anomalies(anomalies: List[AnomalyDevice]) -> str:
    """이상치 목록을 텍스트로 포맷팅"""
    if not anomalies:
        return "이상치가 감지되지 않았습니다."
    
    lines = []
    for a in anomalies:
        lines.append(
            f"- {a.device_name} ({a.device_mac}): "
            f"{a.current_amp}A (예상: {a.expected_amp}A, "
            f"편차: +{a.deviation_percent}%, 심각도: {a.severity})"
        )
    return "\n".join(lines)


def _format_standby_devices(devices: List[StandbyPowerDevice]) -> str:
    """대기전력 디바이스 목록을 텍스트로 포맷팅"""
    if not devices:
        return "대기전력 낭비가 감지되지 않았습니다."
    
    lines = []
    for d in devices:
        lines.append(
            f"- {d.device_name}: {d.avg_standby_power_watts}W "
            f"→ 월 {d.monthly_waste_kwh}kWh ({d.monthly_waste_cost:,}원 낭비)"
        )
    return "\n".join(lines)


def _parse_openai_response(text: str, report_data: AIReportData) -> OpenAIAnalysisResponse:
    """OpenAI 응답을 구조화된 형태로 파싱"""
    lines = text.split("\n")
    
    summary = []
    recommendations = []
    anomaly_insights = []
    standby_insights = []
    estimated_savings = []
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 섹션 구분
        if "요약" in line or "전체" in line:
            current_section = "summary"
            continue
        elif "이상치" in line:
            current_section = "anomaly"
            continue
        elif "대기전력" in line:
            current_section = "standby"
            continue
        elif "권장" in line or "개선" in line:
            current_section = "recommendations"
            continue
        elif "절감" in line or "효과" in line:
            current_section = "savings"
            continue
        
        # 내용 추가
        if current_section == "summary":
            summary.append(line)
        elif current_section == "anomaly":
            anomaly_insights.append(line)
        elif current_section == "standby":
            standby_insights.append(line)
        elif current_section == "recommendations":
            if line.startswith("-") or line.startswith("•") or line[0].isdigit():
                recommendations.append(line.lstrip("-•0123456789. "))
        elif current_section == "savings":
            estimated_savings.append(line)
    
    return OpenAIAnalysisResponse(
        summary=" ".join(summary) if summary else text[:200],
        recommendations=recommendations[:5] if recommendations else [
            "이상치가 발견된 디바이스의 사용 패턴을 확인하세요.",
            "대기전력이 높은 디바이스는 사용하지 않을 때 전원을 차단하세요.",
            "스케줄 기능을 활용하여 자동으로 전원을 관리하세요."
        ],
        anomaly_insights=" ".join(anomaly_insights) if anomaly_insights else 
            f"{report_data.total_anomaly_count}개의 이상치가 감지되었습니다. "
            "예상보다 높은 전력 소비가 발생하고 있습니다.",
        standby_insights=" ".join(standby_insights) if standby_insights else
            f"월 {report_data.total_standby_waste_kwh}kWh의 대기전력이 낭비되고 있습니다. "
            f"이는 약 {report_data.total_standby_waste_cost:,}원의 전기요금에 해당합니다.",
        estimated_savings=" ".join(estimated_savings) if estimated_savings else
            f"대기전력을 차단하면 월 최대 {report_data.total_standby_waste_cost:,}원을 절약할 수 있습니다."
    )


# ==================== API Endpoints ====================

@router.get("/report", summary="AI 전력 분석 리포트 데이터 조회")
async def get_ai_report(db: AsyncSession = Depends(get_db)):
    """
    전력 데이터를 분석하여 이상치와 대기전력 낭비를 탐지합니다.
    OpenAI 분석 전 원본 데이터를 제공합니다.
    """
    report_data = await get_ai_report_data(db)
    return report_data


@router.get("/analyze", response_model=OpenAIAnalysisResponse, summary="OpenAI 전력 분석")
async def analyze_power_with_ai(db: AsyncSession = Depends(get_db)):
    """
    AI 리포트 데이터를 OpenAI에 전달하여 사용자 친화적인 분석 결과를 생성합니다.
    """
    # 1. AI 리포트 데이터 생성
    report_data = await get_ai_report_data(db)
    
    # 2. OpenAI로 분석
    analysis = await analyze_with_openai(report_data)
    
    return analysis


@router.get("/full-report", summary="전체 분석 리포트 (데이터 + AI 분석)")
async def get_full_analysis_report(db: AsyncSession = Depends(get_db)):
    """
    AI 리포트 데이터와 OpenAI 분석을 함께 반환합니다.
    """
    report_data = await get_ai_report_data(db)
    analysis = await analyze_with_openai(report_data)
    
    return {
        "report_data": report_data,
        "ai_analysis": analysis,
        "generated_at": datetime.now().isoformat()
    }
