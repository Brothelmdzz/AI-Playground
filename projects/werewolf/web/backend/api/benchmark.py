# ==================== Benchmark API ====================
"""Benchmark 管理 API"""

from fastapi import APIRouter, HTTPException

from ..models.schemas import BenchmarkRequest, BenchmarkResult
from ..services.benchmark_service import benchmark_service

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


@router.post("", response_model=BenchmarkResult)
async def start_benchmark(request: BenchmarkRequest):
    """启动 Benchmark"""
    session = await benchmark_service.start_benchmark(request)
    return benchmark_service.get_result(session)


@router.get("/{benchmark_id}", response_model=BenchmarkResult)
async def get_benchmark(benchmark_id: str):
    """获取 Benchmark 结果"""
    session = await benchmark_service.get_session(benchmark_id)
    if not session:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark_service.get_result(session)


@router.post("/{benchmark_id}/cancel")
async def cancel_benchmark(benchmark_id: str):
    """取消 Benchmark"""
    success = await benchmark_service.cancel_benchmark(benchmark_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel benchmark")
    return {"message": "Benchmark cancelled"}
