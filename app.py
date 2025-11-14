"""
FastAPI application for Instagram Story automation
Accepts product data via HTTP POST and manages story creation and posting
"""

import logging
import os
import httpx
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from instagrapi import Client

from config import settings, log_configuration
from models import PostStoryRequest, PostStoryResponse, AffiliateConversionStatus, SimpleMediaRequest
from create_promo_story_html import create_html_story
from post_html_story import post_html_story_to_instagram
from app_modules.affiliate.manager import AffiliateManager

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

# Initialize AffiliateManager
affiliate_manager = AffiliateManager()

# Register Mercado Livre converter
from app_modules.affiliate.converters.mercadolivre import MercadoLivreConverter

try:
    ml_converter = MercadoLivreConverter('sessions/ml_cookies.json')
    affiliate_manager.register_converter('mercadolivre', ml_converter)
    logger.info("Mercado Livre converter registered successfully")
except FileNotFoundError:
    logger.warning(
        "Mercado Livre cookies not found. "
        "ML affiliate conversion will not be available. "
        "Run: python generate_ml_cookies.py"
    )
except Exception as e:
    logger.error(f"Failed to register Mercado Livre converter: {e}")

# Register Amazon converter
from app_modules.affiliate.converters.amazon import AmazonConverter
import os

amazon_tag = os.getenv('AMAZON_ASSOCIATE_TAG')
tracking_id = os.getenv('AMAZON_TRACKING_ID')  # Optional tracking ID

# Use tracking ID if specified, otherwise use associate tag
final_tag = tracking_id if tracking_id else amazon_tag

if amazon_tag:
    try:
        # Cookies are OPTIONAL for Amazon (used only for validation)
        amazon_converter = AmazonConverter('sessions/amazon_cookies.json', final_tag)
        affiliate_manager.register_converter('amazon', amazon_converter)
        logger.info(f"Amazon converter registered - Store: {amazon_tag}, Tracking: {tracking_id}" if tracking_id else f"Amazon converter registered with tag: {amazon_tag}")
    except FileNotFoundError:
        logger.info(
            "Amazon cookies not found (optional). "
            "Conversion will work without cookies. "
            "For advanced validation, run: python generate_amazon_cookies.py"
        )
        # Still register converter without cookies (they're optional)
        amazon_converter = AmazonConverter('sessions/amazon_cookies.json', final_tag)
        affiliate_manager.register_converter('amazon', amazon_converter)
        logger.info(f"Amazon converter registered (no cookies) - Store: {amazon_tag}, Tracking: {tracking_id}" if tracking_id else f"Amazon converter registered (no cookies) with tag: {amazon_tag}")
    except Exception as e:
        logger.error(f"Failed to register Amazon converter: {e}")
else:
    logger.warning(
        "AMAZON_ASSOCIATE_TAG not set in environment. "
        "Amazon affiliate conversion will not be available. "
        "Set AMAZON_ASSOCIATE_TAG=your-tag-20 in .env file"
    )

# Register Shopee converter
from app_modules.affiliate.converters.shopee import ShopeeConverter

try:
    # Shopee uses AppID + Secret authentication (no cookies needed)
    shopee_converter = ShopeeConverter(default_sub_id='promozonestories')
    affiliate_manager.register_converter('shopee', shopee_converter)
    logger.info("Shopee converter registered successfully")
except ValueError as e:
    logger.warning(
        f"Shopee credentials not found: {e}. "
        "Shopee affiliate conversion will not be available. "
        "Set SHOPEE_APP_ID and SHOPEE_APP_PASSWORD in .env file"
    )
except Exception as e:
    logger.error(f"Failed to register Shopee converter: {e}")


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


# Simple story posting endpoint (no affiliate processing)
@app.post("/post-story", response_model=PostStoryResponse, status_code=200)
async def post_simple_story(request: SimpleMediaRequest) -> PostStoryResponse:
    """
    Post a simple media story to Instagram without affiliate processing

    Downloads media from provided URL and posts directly to Instagram.
    No affiliate link conversion or promotional overlays.

    Args:
        request: SimpleMediaRequest with media_url and optional media_type

    Returns:
        PostStoryResponse with status, message, and story_id (if successful)

    Raises:
        HTTPException(400): If validation or download fails
        HTTPException(500): If posting fails
    """
    request_id = f"{datetime.now(timezone.utc).timestamp()}"
    temp_media_path = None

    try:
        # Log incoming request
        logger.info(f"[{request_id}] Received simple story request: {request.media_url}")

        # Get Instagram credentials
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

        # Step 1: Download media from URL
        logger.info(f"[{request_id}] Downloading media from URL...")
        try:
            # Determine file extension from URL
            url_lower = request.media_url.lower()
            if url_lower.endswith(('.mp4', '.mov', '.avi')):
                file_ext = '.mp4'
                detected_type = 'video'
            elif url_lower.endswith(('.jpg', '.jpeg', '.png')):
                file_ext = '.jpg'
                detected_type = 'photo'
            else:
                # Default to photo if can't determine
                file_ext = '.jpg'
                detected_type = 'photo'
                logger.warning(f"[{request_id}] Could not determine media type from URL, defaulting to photo")

            # Use provided media_type or auto-detected
            media_type = request.media_type if request.media_type else detected_type

            # Create temporary file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_media_path = f"temp_simple_story_{timestamp}{file_ext}"

            # Download media
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(request.media_url)
                response.raise_for_status()

                # Save to temporary file
                with open(temp_media_path, 'wb') as f:
                    f.write(response.content)

            logger.info(f"[{request_id}] Media downloaded successfully: {temp_media_path} (type: {media_type})")

        except httpx.HTTPStatusError as e:
            logger.error(f"[{request_id}] Failed to download media (HTTP {e.response.status_code}): {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": f"Failed to download media from URL: HTTP {e.response.status_code}",
                    "error_code": "DOWNLOAD_FAILED"
                }
            )
        except Exception as e:
            logger.error(f"[{request_id}] Error downloading media: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": f"Failed to download media: {str(e)}",
                    "error_code": "DOWNLOAD_FAILED"
                }
            )

        # Step 2: Login to Instagram
        logger.info(f"[{request_id}] Logging in to Instagram...")
        cl = Client()

        # Session management (same pattern as post_html_story_to_instagram)
        session_dir = os.getenv('INSTAGRAM_SESSION_PATH', 'sessions')
        os.makedirs(session_dir, exist_ok=True)
        session_file = os.path.join(session_dir, f"session_{instagram_username}.json")

        try:
            if os.path.exists(session_file):
                logger.info(f"[{request_id}] Loading saved Instagram session...")
                cl.load_settings(session_file)
                cl.login(instagram_username, instagram_password)
                logger.info(f"[{request_id}] Instagram login successful (saved session)")
            else:
                logger.info(f"[{request_id}] First Instagram login - saving session...")
                cl.login(instagram_username, instagram_password)
                cl.dump_settings(session_file)
                logger.info(f"[{request_id}] Instagram login successful (new session saved)")
        except Exception as e:
            logger.error(f"[{request_id}] Instagram login failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": f"Instagram authentication failed: {str(e)}",
                    "error_code": "AUTH_FAILED"
                }
            )

        # Step 3: Post to Instagram
        logger.info(f"[{request_id}] Posting {media_type} to Instagram...")
        try:
            if media_type == 'video':
                story = cl.video_upload_to_story(temp_media_path)
            else:  # photo
                story = cl.photo_upload_to_story(temp_media_path)

            story_id = str(story.pk)
            logger.info(f"[{request_id}] Story posted successfully (ID: {story_id})")

        except Exception as e:
            logger.error(f"[{request_id}] Failed to post story to Instagram: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": f"Failed to post story: {str(e)}",
                    "error_code": "POSTING_FAILED"
                }
            )

        # Success response
        logger.info(f"[{request_id}] Simple story request completed successfully")
        return PostStoryResponse(
            status="success",
            message="Story posted successfully",
            story_id=story_id,
            error_code=None,
            affiliate_conversion_status=None  # No affiliate processing for simple stories
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
    finally:
        # Cleanup: Remove temporary media file
        if temp_media_path and os.path.exists(temp_media_path):
            try:
                os.remove(temp_media_path)
                logger.info(f"[{request_id}] Cleaned up temporary file: {temp_media_path}")
            except Exception as e:
                logger.warning(f"[{request_id}] Failed to cleanup temporary file: {str(e)}")


# Affiliate story posting endpoint
@app.post("/create-post-affiliate-story", response_model=PostStoryResponse, status_code=200)
async def create_post_affiliate_story(request: PostStoryRequest) -> PostStoryResponse:
    """
    Create and post a promotional affiliate story to Instagram

    Accepts product data, converts affiliate link, generates promotional story image with overlays,
    and posts to Instagram account.

    Args:
        request: PostStoryRequest with product details including affiliate link

    Returns:
        PostStoryResponse with status, message, story_id, and affiliate conversion status

    Raises:
        HTTPException(400): If validation fails
        HTTPException(500): If rendering or posting fails
    """

    request_id = f"{datetime.now(timezone.utc).timestamp()}"

    try:
        # Log incoming request (without sensitive data)
        logger.info(f"[{request_id}] Received request for product: {request.product_name}")
        logger.debug(f"[{request_id}] Template: {request.template_scenario}, Marketplace: {request.marketplace_name}")

        # Step 0: Convert affiliate link (if possible)
        logger.info(f"[{request_id}] Converting affiliate link...")
        conversion_result = await affiliate_manager.convert_link(request.affiliate_link)

        # Use converted link (or original if fallback)
        final_link = conversion_result['link']

        if conversion_result['status'] == 'fallback':
            logger.warning(f"[{request_id}] Affiliate conversion failed, using original link: {conversion_result['error']}")
        else:
            logger.info(f"[{request_id}] Affiliate link converted successfully")

        # Auto-select template scenario if not provided
        if request.template_scenario is None:
            # Template selection logic based on available data:
            # Scenario 1: Basic (only price)
            # Scenario 2: With coupon (price + coupon_code)
            # Scenario 3: With discount (price + price_old)
            # Scenario 4: Complete (price + price_old + coupon_code)

            has_old_price = request.price_old is not None and request.price_old.strip() != ""
            has_coupon = request.coupon_code is not None and request.coupon_code.strip() != ""

            if has_old_price and has_coupon:
                template_scenario = 4  # Complete: old price + coupon
            elif has_coupon:
                template_scenario = 2  # With coupon only
            elif has_old_price:
                template_scenario = 3  # With discount only
            else:
                template_scenario = 1  # Basic

            logger.info(f"[{request_id}] Auto-selected template scenario: {template_scenario} "
                       f"(old_price={has_old_price}, coupon={has_coupon})")
        else:
            template_scenario = request.template_scenario
            # Validate template scenario if provided
            if template_scenario not in [1, 2, 3, 4]:
                logger.warning(f"[{request_id}] Invalid template_scenario: {template_scenario}")
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
            # Use custom headline or default
            headline = request.headline if request.headline else "OFERTA IMPERDÍVEL"

            result = await create_html_story(
                product_image_path=request.product_image_url,  # URL will be downloaded by create_html_story
                headline=headline,
                product_name=request.product_name,
                price_new=request.price,
                price_old=request.price_old,  # Optional field from request
                coupon_code=request.coupon_code,  # Optional field from request
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
            success, story_id = await post_html_story_to_instagram(
                username=instagram_username,
                password=instagram_password,
                product_image_path=request.product_image_url,
                headline=headline,  # Use same headline from step 1
                product_name=request.product_name,
                price_new=request.price,
                price_old=request.price_old,  # Optional field from request
                coupon_code=request.coupon_code,  # Optional field from request
                source=request.marketplace_name,
                product_url=final_link,  # Use converted link
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

            logger.info(f"[{request_id}] Story posted successfully to Instagram (ID: {story_id})")

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
            story_id=story_id,
            error_code=None,
            affiliate_conversion_status=AffiliateConversionStatus(
                status=conversion_result['status'],
                marketplace=conversion_result['marketplace'],
                error=conversion_result['error']
            )
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
