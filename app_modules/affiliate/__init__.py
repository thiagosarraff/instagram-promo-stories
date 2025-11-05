"""Affiliate link conversion module"""

from app_modules.affiliate.manager import AffiliateManager
from app_modules.affiliate.base import BaseAffiliateConverter
from app_modules.affiliate.exceptions import (
    AffiliateConversionError,
    InvalidLinkError,
    ConversionError,
    CookieExpiredError,
    MarketplaceNotSupportedError
)

__all__ = [
    'AffiliateManager',
    'BaseAffiliateConverter',
    'AffiliateConversionError',
    'InvalidLinkError',
    'ConversionError',
    'CookieExpiredError',
    'MarketplaceNotSupportedError',
]
