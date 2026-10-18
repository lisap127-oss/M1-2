"""
Pydantic 스키마
---------------
요청 바디를 검증(validation)하기 위한 모델들.
- 잘못된 타입/누락된 필드를 FastAPI가 자동으로 422 에러로 걸러준다.
- 날짜 형식, 값의 범위 등 도메인 규칙도 여기서 강제한다.
"""

from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------
# 데이터(학습 시간 기록) 스키마
# ---------------------------------------------------------------
class DataCreate(BaseModel):
    """새 데이터 추가 요청. (date, value, memo)"""
    date: str = Field(..., description="기록 날짜 (YYYY-MM-DD)", examples=["2025-01-15"])
    value: float = Field(..., ge=0, le=1440, description="공부 시간(분). 0~1440")
    memo: Optional[str] = Field("", max_length=200, description="메모(과목 등)")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        # YYYY-MM-DD 형식인지 확인
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("date는 YYYY-MM-DD 형식이어야 합니다.")
        return v


class DataUpdate(BaseModel):
    """데이터 수정 요청. 일부 필드만 보낼 수 있다."""
    date: Optional[str] = None
    value: Optional[float] = Field(None, ge=0, le=1440)
    memo: Optional[str] = Field(None, max_length=200)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("date는 YYYY-MM-DD 형식이어야 합니다.")
        return v


class DataItem(BaseModel):
    """데이터 응답 모델."""
    id: str
    date: str
    value: float
    memo: str = ""


# ---------------------------------------------------------------
# 대화 기록 스키마
# ---------------------------------------------------------------
class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ConversationCreate(BaseModel):
    """대화 저장 요청."""
    title: Optional[str] = Field(None, max_length=100)
    messages: List[Message] = Field(..., min_length=1)


class ConversationItem(BaseModel):
    id: str
    title: str
    messages: List[Message]
    created_at: Optional[str] = None


# ---------------------------------------------------------------
# 챗봇 스키마
# ---------------------------------------------------------------
class ChatRequest(BaseModel):
    """AI 챗봇 요청."""
    message: str = Field(..., min_length=1, max_length=2000, description="사용자 질문")
    conversation_id: Optional[str] = Field(
        None, description="이어서 대화할 기존 대화 ID (없으면 새 대화 생성)"
    )


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
