"""
환경 변수 설정 모듈
------------------
민감한 값(OpenAI 키, Firebase 서비스 계정 키)은 절대 코드에 하드코딩하지 않고
환경 변수(.env 또는 배포 플랫폼의 Environment)에서 읽어온다.
"""

import os
from dotenv import load_dotenv

# 로컬 개발 시 .env 파일을 읽는다. (배포 환경에서는 플랫폼 환경변수를 사용)
load_dotenv()


class Settings:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    # 비용 방어: 응답 토큰 상한
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "500"))

    # Firebase
    # 서비스 계정 키를 JSON '문자열' 그대로 넣는 방식(FIREBASE_SERVICE_ACCOUNT_JSON)과
    # 파일 경로로 넣는 방식(GOOGLE_APPLICATION_CREDENTIALS) 둘 다 지원한다.
    FIREBASE_SERVICE_ACCOUNT_JSON: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # CORS 허용 도메인 (쉼표로 구분). 예: "http://localhost:5500,https://myapp.vercel.app"
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")

    @property
    def allowed_origins_list(self):
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
