"""
AI 챗봇 API 라우터
------------------
POST /api/chat
동작 흐름:
  1) 데이터 요약 조회 (ai_service 내부에서 수행)
  2) 요약을 시스템 프롬프트에 주입
  3) GPT 호출
  4) (사용자 메시지 + AI 응답)을 conversations에 자동 저장
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest, ChatResponse
from ..services import ai_service, conversation_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse, summary="AI 대화 (컨텍스트 주입)")
def chat(payload: ChatRequest):
    # 이어지는 대화라면 이전 메시지를 불러와 문맥으로 사용
    history = []
    if payload.conversation_id:
        prev = conversation_service.get_conversation(payload.conversation_id)
        if prev:
            history = prev.get("messages", [])

    try:
        reply = ai_service.chat(payload.message, history=history)
    except RuntimeError as e:
        # 예: OPENAI_API_KEY 미설정
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 호출 실패: {e}")

    # 대화 자동 저장
    user_msg = {"role": "user", "content": payload.message}
    ai_msg = {"role": "assistant", "content": reply}
    conv_id = conversation_service.append_and_save(
        payload.conversation_id, user_msg, ai_msg
    )

    return ChatResponse(reply=reply, conversation_id=conv_id)
