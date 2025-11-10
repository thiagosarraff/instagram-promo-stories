"""
Shopee Affiliate Converter - Official Open API Implementation

This converter uses Shopee's official Open API to generate affiliate short links.

Official API Documentation:
https://affiliate.shopee.com.br/open_api/list?type=short_link

Authentication:
- Uses AppID and Secret Key
- SHA256 signature: SHA256(AppId + Timestamp + Payload + Secret)
- Header format: Authorization: SHA256 Credential={AppID}, Signature={signature}, Timestamp={timestamp}

Example:
    converter = ShopeeConverter(app_id='123456', app_secret='your_secret_key')
    short_link = await converter.convert_link('https://shopee.com.br/product-i.123.456')
    # Returns: https://s.shopee.com.br/XXXXX
"""

import os
import json
import time
import hashlib
import httpx
import re
from typing import Optional, Dict
from app_modules.affiliate.base import BaseAffiliateConverter
from app_modules.affiliate.exceptions import (
    ConversionError,
    InvalidLinkError,
    ShopeeInvalidLinkError,
    ShopeeAPIError,
    ShopeeRateLimitError,
    ShopeeInvalidSessionError
)


class ShopeeConverter(BaseAffiliateConverter):
    """
    Shopee Affiliate Converter using official Open API

    Converts Shopee product URLs to affiliate short links using
    the official GraphQL API with SHA256 signature authentication.
    """

    # API Configuration
    API_ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"

    # Shopee domains
    SHOPEE_DOMAINS = [
        'shopee.com.br',
        's.shopee.com.br',
        'shope.ee'
    ]

    def __init__(self, cookie_file: str = None, app_id: str = None, app_secret: str = None, default_sub_id: str = 'promozonestories'):
        """
        Initialize Shopee converter with API credentials

        Args:
            cookie_file: Legacy parameter, not used (kept for compatibility)
            app_id: Shopee App ID (from environment or parameter)
            app_secret: Shopee App Secret (from environment or parameter)
            default_sub_id: Default tracking ID for sub_id[0] (default: 'promozonestories')
        """
        # Initialize parent (even though we don't use cookie_file)
        super().__init__(cookie_file or 'sessions/shopee_cookies.json')

        self.marketplace_name = 'shopee'

        # Get credentials from environment or parameters
        # Use explicit None check to allow empty strings (for testing)
        self.app_id = app_id if app_id is not None else os.getenv('SHOPEE_APP_ID')
        self.app_secret = app_secret if app_secret is not None else os.getenv('SHOPEE_APP_PASSWORD')

        # Validate credentials (only when not explicitly set to empty for testing)
        if app_id is None and app_secret is None:
            # Normal usage - require credentials from env
            if not self.app_id or not self.app_secret:
                raise ValueError(
                    "Shopee credentials not found. "
                    "Set SHOPEE_APP_ID and SHOPEE_APP_PASSWORD in .env file or pass as parameters."
                )

        self.default_sub_id = default_sub_id

        # HTTP client
        self.client = httpx.AsyncClient(timeout=30.0)

    async def convert_link(self, original_link: str) -> str:
        """
        Convert Shopee product URL to affiliate short link

        Args:
            original_link: Original Shopee product URL

        Returns:
            Affiliate short link (https://s.shopee.com.br/XXXXX)

        Raises:
            ShopeeInvalidLinkError: If link is not from Shopee
            ShopeeAPIError: If API request fails
            ShopeeRateLimitError: If rate limit exceeded
        """
        # Validate Shopee link
        if not self._is_shopee_link(original_link):
            error_msg = f"Link não é da Shopee: {original_link}"
            self._log_conversion(original_link, None, 'error', error_msg)
            raise ShopeeInvalidLinkError(error_msg)

        # Validate URL format
        try:
            self._validate_original_link(original_link)
        except InvalidLinkError as e:
            self._log_conversion(original_link, None, 'error', str(e))
            raise ShopeeInvalidLinkError(f"URL malformada: {original_link}") from e

        try:
            # Generate affiliate short link using official API
            short_link = await self._generate_short_link(original_link)

            # Log success
            self._log_conversion(original_link, short_link, 'success')

            return short_link

        except ShopeeRateLimitError:
            # Rate limit error - use fallback
            self._log_conversion(original_link, original_link, 'fallback', 'Rate limit exceeded')
            return original_link

        except Exception as e:
            # Any other error - use fallback
            error_msg = f"Erro na conversão Shopee: {str(e)}"
            self._log_conversion(original_link, original_link, 'fallback', error_msg)
            return original_link

    async def _generate_short_link(self, original_url: str) -> str:
        """
        Generate short link using Shopee Official GraphQL API

        Args:
            original_url: Original product URL

        Returns:
            Short link from API response

        Raises:
            ShopeeAPIError: If API request fails
            ShopeeRateLimitError: If rate limit exceeded
        """
        # Create GraphQL mutation with proper newlines
        mutation = (
            "mutation {\n"
            "    generateShortLink(input: {\n"
            f"        originUrl: \"{original_url}\",\n"
            f"        subIds: [\"{self.default_sub_id}\", \"\", \"\", \"\", \"\"]\n"
            "    }) {\n"
            "        shortLink\n"
            "    }\n"
            "}"
        )

        # Create payload
        payload = {
            "query": mutation
        }

        # Generate timestamp (Unix timestamp in seconds)
        timestamp = str(int(time.time()))

        # Generate signature
        signature = self._generate_signature(payload, timestamp)

        # Create authorization header
        auth_header = f"SHA256 Credential={self.app_id}, Signature={signature}, Timestamp={timestamp}"

        # Make request
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }

        try:
            response = await self.client.post(
                self.API_ENDPOINT,
                headers=headers,
                json=payload
            )

            # Check for rate limiting
            if response.status_code == 429:
                raise ShopeeRateLimitError("Rate limit excedido pela API da Shopee")

            # Check for authentication errors
            if response.status_code == 401:
                raise ShopeeInvalidSessionError(
                    "Credenciais inválidas. Verifique SHOPEE_APP_ID e SHOPEE_APP_PASSWORD no .env"
                )

            # Check for other errors
            if response.status_code != 200:
                raise ShopeeAPIError(
                    f"API retornou status {response.status_code}: {response.text}"
                )

            # Parse response (httpx uses synchronous json())
            data = response.json()

            # Extract short link from response
            if 'data' in data and 'generateShortLink' in data['data']:
                short_link = data['data']['generateShortLink']['shortLink']
                return short_link

            # Check for errors in response
            if 'errors' in data:
                error_msg = data['errors'][0].get('message', 'Unknown error')
                raise ShopeeAPIError(f"GraphQL error: {error_msg}")

            # Unexpected response format
            raise ShopeeAPIError(f"Formato de resposta inesperado: {data}")

        except httpx.RequestError as e:
            raise ShopeeAPIError(f"Erro de rede ao chamar API da Shopee: {str(e)}") from e

    def _generate_signature(self, payload: Dict, timestamp: str) -> str:
        """
        Generate SHA256 signature for API authentication

        Formula: SHA256(AppId + Timestamp + Payload + Secret)

        Args:
            payload: Request payload (dict)
            timestamp: Unix timestamp (string)

        Returns:
            Hexadecimal signature string
        """
        # Convert payload to JSON string using COMPACT format (no spaces)
        # Shopee API requires compact JSON format for signature validation
        # Format: {"key":"value"} without spaces after : and ,
        payload_str = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))

        # Concatenate: AppId + Timestamp + Payload + Secret
        signature_base = f"{self.app_id}{timestamp}{payload_str}{self.app_secret}"

        # Generate SHA256 hash
        signature = hashlib.sha256(signature_base.encode('utf-8')).hexdigest()

        return signature

    def _is_shopee_link(self, url: str) -> bool:
        """
        Check if URL is from Shopee

        Args:
            url: URL to check

        Returns:
            True if URL is from Shopee
        """
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.SHOPEE_DOMAINS)

    def _extract_product_id(self, url: str) -> Optional[tuple]:
        """
        Extract product ID from Shopee URL

        Format: https://shopee.com.br/PRODUCT-NAME-i.{shop_id}.{item_id}

        Args:
            url: Shopee product URL

        Returns:
            Tuple of (shop_id, item_id) or None if not found
        """
        # Pattern: -i.{shop_id}.{item_id}
        pattern = r'-i\.(\d+)\.(\d+)'
        match = re.search(pattern, url)

        if match:
            return (match.group(1), match.group(2))

        return None

    async def load_cookies(self) -> Dict:
        """
        Legacy method - not used in official API implementation

        Kept for compatibility with BaseAffiliateConverter interface.
        Returns empty dict since we use AppID/Secret authentication.
        """
        return {
            'marketplace': 'shopee',
            'auth_method': 'AppID + Secret (SHA256)',
            'notes': 'This converter uses official API, not cookies'
        }

    async def validate_cookies(self) -> bool:
        """
        Legacy method - not used in official API implementation

        Kept for compatibility with BaseAffiliateConverter interface.
        Validates credentials by checking if AppID and Secret are set.
        """
        return bool(self.app_id and self.app_secret)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
            else:
                loop.run_until_complete(self.close())
        except Exception:
            pass  # Ignore cleanup errors
