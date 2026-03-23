"""Document ingest endpoint."""

from fastapi import APIRouter, File, UploadFile

from app.ingest.pipeline import IngestPipeline
from app.models.schemas import IngestResponse

router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    pipeline = IngestPipeline()
    result = await pipeline.run_from_upload(file)
    return result
