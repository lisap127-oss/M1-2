"""
대화 기록 서비스
----------------
Firestore의 `conversations` 컬렉션에 대화를 저장/조회/삭제한다.
각 문서는 title, messages(list), created_at 을 가진다.
"""

from datetime import datetime
from ..firebase import get_db, COLLECTION_CONVERSATIONS


def create_conversation(title: str | None, messages: list) -> dict:
    """대화 저장. title이 없으면 첫 사용자 메시지로 자동 생성."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_CONVERSATIONS).document()

    if not title:
        first_user = next((m["content"] for m in messages if m["role"] == "user"), "새 대화")
        title = (first_user[:20] + "...") if len(first_user) > 20 else first_user

    item = {
        "title": title,
        "messages": messages,
        "created_at": datetime.utcnow().isoformat(),
    }
    doc_ref.set(item)
    return {"id": doc_ref.id, **item}


def list_conversations(include_messages: bool = False) -> list:
    """
    대화 목록 조회 (최신순).
    기본은 목록용으로 messages를 제외하고, include_messages=True면 포함한다.
    """
    db = get_db()
    docs = db.collection(COLLECTION_CONVERSATIONS).stream()
    result = []
    for d in docs:
        data = d.to_dict()
        row = {
            "id": d.id,
            "title": data.get("title", ""),
            "created_at": data.get("created_at"),
        }
        if include_messages:
            row["messages"] = data.get("messages", [])
        result.append(row)
    result.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return result


def get_conversation(doc_id: str) -> dict | None:
    """특정 대화의 전체 messages 조회."""
    db = get_db()
    snap = db.collection(COLLECTION_CONVERSATIONS).document(doc_id).get()
    if not snap.exists:
        return None
    data = snap.to_dict()
    return {
        "id": doc_id,
        "title": data.get("title", ""),
        "messages": data.get("messages", []),
        "created_at": data.get("created_at"),
    }


def delete_conversation(doc_id: str) -> bool:
    """대화 삭제."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_CONVERSATIONS).document(doc_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


def append_and_save(conversation_id: str | None, user_msg: dict, ai_msg: dict) -> str:
    """
    챗봇 응답 후 대화를 자동 저장한다.
    - conversation_id가 있으면 해당 대화에 이어붙이고,
    - 없으면 새 대화를 만든다.
    저장된 대화 ID를 반환한다.
    """
    db = get_db()
    if conversation_id:
        ref = db.collection(COLLECTION_CONVERSATIONS).document(conversation_id)
        snap = ref.get()
        if snap.exists:
            messages = snap.to_dict().get("messages", [])
            messages.extend([user_msg, ai_msg])
            ref.update({"messages": messages})
            return conversation_id

    # 새 대화 생성
    created = create_conversation(None, [user_msg, ai_msg])
    return created["id"]
