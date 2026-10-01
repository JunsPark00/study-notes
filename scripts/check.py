#!/usr/bin/env python3
"""Static integrity checks, intentionally separate from browser interaction checks."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import json,re,sys
ROOT=Path(__file__).resolve().parent.parent
DOCS=ROOT/'docs'; BASE='/study-notes/'
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.images=[];self.math=0;self.lang=None;self.h1=0;self.headings=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.append(d['id'])
        if tag=='html':self.lang=d.get('lang')
        if tag=='h1':self.h1+=1
        if tag=='math':self.math+=1
        if tag=='img' and d.get('src'):self.images.append(d)
        if tag in ['a','link']:self.links.append(d.get('href',''))
        if tag in ['img','script'] and d.get('src'):self.links.append(d['src'])
        if 'data-zoom' in d:self.links.append(d['data-zoom'])
errors=[];pages={};external=set();link_count=0
for file in DOCS.rglob('*.html'):
    p=Page();p.feed(file.read_text());pages[file.resolve()]=p
    if p.lang!='ko':errors.append(f'{file}: language missing')
    if p.h1!=1:errors.append(f'{file}: expected one h1, got {p.h1}')
    if len(p.ids)!=len(set(p.ids)):errors.append(f'{file}: duplicate IDs')
    for img in p.images:
        if not img.get('alt'):errors.append(f'{file}: missing image alt')
    content=file.read_text()
    if 'katex-error' in content:errors.append(f'{file}: KaTeX error')
    if re.search(r'github\.com/JunsPark00/(?!study-notes)|slack\.com|/workspace/|sediment://',content):errors.append(f'{file}: prohibited source reference')
    if '$$' in content:errors.append(f'{file}: unrendered display delimiter')
for file,page in pages.items():
    for link in page.links:
        if not link:errors.append(f'{file}: empty URL');continue
        parsed=urlsplit(link)
        if parsed.scheme in ('https','http'):
            external.add(link);continue
        if parsed.scheme:errors.append(f'{file}: unsupported scheme {link}');continue
        link_count+=1
        if parsed.path.startswith(BASE):target=DOCS/unquote(parsed.path[len(BASE):])
        elif parsed.path.startswith('/'):
            errors.append(f'{file}: wrong project base {link}');continue
        elif parsed.path:target=file.parent/unquote(parsed.path)
        else:target=file
        if target.is_dir():target=target/'index.html'
        target=target.resolve()
        if not target.is_file():errors.append(f'{file}: missing {link}');continue
        if parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:errors.append(f'{file}: missing anchor {link}')
for file in DOCS.rglob('*.css'):
    for asset in re.findall(r'url\([\'\"]?([^\'\")]+)',file.read_text()):
        if asset.startswith('data:'):continue
        if not (file.parent/asset).is_file():errors.append(f'{file}: missing CSS asset {asset}')
for n in range(1,9):
    f=(DOCS/f'chapters/chapter{n:02}.html').resolve()
    p=pages[f]
    if not p.math:errors.append(f'{f}: math absent')
    if len([x for x in p.ids if x.startswith(f'ch{n:02}_')])!=4:errors.append(f'{f}: expected 4 formula cards')
for file in DOCS.rglob('*'):
    if file.is_file() and file.suffix.lower() in ['.pdf','.ipynb']:errors.append(f'Unexpected restricted file: {file}')
for name,expected in [('diagrams',34)]:
    count=len(list((DOCS/'assets'/name).glob('*')))
    if count!=expected:errors.append(f'{name}: expected {expected} assets, got {count}')
summary={'status':'passed' if not errors else 'failed','html_pages':len(pages),'chapters':8,'local_links_checked':link_count,'unique_external_links':len(external),'mathml_expressions':sum(p.math for p in pages.values()),'original_diagrams':17,'formula_cards':32,'standalone_scripts':8,'deployment_file_count':sum(p.is_file() for p in DOCS.rglob('*')),'deployment_bytes':sum(p.stat().st_size for p in DOCS.rglob('*') if p.is_file()),'browser_ui':'not covered by static integrity checks','errors':errors}
(ROOT/'qa').mkdir(exist_ok=True)
(ROOT/'qa/static-check.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(ROOT/'qa/external-links.txt').write_text('\n'.join(sorted(external))+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2));sys.exit(bool(errors))
