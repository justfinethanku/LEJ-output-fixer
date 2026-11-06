"""Save an interviewed preset from a JSON object on stdin; print its path and name."""

import json
import os
from pathlib import Path
import re
import sys


def create_preset(data, config_dir=None):
    """Create a new user preset without replacing a file or changing settings."""
    if not isinstance(data, dict):
        raise ValueError('Preset input must be a JSON object.')
    for field in ('name', 'description', 'instructions'):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{field} must be a nonempty string.')
    for field in ('name', 'description'):
        if any(c in data[field] for c in '\r\n'):
            raise ValueError(f'{field} must fit on one line.')
    keep = data.get('keep_coding_instructions', True)
    if not isinstance(keep, bool):
        raise ValueError('keep_coding_instructions must be a JSON boolean.')

    # User text is data, including quotes, YAML punctuation and Unicode.
    # JSON strings are also YAML double-quoted scalars.
    metadata = '\n'.join(
        f'{field}: {json.dumps(data[field], ensure_ascii=False)}'
        for field in ('name', 'description')
    )
    content = (
        f'---\n{metadata}\nkeep-coding-instructions: {str(keep).lower()}\n---\n\n'
        f'{data["instructions"].rstrip()}\n'
    )
    slug = ''.join(c if c.isalnum() else '-' for c in data['name'].lower())
    slug = re.sub('-+', '-', slug).strip('-')[:60].rstrip('-') or 'custom-style'
    if config_dir is None:
        config_dir = os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude'
    directory = Path(config_dir).expanduser() / 'output-styles'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{slug}.md'
    # Exclusive creation also handles two simultaneous saves and symlink collisions.
    with path.open('x', encoding='utf-8') as output:
        output.write(content)
    return {'path': str(path.resolve()), 'reference': data['name']}


def main():
    try:
        result = create_preset(json.load(sys.stdin))
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
