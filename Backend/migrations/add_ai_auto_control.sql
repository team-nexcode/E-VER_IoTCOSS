-- AI 자동 제어 필드 추가
ALTER TABLE device_mac ADD COLUMN IF NOT EXISTS ai_auto_control BOOLEAN DEFAULT FALSE NOT NULL;

-- 기존 레코드에 기본값 설정
UPDATE device_mac SET ai_auto_control = FALSE WHERE ai_auto_control IS NULL;

-- 인덱스 추가 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_device_mac_ai_auto_control ON device_mac(ai_auto_control) WHERE ai_auto_control = TRUE;
