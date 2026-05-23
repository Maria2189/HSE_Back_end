import asyncio
import time
from fastapi import APIRouter
from app.schemas.homework import CalculateRequest, CalculateResponse, CalculationResult

router = APIRouter(tags=["Homework 1"])

async def process_number(number: int, delay: float) -> CalculationResult:
    start_time = time.time()
    
    # Имитация асинхронной задержки
    await asyncio.sleep(delay)
    
    end_time = time.time()
    
    return CalculationResult(
        number=number,
        square=number ** 2,
        delay=delay,
        time=round(end_time - start_time, 2)
    )

@router.post("/calculate/", response_model=CalculateResponse)
async def calculate_squares(request: CalculateRequest):
    start_total = time.time()
    
    tasks = [
        process_number(num, delay) 
        for num, delay in zip(request.numbers, request.delays)
    ]
    results = await asyncio.gather(*tasks)
    
    end_total = time.time()
    total_time = round(end_total - start_total, 2)
    
    sequential_time = sum(request.delays)
    
    return CalculateResponse(
        results=results,
        total_time=total_time,
        parallel_faster_than_sequential=total_time < sequential_time
    )