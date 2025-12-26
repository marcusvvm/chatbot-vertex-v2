from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CorpusCreate(BaseModel):
    department_name: str = Field(..., description="Nome do departamento (ex: 'Juridico', 'RH')")
    description: Optional[str] = None

class CorpusResponse(BaseModel):
    id: str
    display_name: str
    name: str  # Full resource name
    create_time: Optional[datetime] = None
