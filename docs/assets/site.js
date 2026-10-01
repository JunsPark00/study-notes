'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const $$ = s => [...document.querySelectorAll(s)];
  const searchDialog = $('#search-dialog');
  const input = $('#search-input');
  const results = $('#search-results');
  const status = $('#search-status');
  let indexPromise;
  let currentSearch = 0;
  const normalize = value => value.toLocaleLowerCase('ko').normalize('NFKC');
  const loadIndex = () => indexPromise || (indexPromise = fetch(document.body.dataset.base+'assets/search-index.json').then(response => { if (!response.ok) throw new Error('검색 자료를 불러올 수 없습니다'); return response.json(); }).catch(error => { indexPromise = null; throw error; }));
  const openSearch = () => { if (!searchDialog.open) searchDialog.showModal(); input.focus(); loadIndex().catch(() => { status.textContent = '검색 자료를 불러오지 못했습니다. 잠시 후 다시 검색해 주세요.'; }); };
  $$('.search-trigger').forEach(button => button.addEventListener('click', openSearch));
  $$('dialog').forEach(dialog => {
    dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });
  });
  document.addEventListener('keydown', event => {
    if ((event.key === '/' || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k')) && !event.altKey && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable && !$('#figure-dialog').open) {
      event.preventDefault(); openSearch();
    }
  });
  $('#search-form').addEventListener('submit', event => event.preventDefault());
  const highlight = (element,text,term) => {
    const lower=normalize(text), needle=normalize(term);
    let pos=0, found=lower.indexOf(needle);
    if (!needle) { element.textContent=text; return; }
    while(found!==-1){
      element.append(document.createTextNode(text.slice(pos,found)));
      const mark=document.createElement('mark');mark.textContent=text.slice(found,found+term.length);element.append(mark);
      pos=found+term.length;found=lower.indexOf(needle,pos);
    }
    element.append(document.createTextNode(text.slice(pos)));
  };
  input.addEventListener('input', async () => {
    const request = ++currentSearch;
    const query=input.value.trim();
    results.replaceChildren();
    if (!query) { status.textContent='개념이나 키워드를 입력하면 모든 장에서 찾아드립니다'; return; }
    status.textContent='검색 중…';
    try {
      const data=await loadIndex(); if (request!==currentSearch) return;
      const terms=normalize(query).split(/\s+/);
      const matches=data.map(record=>{
        const haystack=normalize(record.chapterTitle+' '+record.title+' '+record.text);
        const score=terms.every(term=>haystack.includes(term)) ? terms.reduce((score,term)=>score+(normalize(record.title).includes(term)?12:0)+(normalize(record.chapterTitle).includes(term)?4:0),1) : 0;
        return {...record,score};
      }).filter(record=>record.score).sort((a,b)=>b.score-a.score || a.chapter-b.chapter);
      status.textContent=matches.length ? `${matches.length}개의 문단을 찾았습니다${matches.length>30?' · 앞의 30개 표시':''}` : '검색 결과가 없습니다. 다른 개념이나 짧은 키워드로 검색해 보세요.';
      for(const record of matches.slice(0,30)){
        const a=document.createElement('a');a.className='search-result';a.href=record.url;
        const chapter=document.createElement('span');chapter.textContent=`${record.chapter}장 · ${record.chapterTitle}`;
        const title=document.createElement('strong');highlight(title,record.title,query);
        const preview=document.createElement('p');const text=record.text.replace(/\s+/g,' ').trim();const at=normalize(text).indexOf(terms[0]);const start=Math.max(0,at-40);const snippet=(start?'…':'')+text.slice(start,start+150)+(text.length>start+150?'…':'');highlight(preview,snippet,query);
        a.append(chapter,title,preview);a.addEventListener('click',()=>searchDialog.close());results.append(a);
      }
    } catch(error){if(request===currentSearch)status.textContent='검색 자료를 불러오지 못했습니다. 연결을 확인하고 다시 검색해 주세요.';}
  });
  const figureDialog=$('#figure-dialog'), figureImage=$('#figure-image'), viewport=$('.figure-viewport'), sizeButton=$('#figure-size');
  $$('[data-zoom]').forEach(link=>link.addEventListener('click',event=>{
    event.preventDefault();figureImage.src=link.dataset.zoom;figureImage.alt=link.dataset.caption;$('#figure-title').textContent=link.dataset.caption;
    viewport.classList.remove('is-actual');sizeButton.textContent='실제 크기';sizeButton.setAttribute('aria-pressed','false');figureDialog.showModal();
  }));
  sizeButton.addEventListener('click',()=>{const actual=viewport.classList.toggle('is-actual');sizeButton.setAttribute('aria-pressed',String(actual));sizeButton.textContent=actual?'화면에 맞추기':'실제 크기';});
  figureDialog.addEventListener('close',()=>{figureImage.removeAttribute('src');});
  const menu=$('#chapter-menu');
  if(menu){
    const query=matchMedia('(max-width:680px)');
    const setMenu=()=>{menu.open=!query.matches;}; setMenu();query.addEventListener('change',setMenu);
  }
  const headings=$$('.prose h2[id]');
  const tocLinks=$$('.local-toc a');
  const progress=$('.reading-progress span');
  if(headings.length){
    const update=()=>{
      let current=headings[0].id;
      for(const heading of headings){if(heading.getBoundingClientRect().top<150)current=heading.id;}
      tocLinks.forEach(link=>{const active=link.hash==='#'+current;link.classList.toggle('active',active);if(active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
      if(progress){const main=$('.chapter-main');const total=main.offsetHeight-innerHeight;const amount=Math.max(0,Math.min(1,(scrollY-main.offsetTop)/Math.max(1,total)));progress.style.width=amount*100+'%';}
    };
    let pending=false;window.addEventListener('scroll',()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{update();pending=false;});},{passive:true});window.addEventListener('resize',update);update();
    $$('.mobile-toc a').forEach(link=>link.addEventListener('click',()=>{$('.mobile-toc').open=false;}));
  }
})();
