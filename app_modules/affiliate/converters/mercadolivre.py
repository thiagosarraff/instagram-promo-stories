"""Mercado Livre affiliate link converter"""

import re
import json
from typing import Dict, Optional
from pathlib import Path
from playwright.async_api import async_playwright, PlaywrightContextManager
from bs4 import BeautifulSoup

from app_modules.affiliate.base import BaseAffiliateConverter
from app_modules.affiliate.exceptions import (
    ConversionError,
    InvalidLinkError,
    CookieExpiredError,
    MLRateLimitError,
    MLInvalidSessionError,
    MLProductNotFoundError,
    MLAPIError
)
from app_modules.affiliate.logger import affiliate_logger


class MercadoLivreConverter(BaseAffiliateConverter):
    """
    Converter para links de afiliados do Mercado Livre

    Implementação baseada em descoberta realizada em 2025-11-05
    Ver docs/discovery/mercadolivre-discovery.md para detalhes técnicos

    API Endpoint: POST https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links
    CSRF Token: Extraído de meta tag HTML em https://produto.mercadolivre.com.br/
    """

    # API Configuration
    API_ENDPOINT = "https://www.mercadolivre.com.br/affiliate-program/api/v2/stripe/user/links"
    CSRF_PAGE = "https://produto.mercadolivre.com.br/"

    # URL Patterns
    ML_DOMAINS = [
        r'mercadolivre\.com\.br',
        r'mercadolivre\.com',  # Short links: mercadolivre.com/sec/xxxxx
        r'mercadolibre\.com',
        r'produto\.mercadolivre\.com\.br',
    ]

    PRODUCT_ID_PATTERNS = [
        r'MLB-?(\d+)',  # MLB-3967173105 or MLB3967173105
    ]

    def __init__(self, cookie_file: str, default_tag: str = "promozonestories"):
        """
        Initialize MercadoLivreConverter

        Args:
            cookie_file: Path to JSON file containing ML cookies
            default_tag: Default tracking tag for affiliate links
        """
        super().__init__(cookie_file)
        self.marketplace_name = 'mercadolivre'
        self.default_tag = default_tag
        self.cookies = None
        self.csrf_token = None
        self.playwright: Optional[PlaywrightContextManager] = None

    async def convert_link(self, original_link: str) -> str:
        """
        Convert Mercado Livre product link to affiliate link

        Args:
            original_link: Original ML product URL

        Returns:
            Affiliate link (short_url from API response)

        Raises:
            InvalidLinkError: If not a valid ML link
            MLInvalidSessionError: If cookies are invalid
            MLRateLimitError: If rate limit is hit
            MLProductNotFoundError: If product doesn't exist
            ConversionError: For other errors
        """
        # Validate it's a ML link
        if not self._is_mercadolivre_link(original_link):
            raise InvalidLinkError(f'Link não é do Mercado Livre: {original_link}')

        # Check if it's already an affiliate link and extract real product URL
        if self._is_affiliate_link(original_link):
            affiliate_logger.info(f'Link de afiliado detectado, extraindo link do produto...')
            original_link = await self._extract_product_link_from_affiliate(original_link)
            affiliate_logger.info(f'Link do produto extraido com sucesso')

        # Validate basic URL format
        self._validate_original_link(original_link)

        # Load cookies if not loaded
        if not self.cookies:
            await self.load_cookies()

        # Validate cookies
        if not await self.validate_cookies():
            raise MLInvalidSessionError('Cookies expirados ou inválidos. Execute generate_ml_cookies.py')

        # Extract CSRF token (cached for session)
        if not self.csrf_token:
            self.csrf_token = await self._extract_csrf_token()

        # Make API request
        try:
            affiliate_link = await self._make_api_request(original_link)
            self._log_conversion(original_link, affiliate_link, 'success')
            return affiliate_link

        except (MLRateLimitError, MLInvalidSessionError, MLProductNotFoundError) as e:
            # Log and re-raise specific errors
            self._log_conversion(original_link, None, 'error', str(e))
            raise

        except Exception as e:
            # Log generic error and fallback to original
            error_msg = f'Erro na conversão ML: {str(e)}'
            self._log_conversion(original_link, original_link, 'fallback', error_msg)
            affiliate_logger.warning(f'{error_msg} - Usando link original')
            return original_link

    async def load_cookies(self) -> Dict:
        """
        Load cookies from JSON file

        Returns:
            Dictionary with cookie data

        Raises:
            FileNotFoundError: If cookie file doesn't exist
        """
        cookie_path = Path(self.cookie_file)

        if not cookie_path.exists():
            raise FileNotFoundError(
                f'Arquivo de cookies não encontrado: {self.cookie_file}\n'
                f'Execute: python generate_ml_cookies.py'
            )

        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)

        self.cookies = cookie_data.get('cookies', [])
        affiliate_logger.info(f'Cookies do ML carregados: {len(self.cookies)} cookies')

        return cookie_data

    async def validate_cookies(self) -> bool:
        """
        Validate if cookies are still valid

        Returns:
            True if valid, False otherwise
        """
        if not self.cookies:
            return False

        # Check for critical cookies
        cookie_dict = {c['name']: c for c in self.cookies}
        critical_cookies = ['ssid', 'nsa_rotok', '_csrf']

        for cookie_name in critical_cookies:
            if cookie_name not in cookie_dict:
                affiliate_logger.warning(f'Cookie crítico ausente: {cookie_name}')
                return False

        # Check JWT expiration (nsa_rotok)
        nsa_token = cookie_dict.get('nsa_rotok', {}).get('value', '')
        if nsa_token:
            try:
                # Decode JWT payload (simple base64 decode, no verification)
                import base64
                payload_part = nsa_token.split('.')[1]
                # Add padding if needed
                payload_part += '=' * (4 - len(payload_part) % 4)
                payload = json.loads(base64.b64decode(payload_part))

                import time
                if payload.get('exp', 0) < time.time():
                    affiliate_logger.warning('JWT token expirado')
                    return False

            except Exception as e:
                affiliate_logger.warning(f'Erro ao validar JWT: {e}')
                return False

        return True

    def _is_mercadolivre_link(self, url: str) -> bool:
        """Check if URL is from Mercado Livre"""
        return any(re.search(pattern, url) for pattern in self.ML_DOMAINS)

    def _extract_product_id(self, url: str) -> Optional[str]:
        """
        Extract product ID from ML URL

        Examples:
            - https://produto.mercadolivre.com.br/MLB-3967173105-...
            - https://www.mercadolivre.com.br/p/MLB3967173105

        Returns:
            Product ID (e.g., 'MLB3967173105') or None
        """
        for pattern in self.PRODUCT_ID_PATTERNS:
            match = re.search(pattern, url)
            if match:
                # Return MLB + digits
                return 'MLB' + match.group(1)

        return None

    def _is_affiliate_link(self, url: str) -> bool:
        """
        Check if URL is already an affiliate link

        Detects:
            - Long format: /social/username?...
            - Short format: /sec/xxxxx
            - Query params: matt_tool=

        Returns:
            True if it's an affiliate link, False otherwise
        """
        return '/social/' in url or '/sec/' in url or 'matt_tool=' in url

    async def _extract_product_link_from_affiliate(self, affiliate_url: str) -> str:
        """
        Extract real product link from affiliate page via scraping

        Handles both:
            - Long affiliate links: https://www.mercadolivre.com.br/social/username?...
            - Short affiliate links: https://mercadolivre.com/sec/xxxxx

        Args:
            affiliate_url: Affiliate link

        Returns:
            Real product URL with MLB code

        Raises:
            ConversionError: If product link cannot be extracted
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )

                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='pt-BR',
                )

                page = await context.new_page()

                affiliate_logger.info(f'Acessando página de afiliado: {affiliate_url}')

                # Navigate to affiliate page
                await page.goto(affiliate_url, wait_until='networkidle', timeout=15000)

                # Wait for page to fully load
                await page.wait_for_timeout(2000)

                # Try multiple strategies to find product link
                product_link = await page.evaluate("""
                    () => {
                        // Strategy 1: Look for direct product links
                        const productSelectors = [
                            'a[href*="produto.mercadolivre.com.br/MLB-"]',
                            'a[href*="/MLB-"]',
                            'a[href*="MLB"]'
                        ];

                        for (const selector of productSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.href.includes('MLB')) {
                                return element.href;
                            }
                        }

                        // Strategy 2: Look for "Ir para produto" button/link
                        const buttonTexts = ['Ir para produto', 'Ver produto', 'Acessar produto'];
                        for (const text of buttonTexts) {
                            const buttons = Array.from(document.querySelectorAll('button, a'));
                            const button = buttons.find(b => b.textContent.trim().includes(text));
                            if (button) {
                                // Check if button is inside a link
                                const link = button.closest('a') || button.parentElement.querySelector('a');
                                if (link && link.href.includes('MLB')) {
                                    return link.href;
                                }
                                // Check if button itself is a link
                                if (button.tagName === 'A' && button.href.includes('MLB')) {
                                    return button.href;
                                }
                            }
                        }

                        // Strategy 3: Find ANY link with MLB code
                        const allLinks = Array.from(document.querySelectorAll('a'));
                        const mlbLink = allLinks.find(a => a.href && /MLB-?\\d+/.test(a.href));
                        if (mlbLink) {
                            return mlbLink.href;
                        }

                        return null;
                    }
                """)

                await browser.close()

                if not product_link:
                    # Log page content for debugging
                    page_content = await page.content()
                    affiliate_logger.error(f'HTML da página (primeiros 1000 chars): {page_content[:1000]}')
                    raise ConversionError(
                        f'Não foi possível extrair link do produto da página de afiliado: {affiliate_url}\n'
                        f'A página pode ter mudado de estrutura ou o link pode estar inválido.'
                    )

                affiliate_logger.info(f'Link do produto extraido: {product_link}')
                return product_link

        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f'Erro ao extrair link de página de afiliado: {e}')

    async def _extract_csrf_token(self) -> str:
        """
        Extract CSRF token from ML page HTML

        Returns:
            CSRF token string

        Raises:
            ConversionError: If token cannot be extracted
        """
        try:
            async with async_playwright() as p:
                # Launch browser with stealth settings to avoid detection
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                    ]
                )

                # Create context with realistic user agent and viewport
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='pt-BR',
                )

                # Add cookies
                await context.add_cookies(self.cookies)

                # Navigate to ML page
                page = await context.new_page()

                # Try multiple possible URLs to extract CSRF token
                csrf_urls_to_try = [
                    'https://produto.mercadolivre.com.br/',
                    'https://www.mercadolivre.com.br/',
                ]

                csrf_token = None

                for url in csrf_urls_to_try:
                    try:
                        await page.goto(url, wait_until='load', timeout=10000)

                        # Wait for JavaScript to execute and meta tags to be inserted
                        await page.wait_for_timeout(2000)

                        # Try to extract CSRF token
                        csrf_token = await page.evaluate(
                            "document.querySelector('meta[name=\"csrf-token\"]')?.content"
                        )

                        if csrf_token:
                            affiliate_logger.info(f'CSRF token extraído de {url}: {csrf_token[:20]}...')
                            break
                        else:
                            # Log for debugging
                            affiliate_logger.warning(f'CSRF token não encontrado em {url}, tentando próxima URL...')

                    except Exception as e:
                        affiliate_logger.warning(f'Falha ao tentar {url}: {e}')
                        continue

                await browser.close()

                if not csrf_token:
                    # Log HTML for debugging
                    affiliate_logger.error('CSRF token não encontrado. Verifique se os cookies estão válidos.')
                    raise ConversionError(
                        'CSRF token não encontrado na página ML. '
                        'Possíveis causas: (1) Cookies expirados, (2) Sessão inválida, '
                        '(3) ML mudou estrutura da página. '
                        'Execute: python generate_ml_cookies.py'
                    )

                return csrf_token

        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f'Erro ao extrair CSRF token: {e}')

    async def _make_api_request(self, original_link: str) -> str:
        """
        Make API request to generate affiliate link

        Args:
            original_link: Original product URL

        Returns:
            Affiliate link (short_url)

        Raises:
            MLRateLimitError: If rate limit hit
            MLInvalidSessionError: If session invalid
            MLProductNotFoundError: If product not found
            MLAPIError: For other API errors
        """
        # Convert cookies list to dict format for request
        cookie_dict = {c['name']: c['value'] for c in self.cookies}

        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'x-csrf-token': self.csrf_token,
            'Origin': 'https://produto.mercadolivre.com.br',
            'Referer': 'https://produto.mercadolivre.com.br/',
        }

        # Prepare payload
        payload = {
            'url': original_link,
            'tag': self.default_tag
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='pt-BR',
                )

                # Add cookies to context
                await context.add_cookies(self.cookies)

                # Make POST request using Playwright's request context
                # Important: Playwright's request.post expects 'data' for JSON
                import json as json_module
                response = await context.request.post(
                    self.API_ENDPOINT,
                    headers=headers,
                    data=json_module.dumps(payload)
                )

                status_code = response.status

                # Log response for debugging
                try:
                    response_body = await response.text()
                    affiliate_logger.info(f'API ML response ({status_code}): {response_body[:500]}')
                except:
                    pass

                # Handle error status codes
                if status_code == 429:
                    await browser.close()
                    raise MLRateLimitError('Rate limit do ML atingido. Aguarde alguns minutos.')

                elif status_code in [401, 403]:
                    await browser.close()
                    raise MLInvalidSessionError(
                        'Sessão inválida ou CSRF token expirado. '
                        'Execute generate_ml_cookies.py novamente.'
                    )

                elif status_code == 404:
                    await browser.close()
                    raise MLProductNotFoundError(f'Produto não encontrado: {original_link}')

                elif status_code != 200:
                    await browser.close()
                    raise MLAPIError(f'Erro da API ML: {status_code}')

                # Parse response
                response_data = await response.json()
                await browser.close()

                # Extract short_url (affiliate link)
                affiliate_link = response_data.get('short_url')

                if not affiliate_link:
                    raise MLAPIError('API não retornou short_url')

                return affiliate_link

        except (MLRateLimitError, MLInvalidSessionError, MLProductNotFoundError, MLAPIError):
            # Re-raise ML-specific exceptions
            raise

        except Exception as e:
            raise ConversionError(f'Erro ao fazer request para API ML: {e}')
