"""
Unit tests for FastAPI Instagram Story endpoint
Tests request validation, response structure, and error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import app
from models import PostStoryRequest, PostStoryResponse


client = TestClient(app)


class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check_returns_200(self):
        """Health check should return 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_check_has_timestamp(self):
        """Health check response should include timestamp"""
        response = client.get("/health")
        assert "timestamp" in response.json()


class TestPostStoryValidation:
    """Tests for request validation"""

    def test_valid_request_structure(self):
        """Valid request should be accepted"""
        valid_request = {
            "product_name": "Carregador Apple USB-C 20W",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }
        # Should not raise validation error
        request = PostStoryRequest(**valid_request)
        assert request.product_name == "Carregador Apple USB-C 20W"
        assert request.template_scenario == 1

    def test_missing_product_name(self):
        """Request without product_name should fail"""
        invalid_request = {
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_missing_price(self):
        """Request without price should fail"""
        invalid_request = {
            "product_name": "Product",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_missing_product_image_url(self):
        """Request without product_image_url should fail"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_missing_affiliate_link(self):
        """Request without affiliate_link should fail"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_missing_marketplace_name(self):
        """Request without marketplace_name should fail"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "template_scenario": 1
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_missing_template_scenario(self):
        """Request without template_scenario should fail"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre"
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_invalid_template_scenario_too_low(self):
        """Template scenario must be >= 1"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 0
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_invalid_template_scenario_too_high(self):
        """Template scenario must be <= 4"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 5
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)

    def test_empty_product_name(self):
        """Product name cannot be empty"""
        invalid_request = {
            "product_name": "",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }
        with pytest.raises(ValueError):
            PostStoryRequest(**invalid_request)


class TestResponseModel:
    """Tests for response model structure"""

    def test_success_response_structure(self):
        """Success response should have correct structure"""
        response = PostStoryResponse(
            status="success",
            message="Story posted successfully",
            story_id="123456789",
            error_code=None
        )
        assert response.status == "success"
        assert response.message == "Story posted successfully"
        assert response.story_id == "123456789"
        assert response.error_code is None

    def test_error_response_structure(self):
        """Error response should have correct structure"""
        response = PostStoryResponse(
            status="error",
            message="Failed to render story",
            story_id=None,
            error_code="RENDERING_FAILED"
        )
        assert response.status == "error"
        assert response.message == "Failed to render story"
        assert response.story_id is None
        assert response.error_code == "RENDERING_FAILED"

    def test_response_is_json_serializable(self):
        """Response should be JSON serializable"""
        response = PostStoryResponse(
            status="success",
            message="Test",
            story_id=None,
            error_code=None
        )
        response_dict = response.model_dump()
        assert "status" in response_dict
        assert "message" in response_dict


class TestPostStoryEndpoint:
    """Tests for /post-story endpoint"""

    @patch('app.post_html_story_to_instagram')
    @patch('app.create_html_story')
    def test_successful_post_story(self, mock_create, mock_post):
        """Successful story posting should return 200 with success response"""
        # Mock the existing functions
        mock_create.return_value = ("test_story.jpg", {"x": 0.5, "y": 0.85, "width": 0.6, "height": 0.08})
        mock_post.return_value = True

        valid_request = {
            "product_name": "Carregador Apple USB-C 20W",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }

        response = client.post("/post-story", json=valid_request)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Story posted successfully"

    def test_missing_required_field_returns_422(self):
        """Missing required field should return 422 Unprocessable Entity"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            # Missing product_image_url
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }

        response = client.post("/post-story", json=invalid_request)
        assert response.status_code == 422

    def test_invalid_template_scenario_returns_422(self):
        """Invalid template_scenario should return 422"""
        invalid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 5  # Invalid: > 4
        }

        response = client.post("/post-story", json=invalid_request)
        assert response.status_code == 422

    @patch('app.post_html_story_to_instagram')
    @patch('app.create_html_story')
    def test_story_creation_failure_returns_500(self, mock_create, mock_post):
        """Story creation failure should return 500 with error details"""
        mock_create.return_value = None  # Simulate creation failure

        valid_request = {
            "product_name": "Carregador Apple USB-C 20W",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }

        response = client.post("/post-story", json=valid_request)

        assert response.status_code == 500
        data = response.json()
        # FastAPI wraps HTTPException detail in "detail" key
        detail = data.get("detail", data)
        assert detail["status"] == "error"
        assert detail["error_code"] == "RENDERING_FAILED"

    @patch('app.post_html_story_to_instagram')
    @patch('app.create_html_story')
    def test_instagram_posting_failure_returns_500(self, mock_create, mock_post):
        """Instagram posting failure should return 500 with error details"""
        mock_create.return_value = ("test_story.jpg", {"x": 0.5, "y": 0.85, "width": 0.6, "height": 0.08})
        mock_post.return_value = False  # Simulate posting failure

        valid_request = {
            "product_name": "Carregador Apple USB-C 20W",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }

        response = client.post("/post-story", json=valid_request)

        assert response.status_code == 500
        data = response.json()
        # FastAPI wraps HTTPException detail in "detail" key
        detail = data.get("detail", data)
        assert detail["status"] == "error"
        assert detail["error_code"] == "POSTING_FAILED"

    @patch('app.post_html_story_to_instagram')
    @patch('app.create_html_story')
    def test_response_includes_error_message_on_failure(self, mock_create, mock_post):
        """Error response should include descriptive message"""
        mock_create.return_value = None

        valid_request = {
            "product_name": "Product",
            "price": "R$ 35,41",
            "product_image_url": "https://example.com/product.jpg",
            "affiliate_link": "https://mercadolivre.com.br/product-123",
            "marketplace_name": "mercadolivre",
            "template_scenario": 1
        }

        response = client.post("/post-story", json=valid_request)

        assert response.status_code == 500
        data = response.json()
        # FastAPI wraps HTTPException detail in "detail" key
        detail = data.get("detail", data)
        assert "message" in detail
        assert len(detail["message"]) > 0


class TestMarketplaces:
    """Tests for different marketplace support"""

    def test_mercadolivre_marketplace(self):
        """Should support mercadolivre marketplace"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://mercadolivre.com.br/product-123",
            marketplace_name="mercadolivre",
            template_scenario=1
        )
        assert request.marketplace_name == "mercadolivre"

    def test_amazon_marketplace(self):
        """Should support amazon marketplace"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://amazon.com.br/product-123",
            marketplace_name="amazon",
            template_scenario=2
        )
        assert request.marketplace_name == "amazon"

    def test_custom_marketplace(self):
        """Should support custom marketplace names"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://shop.example.com/product",
            marketplace_name="custom_shop",
            template_scenario=3
        )
        assert request.marketplace_name == "custom_shop"


class TestAllTemplateScenarios:
    """Tests for all template scenarios"""

    def test_template_scenario_1(self):
        """Should accept template_scenario 1"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://example.com/product",
            marketplace_name="test",
            template_scenario=1
        )
        assert request.template_scenario == 1

    def test_template_scenario_2(self):
        """Should accept template_scenario 2"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://example.com/product",
            marketplace_name="test",
            template_scenario=2
        )
        assert request.template_scenario == 2

    def test_template_scenario_3(self):
        """Should accept template_scenario 3"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://example.com/product",
            marketplace_name="test",
            template_scenario=3
        )
        assert request.template_scenario == 3

    def test_template_scenario_4(self):
        """Should accept template_scenario 4"""
        request = PostStoryRequest(
            product_name="Product",
            price="R$ 35,41",
            product_image_url="https://example.com/product.jpg",
            affiliate_link="https://example.com/product",
            marketplace_name="test",
            template_scenario=4
        )
        assert request.template_scenario == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
