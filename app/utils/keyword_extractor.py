from typing import List
import re
def extract_keywords(text: str) -> List[str]:
    words = re.findall(r'\b[A-Za-z]{3,}\b', text.lower())
    return sorted(list(set(words)))[:20]
