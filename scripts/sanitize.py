"""Sanitize only the explicitly staged evidence tree before public upload."""
import os
from pathlib import Path
import re
import sys

SECRET_NAMES=('KRILL_API_KEY','OPENAI_API_KEY','CODEX_API_KEY','GH_TOKEN',
              'GITHUB_TOKEN','GITHUB_PERSONAL_ACCESS_TOKEN')


def redact(text):
    for name in SECRET_NAMES:
        key = os.environ.get(name, '')
        if key:
            text = text.replace(key, '[REDACTED]')
    return re.sub(r'\b(?:nb_|gh[pousr]_|github_pat_)[A-Za-z0-9_-]{16,}\b', '[REDACTED]', text)


def sanitize(root):
    root = Path(root)
    if not root.exists():
        return
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.name in {'auth.json', '.env'}:
            path.unlink()
            continue
        try:
            original = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            raise RuntimeError(f'Unexpected binary evidence: {path}')
        cleaned = redact(original)
        if cleaned != original:
            path.write_text(cleaned, encoding='utf-8')
        for name in SECRET_NAMES:
            key = os.environ.get(name, '')
            if key and key in path.read_text(encoding='utf-8'):
                raise RuntimeError('Secret survived sanitization')


if __name__ == '__main__':
    sanitize(sys.argv[1])
    print('Evidence sanitized and scanned')
