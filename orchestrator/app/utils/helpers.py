"""Helper utilities and common functions."""

import asyncio
import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml
from tenacity import retry, stop_after_attempt, wait_exponential


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Args:
        text: Text to slugify

    Returns:
        str: Slugified text
    """
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def calculate_checksum(data: bytes) -> str:
    """
    Calculate SHA256 checksum of data.

    Args:
        data: Data to checksum

    Returns:
        str: Hex digest of checksum
    """
    return hashlib.sha256(data).hexdigest()


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration (e.g., "2h 30m 15s")
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes to human-readable size.

    Args:
        bytes_size: Size in bytes

    Returns:
        str: Formatted size (e.g., "1.5 GB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def parse_yaml(content: str) -> Dict[str, Any]:
    """
    Parse YAML content.

    Args:
        content: YAML content string

    Returns:
        Dict[str, Any]: Parsed YAML data
    """
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {str(e)}")


def dump_yaml(data: Dict[str, Any]) -> str:
    """
    Dump data to YAML string.

    Args:
        data: Data to dump

    Returns:
        str: YAML string
    """
    return yaml.dump(data, default_flow_style=False, sort_keys=False)


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid URL
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def is_valid_ip(ip: str) -> bool:
    """
    Check if IP address is valid.

    Args:
        ip: IP address to validate

    Returns:
        bool: True if valid IP
    """
    import ipaddress

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List[List[Any]]: List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def run_in_parallel(
    tasks: List[Any],
    max_concurrent: int = 5,
) -> List[Any]:
    """
    Run async tasks in parallel with concurrency limit.

    Args:
        tasks: List of coroutines to run
        max_concurrent: Maximum concurrent tasks

    Returns:
        List[Any]: Results from tasks
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*[bounded_task(task) for task in tasks])


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def retry_async(coro):
    """
    Retry async function with exponential backoff.

    Args:
        coro: Coroutine to retry

    Returns:
        Any: Result from coroutine
    """
    return await coro


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[: 255 - len(ext) - 1] + ("." + ext if ext else "")
    return filename


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        str: ISO formatted timestamp
    """
    return datetime.utcnow().isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO formatted timestamp.

    Args:
        timestamp_str: ISO formatted timestamp string

    Returns:
        datetime: Parsed datetime object
    """
    return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.

    Args:
        url: URL to extract domain from

    Returns:
        Optional[str]: Domain or None if invalid URL
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return None
