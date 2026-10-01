#!/usr/bin/env python3
"""Registry-driven static integrity checks; browser interaction QA is separate."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import hashlib,json,os,re,sys
ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path(os.environ.get('SITE_CONTENT_DIR',ROOT/'content')).resolve()
DOCS=Path(os.environ.get('SITE_OUT_DIR',ROOT/'docs')).resolve()
QA=Path(os.environ.get('SITE_QA_DIR',ROOT/'qa')).resolve()
BASE=os.environ.get('SITE_BASE','/study-notes/')
books=json.loads((SOURCE/'books.json').read_text())
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.links=[];self.images=[];self.math=0;self.lang=None;self.h1=0;self.canonical=None;self.book=None
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if 'id' in d:self.ids.append(d['id'])
        if tag=='html':self.lang=d.get('lang')
        if tag=='body':self.book=d.get('data-book')
        if tag=='h1':self.h1+=1
        if tag=='math':self.math+=1
        if tag=='img' and d.get('src'):self.images.append(d)
        if tag=='link' and d.get('rel')=='canonical':self.canonical=d.get('href')
        if tag in ['a','link']:self.links.append(d.get('href',''))
        if tag in ['img','script'] and d.get('src'):self.links.append(d['src'])
        if 'data-zoom' in d:self.links.append(d['data-zoom'])
errors=[];pages={};external=set();link_count=0
for file in DOCS.rglob('*.html'):
    content=file.read_text();p=Page();p.feed(content);pages[file.resolve()]=p
    if p.lang!='ko':errors.append(f'{file}: language missing')
    if p.h1!=1:errors.append(f'{file}: expected one h1, got {p.h1}')
    if len(p.ids)!=len(set(p.ids)):errors.append(f'{file}: duplicate IDs')
    for img in p.images:
        if not img.get('alt'):errors.append(f'{file}: missing image alt')
    if 'katex-error' in content:errors.append(f'{file}: KaTeX error')
    if re.search(r'github\.com/JunsPark00/(?!study-notes)|slack\.com|/workspace/|sediment://',content):errors.append(f'{file}: prohibited source reference')
    if '$$' in content:errors.append(f'{file}: unrendered display delimiter')
    if not p.canonical:errors.append(f'{file}: missing canonical URL')

def check_link(file,link):
    global link_count
    if not link:errors.append(f'{file}: empty URL');return
    parsed=urlsplit(link)
    if parsed.scheme in ('https','http'):
        external.add(link)
        if parsed.path.lower().endswith('.pdf'):errors.append(f'{file}: prohibited book PDF link {link}')
        return
    if parsed.scheme:errors.append(f'{file}: unsupported scheme {link}');return
    link_count+=1
    if parsed.path.startswith(BASE):target=DOCS/unquote(parsed.path[len(BASE):])
    elif parsed.path.startswith('/'):
        errors.append(f'{file}: wrong project base {link}');return
    elif parsed.path:target=file.parent/unquote(parsed.path)
    else:target=file
    if target.is_dir():target=target/'index.html'
    target=target.resolve()
    if not target.is_relative_to(DOCS):errors.append(f'{file}: link escapes output directory {link}');return
    if not target.is_file():errors.append(f'{file}: missing {link}');return
    if parsed.fragment and target in pages and unquote(parsed.fragment) not in pages[target].ids:errors.append(f'{file}: missing anchor {link}')
for file,page in pages.items():
    for link in page.links:check_link(file,link)
for file in DOCS.rglob('*.css'):
    for asset in re.findall(r'url\([\'\"]?([^\'\")]+)',file.read_text()):
        if not asset.startswith('data:'):check_link(file,asset)
for file in list(DOCS.rglob('*.js'))+list(DOCS.rglob('*.mjs')):
    for asset in re.findall(r"(?:from\s+|import\s*)['\"]([^'\"]+)['\"]",file.read_text()):check_link(file,asset)
chapter_count=diagram_count=formula_count=example_count=math_count=legacy_count=0
expected_pages={'index.html','about.html','404.html'}
chapters_by_book={}
for b in books:
    prefix=f'books/{b["id"]}/'
    chapters=json.loads((SOURCE/b['chaptersFile']).read_text());chapters_by_book[b['id']]={c['number']:c for c in chapters}
    formulas=json.loads((SOURCE/b['formulasFile']).read_text()) if b.get('formulasFile') else []
    diagrams=json.loads((SOURCE/b['diagramsFile']).read_text()) if b.get('diagramsFile') else []
    chapter_count+=len(chapters);diagram_count+=len(diagrams);formula_count+=len(formulas)
    expected_pages.update([prefix+'index.html',prefix+'about.html'])
    for c in chapters:
        relative=prefix+f'chapters/chapter{c["number"]:02}.html';expected_pages.add(relative)
        f=(DOCS/relative).resolve();p=pages.get(f)
        if not p:errors.append(f'Missing chapter page: {relative}');continue
        if p.book!=b['id']:errors.append(f'{relative}: incorrect book context')
        if p.canonical!='https://junspark00.github.io'+BASE+relative:errors.append(f'{relative}: incorrect canonical')
        math_count+=p.math
        expected_formulas=[x for x in formulas if x['chapter']==c['number']]
        for form in expected_formulas:
            if form['id'] not in p.ids:errors.append(f'{relative}: missing formula card {form["id"]}')
        if b.get('legacyChapterUrls'):
            legacy=f'chapters/chapter{c["number"]:02}.html';expected_pages.add(legacy);legacy_count+=1
            if not (DOCS/legacy).exists() or (DOCS/legacy).read_bytes()!=f.read_bytes():errors.append(f'{legacy}: readable canonical compatibility page differs')
    for d in diagrams:
        for key in ['image','svg']:
            if d.get(key):check_link(DOCS/'index.html',BASE+d[key])
    if b.get('examplesManifest'):
        manifest=DOCS/b['examplesManifest'];data=json.loads(manifest.read_text());example_count+=len(data['chapters'])
        for example in data['chapters']:
            script=manifest.parent/example['file']
            if not script.is_file():errors.append(f'Missing standalone example: {script}')
            elif example.get('sha256') and hashlib.sha256(script.read_bytes()).hexdigest()!=example['sha256']:errors.append(f'Example checksum changed: {script}')
    for relative in [prefix+'index.html',prefix+'about.html']:
        p=pages.get((DOCS/relative).resolve())
        if not p or p.book!=b['id']:errors.append(f'{relative}: missing or incorrect book context')
actual_pages={file.relative_to(DOCS).as_posix() for file in pages}
if actual_pages!=expected_pages:errors.append(f'Generated page mismatch: missing {sorted(expected_pages-actual_pages)}, unexpected {sorted(actual_pages-expected_pages)}')
page_manifest=json.loads((DOCS/'assets/page-manifest.json').read_text())
if set(page_manifest)!=expected_pages:errors.append('Page manifest does not match registry')
search=json.loads((DOCS/'assets/search-index.json').read_text())
for r in search:
    b=next((b for b in books if b['id']==r.get('bookId')),None)
    if not b or r.get('bookTitle')!=b['title']:errors.append('Search record missing valid book identity');continue
    if r.get('chapter') not in chapters_by_book[b['id']]:errors.append('Search record has invalid chapter')
    if not r['url'].startswith(BASE+f'books/{b["id"]}/'):errors.append('Search record crosses book scope')
    check_link(DOCS/'index.html',r['url'])
for b in books:
    for c in chapters_by_book[b['id']]:
        if not any(r.get('bookId')==b['id'] and r.get('chapter')==c for r in search):errors.append(f'Unsearchable chapter {b["id"]}/{c}')
for file in DOCS.rglob('*'):
    if file.is_file() and file.suffix.lower() in ['.pdf','.ipynb']:errors.append(f'Unexpected restricted file: {file}')
summary={'status':'passed' if not errors else 'failed','books':len(books),'html_pages':len(pages),'chapters':chapter_count,'legacy_compatible_pages':legacy_count,'local_links_checked':link_count,'unique_external_links':len(external),'mathml_expressions':math_count,'original_diagrams':diagram_count,'formula_cards':formula_count,'standalone_scripts':example_count,'search_sections':len(search),'deployment_file_count':sum(p.is_file() for p in DOCS.rglob('*')),'deployment_bytes':sum(p.stat().st_size for p in DOCS.rglob('*') if p.is_file()),'browser_ui':'not covered by static integrity checks','errors':errors}
QA.mkdir(exist_ok=True,parents=True)
(QA/'static-check.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(QA/'external-links.txt').write_text('\n'.join(sorted(external))+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2));sys.exit(bool(errors))
