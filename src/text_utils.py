import re


def is_binary_data(text):
    """Check if text contains binary data"""
    if not isinstance(text, str):
        return True
    
    # Check for high percentage of non-printable characters
    printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
    if len(text) > 0 and printable_chars / len(text) < 0.7:
        return True
    
    # Check for null bytes or other binary indicators
    if '\x00' in text or len([c for c in text if ord(c) < 32 and c not in '\n\r\t']) > len(text) * 0.1:
        return True
        
    return False


def is_title_case(text):
    """Check if text is in title case (each word starts with uppercase)"""
    if is_binary_data(text):
        return False
    words = text.strip().split()
    return len(words) > 0 and all(w[0].isupper() for w in words if w[0].isalpha())


def is_all_upper(text):
    """Check if text is all uppercase"""
    if is_binary_data(text):
        return False
    return text.isupper() and any(c.isalpha() for c in text)


def clean_text(text, max_words=150):
    """Clean and truncate text to a reasonable length"""
    if not isinstance(text, str):
        return ""
    
    # Filter out binary data
    if is_binary_data(text):
        return ""
    
    # Remove non-printable characters except common whitespace
    cleaned = ''.join(char for char in text if char.isprintable() or char in '\n\r\t ')
    
    # Replace tabs and normalize whitespace
    cleaned = cleaned.replace('\t', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Check again after cleaning
    if is_binary_data(cleaned):
        return ""

    words = cleaned.split()
    if len(words) <= max_words:
        return cleaned.strip()
    
    # Find the index for the first word after the threshold
    prefix = words[:max_words]
    suffix = words[max_words:]

    # Now build the suffix string, adding words until we hit a full stop at the end of a word
    collected = []
    found_period = False
    for word in suffix:
        collected.append(word)
        if word.endswith('.'):
            found_period = True
            break
    
    if not found_period:
        # If no period found, just use what we have (avoid infinite strings)
        return " ".join(prefix + collected).strip() + " ..."
    
    return " ".join(prefix + collected).strip()


def is_bold_font(span):
    """Check if a text span uses bold formatting"""
    bold_flag = (span["flags"] & 2) != 0
    bold_name = any(word in span["font"].lower() for word in ["bold", "black", "heavy"])
    return bold_flag or bold_name
