"""Custom exceptions for affiliate conversion module"""


class AffiliateConversionError(Exception):
    """Base exception for affiliate conversion errors"""
    pass


class InvalidLinkError(AffiliateConversionError):
    """Raised when link is malformed or invalid"""
    pass


class ConversionError(AffiliateConversionError):
    """Raised when link conversion fails"""
    pass


class CookieExpiredError(AffiliateConversionError):
    """Raised when authentication cookies are expired"""
    pass


class MarketplaceNotSupportedError(AffiliateConversionError):
    """Raised when marketplace is not supported"""
    pass


# Mercado Livre specific exceptions
class MLRateLimitError(AffiliateConversionError):
    """Raised when Mercado Livre rate limit is hit"""
    pass


class MLInvalidSessionError(AffiliateConversionError):
    """Raised when Mercado Livre session/cookies are invalid"""
    pass


class MLProductNotFoundError(AffiliateConversionError):
    """Raised when product is not found on Mercado Livre"""
    pass


class MLAPIError(AffiliateConversionError):
    """Raised for generic Mercado Livre API errors"""
    pass
