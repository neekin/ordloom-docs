#!/usr/bin/env python3
"""Check VitePress/Markdown navigation, local routes and executable examples."""
import argparse
import ast
from collections import Counter
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / 'docs'
LINK = re.compile(r'!?\[[^\]]*\]\(([^)]+)\)')
errors = []
counts = {'links': 0, 'python': 0, 'json': 0}

def error(path, message):
    errors.append(f'{path.relative_to(ROOT)}: {message}')

def read_blocks(path):
    source = path.read_text(encoding='utf-8')
    front = re.match(r'^---\n(.*?)\n---\n', source, re.DOTALL)
    home = bool(front and re.search(r'^layout:\s*home\s*$', front[1], re.MULTILINE))
    if front:
        for target in re.findall(r'^\s*link:\s*(\S+)\s*$', front[1], re.MULTILINE):
            check_links(path, f'[frontmatter link]({target})')
        source = source[front.end():]
    lines = source.splitlines()
    visible, block, language = [], [], None
    for line in lines:
        fence = re.match(r'^```(\w*)\s*$', line)
        if fence:
            if language is None:
                language = fence[1]
                block = []
            else:
                source = '\n'.join(block)
                try:
                    if language == 'python':
                        ast.parse(source)
                        counts['python'] += 1
                    elif language == 'json':
                        json.loads(source)
                        counts['json'] += 1
                except (SyntaxError, ValueError) as exc:
                    error(path, f'invalid {language} example: {exc}')
                language = None
            continue
        if language is None:
            visible.append(line)
        else:
            block.append(line)
    if language is not None:
        error(path, 'unclosed fenced code block')
    if not home and len(re.findall(r'^# ', '\n'.join(visible), re.MULTILINE)) != 1:
        error(path, 'expected exactly one page title')
    return '\n'.join(visible)

def check_links(path, source):
    for target in LINK.findall(source):
        target = target.strip().strip('<>').split(' ', 1)[0]
        parsed = urlsplit(target)
        if parsed.scheme or target.startswith('//') or not parsed.path:
            continue
        counts['links'] += 1
        local = unquote(parsed.path)
        if path.is_relative_to(BOOK) and local.startswith('/'):
            route = local.lstrip('/')
            base = BOOK / route
            markdown = base.with_suffix('.md') if base.suffix == '.html' else Path(str(base) + '.md')
            candidates = [base, markdown, base / 'index.md', base / 'README.md', BOOK / 'public' / route]
            if not route: candidates = [BOOK / 'README.md', BOOK / 'index.md']
            destination = next((value.resolve() for value in candidates if value.is_file()), base.resolve())
        else:
            destination = (path.parent / local).resolve()
        try:
            destination.relative_to(ROOT)
        except ValueError:
            error(path, f'link escapes the repository: {target}')
            continue
        if not destination.is_file():
            error(path, f'missing local link: {target}')
        if path.is_relative_to(BOOK):
            try:
                destination.relative_to(BOOK)
            except ValueError:
                error(path, f'GitBook link leaves mapped content; use a public URL: {target}')

def check_navigation():
    summary = BOOK / 'SUMMARY.md'
    targets = [(summary.parent / unquote(urlsplit(target).path)).resolve()
               for target in LINK.findall(summary.read_text())]
    for path, count in Counter(targets).items():
        if count > 1:
            error(summary, f'duplicate navigation target: {path.relative_to(ROOT)}')
    expected = set(BOOK.rglob('*.md')) - {summary}
    for path in sorted(expected - set(targets)):
        error(summary, f'page missing from navigation: {path.relative_to(ROOT)}')
    for config in [ROOT / '.gitbook.yaml', BOOK / '.gitbook.yaml']:
        if not config.is_file(): continue
        match = re.search(r'^root:\s*(.+)$', config.read_text(), re.MULTILINE)
        if not match or (config.parent / match[1].strip()).resolve() != BOOK:
            error(config, 'content root does not resolve to docs/')
    return len(expected)

def check_schema(schema_path):
    try:
        import yaml
        import jsonschema
    except ImportError:
        error(ROOT / 'gitbook-docs.yaml', '--schema requires PyYAML and jsonschema')
        return
    config = yaml.safe_load((ROOT / 'gitbook-docs.yaml').read_text())
    schema = yaml.safe_load(Path(schema_path).read_text())
    try:
        jsonschema.Draft202012Validator(schema).validate(config)
    except jsonschema.ValidationError as exc:
        error(ROOT / 'gitbook-docs.yaml', f'official schema validation failed: {exc.message}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema', help='Optional downloaded official GitBook YAML or JSON schema')
    arguments = parser.parse_args()
    pages = [ROOT / 'README.md', *sorted(BOOK.rglob('*.md')), ROOT / 'examples/quickstart/README.md']
    for path in pages:
        check_links(path, read_blocks(path))
    total = check_navigation()
    for path in sorted((ROOT / 'examples').rglob('*.py')):
        try:
            ast.parse(path.read_text())
        except SyntaxError as exc:
            error(path, f'invalid example source: {exc}')
    if arguments.schema:
        check_schema(arguments.schema)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {total} handbook pages, {counts["links"]} local links/assets, '
          f'{counts["python"]} Python snippets and {counts["json"]} JSON examples.')
    if arguments.schema:
        print('PASS: GitBook site configuration matches the official schema.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
