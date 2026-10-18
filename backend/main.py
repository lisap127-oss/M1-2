"""
FastAPI 앱 진입점
-----------------
- 앱 초기화
- CORS 설정 (프론트엔드 도메인 허용)
- 라우터 등록
- Swagger UI: 실행 후 /docs 에서 확인

로컬 실행:
    uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import data, conversations, chat

app = FastAPI(
    title="나만의 학습 시간 AI 비서 API",
    description="학습 시간 데이터를 이해하고 맞춤형으로 답하는 AI 비서 백엔드",
    version="1.0.0",
)

# CORS: 배포된 프론트엔드(Vercel)와 로컬 개발 서버에서의 호출을 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/", tags=["health"], summary="헬스 체크")
def root():
    return {
        "status": "ok",
        "service": "study-ai-assistant",
        "docs": "/docs",
    }
