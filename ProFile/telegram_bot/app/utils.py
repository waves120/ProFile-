
import re

URL_RE = re.compile(r'(https?://\S+)', re.IGNORECASE)
TAG_RE = re.compile(r'(^|\s)#(\w{1,32})')

def extract_url(text: str|None) -> str|None:
    if not text: return None
    m = URL_RE.search(text)
    return m.group(1) if m else None

def extract_tags(text: str|None) -> str|None:
    if not text: return None
    tags = [t[1] for t in TAG_RE.findall(text)]
    return " ".join(sorted(set(f"#{t}" for t in tags))) if tags else None
