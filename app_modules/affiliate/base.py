"""Base abstract class for affiliate converters"""

from abc import ABC, abstractmethod
from typing import Dict
import re
from app_modules.affiliate.exceptions import InvalidLinkError
from app_modules.affiliate.logger import affiliate_logger


class BaseAffiliateConverter(ABC):
    """
    Abstract base class for marketplace affiliate converters

    All marketplace-specific converters must inherit from this class
    and implement the abstract methods.
    """

    def __init__(self, cookie_file: str):
        """
        Initialize converter with cookie file path

        Args:
            cookie_file: Path to JSON file containing authentication cookies
        """
        self.cookie_file = cookie_file
        self.marketplace_name = None  # Must be set by subclass

    @abstractmethod
    async def convert_link(self, original_link: str) -> str:
        """
        Convert original product link to affiliate link

        Args:
            original_link: Original product URL

        Returns:
            Converted affiliate link

        Raises:
            ConversionError: If conversion fails
            InvalidLinkError: If link is malformed
            CookieExpiredError: If authentication cookies are expired
        """
        pass

    @abstractmethod
    async def load_cookies(self) -> Dict:
        """
        Load authentication cookies from JSON file

        Returns:
            Dictionary containing cookie data

        Raises:
            FileNotFoundError: If cookie file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        pass

    @abstractmethod
    async def validate_cookies(self) -> bool:
        """
        Validate if authentication cookies are still valid

        Returns:
            True if cookies are valid, False otherwise
        """
        pass

    def _validate_original_link(self, link: str) -> bool:
        """
        Basic URL validation using regex

        Args:
            link: URL string to validate

        Returns:
            True if link is a valid URL

        Raises:
            InvalidLinkError: If link is malformed
        """
        # Basic URL regex pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',  # path
            re.IGNORECASE
        )

        if not url_pattern.match(link):
            raise InvalidLinkError(f"Invalid URL format: {link}")

        return True

    def _log_conversion(
        self,
        original_link: str,
        converted_link: str,
        status: str,
        error: str = None
    ):
        """
        Log conversion attempt with structured logging

        Args:
            original_link: Original product URL
            converted_link: Converted affiliate link (or None if failed)
            status: Conversion status ('success', 'fallback', 'error')
            error: Optional error message
        """
        affiliate_logger.log_conversion(
            marketplace=self.marketplace_name or 'unknown',
            original_link=original_link,
            converted_link=converted_link,
            status=status,
            error=error
        )
