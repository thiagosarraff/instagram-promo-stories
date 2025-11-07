"""Amazon Associates affiliate link converter"""

import re
import json
from typing import Dict, Optional
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from playwright.async_api import async_playwright, PlaywrightContextManager

from app_modules.affiliate.base import BaseAffiliateConverter
from app_modules.affiliate.exceptions import (
    ConversionError,
    InvalidLinkError,
    CookieExpiredError,
    AmazonRateLimitError,
    AmazonInvalidSessionError,
    AmazonProductNotFoundError,
    AmazonInvalidAssociateTagError,
    AmazonCaptchaError,
    AmazonAPIError
)
from app_modules.affiliate.logger import affiliate_logger


class AmazonConverter(BaseAffiliateConverter):
    """
    Converter para links de afiliados da Amazon Associates

    Implementação baseada em descoberta realizada em 2025-01-06
    Ver docs/discovery/amazon-discovery.md para detalhes técnicos

    Método: Construção Simples de URL (não requer API complexa)
    Formato: https://amazon.com.br/dp/ASIN?tag=associate-tag-20
    """

    # URL Patterns
    AMAZON_DOMAINS = [
        r'amazon\.com\.br',
        r'amazon\.com',
        r'amzn\.to',  # Amazon URL shortener
    ]

    ASIN_PATTERNS = [
        r'/dp/([A-Z0-9]{10})',           # /dp/ASIN
        r'/gp/product/([A-Z0-9]{10})',   # /gp/product/ASIN
        r'/ASIN/([A-Z0-9]{10})',         # /ASIN/ASIN
    ]

    def __init__(self, cookie_file: str, associate_tag: str):
        """
        Initialize AmazonConverter

        Args:
            cookie_file: Path to JSON file containing Amazon cookies (optional for validation)
            associate_tag: Amazon Associate Tag (Tracking ID) in format: name-tag-20

        Raises:
            AmazonInvalidAssociateTagError: If associate_tag format is invalid
        """
        super().__init__(cookie_file)
        self.marketplace_name = 'amazon'
        self.associate_tag = associate_tag
        self.cookies = None
        self.playwright: Optional[PlaywrightContextManager] = None

        # Validate Associate Tag format
        if not self._validate_associate_tag(associate_tag):
            raise AmazonInvalidAssociateTagError(
                f'Associate Tag inválida: {associate_tag}. '
                f'Formato esperado: nome-tag-20'
            )

        affiliate_logger.info(f'AmazonConverter inicializado com tag: {associate_tag}')

    async def convert_link(self, original_link: str) -> str:
        """
        Convert Amazon product link to affiliate link

        Uses simple URL construction by adding Associate Tag as query parameter.
        Does NOT require Product Advertising API (PA-API).

        Args:
            original_link: Original Amazon product URL

        Returns:
            Affiliate link with Associate Tag

        Raises:
            InvalidLinkError: If not a valid Amazon link
            ConversionError: If ASIN cannot be extracted
        """
        # Validate it's an Amazon link
        if not self._is_amazon_link(original_link):
            raise InvalidLinkError(f'Link não é da Amazon: {original_link}')

        # Validate basic URL format
        self._validate_original_link(original_link)

        # Extract ASIN
        asin = self._extract_asin(original_link)
        if not asin:
            raise ConversionError(
                f'Não foi possível extrair ASIN do link: {original_link}. '
                f'Link pode estar malformado ou não ser de produto.'
            )

        # Build affiliate link (simple URL construction)
        affiliate_link = self._build_affiliate_link(asin)

        # Log successful conversion
        self._log_conversion(original_link, affiliate_link, 'success')
        affiliate_logger.info(
            f'Link Amazon convertido com sucesso: {original_link[:50]}... -> '
            f'{affiliate_link[:50]}...'
        )

        return affiliate_link

    def _build_affiliate_link(self, asin: str) -> str:
        """
        Constrói link de afiliado adicionando Associate Tag

        Amazon permite adicionar tag diretamente na URL:
        https://amazon.com.br/dp/ASIN?tag=associate-tag-20

        Args:
            asin: Amazon Standard Identification Number (10 chars)

        Returns:
            Affiliate link with Associate Tag
        """
        return f'https://amazon.com.br/dp/{asin}?tag={self.associate_tag}'

    async def load_cookies(self) -> Dict:
        """
        Load cookies from JSON file

        Cookies are OPTIONAL for Amazon converter (used only for validation).

        Returns:
            Dictionary with cookie data

        Raises:
            FileNotFoundError: If cookie file doesn't exist
        """
        cookie_path = Path(self.cookie_file)

        if not cookie_path.exists():
            affiliate_logger.warning(
                f'Arquivo de cookies não encontrado: {self.cookie_file}. '
                f'Cookies são opcionais para Amazon. '
                f'Para validação avançada, execute: python generate_amazon_cookies.py'
            )
            return {}

        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)

        # Validate that file contains Associate Tag
        if 'associate_tag' in cookie_data:
            file_tag = cookie_data.get('associate_tag')
            if file_tag != self.associate_tag:
                affiliate_logger.warning(
                    f'Associate Tag mismatch: arquivo={file_tag}, config={self.associate_tag}'
                )

        self.cookies = cookie_data.get('cookies', [])
        affiliate_logger.info(f'Cookies da Amazon carregados: {len(self.cookies)} cookies')

        return cookie_data

    async def validate_cookies(self) -> bool:
        """
        Validate if cookies are still valid

        Cookies are OPTIONAL for Amazon converter.
        This method is provided for advanced validation only.

        Returns:
            True if cookies are valid or not loaded, False otherwise
        """
        if not self.cookies:
            # No cookies loaded, but that's OK for Amazon
            affiliate_logger.info('Cookies não carregados (opcional para Amazon)')
            return True

        # Check for critical cookies
        cookie_dict = {c['name']: c for c in self.cookies}
        critical_cookies = ['session-id', 'ubid-acbbr']

        for cookie_name in critical_cookies:
            if cookie_name not in cookie_dict:
                affiliate_logger.warning(f'Cookie crítico ausente: {cookie_name}')
                return False

        # Check expiration (basic check on expires field)
        import time
        for cookie in self.cookies:
            if 'expires' in cookie:
                if cookie['expires'] < time.time():
                    affiliate_logger.warning(f'Cookie expirado: {cookie["name"]}')
                    return False

        return True

    async def validate_product_exists(self, affiliate_link: str) -> bool:
        """
        OPTIONAL: Validate if product exists on Amazon

        This is an advanced feature that requires Playwright.
        Conversion works without this validation.

        Args:
            affiliate_link: Affiliate link to validate

        Returns:
            True if product exists, False otherwise

        Raises:
            AmazonProductNotFoundError: If product doesn't exist (404)
            AmazonCaptchaError: If CAPTCHA is detected
            AmazonRateLimitError: If rate limit is hit
        """
        try:
            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='pt-BR',
                )

                # Add cookies if available
                if self.cookies:
                    await context.add_cookies(self.cookies)

                page = await context.new_page()
                response = await page.goto(affiliate_link, wait_until='load', timeout=10000)

                status_code = response.status

                # Check for error statuses
                if status_code == 404:
                    await browser.close()
                    raise AmazonProductNotFoundError(f'Produto não encontrado: {affiliate_link}')

                elif status_code in [429, 503]:
                    await browser.close()
                    raise AmazonRateLimitError('Rate limit da Amazon atingido')

                elif status_code == 200:
                    # Check for CAPTCHA
                    content = await page.content()
                    if 'captcha' in content.lower() or 'robot' in content.lower():
                        await browser.close()
                        raise AmazonCaptchaError('CAPTCHA detectado pela Amazon')

                    await browser.close()
                    return True

                else:
                    await browser.close()
                    affiliate_logger.warning(f'Status inesperado da Amazon: {status_code}')
                    return False

        except (AmazonProductNotFoundError, AmazonCaptchaError, AmazonRateLimitError):
            # Re-raise Amazon-specific exceptions
            raise

        except Exception as e:
            affiliate_logger.warning(f'Erro ao validar produto Amazon: {e}')
            # Don't fail conversion on validation errors
            return False

    def _is_amazon_link(self, url: str) -> bool:
        """
        Check if URL is from Amazon

        Args:
            url: URL string to check

        Returns:
            True if URL matches Amazon domain patterns
        """
        return any(re.search(pattern, url) for pattern in self.AMAZON_DOMAINS)

    def _extract_asin(self, url: str) -> Optional[str]:
        """
        Extract ASIN (Amazon Standard Identification Number) from URL

        ASINs are 10-character alphanumeric codes.

        Examples:
            - https://amazon.com.br/dp/B08N5WRWNW
            - https://amazon.com.br/produto-name/dp/B08N5WRWNW/ref=sr_1_1
            - https://amazon.com.br/gp/product/B08N5WRWNW

        Args:
            url: Amazon product URL

        Returns:
            ASIN (e.g., 'B08N5WRWNW') or None if not found
        """
        for pattern in self.ASIN_PATTERNS:
            match = re.search(pattern, url)
            if match:
                asin = match.group(1)
                # Debug log removed - use info in production if needed
                return asin

        # Warning only for invalid URLs
        if len(url) > 50:
            affiliate_logger.warning(f'ASIN não encontrado em: {url[:50]}...')
        else:
            affiliate_logger.warning(f'ASIN não encontrado em: {url}')
        return None

    def _validate_associate_tag(self, tag: str) -> bool:
        """
        Validate Amazon Associate Tag format

        Valid format: nome-tag-20 (word-word-number)
        Examples: promozone-20, tech-store-21, meu123site-20

        Args:
            tag: Associate Tag to validate

        Returns:
            True if format is valid
        """
        # Pattern: alphanumeric + hyphens, ending with -<number>
        # Allows multiple words separated by hyphens
        pattern = r'^[a-zA-Z0-9.]+(-[a-zA-Z0-9.]+)*-\d+$'
        return bool(re.match(pattern, tag))
