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


# Amazon specific exceptions
class AmazonRateLimitError(AffiliateConversionError):
    """Raised when Amazon rate limit is hit"""
    pass


class AmazonInvalidSessionError(AffiliateConversionError):
    """Raised when Amazon session/cookies are invalid"""
    pass


class AmazonProductNotFoundError(AffiliateConversionError):
    """Raised when product is not found on Amazon"""
    pass


class AmazonInvalidAssociateTagError(AffiliateConversionError):
    """Raised when Amazon Associate Tag format is invalid"""
    pass


class AmazonCaptchaError(AffiliateConversionError):
    """Raised when Amazon CAPTCHA is detected"""
    pass


class AmazonAPIError(AffiliateConversionError):
    """Raised for generic Amazon API errors"""
    pass


# Shopee specific exceptions
class ShopeeRateLimitError(AffiliateConversionError):
    """Raised when Shopee rate limit is hit"""
    pass


class ShopeeInvalidSessionError(AffiliateConversionError):
    """Raised when Shopee session/cookies are invalid"""
    pass


class ShopeeProductNotFoundError(AffiliateConversionError):
    """Raised when product is not found on Shopee"""
    pass


class ShopeeInvalidLinkError(AffiliateConversionError):
    """Raised when Shopee link format is invalid"""
    pass


class ShopeeAPIError(AffiliateConversionError):
    """Raised for generic Shopee API errors"""
    pass
