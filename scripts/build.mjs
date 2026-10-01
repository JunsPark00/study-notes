import fs from 'node:fs';
import path from 'node:path';
import MarkdownIt from 'markdown-it';
import katex from 'katex';

const ROOT = path.resolve(import.meta.dirname, '..');
const SOURCE = path.join(ROOT, 'content');
const OUT = path.join(ROOT, 'docs');
const BASE = process.env.SITE_BASE || '/study-notes/';
if (!BASE.startsWith('/') || !BASE.endsWith('/')) throw new Error('SITE_BASE must start and end with /');
const ORIGIN = 'https://junspark00.github.io';
const read = f => fs.readFileSync(path.join(SOURCE, f), 'utf8');
const json = f => JSON.parse(read(f));
const chapters = json('chapters.json');
const formulas = json('formulas.json');
const diagrams = json('diagrams.json');
const videos = json('videos.json');
const examples = JSON.parse(fs.readFileSync(path.join(OUT,'examples/manifest.json'),'utf8')).chapters;
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const url = s => BASE+s;
const chapterUrl = n => url(`chapters/chapter${String(n).padStart(2,'0')}.html`);
const descriptions = [
  '모델, 이산화, 최적 제어와 상태 추정을 하나의 제어 순환으로 연결합니다.',
  '제약을 만족하는 해가 다음 시점에도 존재하는 이유와 안정성 조건을 살펴봅니다.',
  '모델 오차와 외란을 최악의 경우와 확률의 관점에서 다룹니다.',
  '센서와 모델을 결합해 보이지 않는 상태를 추정하고, 과거 정보를 요약합니다.',
  '추정과 제어를 연결하고, 외란 모델과 정상 목표로 추종 오차를 다룹니다.',
  '서로 연결된 제어기들이 예측과 자원을 나누며 협력하는 방법을 살펴봅니다.',
  '최적화의 답을 미리 구해 두고, 상태에 맞는 제어법칙을 찾아 적용합니다.',
  '이산화부터 SQP와 도함수 검증까지, 실제로 풀 수 있는 문제를 구성합니다.'
];
const tags = [ ['모델','LQR','상태 추정'], ['실행 가능성','종단 조건'], ['불확실성','Tube MPC'], ['Kalman filter','MHE'], ['추정 오차','Offset-free'], ['협력','공유 제약'], ['mpQP','활성 집합'], ['Shooting','SQP'] ];
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
const oldLink=md.renderer.rules.link_open || ((ts,i,o,e,self)=>self.renderToken(ts,i,o));
md.renderer.rules.link_open=(ts,i,o,e,self)=>{
  let href=ts[i].attrGet('href');
  if(href?.startsWith('../../docs/assets/'))ts[i].attrSet('href',url(href.slice(11)));
  else if(href?.startsWith('../assets/'))ts[i].attrSet('href',url(href.slice(3)));
  if(/^https?:/.test(href))ts[i].attrSet('rel','noopener noreferrer');
  return oldLink(ts,i,o,e,self);
};
md.renderer.rules.image=(ts,i)=>{
  const t=ts[i], src=t.attrGet('src').replace('../../docs/assets/','assets/').replace('../assets/','assets/');
  const d=diagrams.find(d=>d.svg===src || d.image===src);
  const alt=d?.alt || t.content;
  return `<a class="figure-link" href="${url(d?.image||src)}" data-zoom="${url(d?.svg||src)}" data-caption="${esc(d?.caption||alt)}" aria-label="${esc(d?.caption||alt)} 확대 보기"><img src="${url(src)}" alt="${esc(alt)}" loading="lazy" decoding="async"><span class="zoom-hint">그림 확대</span></a>`;
};
const iconSearch='<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/></svg>';
const repo='https://github.com/JunsPark00/study-notes';
const footer=()=>`<footer class="site-footer"><div class="footer-inner"><div><a class="footer-brand" href="${url('')}">MPC 학습 노트</a><p>Rawlings · Mayne · Diehl 교재를 읽는 비공식 한국어 노트</p></div><div class="footer-links"><a href="${url('about.html')}">출처와 이용 안내</a><a href="${repo}">GitHub</a><a href="https://sites.engineering.ucsb.edu/~jbraw/mpc/">공식 교재</a></div><p class="footer-fine">AI의 도움으로 작성되었습니다. 수식과 가정은 원전 및 독립 계산으로 확인해 주세요.<br>원전의 저작권은 권리자에게 있으며, 출처 표시는 재사용 허락을 뜻하지 않습니다.</p></div></footer>`;
function shell({title,description,content,kind='home',canonical=''}){
 return `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="${esc(description)}"><meta name="color-scheme" content="light"><title>${esc(title)} · MPC 학습 노트</title><link rel="canonical" href="${ORIGIN+url(canonical)}"><link rel="icon" href="${url('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="${url('assets/katex/katex.min.css')}"><link rel="stylesheet" href="${url('assets/site.css')}"><script src="${url('assets/site.js')}" defer></script></head><body data-base="${BASE}" class="${kind}"><a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="header-inner"><a class="brand" href="${url('')}" aria-label="Study Notes 홈"><span class="brand-mark" aria-hidden="true">M</span><span>Study <b>Notes</b></span></a><nav aria-label="주 메뉴"><a class="header-library" href="${url('')}#library">책장</a><a class="header-about" href="${url('about.html')}">이 노트에 대하여</a><button class="search-trigger" aria-haspopup="dialog">${iconSearch}<span>검색</span><kbd>/</kbd></button></nav></div></header>${content}${footer()}<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-top"><h2 id="search-title">노트 검색</h2><button class="icon-button dialog-close" type="button" aria-label="검색 닫기">×</button></div><form role="search" id="search-form"><label class="sr-only" for="search-input">개념 또는 키워드 검색</label><div class="search-field">${iconSearch}<input id="search-input" type="search" placeholder="MHE, 안정성, Riccati…" autocomplete="off"></div></form><p id="search-status" role="status" aria-live="polite">개념이나 키워드를 입력하면 모든 장에서 찾아드립니다</p><div id="search-results"></div></dialog><dialog id="figure-dialog" aria-labelledby="figure-title"><div class="dialog-top"><h2 id="figure-title">그림 확대</h2><div><button class="text-button" id="figure-size" type="button" aria-pressed="false">실제 크기</button><button class="icon-button dialog-close" type="button" aria-label="그림 닫기">×</button></div></div><div class="figure-viewport"><img id="figure-image" alt=""></div><p class="figure-dialog-hint">Esc 키 또는 닫기 버튼으로 본문에 돌아갑니다</p></dialog></body></html>`;
}
function sidebar(active){
 return `<aside class="chapter-sidebar"><details id="chapter-menu" open><summary>전체 목차 <span aria-hidden="true">⌄</span></summary><div class="sidebar-content"><a class="sidebar-book" href="${url('')}#library"><span class="eyebrow">MODEL PREDICTIVE CONTROL</span><strong>이론을 읽고,<br>계산으로 확인하기</strong></a><nav aria-label="장별 목차">${chapters.map(c=>`<a class="chapter-nav-link ${active===c.number?'current':''}" href="${chapterUrl(c.number)}" ${active===c.number?'aria-current="page"':''}><span class="chapter-num">${String(c.number).padStart(2,'0')}</span><span>${esc(c.title)}</span></a>`).join('')}</nav><a class="sidebar-source" href="${url('about.html')}">출처와 이용 안내</a></div></details></aside>`;
}
const searchIndex=[];
function renderChapter(c){
 const n=c.number;
 let source=read(c.file).replace(/^# .+\n+/,'');
 // These two supplied sections are rendered from their structured metadata below.
 source=source.split('\n## 핵심 수식 카드')[0].trim();
 const tokens=md.parse(source,{}); const toc=[]; let headingN=0, section=null;
 for(let i=0;i<tokens.length;i++){
  const t=tokens[i];
  if(t.type==='heading_open'){
   const heading=tokens[i+1].content,id=`section-${++headingN}`;t.attrSet('id',id);
   if(t.tag==='h2'){toc.push({id,title:heading});section={chapter:n,chapterTitle:c.title,title:heading,url:chapterUrl(n)+'#'+id,text:''};searchIndex.push(section);}
  }
  if(t.type==='inline'&&section)section.text+=' '+t.content.replace(/!\[.*?\]\(.*?\)/g,'').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/\$[^$]*\$/g,' ').replace(/[`*]/g,'');
  if(t.type==='paragraph_open'&& tokens[i+1]?.children?.some(x=>x.type==='image'))t.attrSet('class','figure-block');
  if(t.type==='paragraph_open'&&tokens[i+1]?.content?.match(/^(직접 제작한 개념 도식|보충 계산 시각화)/))t.attrSet('class','figure-caption');
 }
 const html=md.renderer.render(tokens,md.options,{});
 const fc=formulas.filter(f=>f.chapter===n);
 const v=videos.find(v=>v.chapter===n);
 const ex=examples.find(e=>e.chapter===n);
 const exampleHtml=`<section class="example-section" aria-labelledby="standalone-example"><h2 id="standalone-example">직접 실행해 보기</h2><div class="code-note"><span class="eyebrow">STANDALONE PYTHON EXAMPLE</span><h3>${esc(ex.title)}</h3><p>${esc(ex.purpose_ko)}</p><p class="example-scope">${esc(ex.scope_ko)}</p><ul>${ex.verified_claims_ko.map(claim=>`<li>${esc(claim)}</li>`).join('')}</ul><div class="code-links"><a href="${url('examples/'+ex.file)}" download>이 장의 Python 코드</a><a href="${url('examples/README.ko.md')}">전체 예제 실행 안내</a><a href="${url('examples/'+ex.figure)}" data-zoom="${url('examples/'+ex.figure)}" data-caption="${esc(ex.title)} · 독립 실행 결과">실행 그래프 보기</a></div><details class="run-instructions"><summary>설치와 실행 방법</summary><p>Python 3.10 이상과 NumPy, SciPy, Matplotlib을 사용합니다. 코드 파일과 <a href="${url('examples/requirements.txt')}" download>requirements.txt</a>를 같은 폴더에 저장한 뒤 실행하세요.</p><pre><code>python -m pip install -r requirements.txt
${esc(ex.command)}</code></pre><p>결과 JSON과 그래프가 지정한 output 폴더에 저장됩니다. 다른 장의 코드나 계정, 외부 데이터가 필요하지 않습니다.</p><p><a href="${url('examples/README.ko.md')}">전체 실행 안내</a> · <a href="${url('examples/validation_summary.json')}">검증 환경과 결과</a></p></details><details class="source-preview"><summary>Python 코드 읽기</summary><pre><code>${esc(fs.readFileSync(path.join(OUT,'examples',ex.file),'utf8'))}</code></pre></details></div></section>`;
 const cardHtml=`<section class="formula-section" aria-labelledby="formula-cards"><h2 id="formula-cards">핵심 수식 카드</h2><p>핵심 식과 성립 가정을 펼쳐 보며 복습하세요. 수식은 선택·복사가 가능하며 화면 낭독기를 위한 수학 표기를 포함합니다.</p><div class="formula-list">${fc.map((f,i)=>`<details class="formula-card" id="${f.id}"><summary><span class="formula-index">${String(i+1).padStart(2,'0')}</span><span>${esc(f.title)}</span><span class="expand-symbol" aria-hidden="true">+</span></summary><div class="formula-body"><p class="formula-caption">${esc(f.caption)}</p>${f.latex.map(eq=>`<div class="math-block" tabindex="0" aria-label="수식, 가로로 스크롤할 수 있습니다">${renderMath(eq,true)}</div>`).join('')}<div class="assumptions"><strong>성립 가정과 읽을 때의 주의점</strong><ul>${f.assumptions.map(a=>`<li>${esc(a)}</li>`).join('')}</ul></div><p class="small-note">${esc(f.attribution)}</p></div></details>`).join('')}</div></section>`;
 const videoHtml=`<section class="video-section" aria-labelledby="related-video"><h2 id="related-video">관련 영상</h2><div class="video-card"><span class="video-label">영상으로 다시 보기 · ${esc(v.provider)}</span><h3><a href="${v.url}" rel="noopener noreferrer">${esc(v.title)}</a></h3><p>${esc(v.note)}</p><a class="video-source" href="${v.source_url}" rel="noopener noreferrer">영상 제공 기관의 안내</a><p class="small-note">${esc(v.verification_note)}</p></div></section>`;
 toc.push({id:'standalone-example',title:'직접 실행해 보기'},{id:'formula-cards',title:'핵심 수식 카드'},{id:'related-video',title:'관련 영상'});
 const tocHtml=`<nav class="local-toc" aria-label="이 장의 목차"><span class="eyebrow">ON THIS PAGE</span><h2>이 장에서</h2><ol>${toc.map(h=>`<li><a href="#${h.id}">${esc(h.title.replace(/^\d+\.?\s+/,''))}</a></li>`).join('')}</ol></nav>`;
 const prev=n>1?chapters[n-2]:null,next=n<8?chapters[n]:null;
 const nav=`<nav class="page-turn" aria-label="이전 다음 장">${prev?`<a href="${chapterUrl(prev.number)}"><span>이전 장</span><strong>${String(prev.number).padStart(2,'0')} ${prev.title}</strong></a>`:`<a href="${url('')}"><span>책장으로</span><strong>전체 학습 안내</strong></a>`}${next?`<a href="${chapterUrl(next.number)}"><span>다음 장</span><strong>${String(next.number).padStart(2,'0')} ${next.title}</strong></a>`:`<a href="${chapterUrl(1)}"><span>다시 읽기</span><strong>01 MPC 시작하기</strong></a>`}</nav>`;
 const content=`<div class="reading-progress" aria-hidden="true"><span></span></div><div class="reading-layout">${sidebar(n)}<main id="main" class="chapter-main"><header class="chapter-heading"><a class="breadcrumb" href="${url('')}#library">책장 / Model Predictive Control</a><div class="chapter-kicker">CHAPTER ${String(n).padStart(2,'0')} <span>한국어 학습 노트</span></div><h1>${esc(c.title)}</h1><p class="chapter-deck">${descriptions[n-1]}</p><div class="chapter-meta"><span>${n} / 8장</span><span>개념 도식 ${c.diagram_count}</span><span>핵심 수식 카드 4</span></div></header><details class="mobile-toc"><summary>이 장의 목차</summary>${tocHtml}</details><article class="prose">${html}${exampleHtml}${cardHtml}${videoHtml}</article>${nav}</main><aside class="toc-sidebar">${tocHtml}</aside></div>`;
 return shell({title:`${n}장 · ${c.title}`,description:descriptions[n-1],content,kind:'chapter',canonical:`chapters/chapter${String(n).padStart(2,'0')}.html`});
}
function renderHome(){
 const content=`<main id="main" class="home-main"><section class="home-intro"><div class="intro-copy"><p class="eyebrow">A NOTEBOOK ON CONTROL THEORY</p><h1>모델 예측 제어,<br>개념에서 계산까지<span class="accent-dot">.</span></h1><p class="intro-text">미래를 예측하고, 지금의 입력을 결정하는 방법.<br>교재를 따라 읽으며 수식의 가정과 계산의 의미를<br class="desktop-break"> 한국어로 차근차근 정리합니다.</p><a class="primary-link" href="${chapterUrl(1)}">1장부터 읽기</a><span class="intro-footnote">8개의 장 · 개념 도식 17개 · 수식 카드 32개</span></div><div class="reference-card"><div class="reference-topline"><span>함께 읽는 책</span><span>01</span></div><div class="reference-title">Model<br>Predictive<br>Control</div><div class="reference-subtitle">Theory, Computation,<br>and Design</div><div class="reference-rule"></div><p class="reference-author">James B. Rawlings<br>David Q. Mayne · Moritz M. Diehl</p><div class="reference-bottom"><span>2nd edition · 1st printing · 2017</span><span>학습 노트</span></div></div></section><section class="library-section" id="library" aria-labelledby="library-title"><div class="section-heading"><div><span class="eyebrow">THE CHAPTERS</span><h2 id="library-title">한 장씩, 깊이 있게</h2></div><p>기초 모델에서 수치 최적 제어까지 이어지는 학습 순서</p></div><div class="chapter-grid">${chapters.map(c=>`<a class="chapter-card" href="${chapterUrl(c.number)}"><div class="card-top"><span class="card-number">${String(c.number).padStart(2,'0')}</span><span class="card-category">${c.number<3?'FOUNDATIONS':c.number<7?'ESTIMATION & CONTROL':'COMPUTATION'}</span></div><h3>${esc(c.title)}</h3><p>${descriptions[c.number-1]}</p><div class="card-tags">${tags[c.number-1].map(t=>`<span>${t}</span>`).join('')}</div><span class="card-read">학습 노트 읽기</span></a>`).join('')}</div></section><section class="reading-note"><span class="note-label">읽기 전에</span><div><h2>식을 외우기 전에, 가정을 확인하세요</h2><p>각 장은 개념 설명, 손계산 예제, 보충 문제와 힌트로 이어집니다. 직접 제작한 도식과 펼쳐 보는 수식 카드는 복습을 돕습니다. 영상은 관련 주제를 보완하는 자료이며, 교재의 공식 장별 강의가 아닙니다.</p><p>이곳은 공식 번역이나 원문을 대체하는 자료가 아닙니다. 교재에서 가져온 모델·예제의 출처와 새로 구성한 보충 문제를 구분해 읽어 주세요.</p><a href="${url('about.html')}">출처와 이용 안내 읽기</a></div></section></main>`;
 return shell({title:'책장',description:'Rawlings·Mayne·Diehl의 Model Predictive Control을 읽기 위한 비공식 한국어 학습 노트. 8개 장의 개념, 수식, 예제와 시각화.',content});
}
fs.mkdirSync(path.join(OUT,'chapters'),{recursive:true});
fs.mkdirSync(path.join(OUT,'assets/katex/fonts'),{recursive:true});
for(const c of chapters)fs.writeFileSync(path.join(OUT,`chapters/chapter${String(c.number).padStart(2,'0')}.html`),renderChapter(c));
fs.writeFileSync(path.join(OUT,'index.html'),renderHome());
fs.writeFileSync(path.join(OUT,'about.html'),shell({title:'출처와 이용 안내',description:'학습 노트의 참고 판본, 출처, 저작권과 이용 범위 안내',kind:'about',canonical:'about.html',content:`<main id="main" class="about-main"><a class="breadcrumb" href="${url('')}">책장으로 돌아가기</a><div class="prose">${md.render(read('ATTRIBUTION.ko.md'))}<h2>수식과 시각화</h2><p>본문 수식은 KaTeX로 미리 조판하며 화면 낭독기를 위한 MathML을 포함합니다. 도식 17개와 수식 카드 32개는 학습 설명을 위해 새로 제작했습니다. 원전의 도판이나 스캔 이미지는 포함하지 않습니다.</p><h2>소스와 재현</h2><p>학습 노트 원문, 웹사이트 생성 코드, 독립 실행 예제와 시각화 재생성 스크립트는 <a href="${repo}">GitHub 저장소</a>에서 확인할 수 있습니다. 각 장의 Python 예제는 다른 장이나 외부 저장소를 불러오지 않고 단독 실행할 수 있습니다. 설치 이후 실행에는 네트워크 연결이 필요하지 않습니다.</p><p>KaTeX는 MIT 라이선스에 따라 포함됩니다. 해당 라이선스는 수식 표시 소프트웨어에만 적용되며, 교재나 이 사이트의 학습 자료에 대한 포괄적인 이용 허락을 뜻하지 않습니다. <a href="${url('assets/katex/LICENSE.txt')}">KaTeX 라이선스 보기</a></p></div></main>`}));
fs.writeFileSync(path.join(OUT,'404.html'),shell({title:'페이지를 찾을 수 없습니다',description:'페이지 주소를 확인하거나 책장으로 돌아가세요.',kind:'about',canonical:'404.html',content:`<main id="main" class="about-main"><p class="eyebrow">404</p><h1>페이지를 찾을 수 없습니다</h1><p>주소가 바뀌었거나 존재하지 않는 페이지입니다.</p><a class="primary-link" href="${url('')}">책장으로 돌아가기</a></main>`}));
fs.writeFileSync(path.join(OUT,'assets/search-index.json'),JSON.stringify(searchIndex));
for(const f of ['site.css','site.js','favicon.svg'])fs.copyFileSync(path.join(ROOT,'src',f),path.join(OUT,'assets',f));
const css=fs.readFileSync(path.join(ROOT,'node_modules/katex/dist/katex.min.css'),'utf8').replace(/,url\([^)]*\) format\("(?:woff|truetype)"\)/g,'');
fs.writeFileSync(path.join(OUT,'assets/katex/katex.min.css'),css);
for(const f of fs.readdirSync(path.join(ROOT,'node_modules/katex/dist/fonts')).filter(f=>f.endsWith('.woff2')))fs.copyFileSync(path.join(ROOT,'node_modules/katex/dist/fonts',f),path.join(OUT,'assets/katex/fonts',f));
fs.copyFileSync(path.join(ROOT,'node_modules/katex/LICENSE'),path.join(OUT,'assets/katex/LICENSE.txt'));
fs.writeFileSync(path.join(OUT,'.nojekyll'),'');
fs.mkdirSync(path.join(ROOT,'qa'),{recursive:true});
fs.writeFileSync(path.join(ROOT,'qa/build-report.json'),JSON.stringify({chapters:chapters.length,diagrams:diagrams.length,formulaCards:formulas.length,renderedExpressions:equationCount,searchSections:searchIndex.length,base:BASE},null,2));
console.log(`Built ${chapters.length} chapters, ${equationCount} expressions, ${searchIndex.length} searchable sections. Base: ${BASE}`);
