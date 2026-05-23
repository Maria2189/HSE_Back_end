from pydantic import BaseModel

class CalculateRequest(BaseModel):
    numbers: list[int]
    delays: list[float]

class CalculationResult(BaseModel):
    number: int
    square: int
    delay: float
    time: float

class CalculateResponse(BaseModel):
    results: list[CalculationResult]
    total_time: float
    parallel_faster_than_sequential: bool