"""Cookie management for affiliate authentication"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def load_cookies_from_json(filepath: str) -> Dict:
    """
    Load cookies from JSON file

    Args:
        filepath: Path to cookie JSON file

    Returns:
        Dictionary containing cookie data

    Raises:
        FileNotFoundError: If cookie file doesn't exist
        json.JSONDecodeError: If JSON is malformed
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_cookie_expiry(cookies: Dict) -> bool:
    """
    Validate if cookies are still valid based on expiration data

    Args:
        cookies: Dictionary containing cookie data with 'expires_at' or 'cookies' list

    Returns:
        True if cookies are valid, False if expired
    """
    from datetime import timezone
    now = datetime.now(timezone.utc)

    # Check top-level expires_at field (if present)
    if 'expires_at' in cookies:
        try:
            expires_at = datetime.fromisoformat(cookies['expires_at'].replace('Z', '+00:00'))
            if now >= expires_at:
                return False
        except (ValueError, AttributeError):
            pass

    # Check individual cookie expiration (if present)
    if 'cookies' in cookies and isinstance(cookies['cookies'], list):
        for cookie in cookies['cookies']:
            if 'expires' in cookie:
                try:
                    # Handle Unix timestamp
                    if isinstance(cookie['expires'], (int, float)):
                        from datetime import timezone
                        expires_dt = datetime.fromtimestamp(cookie['expires'], tz=timezone.utc)
                        if now >= expires_dt:
                            return False
                except (ValueError, OSError):
                    pass

    return True


def get_cookie_age(filepath: str) -> timedelta:
    """
    Calculate age of cookie file based on modification time

    Args:
        filepath: Path to cookie JSON file

    Returns:
        timedelta representing age of the file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(filepath)
    if not file_path.exists():
        raise FileNotFoundError(f"Cookie file not found: {filepath}")

    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return datetime.now() - file_mtime


def get_cookie_list(cookies: Dict) -> List[Dict]:
    """
    Extract cookie list from cookie data structure

    Args:
        cookies: Dictionary containing cookie data

    Returns:
        List of cookie dictionaries for use with Playwright

    Raises:
        ValueError: If cookies structure is invalid
    """
    if 'cookies' in cookies and isinstance(cookies['cookies'], list):
        return cookies['cookies']

    raise ValueError("Invalid cookie structure: missing 'cookies' list")
