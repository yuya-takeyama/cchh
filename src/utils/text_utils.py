"""Text processing utilities"""

import re


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return suffix[:max_length]

    return text[: max_length - len(suffix)] + suffix


def truncate_middle(text: str, max_length: int, separator: str = " ... ") -> str:
    """Truncate text in the middle, preserving start and end

    Args:
        text: Text to truncate
        max_length: Maximum length (including separator)
        separator: Separator to use in middle

    Returns:
        Truncated text with middle removed
    """
    if len(text) <= max_length:
        return text

    if max_length <= len(separator):
        return text[:max_length]

    # Calculate how much to keep from each side
    available = max_length - len(separator)
    start_len = available // 2
    end_len = available - start_len

    return text[:start_len] + separator + text[-end_len:]


def escape_markdown(text: str) -> str:
    """Escape special markdown characters

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for markdown
    """
    # Characters that need escaping in markdown
    special_chars = r"*_`~[]()#+-!|{}"
    pattern = f"([{re.escape(special_chars)}])"
    return re.sub(pattern, r"\\\1", text)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_float < 1024.0:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} PB"


def extract_error_message(error_text: str, max_length: int = 100) -> str:
    """Extract meaningful error message from exception text

    Args:
        error_text: Full error/exception text
        max_length: Maximum length for extracted message

    Returns:
        Extracted error message
    """
    # Try to find the actual error message
    lines = error_text.strip().split("\n")

    # Look for lines that likely contain the error message
    for line in reversed(lines):
        line = line.strip()
        if line and not line.startswith(" ") and not line.startswith("File"):
            # Found a likely error message
            return truncate_text(line, max_length)

    # Fallback: use first non-empty line
    for line in lines:
        line = line.strip()
        if line:
            return truncate_text(line, max_length)

    return truncate_text(error_text, max_length)


def normalize_path(path: str, home_symbol: bool = True) -> str:
    """Normalize file path for display

    Args:
        path: File path to normalize
        home_symbol: Replace home directory with ~

    Returns:
        Normalized path
    """
    import os

    # Expand user and normalize
    normalized = os.path.normpath(os.path.expanduser(path))

    if home_symbol:
        home = os.path.expanduser("~")
        if normalized.startswith(home):
            normalized = "~" + normalized[len(home) :]

    return normalized


def is_binary_content(content: str, sample_size: int = 512) -> bool:
    """Check if content appears to be binary

    Args:
        content: Content to check
        sample_size: How many bytes to check

    Returns:
        True if content appears binary
    """
    # Check first N bytes
    sample = content[:sample_size]

    # Count non-text characters
    non_text_chars = 0
    for char in sample:
        # Check for common non-text bytes
        if ord(char) < 32 and char not in "\n\r\t":
            non_text_chars += 1

    # If more than 30% non-text, probably binary
    return non_text_chars > len(sample) * 0.3
