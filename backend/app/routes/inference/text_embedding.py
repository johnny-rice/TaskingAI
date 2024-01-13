from fastapi import APIRouter, Depends, Request
from common.database.postgres.pool import postgres_db_pool
from typing import Dict
from ..utils import auth_info_required, check_http_error
from app.schemas.inference.text_embedding import TextEmbeddingRequest, TextEmbeddingResponse
from common.services.inference.text_embedding import text_embedding
from common.services.model.model import get_model
from common.models import Model, ModelSchema, ModelType
from common.error import raise_http_error, ErrorCode

router = APIRouter()


@router.post(
    "/inference/text_embedding",
    summary="Text Embedding",
    operation_id="text_embedding",
    tags=["Inference"],
    responses={422: {"description": "Unprocessable Entity"}},
    description="Model inference for text embedding.",
    response_model=TextEmbeddingResponse,
)
async def api_text_embedding(
    request: Request,
    data: TextEmbeddingRequest,
    auth_info: Dict = Depends(auth_info_required),
    postgres_conn=Depends(postgres_db_pool.get_db_connection),
):
    # validate model
    model: Model = await get_model(
        postgres_conn=postgres_conn,
        model_id=data.model_id,
    )

    # validate model type
    model_schema: ModelSchema = model.model_schema()
    if not model_schema.type == ModelType.TEXT_EMBEDDING:
        raise_http_error(
            error_code=ErrorCode.REQUEST_VALIDATION_ERROR,
            message=f"Model {model.model_id} is not a text embedding model",
        )

    # generate none stream response
    response = await text_embedding(
        provider_id=model_schema.provider_id,
        provider_model_id=model_schema.provider_model_id,
        credentials=model.encrypted_credentials,  # todo: use decrypted_credentials
        input_text_list=data.input,
        input_type=data.input_type,
    )
    check_http_error(response)
    return TextEmbeddingResponse(data=response.json()["data"])
