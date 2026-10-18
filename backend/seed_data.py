"""
샘플 학습 시간 데이터 시딩 스크립트
-----------------------------------
- 최근 약 130일치의 '일별 공부 시간(분)' 데이터를 생성한다. (100개 이상 요구 충족)
- 두 가지 용도로 쓸 수 있다.
  1) --csv     : data/study_time_sample.csv 로 저장만 한다 (Firebase 불필요)
  2) (옵션 없음): Firestore의 data 컬렉션에 실제로 업로드한다 (환경변수 필요)

실행:
    python seed_data.py --csv        # CSV만 생성
    python seed_data.py              # Firestore에 업로드
"""

import sys
import csv
import os
import random
from datetime import date, timedelta

random.seed(42)  # 재현성

DAYS = 130
END = date(2025, 1, 31)
START = END - timedelta(days=DAYS - 1)

SUBJECTS = ["Python", "영어", "알고리즘", "수학", "CS이론", "프로젝트"]


def generate_rows():
    """요일/추세를 반영한 현실적인 학습 시간 데이터를 만든다."""
    rows = []
    d = START
    trend = 0  # 뒤로 갈수록 조금씩 공부량이 느는 완만한 상승 추세
    while d <= END:
        weekday = d.weekday()  # 0=월 ... 6=일
        # 주말엔 공부량이 다소 적고, 평일엔 많게
        base = 150 if weekday < 5 else 90
        noise = random.randint(-40, 50)
        minutes = max(0, round(base + trend + noise))
        # 가끔 아예 공부 안 한 날(0분)도 섞어 현실성 부여
        if random.random() < 0.06:
            minutes = 0
        subject = random.choice(SUBJECTS)
        rows.append({"date": d.isoformat(), "value": minutes, "memo": subject})
        trend += 0.4
        d += timedelta(days=1)
    return rows


def save_csv(rows):
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "study_time_sample.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "value", "memo"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV 저장 완료: {path} ({len(rows)}행)")


def upload_firestore(rows):
    """Firestore data 컬렉션에 업로드한다. (환경변수 설정 필요)"""
    from app.firebase import get_db, COLLECTION_DATA
    from datetime import datetime
    db = get_db()
    col = db.collection(COLLECTION_DATA)
    for r in rows:
        col.add({
            "date": r["date"],
            "value": float(r["value"]),
            "memo": r["memo"],
            "created_at": datetime.utcnow().isoformat(),
        })
    print(f"Firestore 업로드 완료: {len(rows)}건")


if __name__ == "__main__":
    rows = generate_rows()
    if "--csv" in sys.argv:
        save_csv(rows)
    else:
        save_csv(rows)          # CSV도 함께 남기고
        upload_firestore(rows)  # Firestore 업로드
