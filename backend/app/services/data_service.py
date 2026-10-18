"""
데이터(학습 시간 기록) 서비스
-----------------------------
Firestore의 `data` 컬렉션에 대한 CRUD와, AI 프롬프트 주입에 쓸 '요약(summary)'
및 보너스용 '통계(statistics)'를 계산한다.

라우터(HTTP 레이어)와 분리해, 비즈니스 로직을 이 파일에 모은다.
→ 테스트/재사용이 쉽고, 라우터는 요청/응답 변환만 담당한다.
"""

from datetime import datetime
from statistics import mean, pstdev

from ..firebase import get_db, COLLECTION_DATA


# ---------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------
def create_data(payload: dict) -> dict:
    """새 데이터 추가."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_DATA).document()
    item = {
        "date": payload["date"],
        "value": float(payload["value"]),
        "memo": payload.get("memo", "") or "",
        "created_at": datetime.utcnow().isoformat(),
    }
    doc_ref.set(item)
    return {"id": doc_ref.id, **_public_fields(item)}


def list_data() -> list:
    """데이터 목록 조회 (날짜 오름차순)."""
    db = get_db()
    docs = db.collection(COLLECTION_DATA).stream()
    items = [{"id": d.id, **_public_fields(d.to_dict())} for d in docs]
    items.sort(key=lambda x: x["date"])
    return items


def update_data(doc_id: str, payload: dict) -> dict | None:
    """데이터 수정. 존재하지 않으면 None 반환."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_DATA).document(doc_id)
    snap = doc_ref.get()
    if not snap.exists:
        return None
    # None이 아닌 필드만 갱신
    updates = {k: v for k, v in payload.items() if v is not None}
    if "value" in updates:
        updates["value"] = float(updates["value"])
    doc_ref.update(updates)
    merged = {**snap.to_dict(), **updates}
    return {"id": doc_id, **_public_fields(merged)}


def delete_data(doc_id: str) -> bool:
    """데이터 삭제. 성공 여부 반환."""
    db = get_db()
    doc_ref = db.collection(COLLECTION_DATA).document(doc_id)
    if not doc_ref.get().exists:
        return False
    doc_ref.delete()
    return True


# ---------------------------------------------------------------
# 요약 / 통계
# ---------------------------------------------------------------
def get_summary() -> dict:
    """
    프롬프트 주입용 요약 정보.
    기간, 개수, 기본 통계(합/평균/최대/최소), 최근 추세를 계산한다.
    """
    items = list_data()
    if not items:
        return {
            "period": "데이터 없음",
            "count": 0,
            "metrics": {"total": 0, "average": 0, "max": 0, "min": 0},
            "trend": "데이터가 없어 추세를 계산할 수 없습니다.",
        }

    values = [it["value"] for it in items]
    dates = [it["date"] for it in items]

    metrics = {
        "total": round(sum(values), 1),
        "average": round(mean(values), 1),
        "max": round(max(values), 1),
        "min": round(min(values), 1),
    }

    return {
        "period": f"{min(dates)} ~ {max(dates)}",
        "count": len(items),
        "metrics": metrics,
        "trend": _trend_text(values),
    }


def get_statistics() -> dict:
    """
    (보너스) 요약을 넘어선 추가 지표.
    - 표준편차(꾸준함 지표)
    - 요일별 평균
    - 프론트 차트용 일별 시계열(series)
    - 7일 이동평균 series
    """
    items = list_data()
    if not items:
        return {"count": 0, "series": [], "moving_average_7": [],
                "weekday_average": {}, "std_dev": 0}

    values = [it["value"] for it in items]
    series = [{"date": it["date"], "value": it["value"]} for it in items]

    # 7일 이동평균
    ma7 = []
    for i in range(len(values)):
        window = values[max(0, i - 6): i + 1]
        ma7.append({"date": items[i]["date"], "value": round(mean(window), 1)})

    # 요일별 평균 (0=월 ... 6=일)
    weekday_names = ["월", "화", "수", "목", "금", "토", "일"]
    buckets = {name: [] for name in weekday_names}
    for it in items:
        try:
            wd = datetime.fromisoformat(it["date"]).weekday()
            buckets[weekday_names[wd]].append(it["value"])
        except ValueError:
            continue
    weekday_average = {
        name: round(mean(vals), 1) if vals else 0 for name, vals in buckets.items()
    }

    return {
        "count": len(items),
        "std_dev": round(pstdev(values), 1) if len(values) > 1 else 0,
        "weekday_average": weekday_average,
        "series": series,
        "moving_average_7": ma7,
    }


# ---------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------
def _public_fields(item: dict) -> dict:
    """응답에 노출할 필드만 추린다(created_at 등 내부 필드 제외)."""
    return {
        "date": item.get("date", ""),
        "value": float(item.get("value", 0)),
        "memo": item.get("memo", ""),
    }


def _trend_text(values: list) -> str:
    """
    최근 추세를 간단히 판정한다.
    최근 구간 평균과 그 이전 구간 평균을 비교해 증가/감소/유지를 판단한다.
    """
    n = len(values)
    if n < 4:
        return "데이터가 적어 추세 판단이 어렵습니다."

    half = n // 2
    prev_avg = mean(values[:half])
    recent_avg = mean(values[half:])
    if prev_avg == 0:
        return "유지"

    change = (recent_avg - prev_avg) / prev_avg * 100
    if change > 5:
        return f"상승 (최근 구간 평균 +{change:.0f}%)"
    elif change < -5:
        return f"하락 (최근 구간 평균 {change:.0f}%)"
    else:
        return f"유지 (변동 {change:+.0f}%)"
