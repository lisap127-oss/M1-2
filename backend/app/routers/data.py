"""
데이터 API 라우터
-----------------
CRUD 4개 + summary 1개 + (보너스) statistics 1개.
경로 순서 주의: /summary, /statistics 를 /{doc_id} 보다 먼저 선언해야
'summary'가 id로 잘못 매칭되지 않는다.
"""

from fastapi import APIRouter, HTTPException
from ..models.schemas import DataCreate, DataUpdate
from ..services import data_service

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/summary", summary="데이터 요약 (프롬프트 주입용)")
def get_summary():
    return data_service.get_summary()


@router.get("/statistics", summary="확장 통계 (보너스)")
def get_statistics():
    return data_service.get_statistics()


@router.post("", summary="새 데이터 추가", status_code=201)
def create_data(payload: DataCreate):
    return data_service.create_data(payload.model_dump())


@router.get("", summary="데이터 목록 조회")
def list_data():
    return data_service.list_data()


@router.put("/{doc_id}", summary="데이터 수정")
def update_data(doc_id: str, payload: DataUpdate):
    updated = data_service.update_data(doc_id, payload.model_dump())
    if updated is None:
        raise HTTPException(status_code=404, detail="해당 데이터를 찾을 수 없습니다.")
    return updated


@router.delete("/{doc_id}", summary="데이터 삭제")
def delete_data(doc_id: str):
    ok = data_service.delete_data(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="해당 데이터를 찾을 수 없습니다.")
    return {"deleted": True, "id": doc_id}
