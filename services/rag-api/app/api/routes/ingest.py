"""Document ingest endpoint."""

from fastapi import APIRouter, UploadFile, File
from app.models.schemas import IngestResponse
from app.ingest.pipeline import IngestPipeline

router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    pipeline = IngestPipeline()
    result = await pipeline.run_from_upload(file)
    return result
