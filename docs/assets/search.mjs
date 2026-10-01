/** Pure shared search logic, used by the browser and the multi-book regression test. */
export const normalize = value => String(value ?? '').toLocaleLowerCase('ko').normalize('NFKC');
export function searchRecords(records, query, scope='') {
  const terms=normalize(query).trim().split(/\s+/).filter(Boolean);
  if(!terms.length)return [];
  return records.filter(record=>!scope || record.bookId===scope).map(record=>{
    const title=normalize(record.title), chapter=normalize(record.chapterTitle), book=normalize(record.bookTitle);
    const haystack=book+' '+chapter+' '+title+' '+normalize(record.text);
    const score=terms.every(term=>haystack.includes(term)) ? terms.reduce((sum,term)=>sum+(title.includes(term)?12:0)+(chapter.includes(term)?4:0)+(book.includes(term)?2:0),1) : 0;
    return {...record,score};
  }).filter(record=>record.score).sort((a,b)=>b.score-a.score || a.bookTitle.localeCompare(b.bookTitle,'ko') || a.chapter-b.chapter);
}
