#!/usr/bin/env node
/**
 * Multi-book integration contract. The second book exists only in an OS temp
 * directory; this script never builds into the checked-in publication tree.
 * Run: node scripts/test-multi-book.mjs
 * Set KEEP_MULTI_BOOK_FIXTURE=1 to retain temporary files for debugging.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const REAL_CONTENT = path.join(ROOT, 'content');
const REAL_DOCS = path.join(ROOT, 'docs');
const FIXTURE_ID = 'fixture-sparse-only';
const FIXTURE_TITLE = 'Fixture & Sparse Notes';
const FIXTURE_MARKER = 'MULTI_BOOK_FIXTURE_NEVER_PUBLISH';
const FIXTURE_ATTRIBUTION = 'Independent fixture attribution, for integration testing only.';
const SHARED_QUERY = 'MPC';
const BASE = '/study-notes/';
const failures = [];
const passed = [];
const checks = { htmlPages: 0, localLinks: 0, searchRecords: 0, negativeBuilds: 0 };
let temporary;
let buildRoot;

const read = file => fs.readFileSync(file, 'utf8');
const readJson = file => JSON.parse(read(file));
const writeJson = (file, value) => fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
const chapterFile = number => `chapter${String(number).padStart(2, '0')}.html`;
const bookRoute = id => `books/${id}/`;
const chapterRoute = (id, number) => `${bookRoute(id)}chapters/${chapterFile(number)}`;
const filesUnder = directory => fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
  const file = path.join(directory, entry.name);
  return entry.isDirectory() ? filesUnder(file) : entry.isFile() ? [file] : [];
});
const decode = value => value.replace(/&(?:amp|quot|apos|lt|gt|#39);/g, entity => ({
  '&amp;': '&', '&quot;': '"', '&apos;': "'", '&#39;': "'", '&lt;': '<', '&gt;': '>',
})[entity]);
const plain = html => decode(html.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim());
const attributes = tag => Object.fromEntries([...tag.matchAll(/([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))/g)]
  .map(match => [match[1].toLowerCase(), decode(match[2] ?? match[3] ?? match[4])]));
const tags = html => [...html.matchAll(/<([a-z][\w:-]*)\b[^>]*>/gi)]
  .map(match => ({ name: match[1].toLowerCase(), attrs: attributes(match[0]) }));
const titleOf = html => plain(html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i)?.[1] || '');
const headingOf = html => plain(html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/i)?.[1] || '');
function region(html, tag, className) {
  const expression = new RegExp(`<${tag}\\b[^>]*class=["'][^"']*\\b${className}\\b[^"']*["'][^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i');
  const match = html.match(expression);
  assert.ok(match, `Expected ${tag}.${className}`);
  return match[1];
}
function assertCanonical(html, route, base = BASE) {
  const canonical = tags(html).filter(tag => tag.name === 'link' && tag.attrs.rel === 'canonical');
  assert.equal(canonical.length, 1, 'Page should have exactly one canonical URL');
  assert.equal(new URL(canonical[0].attrs.href).pathname, base + route);
}
function hrefs(html) {
  return tags(html).filter(tag => tag.name === 'a').map(tag => tag.attrs.href).filter(Boolean);
}
async function test(name, work) {
  try {
    await work();
    passed.push(name);
    console.log(`PASS ${name}`);
  } catch (error) {
    failures.push({ test: name, message: error.message });
    console.error(`FAIL ${name}: ${error.message}`);
  }
}
function build(content, output, qa, base = BASE) {
  return spawnSync(process.execPath, ['scripts/build.mjs'], {
    cwd: buildRoot,
    encoding: 'utf8',
    timeout: 120_000,
    maxBuffer: 8 * 1024 * 1024,
    env: { ...process.env, SITE_CONTENT_DIR: content, SITE_OUT_DIR: output, SITE_QA_DIR: qa, SITE_BASE: base },
  });
}
function assertBuildSucceeded(result) {
  assert.ifError(result.error);
  assert.equal(result.status, 0, `Build failed:\n${result.stdout}\n${result.stderr}`);
}
function assertFixtureNotPublished() {
  assert.ok(!fs.existsSync(path.join(REAL_DOCS, bookRoute(FIXTURE_ID))), 'Fixture book escaped into the real publication directory');
  const inspect = filesUnder(REAL_DOCS).filter(file => /\.(?:html|json|mjs|js|md)$/i.test(file));
  for (const file of inspect) {
    const source = read(file);
    assert.ok(!source.includes(FIXTURE_ID) && !source.includes(FIXTURE_MARKER), `Fixture content was published in ${path.relative(ROOT, file)}`);
  }
  assert.ok(!read(path.join(REAL_CONTENT, 'books.json')).includes(FIXTURE_ID), 'Fixture was added to the real book registry');
}
function assertLocalLinks(output, base = BASE) {
  const files = filesUnder(output);
  const pages = new Map(files.filter(file => file.endsWith('.html')).map(file => {
    const html = read(file);
    const elements = tags(html);
    return [path.resolve(file), { html, elements, ids: new Set(elements.map(tag => tag.attrs.id).filter(Boolean)) }];
  }));
  const errors = [];
  let links = 0;
  function checkLink(file, link) {
    if (!link) { errors.push(`${path.relative(output, file)}: empty link`); return; }
    if (/^(?:https?:|\/\/|data:|mailto:|tel:)/i.test(link)) return;
    const pageUrl = new URL(base + path.relative(output, file).split(path.sep).join('/'), 'https://fixture.invalid');
    const url = new URL(link, pageUrl);
    if (url.origin !== pageUrl.origin) return;
    links++;
    if (!url.pathname.startsWith(base)) {
      errors.push(`${path.relative(output, file)}: link outside site base: ${link}`);
      return;
    }
    let target = path.resolve(output, decodeURIComponent(url.pathname.slice(base.length)));
    if (target !== output && !target.startsWith(output + path.sep)) {
      errors.push(`${path.relative(output, file)}: link escapes output: ${link}`);
      return;
    }
    if (fs.existsSync(target) && fs.statSync(target).isDirectory()) target = path.join(target, 'index.html');
    if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
      errors.push(`${path.relative(output, file)}: missing target: ${link}`);
    } else if (url.hash && pages.has(target) && !pages.get(target).ids.has(decodeURIComponent(url.hash.slice(1)))) {
      errors.push(`${path.relative(output, file)}: missing anchor: ${link}`);
    }
  }
  for (const [file, page] of pages) {
    for (const tag of page.elements) {
      if (['a', 'link'].includes(tag.name) && 'href' in tag.attrs) checkLink(file, tag.attrs.href);
      if (['img', 'script', 'source'].includes(tag.name) && 'src' in tag.attrs) checkLink(file, tag.attrs.src);
      if ('data-zoom' in tag.attrs) checkLink(file, tag.attrs['data-zoom']);
    }
  }
  for (const file of files.filter(file => file.endsWith('.css'))) {
    for (const match of read(file).matchAll(/url\(\s*["']?([^\s"')]+)["']?\s*\)/g)) checkLink(file, match[1]);
  }
  for (const record of readJson(path.join(output, 'assets/search-index.json'))) checkLink(path.join(output, 'index.html'), record.url);
  checks.htmlPages += pages.size;
  checks.localLinks += links;
  assert.equal(errors.length, 0, `Broken local links (${errors.length}):\n${errors.slice(0, 30).join('\n')}`);
}

try {
  assert.ok(fs.existsSync(path.join(REAL_CONTENT, 'books.json')), 'Multi-book implementation is not ready: content/books.json is missing');
  assert.ok(fs.existsSync(path.join(ROOT, 'src/search.mjs')), 'Multi-book implementation is not ready: src/search.mjs is missing');
  const originalBooks = readJson(path.join(REAL_CONTENT, 'books.json'));
  assert.ok(Array.isArray(originalBooks) && originalBooks.length, 'Book registry should be a nonempty array');
  assert.ok(!originalBooks.some(book => book.id === FIXTURE_ID), 'The test-only fixture id is reserved');
  const mpcBook = originalBooks.find(book => /MPC|Model Predictive Control/i.test(`${book.id} ${book.title}`)) || originalBooks[0];
  const mpcChapters = readJson(path.join(REAL_CONTENT, mpcBook.chaptersFile));
  assert.ok(mpcChapters.length, 'The existing book should have chapters');

  temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'study-notes-multi-book-'));
  // Execute the exact implementation in a disposable project root too. Even a
  // regression that ignores SITE_OUT_DIR cannot modify the real docs directory.
  buildRoot = path.join(temporary, 'project');
  fs.mkdirSync(buildRoot);
  for (const folder of ['scripts', 'src', 'content', 'docs']) {
    fs.cpSync(path.join(ROOT, folder), path.join(buildRoot, folder), { recursive: true });
  }
  fs.copyFileSync(path.join(ROOT, 'package.json'), path.join(buildRoot, 'package.json'));
  fs.symlinkSync(path.join(ROOT, 'node_modules'), path.join(buildRoot, 'node_modules'), 'junction');
  const content = path.join(temporary, 'content');
  const output = path.join(temporary, 'docs');
  const qa = path.join(temporary, 'qa');
  fs.cpSync(REAL_CONTENT, content, { recursive: true });
  fs.cpSync(REAL_DOCS, output, { recursive: true });
  fs.mkdirSync(path.join(content, 'fixture'), { recursive: true });
  const fixtureChapters = [
    { number: 2, title: 'Sparse beginning', file: 'fixture/chapter02.md', description: 'First chapter even though its number is two.', tags: ['sparse', 'fixture'], category: 'TEST FOUNDATIONS' },
    { number: 5, title: 'Sparse ending', file: 'fixture/chapter05.md' },
  ];
  const fixture = {
    id: FIXTURE_ID,
    title: FIXTURE_TITLE,
    subtitle: 'An isolated two-chapter test book',
    authors: ['Integration Test Author'],
    category: 'TESTING',
    description: 'Checks metadata-driven books without optional resources.',
    chaptersFile: 'fixture/chapters.json',
    attributionFile: 'fixture/ATTRIBUTION.md',
  };
  fs.writeFileSync(path.join(content, 'fixture/chapter02.md'), `# Sparse beginning\n\n## MPC fixture shared topic\n\n${FIXTURE_MARKER} begins here. MPC is also discussed in the real book.\n\n## Distinct first section\n\nOnly this fixture contains sparsebeginningtoken.\n\n[Continue to the ending](chapter05.md#section-1).\n`);
  fs.writeFileSync(path.join(content, 'fixture/chapter05.md'), '# Sparse ending\n\n## MPC fixture ending\n\nThis last chapter contains sparseendingtoken and MPC.\n');
  fs.writeFileSync(path.join(content, 'fixture/ATTRIBUTION.md'), `# Fixture sources\n\n${FIXTURE_ATTRIBUTION}\n`);
  writeJson(path.join(content, fixture.chaptersFile), fixtureChapters);
  const validBooks = [...originalBooks, fixture];
  writeJson(path.join(content, 'books.json'), validBooks);
  assertBuildSucceeded(build(content, output, qa));
  const page = route => read(path.join(output, route));
  const library = page('index.html');
  const fixtureHome = page(`${bookRoute(FIXTURE_ID)}index.html`);
  const first = page(chapterRoute(FIXTURE_ID, 2));
  const last = page(chapterRoute(FIXTURE_ID, 5));
  const fixtureAbout = page(`${bookRoute(FIXTURE_ID)}about.html`);
  const mpcFirst = page(chapterRoute(mpcBook.id, mpcChapters[0].number));
  const index = readJson(path.join(output, 'assets/search-index.json'));
  checks.searchRecords = index.length;

  await test('isolated build writes the requested output and QA directories', () => {
    assert.ok(fs.existsSync(path.join(qa, 'build-report.json')), 'Build report did not respect SITE_QA_DIR');
    assertFixtureNotPublished();
  });
  await test('neutral library links every registered book', () => {
    assert.ok(/Study Notes|학습 노트|책장/.test(titleOf(library)), 'Library should use site-wide branding');
    assert.ok(!titleOf(library).includes(mpcBook.title), 'Library title is scoped to the first book');
    assert.ok(!/모델 예측 제어|Model Predictive Control/i.test(headingOf(library)), 'Library hero is still hardcoded to MPC');
    for (const book of validBooks) {
      assert.ok(hrefs(library).includes(BASE + bookRoute(book.id)), `Library is missing the ${book.id} landing-page link`);
      assert.ok(plain(library).includes(book.title), `Library is missing the ${book.id} title`);
    }
    assertCanonical(library, '');
  });
  await test('book landing pages are metadata-driven and chapter-scoped', () => {
    assert.ok(titleOf(fixtureHome).includes(FIXTURE_TITLE));
    assert.ok(headingOf(fixtureHome).includes(FIXTURE_TITLE));
    for (const text of [fixture.subtitle, fixture.authors[0], fixture.description]) assert.ok(plain(fixtureHome).includes(text), `Book metadata missing: ${text}`);
    const links = hrefs(fixtureHome);
    for (const chapter of fixtureChapters) assert.ok(links.includes(BASE + chapterRoute(FIXTURE_ID, chapter.number)));
    assert.ok(!links.some(link => link.includes(`/books/${mpcBook.id}/chapters/`)), 'Fixture landing page contains another book’s chapters');
    assertCanonical(fixtureHome, bookRoute(FIXTURE_ID));
  });
  await test('chapter title, breadcrumb, sidebar, and canonical use their own book', () => {
    for (const [html, chapter] of [[first, fixtureChapters[0]], [last, fixtureChapters[1]]]) {
      assert.ok(titleOf(html).includes(FIXTURE_TITLE), 'Chapter document title is missing book context');
      assert.equal(headingOf(html), chapter.title);
      const sidebar = region(html, 'aside', 'chapter-sidebar');
      assert.ok(plain(sidebar).includes(FIXTURE_TITLE), 'Sidebar is missing its own book title');
      const chapterLinks = hrefs(sidebar).filter(link => link.includes('/chapters/'));
      assert.deepEqual(new Set(chapterLinks), new Set(fixtureChapters.map(item => BASE + chapterRoute(FIXTURE_ID, item.number))));
      assert.ok(hrefs(sidebar).includes(BASE + bookRoute(FIXTURE_ID) + 'about.html'), 'Sidebar source link belongs to another book');
      const breadcrumb = /class=["'][^"']*\bbreadcrumbs\b/.test(html) ? region(html, 'nav', 'breadcrumbs') : region(html, 'a', 'breadcrumb');
      assert.ok(plain(breadcrumb).includes(FIXTURE_TITLE), 'Breadcrumb is hardcoded to the first book');
      assertCanonical(html, chapterRoute(FIXTURE_ID, chapter.number));
    }
    assert.ok(titleOf(mpcFirst).includes(mpcBook.title), 'Original book lost its own chapter context');
    assert.ok(!region(mpcFirst, 'aside', 'chapter-sidebar').includes(FIXTURE_TITLE), 'Fixture chapters leaked into original-book sidebar');
  });
  await test('sparse chapter numbers use list order for previous and next navigation', () => {
    const firstTurn = hrefs(region(first, 'nav', 'page-turn'));
    const lastTurn = hrefs(region(last, 'nav', 'page-turn'));
    assert.ok(firstTurn.includes(BASE + chapterRoute(FIXTURE_ID, 5)), 'First listed chapter does not lead to the second listed chapter');
    assert.ok(lastTurn.includes(BASE + chapterRoute(FIXTURE_ID, 2)), 'Last listed chapter does not lead back to the first listed chapter');
    for (const link of [...firstTurn, ...lastTurn]) {
      assert.ok(link.startsWith(BASE + bookRoute(FIXTURE_ID)) || link === BASE || link === BASE + '#library', `Page turn crosses books: ${link}`);
      if (link.includes('/chapters/')) assert.ok([2, 5].some(number => link === BASE + chapterRoute(FIXTURE_ID, number)), `Invented chapter in page turn: ${link}`);
    }
    assert.ok(!/\/\s*8\s*장|8개의 장|핵심 수식 카드\s*4|개념 도식\s*17/.test(plain(first + last)), 'Chapter summary retains hardcoded MPC counts');
  });
  await test('absent optional resources render no empty resource sections', () => {
    for (const html of [first, last]) {
      const headings = [...html.matchAll(/<h[23]\b[^>]*>([\s\S]*?)<\/h[23]>/gi)].map(match => plain(match[1]));
      for (const heading of ['직접 실행해 보기', '핵심 수식 카드', '관련 영상']) assert.ok(!headings.includes(heading), `Absent resource rendered heading: ${heading}`);
      for (const id of ['standalone-example', 'formula-cards', 'related-video']) assert.ok(!tags(html).some(tag => tag.attrs.id === id), `Absent resource rendered #${id}`);
      assert.ok(!/\b(?:undefined|NaN)\b/.test(plain(html)), 'Missing metadata leaked into rendered text');
    }
  });
  await test('book attribution pages remain independent', () => {
    assert.ok(plain(fixtureAbout).includes(FIXTURE_ATTRIBUTION));
    assert.ok(titleOf(fixtureAbout).includes(FIXTURE_TITLE));
    assertCanonical(fixtureAbout, bookRoute(FIXTURE_ID) + 'about.html');
    const originalAbout = page(bookRoute(mpcBook.id) + 'about.html');
    assert.ok(!plain(originalAbout).includes(FIXTURE_ATTRIBUTION));
    assert.ok(!/Rawlings|Mayne|Diehl/.test(plain(fixtureAbout)), 'Fixture attribution includes another book’s authors');
  });
  await test('legacy chapter URLs remain readable canonical copies', () => {
    for (const book of originalBooks.filter(item => item.legacyChapterUrls)) {
      for (const chapter of readJson(path.join(content, book.chaptersFile))) {
        const legacy = page(`chapters/${chapterFile(chapter.number)}`);
        const current = page(chapterRoute(book.id, chapter.number));
        assert.equal(headingOf(legacy), headingOf(current));
        assert.ok(legacy.includes('<article'), 'Legacy page is only a redirect or empty shell');
        assert.ok(!/<meta\b[^>]*http-equiv=["']refresh/i.test(legacy), 'Legacy page uses a meta refresh');
        assertCanonical(legacy, chapterRoute(book.id, chapter.number));
        assert.equal(plain(region(legacy, 'article', 'prose')), plain(region(current, 'article', 'prose')));
      }
    }
    assert.ok(originalBooks.some(book => book.legacyChapterUrls), 'Existing chapter URLs should have a configured legacy owner');
  });
  await test('search index has complete book context and real section destinations', () => {
    assert.ok(index.length > 0);
    for (const record of index) {
      for (const key of ['bookId', 'bookTitle', 'chapter', 'chapterTitle', 'title', 'url', 'text']) assert.ok(key in record, `Search record is missing ${key}`);
      const book = validBooks.find(item => item.id === record.bookId);
      assert.ok(book, `Unregistered book in search: ${record.bookId}`);
      assert.equal(record.bookTitle, book.title);
      const canonical = BASE + chapterRoute(record.bookId, record.chapter);
      assert.ok(record.url === canonical || record.url.startsWith(canonical + '#'), `Noncanonical search destination: ${record.url}`);
    }
    assert.ok(index.some(record => record.bookId === FIXTURE_ID && record.text.includes(FIXTURE_MARKER)));
  });
  await test('pure search supports all books, one book, normalization, and no input mutation', async () => {
    const { searchRecords } = await import(pathToFileURL(path.join(ROOT, 'src/search.mjs')).href);
    assert.equal(typeof searchRecords, 'function');
    const before = JSON.stringify(index);
    const all = searchRecords(index, SHARED_QUERY);
    assert.ok(all.some(record => record.bookId === mpcBook.id), 'Cross-book search lost original book results');
    assert.ok(all.some(record => record.bookId === FIXTURE_ID), 'Cross-book search lost fixture results');
    for (const id of [mpcBook.id, FIXTURE_ID]) {
      const scoped = searchRecords(index, SHARED_QUERY, id);
      assert.ok(scoped.length > 0, `Scoped search returns no matches for ${id}`);
      assert.ok(scoped.every(record => record.bookId === id), `Scoped search crosses out of ${id}`);
    }
    const unique = searchRecords(index, 'sparseendingtoken');
    assert.ok(unique.length > 0 && unique.every(record => record.bookId === FIXTURE_ID && record.chapter === 5));
    assert.equal(searchRecords(index, 'sparseendingtoken', mpcBook.id).length, 0);
    assert.equal(searchRecords(index, SHARED_QUERY, 'unknown-book').length, 0);
    assert.equal(searchRecords(index, 'definitely-not-a-real-search-term-4f29d').length, 0);
    assert.equal(searchRecords(index, '   ').length, 0);
    assert.deepEqual(searchRecords(index, 'ｍｐｃ', FIXTURE_ID).map(record => record.url), searchRecords(index, 'MPC', FIXTURE_ID).map(record => record.url));
    assert.equal(JSON.stringify(index), before, 'Search mutated its input records');
    assert.equal(read(path.join(output, 'assets/search.mjs')), read(path.join(ROOT, 'src/search.mjs')), 'Served search module differs from tested module');
  });
  await test('search controls expose all books and default to the current book', () => {
    for (const [html, expectedScope] of [[library, ''], [fixtureHome, FIXTURE_ID], [first, FIXTURE_ID], [mpcFirst, mpcBook.id]]) {
      const select = html.match(/<select\b[^>]*id=["']search-book["'][^>]*>([\s\S]*?)<\/select>/i)?.[1];
      assert.ok(select, 'Book scope selector is missing');
      const options = [...select.matchAll(/<option\b([^>]*)>/gi)];
      assert.deepEqual(new Set(options.map(option => attributes(option[0]).value)), new Set(['', ...validBooks.map(book => book.id)]));
      const selected = options.find(option => /\bselected(?:\s|=|>|$)/i.test(option[0]));
      assert.equal(selected ? attributes(selected[0]).value : '', expectedScope);
    }
  });
  await test('every generated HTML, CSS, zoom, and search link resolves', () => assertLocalLinks(output));
  await test('all pages and search URLs respect a different deployment base', () => {
    const alternate = '/fixture-library/';
    assertBuildSucceeded(build(content, output, qa, alternate));
    assertCanonical(page(chapterRoute(FIXTURE_ID, 5)), chapterRoute(FIXTURE_ID, 5), alternate);
    assertLocalLinks(output, alternate);
  });

  await test('chapter array order, not numeric sorting, controls navigation', () => {
    writeJson(path.join(content, fixture.chaptersFile), [...fixtureChapters].reverse());
    try {
      assertBuildSucceeded(build(content, output, qa));
      const beginning = hrefs(region(page(chapterRoute(FIXTURE_ID, 5)), 'nav', 'page-turn'));
      const ending = hrefs(region(page(chapterRoute(FIXTURE_ID, 2)), 'nav', 'page-turn'));
      assert.equal(beginning[1], BASE + chapterRoute(FIXTURE_ID, 2), 'Next chapter ignores registry order');
      assert.equal(ending[0], BASE + chapterRoute(FIXTURE_ID, 5), 'Previous chapter ignores registry order');
    } finally {
      writeJson(path.join(content, fixture.chaptersFile), fixtureChapters);
    }
  });

  await test('generic manuscripts preserve headings that resemble legacy appendices', () => {
    const manuscript = path.join(content, fixtureChapters[1].file);
    const original = read(manuscript);
    try {
      fs.writeFileSync(manuscript, original + '\n## 핵심 수식 카드\n\nOrdinary prose: preserveappendixsentinel.\n');
      assertBuildSucceeded(build(content, output, qa));
      assert.ok(plain(page(chapterRoute(FIXTURE_ID, 5))).includes('preserveappendixsentinel'), 'Generic manuscript was truncated by MPC-specific appendix cleanup');
    } finally { fs.writeFileSync(manuscript, original); }
  });
  await test('manuscripts without h2 headings remain searchable with optional resources', () => {
    const manuscript = path.join(content, fixtureChapters[1].file);
    const original = read(manuscript);
    const books = structuredClone(validBooks);
    try {
      fs.writeFileSync(manuscript, '# Sparse ending\n\nUnsectioned prose includes unsectionedsearchsentinel.\n');
      books.at(-1).formulasFile = 'fixture/formulas.json';
      writeJson(path.join(content, 'fixture/formulas.json'), [{ chapter: 5, id: 'fixture_identity', title: 'Fixture identity', caption: 'A synthetic test formula.', latex: ['x=x'], assumptions: [], attribution: 'Integration fixture' }]);
      writeJson(path.join(content, 'books.json'), books);
      assertBuildSucceeded(build(content, output, qa));
      const entries = readJson(path.join(output, 'assets/search-index.json'));
      assert.ok(entries.some(record => record.bookId === FIXTURE_ID && record.chapter === 5 && record.text.includes('unsectionedsearchsentinel')), 'Optional resource headings hid the unsectioned manuscript from search');
    } finally {
      fs.writeFileSync(manuscript, original);
      writeJson(path.join(content, 'books.json'), validBooks);
    }
  });

  async function invalid(name, mutate, expectedDiagnostic) {
    await test(`validation rejects ${name}`, () => {
      writeJson(path.join(content, 'books.json'), validBooks);
      writeJson(path.join(content, fixture.chaptersFile), fixtureChapters);
      const books = structuredClone(validBooks);
      const chapters = structuredClone(fixtureChapters);
      mutate(books, chapters);
      writeJson(path.join(content, 'books.json'), books);
      writeJson(path.join(content, fixture.chaptersFile), chapters);
      const result = build(content, output, qa);
      checks.negativeBuilds++;
      assert.ifError(result.error);
      assert.notEqual(result.status, 0, `Invalid ${name} was accepted`);
      const diagnostic = `${result.stdout}\n${result.stderr}`;
      assert.match(diagnostic, expectedDiagnostic, `Failure did not explain ${name}: ${diagnostic}`);
    });
  }
  await invalid('duplicate book ids / route slugs', books => books.push({ ...books.at(-1), title: 'Duplicate fixture' }), /duplicate|already|중복/i);
  await invalid('unsafe book route slugs', books => { books.at(-1).id = '../fixture-escape'; }, /id|slug|invalid|안전|형식|경로/i);
  await invalid('duplicate chapter numbers', (_books, chapters) => chapters.push({ ...chapters[0], title: 'Duplicate number' }), /duplicate|already|중복/i);
  await invalid('non-positive chapter numbers', (_books, chapters) => { chapters[0].number = 0; }, /chapter|number|invalid|장|번호/i);
  await invalid('non-integer chapter numbers', (_books, chapters) => { chapters[0].number = 2.5; }, /chapter|number|invalid|장|번호/i);
  await invalid('missing required authors', books => { books.at(-1).authors = []; }, /authors|author|저자/i);
  await invalid('missing chapter manuscript', (_books, chapters) => { chapters[0].file = 'fixture/missing-manuscript.md'; }, /missing-manuscript|manuscript|ENOENT|missing|없/i);
  await invalid('missing chapters manifest', books => { books.at(-1).chaptersFile = 'fixture/missing-chapters.json'; }, /missing-chapters|chaptersFile|ENOENT|missing|없/i);
  await invalid('missing required attribution', books => { books.at(-1).attributionFile = 'fixture/missing-attribution.md'; }, /missing-attribution|attributionFile|ENOENT|missing|없/i);
  await test('the temporary fixture never enters real published content', assertFixtureNotPublished);
} catch (error) {
  failures.push({ test: 'integration setup', message: error.stack || error.message });
  console.error(error.stack || error.message);
} finally {
  if (temporary && process.env.KEEP_MULTI_BOOK_FIXTURE !== '1') fs.rmSync(temporary, { recursive: true, force: true });
  else if (temporary) console.log(`Temporary fixture retained at ${temporary}`);
}

console.log(JSON.stringify({ status: failures.length ? 'failed' : 'passed', testsPassed: passed.length, ...checks, failures }, null, 2));
process.exitCode = failures.length ? 1 : 0;
