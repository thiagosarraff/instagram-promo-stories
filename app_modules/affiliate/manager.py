"""Affiliate Manager - orchestrates conversion across multiple marketplaces"""

from typing import Dict, Optional
from urllib.parse import urlparse
from app_modules.affiliate.base import BaseAffiliateConverter
from app_modules.affiliate.exceptions import MarketplaceNotSupportedError
from app_modules.affiliate.logger import affiliate_logger


class AffiliateManager:
    """
    Manages affiliate link conversion across multiple marketplaces

    Responsibilities:
    - Register marketplace-specific converters
    - Detect marketplace from URL
    - Delegate conversion to appropriate converter
    - Implement fallback mechanism for failed conversions
    """

    def __init__(self):
        """Initialize AffiliateManager with empty converter registry"""
        self._converters: Dict[str, BaseAffiliateConverter] = {}

    def register_converter(self, marketplace: str, converter: BaseAffiliateConverter):
        """
        Register a marketplace converter

        Args:
            marketplace: Marketplace identifier (e.g., 'mercadolivre', 'amazon')
            converter: Instance of BaseAffiliateConverter subclass
        """
        self._converters[marketplace] = converter
        affiliate_logger.logger.info(f"Registered converter for marketplace: {marketplace}")

    def detect_marketplace(self, url: str) -> Optional[str]:
        """
        Detect marketplace from URL domain

        Args:
            url: Product URL

        Returns:
            Marketplace identifier or None if not recognized

        Supported marketplaces:
        - mercadolivre.com.br -> 'mercadolivre'
        - amazon.com.br -> 'amazon'
        - shopee.com.br -> 'shopee'
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove 'www.' prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            # Map domains to marketplace identifiers
            marketplace_map = {
                'mercadolivre.com.br': 'mercadolivre',
                'produto.mercadolivre.com.br': 'mercadolivre',
                'amazon.com.br': 'amazon',
                'www.amazon.com.br': 'amazon',
                'shopee.com.br': 'shopee',
                'www.shopee.com.br': 'shopee',
            }

            # Check for exact match
            if domain in marketplace_map:
                return marketplace_map[domain]

            # Check for partial matches (e.g., subdomains)
            for known_domain, marketplace in marketplace_map.items():
                if known_domain in domain:
                    return marketplace

            return None

        except Exception as e:
            affiliate_logger.logger.error(f"Error detecting marketplace from URL: {e}")
            return None

    async def convert_link(self, original_link: str) -> Dict:
        """
        Convert original link to affiliate link with fallback support

        Args:
            original_link: Original product URL

        Returns:
            Dictionary with conversion result:
            {
                'link': str,              # Converted link or original if fallback
                'status': str,            # 'success' or 'fallback'
                'marketplace': str,       # Marketplace identifier
                'error': Optional[str]    # Error message if fallback
            }
        """
        try:
            # Detect marketplace
            marketplace = self.detect_marketplace(original_link)

            if not marketplace:
                return self._fallback(
                    original_link,
                    'marketplace_not_detected',
                    'Could not detect marketplace from URL'
                )

            # Check if converter is registered
            if marketplace not in self._converters:
                return self._fallback(
                    original_link,
                    marketplace,
                    f'Marketplace not supported yet: {marketplace}'
                )

            # Attempt conversion
            converter = self._converters[marketplace]
            converted_link = await converter.convert_link(original_link)

            # Log success
            affiliate_logger.log_conversion(
                marketplace=marketplace,
                original_link=original_link,
                converted_link=converted_link,
                status='success'
            )

            return {
                'link': converted_link,
                'status': 'success',
                'marketplace': marketplace,
                'error': None
            }

        except Exception as e:
            # Fallback on any error
            marketplace = self.detect_marketplace(original_link) or 'unknown'
            return self._fallback(original_link, marketplace, str(e))

    def _fallback(self, original_link: str, marketplace: str, error: str) -> Dict:
        """
        Handle fallback when conversion fails

        Returns original link with fallback status and logs warning

        Args:
            original_link: Original product URL
            marketplace: Marketplace identifier
            error: Error description

        Returns:
            Fallback response dictionary
        """
        # Log fallback
        affiliate_logger.log_conversion(
            marketplace=marketplace,
            original_link=original_link,
            converted_link=None,
            status='fallback',
            error=error
        )

        return {
            'link': original_link,
            'status': 'fallback',
            'marketplace': marketplace,
            'error': error
        }

    def list_registered_marketplaces(self) -> list:
        """
        Get list of registered marketplace identifiers

        Returns:
            List of marketplace names that have converters registered
        """
        return list(self._converters.keys())
