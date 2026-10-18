"""
Firebase(Firestore) 연동 모듈
-----------------------------
- 서비스 계정 키는 환경 변수로만 주입한다. (코드/저장소에 절대 포함하지 않음)
- 두 가지 주입 방식을 지원한다.
  1) FIREBASE_SERVICE_ACCOUNT_JSON : 키 JSON '내용'을 통째로 문자열로 넣는 방식 (Render 등 배포에 편리)
  2) GOOGLE_APPLICATION_CREDENTIALS : 키 파일 '경로'를 넣는 방식 (로컬 개발에 편리)
- get_db()는 최초 호출 시점에 한 번만 초기화한다(지연 초기화).
"""

import json
import firebase_admin
from firebase_admin import credentials, firestore

from .config import settings

_db = None  # 싱글턴 Firestore 클라이언트


def get_db():
    """Firestore 클라이언트를 반환한다. 최초 1회만 초기화."""
    global _db
    if _db is not None:
        return _db

    if not firebase_admin._apps:  # 아직 앱이 초기화되지 않았다면
        if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
            # 방식 1: JSON 문자열
            cred_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
            cred = credentials.Certificate(cred_dict)
        elif settings.FIREBASE_CREDENTIALS_PATH:
            # 방식 2: 파일 경로
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        else:
            raise RuntimeError(
                "Firebase 자격 증명이 없습니다. "
                "FIREBASE_SERVICE_ACCOUNT_JSON 또는 GOOGLE_APPLICATION_CREDENTIALS "
                "환경 변수를 설정하세요."
            )
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db


# 컬렉션 이름 상수
COLLECTION_DATA = "data"                 # 분석 데이터 저장
COLLECTION_CONVERSATIONS = "conversations"  # 대화 기록 저장
