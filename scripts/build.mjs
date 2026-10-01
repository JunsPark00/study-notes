import fs from 'node:fs';
import path from 'node:path';
import MarkdownIt from 'markdown-it';
import katex from 'katex';

const ROOT = path.resolve(import.meta.dirname, '..');
const SOURCE = path.resolve(process.env.SITE_CONTENT_DIR || path.join(ROOT, 'content'));
const OUT = path.resolve(process.env.SITE_OUT_DIR || path.join(ROOT, 'docs'));
const QA = path.resolve(process.env.SITE_QA_DIR || path.join(ROOT, 'qa'));
const BASE = process.env.SITE_BASE || '/study-notes/';
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(BASE)) throw new Error('SITE_BASE must be a slash-delimited absolute URL path');
const ORIGIN = 'https://junspark00.github.io';
const esc = s => String(s ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const url = s => BASE+s;
const bookPath = b => `books/${b.id}/`;
const bookUrl = b => url(bookPath(b));
const chapterPath = (b,n) => `${bookPath(b)}chapters/chapter${String(n).padStart(2,'0')}.html`;
const chapterUrl = (b,n) => url(chapterPath(b,n));
const fail = message => { throw new Error(message); };
const safePath = (root,file) => {
 if(typeof file!=='string' || !file || path.isAbsolute(file) || file.includes('\\')) fail(`Invalid relative file path: ${file}`);
 const result=path.resolve(root,file);
 if(!result.startsWith(root+path.sep)) fail(`File path escapes its directory: ${file}`);
 return result;
};
const read = f => fs.readFileSync(safePath(SOURCE,f),'utf8');
const json = f => JSON.parse(read(f));
const requiredText = (value,label) => {if(typeof value!=='string' || !value.trim()) fail(`Missing required ${label}`);};
const readArray = (file,label) => {const value=file?json(file):[];if(!Array.isArray(value))fail(`${label} must be an array`);return value;};
const books=json('books.json');
if(!Array.isArray(books) || !books.length) fail('books.json must contain at least one book');
const ids=new Set();let legacyCount=0;
for(const b of books){
 if(typeof b.id!=='string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(b.id)) fail(`Invalid book id/slug: ${b.id}`);
 if(ids.has(b.id)) fail(`Duplicate book id/slug: ${b.id}`);ids.add(b.id);
 for(const field of ['title','category','description','chaptersFile','attributionFile'])requiredText(b[field],`${b.id}.${field}`);
 if(!Array.isArray(b.authors)||!b.authors.length)fail(`Missing authors for ${b.id}`);
 b.authors.forEach(author=>requiredText(author,`${b.id}.authors`));
 if(b.officialUrl && !/^https:\/\//.test(b.officialUrl))fail(`Invalid officialUrl for ${b.id}`);
 b.chapters=readArray(b.chaptersFile,`${b.id}.chapters`);
 if(!b.chapters.length)fail(`Book ${b.id} must have at least one chapter`);
 const numbers=new Set();
 for(const c of b.chapters){
  if(!Number.isInteger(c.number)||c.number<1)fail(`Invalid chapter number for ${b.id}`);
  if(numbers.has(c.number))fail(`Duplicate chapter number ${c.number} for ${b.id}`);numbers.add(c.number);
  requiredText(c.title,`${b.id} chapter title`);requiredText(c.file,`${b.id} chapter file`);read(c.file);
  if(c.tags && (!Array.isArray(c.tags)||c.tags.some(t=>typeof t!=='string')))fail(`Invalid chapter tags for ${b.id}`);
 }
 read(b.attributionFile);
 b.formulas=readArray(b.formulasFile,`${b.id}.formulas`);
 b.diagrams=readArray(b.diagramsFile,`${b.id}.diagrams`);
 b.videos=readArray(b.videosFile,`${b.id}.videos`);
 b.examples=[];
 if(b.examplesManifest){
  const manifest=JSON.parse(fs.readFileSync(safePath(OUT,b.examplesManifest),'utf8'));
  if(!Array.isArray(manifest.chapters))fail(`Invalid examples manifest for ${b.id}`);
  b.examples=manifest.chapters;b.examplesBase=path.posix.dirname(b.examplesManifest)+'/';b.exampleInfo=manifest;
  for(const ex of b.examples){fs.accessSync(safePath(OUT,b.examplesBase+ex.file));if(ex.figure)fs.accessSync(safePath(OUT,b.examplesBase+ex.figure));}
 }
 for(const [label,items] of [['formulas',b.formulas],['diagrams',b.diagrams],['videos',b.videos],['examples',b.examples]]){
  for(const item of items)if(!numbers.has(item.chapter))fail(`${b.id}.${label} refers to missing chapter ${item.chapter}`);
 }
 const formulaIds=new Set();for(const f of b.formulas){if(!f.id || formulaIds.has(f.id))fail(`Duplicate or missing formula id for ${b.id}`);formulaIds.add(f.id);}
 if(b.legacyChapterUrls)legacyCount++;
}
if(legacyCount>1)fail('Only one book can own legacy chapter URLs');
const chapterDescription=(b,c)=>c.description || b.description;
let equationCount=0;
const renderMath = (tex, display=false) => { equationCount++; return katex.renderToString(tex,{displayMode:display,throwOnError:true,strict:'error',output:'htmlAndMathml',trust:false}); };
const md = new MarkdownIt({html:false,linkify:false,typographer:false});
md.block.ruler.before('fence','math_block',(state,startLine,endLine,silent)=>{
  const start=state.bMarks[startLine]+state.tShift[startLine];
  if (state.src.slice(start,state.eMarks[startLine]).trim()!=='$$') return false;
  let next=startLine+1; while(next<endLine && state.src.slice(state.bMarks[next],state.eMarks[next]).trim()!=='$$') next++;
  if(next===endLine) throw new Error('Unclosed display math');
  if(silent) return true;
  const token=state.push('math_block','div',0); token.content=state.getLines(startLine+1,next,state.blkIndent,false).trim(); token.map=[startLine,next+1]; state.line=next+1; return true;
});
md.inline.ruler.before('escape','math_inline',(state,silent)=>{
  if(state.src[state.pos]!=='$' || state.src[state.pos+1]==='$') return false;
  let end=state.pos+1; while((end=state.src.indexOf('$',end))!==-1 && state.src[end-1]==='\\') end++;
  if(end===-1) return false;
  if(!silent){const token=state.push('math_inline','math',0);token.content=state.src.slice(state.pos+1,end);}
  state.pos=end+1;return true;
});
md.renderer.rules.math_inline = ts=>renderMath(ts[0]?.content); // token-index aware below
md.renderer.rules.math_inline = (ts,i)=>renderMath(ts[i].content);
md.renderer.rules.math_block = (ts,i)=>`<div class="math-block" tabindex="0" aria-label="수식, 가로로 스크롤할 수 있습니다">${renderMath(ts[i].content,true)}</div>\n`;
const mediaPath = value => value.replace('../../docs/assets/','assets/').replace('../assets/','assets/');
const mediaUrl = value => /^https?:\/\//.test(value) ? value : value.startsWith(BASE) ? value : url(mediaPath(value));
const oldLink=md.renderer.rules.link_open || ((ts,i,o,e,self)=>self.renderToken(ts,i,o));
md.renderer.rules.link_open=(ts,i,o,e,self)=>{
 const href=ts[i].attrGet('href');
 if(href?.startsWith('../../docs/assets/')||href?.startsWith('../assets/')||href?.startsWith('assets/'))ts[i].attrSet('href',mediaUrl(href));
 else if(e.book && href && !/^(?:https?:|#|\/)/.test(href)){
  const [file,fragment]=href.split('#');
  const source=path.posix.normalize(path.posix.join(path.posix.dirname(e.file||''),file));
  const target=e.book.chapters.find(c=>c.file===source);
  if(target)ts[i].attrSet('href',chapterUrl(e.book,target.number)+(fragment?'#'+fragment:''));
 }
 if(/^https?:/.test(href))ts[i].attrSet('rel','noopener noreferrer');
 return oldLink(ts,i,o,e,self);
};
md.renderer.rules.image=(ts,i,o,e)=>{
 const t=ts[i],src=mediaPath(t.attrGet('src'));
 const d=e.book?.diagrams.find(d=>d.svg===src || d.image===src);
 const alt=d?.alt || t.content;
 return `<a class="figure-link" href="${esc(mediaUrl(d?.image||src))}" data-zoom="${esc(mediaUrl(d?.svg||src))}" data-caption="${esc(d?.caption||alt)}" aria-label="${esc(d?.caption||alt)} 확대 보기"><img src="${esc(mediaUrl(src))}" alt="${esc(alt)}" loading="lazy" decoding="async"><span class="zoom-hint">그림 확대</span></a>`;
};
const iconSearch='<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg>';
const repo='https://github.com/JunsPark00/study-notes';
function footer(book){
 return `<footer class="site-footer"><div class="footer-inner"><div><a class="footer-brand" href="${url('')}">Study Notes</a><p>${book?esc(book.title)+' · '+esc(book.language||'학습 노트'):'책을 읽고, 이해하고, 다시 꺼내 보는 학습 기록'}</p></div><div class="footer-links"><a href="${url('about.html')}">사이트 안내</a>${book?`<a href="${bookUrl(book)}about.html">이 책의 출처</a>`:''}<a href="${repo}">GitHub</a></div><p class="footer-fine">AI의 도움으로 작성되었습니다. 수식과 가정은 원전 및 독립 계산으로 확인해 주세요.<br>원전의 저작권은 권리자에게 있으며, 출처 표시는 재사용 허락을 뜻하지 않습니다.</p></div></footer>`;
}
function shell({title,description,content,kind='home',canonical='',book}){
 const contextTitle=book?`${title} · ${book.title}`:title;
 return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="${esc(description)}"><meta name="color-scheme" content="light"><title>${esc(contextTitle)} · Study Notes</title><link rel="canonical" href="${ORIGIN+url(canonical)}"><link rel="icon" href="${url('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="${url('assets/katex/katex.min.css')}"><link rel="stylesheet" href="${url('assets/site.css')}"><script type="module" src="${url('assets/site.js')}"></script></head><body data-base="${BASE}" data-book="${book?.id||''}" class="${kind}"><a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="header-inner"><a class="brand" href="${url('')}" aria-label="Study Notes 책장"><span class="brand-mark" aria-hidden="true">S</span><span>Study <b>Notes</b></span></a><nav aria-label="주 메뉴"><a class="header-library" href="${url('')}#library">책장</a>${book?`<a class="header-book" href="${bookUrl(book)}">이 책의 목차</a>`:''}<a class="header-about" href="${url('about.html')}">사이트 안내</a><button class="search-trigger" aria-haspopup="dialog">${iconSearch}<span>검색</span><kbd>/</kbd></button></nav></div></header>${content}${footer(book)}<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-top"><h2 id="search-title">학습 노트 검색</h2><button class="icon-button dialog-close" type="button" aria-label="검색 닫기">×</button></div><form role="search" id="search-form"><label class="sr-only" for="search-input">책, 개념 또는 키워드 검색</label><div class="search-field">${iconSearch}<input id="search-input" type="search" placeholder="책 제목, 개념, 키워드…" autocomplete="off"></div><div class="search-scope"><label for="search-book">검색 범위</label><select id="search-book"><option value="">모든 책</option>${books.map(b=>`<option value="${b.id}" ${book?.id===b.id?'selected':''}>${esc(b.title)}</option>`).join('')}</select></div></form><p id="search-status" role="status" aria-live="polite">책 제목이나 개념을 입력해 학습 노트를 찾아보세요</p><div id="search-results"></div></dialog><dialog id="figure-dialog" aria-labelledby="figure-title"><div class="dialog-top"><h2 id="figure-title">그림 확대</h2><div><button class="text-button" id="figure-size" type="button" aria-pressed="false">실제 크기</button><button class="icon-button dialog-close" type="button" aria-label="그림 닫기">×</button></div></div><div class="figure-viewport"><img id="figure-image" alt=""></div><p class="figure-dialog-hint">Esc 키 또는 닫기 버튼으로 본문에 돌아갑니다</p></dialog></body></html>`;
}
function sidebar(book,active){
 return `<aside class="chapter-sidebar"><details id="chapter-menu" open><summary>이 책의 목차 <span aria-hidden="true">⌄</span></summary><div class="sidebar-content"><a class="sidebar-book" href="${bookUrl(book)}"><span class="eyebrow">${esc(book.category)}</span><strong>${esc(book.title)}</strong></a><nav aria-label="${esc(book.title)} 장별 목차">${book.chapters.map(c=>`<a class="chapter-nav-link ${active===c.number?'current':''}" href="${chapterUrl(book,c.number)}" ${active===c.number?'aria-current="page"':''}><span class="chapter-num">${String(c.number).padStart(2,'0')}</span><span>${esc(c.title)}</span></a>`).join('')}</nav><a class="sidebar-source" href="${bookUrl(book)}about.html">이 책의 출처와 이용 안내</a><a class="sidebar-source sidebar-all-books" href="${url('')}#library">전체 책장으로</a></div></details></aside>`;
}
const searchIndex=[];
function renderChapter(book,c){
 const {chapters,formulas,videos,examples}=book;
 const n=c.number;
 let source=read(c.file).replace(/^# .+\n+/,'');
 // These two supplied sections are rendered from their structured metadata below.
 if(book.generatedAppendixHeading)source=source.split('\n## '+book.generatedAppendixHeading)[0].trim();
 const env={book,file:c.file};
 const tokens=md.parse(source,env); const toc=[]; let headingN=0, section=null;
 for(let i=0;i<tokens.length;i++){
  const t=tokens[i];
  if(t.type==='heading_open'){
   const heading=tokens[i+1].content,id=`section-${++headingN}`;t.attrSet('id',id);
   if(t.tag==='h2'){toc.push({id,title:heading});section={bookId:book.id,bookTitle:book.title,chapter:n,chapterTitle:c.title,title:heading,url:chapterUrl(book,n)+'#'+id,text:''};searchIndex.push(section);}
  }
  if(t.type==='inline'&&section)section.text+=' '+t.content.replace(/!\[.*?\]\(.*?\)/g,'').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/\$[^$]*\$/g,' ').replace(/[`*]/g,'');
  if(t.type==='paragraph_open'&& tokens[i+1]?.children?.some(x=>x.type==='image'))t.attrSet('class','figure-block');
  if(t.type==='paragraph_open'&&tokens[i+1]?.content?.match(/^(직접 제작한 개념 도식|보충 계산 시각화)/))t.attrSet('class','figure-caption');
 }
 const html=md.renderer.render(tokens,md.options,env);
 const fc=formulas.filter(f=>f.chapter===n);
 const v=videos.find(v=>v.chapter===n);
 const ex=examples.find(e=>e.chapter===n);
 const exampleHtml=ex?`<section class="example-section" aria-labelledby="standalone-example"><h2 id="standalone-example">직접 실행해 보기</h2><div class="code-note"><span class="eyebrow">STANDALONE PYTHON EXAMPLE</span><h3>${esc(ex.title)}</h3><p>${esc(ex.purpose_ko)}</p><p class="example-scope">${esc(ex.scope_ko)}</p><ul>${ex.verified_claims_ko.map(claim=>`<li>${esc(claim)}</li>`).join('')}</ul><div class="code-links"><a href="${url(book.examplesBase+ex.file)}" download>이 장의 Python 코드</a><a href="${url(book.examplesBase+'README.ko.md')}">전체 예제 실행 안내</a><a href="${url(book.examplesBase+ex.figure)}" data-zoom="${url(book.examplesBase+ex.figure)}" data-caption="${esc(ex.title)} · 독립 실행 결과">실행 그래프 보기</a></div><details class="run-instructions"><summary>설치와 실행 방법</summary><p>Python 3.10 이상과 NumPy, SciPy, Matplotlib을 사용합니다. 코드 파일과 <a href="${url(book.examplesBase+'requirements.txt')}" download>requirements.txt</a>를 같은 폴더에 저장한 뒤 실행하세요.</p><pre><code>python -m pip install -r requirements.txt
${esc(ex.command)}</code></pre><p>결과 JSON과 그래프가 지정한 output 폴더에 저장됩니다. 다른 장의 코드나 계정, 외부 데이터가 필요하지 않습니다.</p><p><a href="${url(book.examplesBase+'README.ko.md')}">전체 실행 안내</a> · <a href="${url(book.examplesBase+'validation_summary.json')}">검증 환경과 결과</a></p></details><details class="source-preview"><summary>Python 코드 읽기</summary><pre><code>${esc(fs.readFileSync(safePath(OUT,book.examplesBase+ex.file),'utf8'))}</code></pre></details></div></section>`:'';
 const cardHtml=fc.length?`<section class="formula-section" aria-labelledby="formula-cards"><h2 id="formula-cards">핵심 수식 카드</h2><p>핵심 식과 성립 가정을 펼쳐 보며 복습하세요. 수식은 선택·복사가 가능하며 화면 낭독기를 위한 수학 표기를 포함합니다.</p><div class="formula-list">${fc.map((f,i)=>`<details class="formula-card" id="${f.id}"><summary><span class="formula-index">${String(i+1).padStart(2,'0')}</span><span>${esc(f.title)}</span><span class="expand-symbol" aria-hidden="true">+</span></summary><div class="formula-body"><p class="formula-caption">${esc(f.caption)}</p>${f.latex.map(eq=>`<div class="math-block" tabindex="0" aria-label="수식, 가로로 스크롤할 수 있습니다">${renderMath(eq,true)}</div>`).join('')}<div class="assumptions"><strong>성립 가정과 읽을 때의 주의점</strong><ul>${f.assumptions.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div><p class="small-note">${esc(f.attribution)}</p></div></details>`).join('')}</div></section>`:'';
 const videoHtml=v?`<section class="video-section" aria-labelledby="related-video"><h2 id="related-video">관련 영상</h2><div class="video-card"><span class="video-label">영상으로 다시 보기 · ${esc(v.provider)}</span><h3><a href="${v.url}" rel="noopener noreferrer">${esc(v.title)}</a></h3><p>${esc(v.note)}</p><a class="video-source" href="${v.source_url}" rel="noopener noreferrer">영상 제공 기관의 안내</a><p class="small-note">${esc(v.verification_note)}</p></div></section>`:'';
 if(ex)toc.push({id:'standalone-example',title:'직접 실행해 보기'});
 if(fc.length)toc.push({id:'formula-cards',title:'핵심 수식 카드'});
 if(v)toc.push({id:'related-video',title:'관련 영상'});
 if(!section)searchIndex.push({bookId:book.id,bookTitle:book.title,chapter:n,chapterTitle:c.title,title:c.title,url:chapterUrl(book,n),text:source});
 const tocHtml=`<nav class="local-toc" aria-label="이 장의 목차"><span class="eyebrow">ON THIS PAGE</span><h2>이 장에서</h2><ol>${toc.map(h=>`<li><a href="#${h.id}">${esc(h.title.replace(/^\d+\.?\s+/,''))}</a></li>`).join('')}</ol></nav>`;

 const position=chapters.findIndex(ch=>ch.number===n),prev=chapters[position-1],next=chapters[position+1];
 const nav=`<nav class="page-turn" aria-label="이전 다음 장">${prev?`<a href="${chapterUrl(book,prev.number)}"><span>이전 장</span><strong>${String(prev.number).padStart(2,'0')} ${esc(prev.title)}</strong></a>`:`<a href="${bookUrl(book)}"><span>이 책의 목차로</span><strong>${esc(book.title)}</strong></a>`}${next?`<a href="${chapterUrl(book,next.number)}"><span>다음 장</span><strong>${String(next.number).padStart(2,'0')} ${esc(next.title)}</strong></a>`:`<a href="${bookUrl(book)}"><span>마지막 장입니다</span><strong>이 책의 목차로 돌아가기</strong></a>`}</nav>`;
 const content=`<div class="reading-progress" aria-hidden="true"><span></span></div><div class="reading-layout">${sidebar(book,n)}<main id="main" class="chapter-main"><header class="chapter-heading"><nav class="breadcrumbs" aria-label="현재 위치"><a href="${url('')}#library">책장</a><span aria-hidden="true">/</span><a href="${bookUrl(book)}">${esc(book.title)}</a></nav><div class="chapter-kicker">CHAPTER ${String(n).padStart(2,'0')} <span>${esc(book.language||'학습 노트')}</span></div><h1>${esc(c.title)}</h1><p class="chapter-deck">${esc(chapterDescription(book,c))}</p><div class="chapter-meta"><span>${position+1} / ${chapters.length}개 장</span>${book.diagrams.some(d=>d.chapter===n)?`<span>개념 도식 ${book.diagrams.filter(d=>d.chapter===n).length}</span>`:''}${fc.length?`<span>핵심 수식 카드 ${fc.length}</span>`:''}</div></header>${toc.length?`<details class="mobile-toc"><summary>이 장의 목차</summary>${tocHtml}</details>`:''}<article class="prose">${html}${exampleHtml}${cardHtml}${videoHtml}</article>${nav}</main><aside class="toc-sidebar">${tocHtml}</aside></div>`;
 return shell({title:`${n}장 · ${c.title}`,description:chapterDescription(book,c),content,kind:'chapter',book,canonical:chapterPath(book,n)});
}
function bookStats(book){
 return [`${book.chapters.length}개 장`,...(book.diagrams.length?[`도식 ${book.diagrams.length}개`]:[]),...(book.formulas.length?[`수식 카드 ${book.formulas.length}개`]:[])];
}
function renderHome(){
 const totalChapters=books.reduce((sum,b)=>sum+b.chapters.length,0);
 const content=`<main id="main" class="home-main"><section class="library-intro"><div><p class="eyebrow">A GROWING LIBRARY OF IDEAS</p><h1>읽은 책이,<br>내 지식이 되는 곳<span class="accent-dot">.</span></h1><p class="intro-text">한 권씩 읽고, 핵심을 정리하고, 다시 꺼내 봅니다.<br>책마다 쌓아 가는 개념과 수식, 예제의 기록.</p><a class="primary-link" href="#library">책장 둘러보기</a></div><div class="library-index" aria-label="책장 현황"><span class="eyebrow">THE COLLECTION</span><p class="collection-number">${String(books.length).padStart(2,'0')}<span>권의 책</span></p><p>${totalChapters}개 장의 학습 노트</p><div class="collection-rule"></div><p class="collection-caption">서로 다른 책,<br>하나씩 깊어지는 이해.</p></div></section><section class="library-section" id="library" aria-labelledby="library-title"><div class="section-heading"><div><span class="eyebrow">THE BOOKSHELF</span><h2 id="library-title">책장</h2></div><p>책을 고르면 소개와 전체 목차를 볼 수 있습니다</p></div><div class="book-grid">${books.map((b,i)=>`<a class="book-card" href="${bookUrl(b)}" data-book-id="${b.id}"><div class="book-cover" aria-hidden="true"><div class="book-cover-top"><span>STUDY NOTES</span><span>${String(i+1).padStart(2,'0')}</span></div><span class="book-cover-title">${esc(b.title)}</span><span class="book-cover-subtitle">${esc(b.subtitle||'')}</span><div class="book-cover-line"></div><span class="book-cover-author">${esc(b.authors.join(' · '))}</span></div><div class="book-card-copy"><span class="eyebrow">${esc(b.category)}</span><h3>${esc(b.title)}</h3>${b.subtitle?`<p class="book-card-subtitle">${esc(b.subtitle)}</p>`:''}<p class="book-card-description">${esc(b.description)}</p><p class="book-card-authors">${esc(b.authors.join(' · '))}</p><div class="card-tags">${bookStats(b).map(s=>`<span>${s}</span>`).join('')}</div><span class="card-read">책 소개와 목차 보기 <span aria-hidden="true">↗</span></span></div></a>`).join('')}</div></section><section class="reading-note"><span class="note-label">노트를 읽는 방법</span><div><h2>책에서 출발해, 이해한 만큼 쌓아 갑니다</h2><p>책별 소개에서 학습 범위와 목차를 확인하세요. 각 장의 설명과 예제를 따라 읽고, 검색으로 필요한 개념을 다시 찾아볼 수 있습니다.</p><p>학습 노트는 원전을 대신하지 않습니다. 책마다 참고 판본과 출처를 따로 기록하며, 원전의 내용과 직접 구성한 보충 설명을 구분합니다.</p><a href="${url('about.html')}">사이트 안내 읽기</a></div></section></main>`;
 return shell({title:'책장',description:'책별로 쌓아 가는 한국어 학습 노트. 책 소개와 장별 목차, 개념·수식·예제를 한곳에서 읽고 검색합니다.',content});
}
function renderBook(book){
 const {chapters}=book;
 const content=`<main id="main" class="home-main"><nav class="breadcrumbs book-breadcrumbs" aria-label="현재 위치"><a href="${url('')}#library">전체 책장</a><span aria-hidden="true">/</span><span>${esc(book.category)}</span></nav><section class="home-intro book-intro"><div class="intro-copy"><p class="eyebrow">${esc(book.category)} · BOOK NOTES</p><h1>${esc(book.title)}</h1>${book.subtitle?`<p class="book-subtitle">${esc(book.subtitle)}</p>`:''}<p class="intro-text">${esc(book.description)}</p><a class="primary-link" href="${chapterUrl(book,chapters[0].number)}">${chapters[0].number}장부터 읽기</a><a class="book-source-link" href="${bookUrl(book)}about.html">이 책의 출처와 이용 안내</a><span class="intro-footnote">${bookStats(book).join(' · ')}</span></div><div class="reference-card"><div class="reference-topline"><span>함께 읽는 책</span><span>${esc(book.category)}</span></div><div class="reference-title">${esc(book.title)}</div>${book.subtitle?`<div class="reference-subtitle">${esc(book.subtitle)}</div>`:''}<div class="reference-rule"></div><p class="reference-author">${book.authors.map(esc).join('<br>')}</p><div class="reference-bottom"><span>${esc(book.edition||'참고 자료는 출처 안내에서 확인')}</span><span>${esc(book.language||'학습 노트')}</span></div></div></section><section class="library-section" id="chapters" aria-labelledby="chapters-title"><div class="section-heading"><div><span class="eyebrow">THE CHAPTERS</span><h2 id="chapters-title">이 책의 목차</h2></div><p>${chapters.length}개 장의 학습 노트</p></div><div class="chapter-grid">${chapters.map(c=>`<a class="chapter-card" href="${chapterUrl(book,c.number)}"><div class="card-top"><span class="card-number">${String(c.number).padStart(2,'0')}</span><span class="card-category">${esc(c.category||book.category)}</span></div><h3>${esc(c.title)}</h3><p>${esc(chapterDescription(book,c))}</p>${c.tags?.length?`<div class="card-tags">${c.tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div>`:''}<span class="card-read">학습 노트 읽기</span></a>`).join('')}</div></section><section class="reading-note"><span class="note-label">읽기 전에</span><div><h2>가정과 출처를 함께 확인하세요</h2><p>이 책을 공부하며 정리한 비공식 학습 자료입니다. 본문의 예제와 보충 설명을 읽을 때 참고 판본, 모델의 가정과 적용 범위를 함께 확인해 주세요.</p><a href="${bookUrl(book)}about.html">이 책의 출처와 이용 안내 읽기</a></div></section></main>`;
 return shell({title:'책 소개와 목차',description:book.description,content,kind:'book',book,canonical:bookPath(book)});
}
function renderBookAbout(book){
 const extras=book.diagrams.length || book.formulas.length?`<h2>수식과 시각화</h2><p>본문 수식은 KaTeX로 미리 조판하며 화면 낭독기를 위한 MathML을 포함합니다. ${book.diagrams.length?`직접 제작한 도식 ${book.diagrams.length}개를 포함합니다. `:''}${book.formulas.length?`수식 카드 ${book.formulas.length}개로 복습할 수 있습니다.`:''} 원전의 도판이나 스캔 이미지는 포함하지 않습니다.</p>`:'';
 return shell({title:'출처와 이용 안내',description:`${book.title} 학습 노트의 참고 판본, 출처와 이용 범위`,kind:'about',book,canonical:bookPath(book)+'about.html',content:`<main id="main" class="about-main"><nav class="breadcrumbs" aria-label="현재 위치"><a href="${url('')}#library">책장</a><span aria-hidden="true">/</span><a href="${bookUrl(book)}">${esc(book.title)}</a></nav><p class="eyebrow">${esc(book.title)}</p><div class="prose">${md.render(read(book.attributionFile),{book,file:book.attributionFile})}${extras}${book.officialUrl?`<p><a href="${esc(book.officialUrl)}" rel="noopener noreferrer">저자·출판사의 공식 교재 안내</a></p>`:''}${book.examples.length?`<h2>계산 예제와 재현</h2><p>이 책의 Python 예제 ${book.examples.length}개는 다른 장이나 외부 저장소를 불러오지 않고 단독 실행할 수 있습니다. 설치 이후 실행에는 네트워크 연결이 필요하지 않습니다. <a href="${url(book.examplesBase+'README.ko.md')}">전체 실행 안내</a></p>`:''}<p><a href="${url('about.html')}">사이트 공통 이용 안내</a></p></div></main>`});
}
function renderAbout(){
 return shell({title:'사이트 안내',description:'Study Notes의 구성, 학습 자료의 출처와 이용 범위',kind:'about',canonical:'about.html',content:`<main id="main" class="about-main"><a class="breadcrumb" href="${url('')}#library">책장으로 돌아가기</a><div class="prose"><h1>Study Notes에 대하여</h1><p>여러 책을 읽으며 개념, 수식과 예제를 한국어로 정리하는 개인 학습 노트입니다. 책마다 소개, 목차, 본문과 출처 안내를 따로 두어 한 권씩 계속 추가할 수 있습니다.</p><h2>책별로 읽고, 함께 검색하기</h2><p>책장에서 책을 고르면 학습 범위와 장별 목차를 볼 수 있습니다. 장 안의 이전·다음 링크는 같은 책 안에서 이어집니다. 검색에서는 모든 책을 함께 찾거나 한 권만 골라 찾을 수 있습니다.</p><h2>참고 자료와 출처</h2><p>공식 번역본이나 원전을 대체하는 자료가 아닙니다. 책마다 참고 판본과 출처, 보충 설명의 범위를 기록합니다.</p><ul>${books.map(b=>`<li><a href="${bookUrl(b)}about.html">${esc(b.title)} · 출처와 이용 안내</a></li>`).join('')}</ul><h2>이용 범위와 검토</h2><p>원전의 저작권은 권리자에게 있습니다. 원전 PDF, 스캔과 출판사 도판은 재배포하지 않습니다. 출처 표시는 교재나 제3자 자료에 대한 포괄적인 재사용 허락을 뜻하지 않습니다.</p><p>AI의 도움으로 작성되어 오류가 있을 수 있습니다. 수식, 가정과 수치 결과는 원전과 독립 계산으로 확인해 주세요.</p><h2>사이트 소스와 수식 표시</h2><p>학습 원고, 책 등록 정보와 사이트 생성 코드는 <a href="${repo}">GitHub 저장소</a>에서 확인할 수 있습니다. 책을 추가하는 방법은 저장소의 안내에 정리되어 있습니다.</p><p>수식은 KaTeX로 미리 조판하며 접근성을 위한 MathML을 포함합니다. 포함된 KaTeX 소프트웨어의 MIT 라이선스는 학습 자료 전체에 적용되지 않습니다. <a href="${url('assets/katex/LICENSE.txt')}">KaTeX 라이선스 보기</a></p></div></main>`});
}

const generated=[];
function writePage(file,html){const target=safePath(OUT,file);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,html);generated.push(file);}
const manifestFile=path.join(OUT,'assets/page-manifest.json');
const previous=fs.existsSync(manifestFile)?JSON.parse(fs.readFileSync(manifestFile,'utf8')):[];
for(const book of books){
 writePage(bookPath(book)+'index.html',renderBook(book));
 writePage(bookPath(book)+'about.html',renderBookAbout(book));
 for(const c of book.chapters){
  const html=renderChapter(book,c);writePage(chapterPath(book,c.number),html);
  // Readable compatibility pages retain fragments and work even with JavaScript disabled.
  // Their canonical link and every navigation URL point to the new book-scoped page.
  if(book.legacyChapterUrls)writePage(`chapters/chapter${String(c.number).padStart(2,'0')}.html`,html);
 }
}
writePage('index.html',renderHome());
writePage('about.html',renderAbout());
writePage('404.html',shell({title:'페이지를 찾을 수 없습니다',description:'페이지 주소를 확인하거나 책장으로 돌아가세요.',kind:'about',canonical:'404.html',content:`<main id="main" class="about-main"><p class="eyebrow">404</p><h1>페이지를 찾을 수 없습니다</h1><p>주소가 바뀌었거나 존재하지 않는 페이지입니다.</p><a class="primary-link" href="${url('')}">책장으로 돌아가기</a></main>`}));
// Remove only HTML pages listed by a prior build; uploaded assets are never removed.
for(const stale of previous.filter(file=>!generated.includes(file))){if(typeof stale==='string' && stale.endsWith('.html'))fs.rmSync(safePath(OUT,stale),{force:true});}
fs.mkdirSync(path.join(OUT,'assets/katex/fonts'),{recursive:true});
fs.writeFileSync(manifestFile,JSON.stringify(generated,null,2)+'\n');
fs.writeFileSync(path.join(OUT,'assets/search-index.json'),JSON.stringify(searchIndex));
for(const f of ['site.css','site.js','search.mjs','favicon.svg'])fs.copyFileSync(path.join(ROOT,'src',f),path.join(OUT,'assets',f));
const css=fs.readFileSync(path.join(ROOT,'node_modules/katex/dist/katex.min.css'),'utf8').replace(/,url\([^)]*\) format\("(?:woff|truetype)"\)/g,'');
fs.writeFileSync(path.join(OUT,'assets/katex/katex.min.css'),css);
for(const f of fs.readdirSync(path.join(ROOT,'node_modules/katex/dist/fonts')).filter(f=>f.endsWith('.woff2')))fs.copyFileSync(path.join(ROOT,'node_modules/katex/dist/fonts',f),path.join(OUT,'assets/katex/fonts',f));
fs.copyFileSync(path.join(ROOT,'node_modules/katex/LICENSE'),path.join(OUT,'assets/katex/LICENSE.txt'));
fs.writeFileSync(path.join(OUT,'.nojekyll'),'');
fs.mkdirSync(QA,{recursive:true});
const bookReports=books.map(b=>({id:b.id,title:b.title,chapters:b.chapters.length,chapterNumbers:b.chapters.map(c=>c.number),diagrams:b.diagrams.length,formulaCards:b.formulas.length,standaloneExamples:b.examples.length,legacyChapterUrls:!!b.legacyChapterUrls}));
const report={books:books.length,bookDetails:bookReports,chapters:bookReports.reduce((n,b)=>n+b.chapters,0),diagrams:bookReports.reduce((n,b)=>n+b.diagrams,0),formulaCards:bookReports.reduce((n,b)=>n+b.formulaCards,0),standaloneExamples:bookReports.reduce((n,b)=>n+b.standaloneExamples,0),renderedExpressions:equationCount,searchSections:searchIndex.length,generatedPages:generated.length,base:BASE};
fs.writeFileSync(path.join(QA,'build-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(`Built ${report.books} books, ${report.chapters} chapters, ${equationCount} expressions, ${searchIndex.length} searchable sections. Base: ${BASE}`);
