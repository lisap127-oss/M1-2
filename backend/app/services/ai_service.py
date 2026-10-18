"""
AI 챗봇 서비스 (컨텍스트 주입)
------------------------------
핵심 아이디어: 일반 GPT는 '내 데이터'를 모른다.
그래서 데이터 요약(summary)을 시스템 프롬프트에 삽입(주입)한 뒤 GPT를 호출한다.
→ AI가 사용자의 실제 학습 기록을 반영해 맞춤형으로 답한다.
"""

from openai import OpenAI

from ..config import settings
from . import data_service


def build_system_prompt(summary: dict) -> str:
    """데이터 요약을 시스템 프롬프트에 끼워넣는다."""
    metrics = summary.get("metrics", {})
    return (
        "당신은 사용자의 학습 시간 데이터를 이해하는 학습 코치 AI 비서입니다.\n"
        "아래 [사용자 데이터 요약]을 반드시 근거로 삼아 구체적인 수치와 함께 답하세요.\n"
        "데이터에 없는 내용은 추측하지 말고, 모른다고 솔직히 말하세요. "
        "답변은 한국어로 간결하고 친근하게 합니다.\n\n"
        "[사용자 데이터 요약]\n"
        f"- 데이터 기간: {summary.get('period')}\n"
        f"- 총 기록 수: {summary.get('count')}개\n"
        f"- 총 공부 시간(분): {metrics.get('total')}\n"
        f"- 일 평균(분): {metrics.get('average')}\n"
        f"- 최대(분): {metrics.get('max')} / 최소(분): {metrics.get('min')}\n"
        f"- 최근 추세: {summary.get('trend')}\n"
    )


def chat(user_message: str, history: list | None = None) -> str:
    """
    GPT를 호출해 답변을 생성한다.
    - history: 이어지는 대화의 이전 메시지(optional)
    """
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    # 1) 최신 데이터 요약을 가져온다
    summary = data_service.get_summary()
    system_prompt = build_system_prompt(summary)

    # 2) 메시지 구성: 시스템 프롬프트 + (이전 대화) + 이번 질문
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        # 시스템 메시지는 제외하고 이어붙인다
        messages.extend([m for m in history if m.get("role") in ("user", "assistant")])
    messages.append({"role": "user", "content": user_message})

    # 3) GPT 호출 (비용 방어를 위해 max_tokens 상한 적용)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=messages,
        max_tokens=settings.OPENAI_MAX_TOKENS,
        temperature=0.7,
    )
    return completion.choices[0].message.content.strip()
