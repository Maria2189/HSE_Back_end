import os
import json
from datetime import datetime
from fastapi import APIRouter
from app.schemas.appeals import AppealCreate

router = APIRouter(
    prefix="/appeals",
    tags=["Appeals"]
)

@router.post("/")
async def create_appeal(appeal: AppealCreate):
    appeal_data = appeal.model_dump(mode='json')
    
    save_directory = "appeals_data"
    os.makedirs(save_directory, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"appeal_{appeal.phone.replace('+', '')}_{timestamp}.json"
    filepath = os.path.join(save_directory, filename)
    
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(appeal_data, file, ensure_ascii=False, indent=4)
        
    return {
        "status": "success",
        "message": "Обращение успешно зарегистрировано и сохранено.",
        "file_created": filename,
        "data": appeal_data
    }