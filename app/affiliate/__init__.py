"""Affiliate link conversion module"""

from app.affiliate.manager import AffiliateManager
from app.affiliate.base import BaseAffiliateConverter
from app.affiliate.exceptions import (
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
