from pydantic import BaseModel
from typing import Optional

class DocumentUploadResponse(BaseModel):
    rag_file_id: str
    gcs_uri: str
    display_name: str
    corpus_id: str
    status: Optional[str] = "imported"
