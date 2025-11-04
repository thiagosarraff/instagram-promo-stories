"""
Pydantic request/response models for FastAPI endpoint
Provides type safety and automatic validation for HTTP requests
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class PostStoryRequest(BaseModel):
    """
    Request model for /post-story endpoint
    Validates all required product data for story generation and posting
    """
    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the product"
    )
    price: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Current price (e.g., 'R$ 35,41')"
    )
    product_image_url: str = Field(
        ...,
        description="URL of the product image"
    )
    affiliate_link: str = Field(
        ...,
        description="Affiliate/product link for story swipe-up"
    )
    marketplace_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Marketplace name (e.g., 'mercadolivre', 'amazon')"
    )
    template_scenario: int = Field(
        ...,
        ge=1,
        le=4,
        description="Template scenario (1-4)"
    )

    @field_validator('template_scenario')
    @classmethod
    def validate_template(cls, v):
        if v not in [1, 2, 3, 4]:
            raise ValueError('template_scenario must be 1, 2, 3, or 4')
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_name": "Carregador Apple USB-C 20W",
                "price": "R$ 35,41",
                "product_image_url": "https://example.com/product.jpg",
                "affiliate_link": "https://mercadolivre.com.br/product-123",
                "marketplace_name": "mercadolivre",
                "template_scenario": 1
            }
        }
    }


class PostStoryResponse(BaseModel):
    """
    Response model for /post-story endpoint
    Returns status and details about the posting operation
    """
    status: str = Field(
        ...,
        description="Status of operation: 'success' or 'error'"
    )
    message: str = Field(
        ...,
        description="Human-readable message about the operation"
    )
    story_id: Optional[str] = Field(
        None,
        description="Instagram story ID if successful"
    )
    error_code: Optional[str] = Field(
        None,
        description="Error code if failed: VALIDATION_ERROR, RENDERING_FAILED, POSTING_FAILED"
    )

    model_config = {
        "json_schema_extra": {
            "example_success": {
                "status": "success",
                "message": "Story posted successfully",
                "story_id": "12345678901234567",
                "error_code": None
            },
            "example_error": {
                "status": "error",
                "message": "Failed to render story image",
                "story_id": None,
                "error_code": "RENDERING_FAILED"
            }
        }
    }
