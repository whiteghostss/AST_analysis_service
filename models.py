from pydantic import BaseModel
from typing import List, Optional

class SourceRequest(BaseModel):
    sessionId: str
    method: str

class ASTAnalysisRequest(BaseModel):
    sessionId: str
    method: str

class PackageRequest(BaseModel):
    sessionId: str
    ast_json: Optional[str] = None

class SourceResponse(BaseModel):
    source: str

class ASTAnalysisResponse(BaseModel):
    ast_json: str
    analysis_status: str

class PackageResponse(BaseModel):
    zip_url: str

