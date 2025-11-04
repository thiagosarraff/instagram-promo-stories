"""
FastAPI application for Instagram Story automation
Accepts product data via HTTP POST and manages story creation and posting
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from config import settings, log_configuration
from models import PostStoryRequest, PostStoryResponse
from create_promo_story_html import create_html_story
from post_html_story import post_html_story_to_instagram

# Configure logging with settings
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_requests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log configuration on startup
log_configuration()

# Create FastAPI application
app = FastAPI(
    title="Instagram Story Automation API",
    description="API endpoint for posting promotional stories to Instagram via n8n integration",
    version="1.0.0"
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    Returns 200 OK if service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Main story posting endpoint
@app.post("/post-story", response_model=PostStoryResponse, status_code=200)
async def post_story(request: PostStoryRequest) -> PostStoryResponse:
    """
    Create and post a promotional story to Instagram

    Accepts product data, generates story image, and posts to Instagram account.

    Args:
        request: PostStoryRequest with product details

    Returns:
        PostStoryResponse with status, message, and story_id (if successful)

    Raises:
        HTTPException(400): If validation fails
        HTTPException(500): If rendering or posting fails
    """

    request_id = f"{datetime.now(timezone.utc).timestamp()}"

    try:
        # Log incoming request (without sensitive data)
        logger.info(f"[{request_id}] Received request for product: {request.product_name}")
        logger.debug(f"[{request_id}] Template: {request.template_scenario}, Marketplace: {request.marketplace_name}")

        # Validate template scenario
        if request.template_scenario not in [1, 2, 3, 4]:
            logger.warning(f"[{request_id}] Invalid template_scenario: {request.template_scenario}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid template_scenario. Must be 1, 2, 3, or 4",
                    "error_code": "VALIDATION_ERROR"
                }
            )

        # Get Instagram credentials from configuration
        try:
            instagram_username = settings.instagram_username
            instagram_password = settings.instagram_password.get_secret_value()
        except Exception as e:
            logger.error(f"[{request_id}] Configuration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Server configuration error: Missing Instagram credentials",
                    "error_code": "CONFIG_ERROR"
                }
            )

        # Generate output path for story image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"story_api_{timestamp}.jpg"

        # Step 1: Create story image
        logger.info(f"[{request_id}] Creating story image...")
        try:
            result = await create_html_story(
                product_image_path=request.product_image_url,  # URL will be downloaded by create_html_story
                headline="OFERTA IMPERDÍVEL",  # Standard headline
                product_name=request.product_name,
                price_new=request.price,
                price_old=None,  # Not provided in request
                coupon_code=None,  # Not provided in request
                source=request.marketplace_name,
                output_path=output_path
            )

            if not result or result[0] is None:
                story_path = None
            else:
                story_path, coords = result

            if not story_path:
                logger.error(f"[{request_id}] Failed to create story image")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "status": "error",
                        "message": "Failed to create story image from product data",
                        "error_code": "RENDERING_FAILED"
                    }
                )

            logger.info(f"[{request_id}] Story image created successfully: {story_path}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error creating story image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": f"Failed to create story image: {str(e)}",
                    "error_code": "RENDERING_FAILED"
                }
            )

        # Step 2: Post to Instagram
        logger.info(f"[{request_id}] Posting to Instagram...")
        try:
            success = post_html_story_to_instagram(
                username=instagram_username,
                password=instagram_password,
                product_image_path=request.product_image_url,
                headline="OFERTA IMPERDÍVEL",
                product_name=request.product_name,
                price_new=request.price,
                price_old=None,
                coupon_code=None,
                source=request.marketplace_name,
                product_url=request.affiliate_link,
                output_path=output_path
            )

            if not success:
                logger.error(f"[{request_id}] Instagram posting returned False")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "status": "error",
                        "message": "Failed to post story to Instagram",
                        "error_code": "POSTING_FAILED"
                    }
                )

            logger.info(f"[{request_id}] Story posted successfully to Instagram")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error posting to Instagram: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": f"Failed to post to Instagram: {str(e)}",
                    "error_code": "POSTING_FAILED"
                }
            )

        # Success response
        logger.info(f"[{request_id}] Request completed successfully")
        return PostStoryResponse(
            status="success",
            message="Story posted successfully",
            story_id=None,  # instagrapi doesn't return story ID easily
            error_code=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
        )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors gracefully"""
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": str(exc),
            "error_code": "VALIDATION_ERROR"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Instagram Story API on {settings.api_host}:{settings.api_port}")
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
