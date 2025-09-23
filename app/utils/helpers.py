"""
Utility helper functions for the financial document processing system.
"""
import hashlib
import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime


def generate_file_hash(file_path: str) -> str:
    """
    Generate MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    filename = re.sub(r'_{2,}', '_', filename)
    
    # Trim length if too long
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def extract_financial_numbers(text: str) -> List[Dict[str, Any]]:
    """
    Extract financial numbers from text using regex patterns.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of extracted numbers with context
    """
    patterns = [
        # Dollar amounts
        r'\$\s*([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?)\s*(million|billion|trillion|k|m|b|t)?',
        # Percentages
        r'([0-9]+(?:\.[0-9]+)?)\s*%',
        # Numbers with units
        r'([0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]+)?)\s*(million|billion|trillion|thousand)',
    ]
    
    extracted = []
    
    for i, pattern in enumerate(patterns):
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            extracted.append({
                'value': match.group(1),
                'unit': match.group(2) if len(match.groups()) > 1 else None,
                'full_match': match.group(0),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'pattern_type': ['currency', 'percentage', 'general'][i]
            })
    
    return extracted


def normalize_financial_value(value_str: str, unit: Optional[str] = None) -> Optional[float]:
    """
    Normalize a financial value to a standard numerical format.
    
    Args:
        value_str: String representation of the value
        unit: Optional unit (million, billion, etc.)
        
    Returns:
        Normalized numerical value or None if invalid
    """
    try:
        # Clean the value string
        clean_value = re.sub(r'[,$]', '', value_str)
        base_value = float(clean_value)
        
        # Apply unit multiplier
        if unit:
            unit_lower = unit.lower()
            multipliers = {
                'k': 1_000,
                'thousand': 1_000,
                'm': 1_000_000,
                'million': 1_000_000,
                'b': 1_000_000_000,
                'billion': 1_000_000_000,
                't': 1_000_000_000_000,
                'trillion': 1_000_000_000_000
            }
            
            multiplier = multipliers.get(unit_lower, 1)
            base_value *= multiplier
        
        return base_value
        
    except (ValueError, TypeError):
        return None


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple text similarity based on word overlap.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    if not text1 or not text2:
        return 0.0
    
    # Tokenize and normalize
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a numerical amount as currency.
    
    Args:
        amount: Numerical amount
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.1f}B {currency}"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M {currency}"
    elif amount >= 1_000:
        return f"${amount/1_000:.1f}K {currency}"
    else:
        return f"${amount:.2f} {currency}"


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input text.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    sanitized = sanitized[:max_length]
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized


def create_document_summary(content: str, max_words: int = 100) -> str:
    """
    Create a simple extractive summary of document content.
    
    Args:
        content: Document content
        max_words: Maximum words in summary
        
    Returns:
        Document summary
    """
    if not content:
        return ""
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if not sentences:
        return content[:500] + "..." if len(content) > 500 else content
    
    # Simple scoring: prefer sentences with financial keywords
    financial_keywords = [
        'revenue', 'profit', 'loss', 'investment', 'financial', 'market',
        'growth', 'performance', 'earnings', 'capital', 'valuation'
    ]
    
    scored_sentences = []
    for sentence in sentences[:20]:  # Limit to first 20 sentences
        score = 0
        sentence_lower = sentence.lower()
        
        # Score based on keyword presence
        for keyword in financial_keywords:
            if keyword in sentence_lower:
                score += 1
        
        # Prefer sentences with numbers
        if re.search(r'\d+', sentence):
            score += 1
        
        # Prefer longer sentences (up to a point)
        words = sentence.split()
        if 15 <= len(words) <= 30:
            score += 1
        
        scored_sentences.append((score, sentence))
    
    # Sort by score and select top sentences
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    
    summary_sentences = []
    word_count = 0
    
    for score, sentence in scored_sentences:
        sentence_words = len(sentence.split())
        if word_count + sentence_words <= max_words:
            summary_sentences.append(sentence)
            word_count += sentence_words
        else:
            break
    
    if not summary_sentences:
        # Fallback: use first sentence
        first_sentence = sentences[0] if sentences else content[:200]
        return first_sentence + "..."
    
    return ". ".join(summary_sentences) + "."


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    uuid_pattern = re.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )
    return bool(uuid_pattern.match(uuid_string))


def get_file_extension(filename: str) -> str:
    """
    Get file extension in lowercase.
    
    Args:
        filename: Filename
        
    Returns:
        File extension (including dot)
    """
    return os.path.splitext(filename)[1].lower()


def timestamp_to_string(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Convert timestamp to formatted string.
    
    Args:
        timestamp: Datetime object
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime(format_str)