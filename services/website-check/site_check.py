"""Offline, standard-library checks of an owner-supplied static website export."""
import argparse
import html
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.title = ''; self.in_title = False; self.viewport = False
        self.lang = ''; self.headings = 0; self.images = []; self.links = []
        self.feed(source)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html': self.lang = a.get('lang', '')
        if tag == 'title': self.in_title = True
        if tag == 'h1': self.headings += 1
        if tag == 'meta' and a.get('name','').lower() == 'viewport':
            self.viewport = 'width=device-width' in a.get('content','').replace(' ', '').lower()
        if tag == 'img' and 'alt' not in a: self.images.append(a.get('src','(no src)'))
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
    def handle_data(self, data):
        if self.in_title: self.title += data

def audit(root):
    root = Path(root).resolve()
    pages = sorted(root.rglob('*.html'))
    if not pages: raise ValueError('No HTML pages found')
    if len(pages) > 100: raise ValueError('Limit: 100 HTML pages')
    findings = []; checked = []
    def add(page, priority, issue, action):
        findings.append(dict(page=page, priority=priority, issue=issue, action=action))
    for path in pages:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Symlink pages are not supported')
        if path.stat().st_size > 2_000_000: raise ValueError('HTML page exceeds 2 MB')
        name = path.relative_to(root).as_posix(); checked.append(name)
        p = Page(path.read_text(encoding='utf-8'))
        for ok, issue, action in [
            (p.title.strip(), 'Missing page title', 'Add a descriptive title.'),
            (p.lang.strip(), 'Missing document language', 'Set the html lang attribute.'),
            (p.viewport, 'Missing mobile viewport declaration', 'Add width=device-width, initial-scale=1.'),
            (p.headings == 1, f'Found {p.headings} main headings', 'Review the heading structure; usually use one clear h1.')]:
            if not ok: add(name, 'Review', issue, action)
        for image in p.images:
            add(name, 'Review', f'Image has no alt attribute: {image}', 'Write useful alternative text or use empty alt for decorative images.')
        for href in sorted(set(p.links)):
            u = urlsplit(href)
            if u.scheme or u.netloc or not u.path: continue
            target = (root / unquote(u.path).lstrip('/') if u.path.startswith('/') else path.parent / unquote(u.path)).resolve()
            if not target.is_relative_to(root):
                add(name, 'Review', f'Link leaves supplied export: {href}', 'Review the intended destination.'); continue
            if target.is_dir(): target = target / 'index.html'
            if not target.exists(): add(name, 'High', f'Local link target absent: {href}', 'Correct the link or provide the destination. Server routes may need manual verification.')
    return dict(generated=datetime.now(timezone.utc).isoformat(), pages=checked, findings=findings,
                limitations=['Static source checks only; no JavaScript execution or screenshots.', 'External links, fragments, forms, live server routes, visual mobile layout and accessibility compliance require manual checks.', 'No security, performance, SEO ranking or conversion guarantee.'], status='DRAFT_FOR_OWNER_REVIEW')

def render(result):
    esc = lambda x: html.escape(str(x))
    rows = ''.join(f"<tr><td>{esc(f['priority'])}</td><td>{esc(f['page'])}</td><td>{esc(f['issue'])}</td><td>{esc(f['action'])}</td></tr>" for f in result['findings'])
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Website review report</title><style>body{font:17px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:24px;color:#17322c}table{border-collapse:collapse;width:100%}td,th{border:1px solid #cddbd6;padding:12px;text-align:left;overflow-wrap:anywhere}h1{font-size:36px}@media print{body{margin:0}}</style><h1>Website review report</h1><p>Internal draft · '+esc(result['generated'])+'</p><p>'+str(len(result['pages']))+' page(s) checked; '+str(len(result['findings']))+' items to review.</p><table><tr><th>Priority</th><th>Page</th><th>Evidence</th><th>Next action</th></tr>'+rows+'</table><h2>Scope and limits</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in result['limitations'])+'</ul></html>'

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('root'); ap.add_argument('--out', required=True)
    args = ap.parse_args(); result = audit(args.root)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    (out/'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    (out/'report.html').write_text(render(result), encoding='utf-8')
    print(f"Checked {len(result['pages'])} pages; {len(result['findings'])} review items. Draft only.")
