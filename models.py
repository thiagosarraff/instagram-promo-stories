"""
Pydantic request/response models for FastAPI endpoint
Provides type safety and automatic validation for HTTP requests
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class SimpleMediaRequest(BaseModel):
    """
    Request model for simple /post-story endpoint
    Accepts media URL for direct posting without affiliate processing
    """
    media_url: str = Field(
        ...,
        description="URL of the media to post (image or video from linksdobarone.shop)"
    )
    media_type: Optional[str] = Field(
        None,
        description="Media type: 'photo' or 'video'. Auto-detected if not provided"
    )

    @field_validator('media_type')
    @classmethod
    def validate_media_type(cls, v):
        if v is not None and v not in ['photo', 'video']:
            raise ValueError('media_type must be "photo" or "video"')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "media_url": "https://linksdobarone.shop/media/story_20250114.jpg"
                },
                {
                    "media_url": "https://linksdobarone.shop/media/promo_video.mp4",
                    "media_type": "video"
                }
            ]
        }
    }


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
    headline: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Headline text at the top of the story (e.g., 'OFERTA IMPERDÍVEL'). Optional - defaults to 'OFERTA IMPERDÍVEL'"
    )
    template_scenario: Optional[int] = Field(
        None,
        ge=1,
        le=4,
        description="Template scenario (1-4). Optional - will be auto-selected if not provided"
    )
    price_old: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Old/strikethrough price (e.g., 'R$ 48,50'). Optional - shows discount if provided"
    )
    coupon_code: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Coupon code (e.g., 'PROMO10'). Optional - displays coupon section if provided"
    )

    @field_validator('headline', 'price_old', 'coupon_code', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        """Convert empty strings to None for optional fields"""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @field_validator('template_scenario')
    @classmethod
    def validate_template(cls, v):
        if v is not None and v not in [1, 2, 3, 4]:
            raise ValueError('template_scenario must be 1, 2, 3, or 4')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_name": "Carregador Apple USB-C 20W",
                    "price": "R$ 35,41",
                    "product_image_url": "https://example.com/product.jpg",
                    "affiliate_link": "https://mercadolivre.com.br/product-123",
                    "marketplace_name": "mercadolivre",
                    "headline": "OFERTA RELÂMPAGO"
                },
                {
                    "product_name": "Fone de Ouvido Bluetooth Sony",
                    "price": "R$ 89,90",
                    "price_old": "R$ 129,90",
                    "product_image_url": "https://example.com/fone.jpg",
                    "affiliate_link": "https://amazon.com.br/fone-sony",
                    "marketplace_name": "amazon",
                    "coupon_code": "TECH15",
                    "headline": "PROMOÇÃO BLACK FRIDAY"
                },
                {
                    "product_name": "Smart TV 50 polegadas",
                    "price": "1899.00",
                    "price_old": "2499.00",
                    "product_image_url": "https://example.com/tv.jpg",
                    "affiliate_link": "https://magalu.com/tv-50",
                    "marketplace_name": "magalu",
                    "headline": "OFERTA ESPECIAL"
                }
            ]
        }
    }


class AffiliateConversionStatus(BaseModel):
    """Affiliate link conversion status details"""
    status: str = Field(
        ...,
        description="Conversion status: 'success' or 'fallback'"
    )
    marketplace: str = Field(
        ...,
        description="Detected marketplace identifier"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if conversion failed"
    )


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
    affiliate_conversion_status: Optional[AffiliateConversionStatus] = Field(
        None,
        description="Affiliate link conversion status"
    )

    model_config = {
        "json_schema_extra": {
            "example_success": {
                "status": "success",
                "message": "Story posted successfully",
                "story_id": "12345678901234567",
                "error_code": None,
                "affiliate_conversion_status": {
                    "status": "success",
                    "marketplace": "mercadolivre",
                    "error": None
                }
            },
            "example_error": {
                "status": "error",
                "message": "Failed to render story image",
                "story_id": None,
                "error_code": "RENDERING_FAILED",
                "affiliate_conversion_status": None
            }
        }
    }
