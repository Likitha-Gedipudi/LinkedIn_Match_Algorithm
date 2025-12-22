"""
Helper utilities and common functions used across the project.
"""

import hashlib
import json
import random
import re
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import pandas as pd
from fake_useragent import UserAgent


# Type variable for decorators
T = TypeVar('T')


def generate_id(data: Union[str, Dict]) -> str:
    """
    Generate a unique ID from data.
    
    Args:
        data: String or dictionary to hash
        
    Returns:
        MD5 hash string
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    
    return hashlib.md5(data.encode()).hexdigest()


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        # Fallback user agents
        fallback_uas = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]
        return random.choice(fallback_uas)


def rate_limit(calls: int, period: int):
    """
    Rate limiting decorator.
    
    Args:
        calls: Number of calls allowed
        period: Time period in seconds
    """
    min_interval = period / calls
    last_called = [0.0]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        return wrapper
    
    return decorator


def retry(max_attempts: int = 3, delay: int = 1, backoff: int = 2):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        
        return wrapper
    
    return decorator


def sanitize_string(text: Optional[str]) -> str:
    """
    Sanitize string by removing extra whitespace and special characters.
    
    Args:
        text: Input string
        
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = " ".join(text.split())
    
    # Remove special characters (keep alphanumeric, spaces, and basic punctuation)
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()


def extract_numbers(text: str) -> List[int]:
    """
    Extract all numbers from text.
    
    Args:
        text: Input string
        
    Returns:
        List of integers found in text
    """
    return [int(n) for n in re.findall(r'\d+', text)]


def parse_experience_years(text: str) -> Optional[int]:
    """
    Parse years of experience from text.
    
    Args:
        text: Text containing experience information
        
    Returns:
        Number of years or None
    """
    # Look for patterns like "5 years", "3+ years", "2-4 years"
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\s*-\s*\d+\s*(?:years?|yrs?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    
    return None


def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill name for consistency.
    
    Args:
        skill: Raw skill name
        
    Returns:
        Normalized skill name
    """
    # Convert to lowercase
    skill = skill.lower().strip()
    
    # Common normalizations
    normalizations = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'ml': 'machine learning',
        'ai': 'artificial intelligence',
        'ds': 'data science',
        'fe': 'frontend',
        'be': 'backend',
    }
    
    return normalizations.get(skill, skill)


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate text similarity using Jaccard similarity.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    # Jaccard similarity
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split items into batches.
    
    Args:
        items: List of items
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division fails
        
    Returns:
        Division result or default
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format timestamp for logging and storage.
    
    Args:
        dt: Datetime object (defaults to now)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def load_json_safe(file_path: str, default: Any = None) -> Any:
    """
    Safely load JSON file.
    
    Args:
        file_path: Path to JSON file
        default: Default value if loading fails
        
    Returns:
        Loaded JSON data or default
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def save_json_safe(data: Any, file_path: str) -> bool:
    """
    Safely save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception:
        return False


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL string
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^https?://[^\s]+$'
    return bool(re.match(pattern, url))


class Timer:
    """Context manager for timing code execution."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.time() - self.start_time
    
    def __str__(self):
        if self.elapsed:
            return f"{self.name}: {self.elapsed:.2f}s"
        return f"{self.name}: Not completed"


def chunks_dataframe(df: pd.DataFrame, chunk_size: int):
    """
    Yield chunks of a DataFrame.
    
    Args:
        df: Input DataFrame
        chunk_size: Size of each chunk
        
    Yields:
        DataFrame chunks
    """
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]
