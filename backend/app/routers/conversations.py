"""
대화 기록 API 라우터
--------------------
- POST   /api/conversations       대화 저장
- GET    /api/conversations       목록 조회 (messages 미포함, 가벼운 목록)
- GET    /api/conversations/{id}  특정 대화 전체 messages 조회 (불러오기)
- DELETE /api/conversations/{id}  대화 삭제
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import ConversationCreate
from ..services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", summary="대화 저장", status_code=201)
def create_conversation(payload: ConversationCreate):
    messages = [m.model_dump() for m in payload.messages]
    return conversation_service.create_conversation(payload.title, messages)


@router.get("", summary="대화 목록 조회 (messages 미포함)")
def list_conversations():
    # 목록 응답에는 messages를 포함하지 않는다(가벼움). 전체는 상세 조회로.
    return conversation_service.list_conversations(include_messages=False)


@router.get("/{doc_id}", summary="특정 대화 전체 조회 (불러오기)")
def get_conversation(doc_id: str):
    conv = conversation_service.get_conversation(doc_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return conv


@router.delete("/{doc_id}", summary="대화 삭제")
def delete_conversation(doc_id: str):
    ok = conversation_service.delete_conversation(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return {"deleted": True, "id": doc_id}
