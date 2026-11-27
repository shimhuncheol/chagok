/**
 * 모여요 — 날짜·시간 협의 웹앱 (Google Apps Script)
 * 만든 사람: 심훈철
 *
 * 처음 쓰는 방법
 * 1) script.google.com → 새 프로젝트 → 이 코드를 Code.gs에 붙여넣기
 * 2) 파일 추가(+) → HTML → 이름을 index 로 → index.html 내용 붙여넣기
 * 3) 배포 → 새 배포 → 유형: 웹 앱
 *    - 다음 사용자 인증 정보로 실행: 나
 *    - 액세스 권한: 모든 사용자
 * 4) 권한 승인 후 나온 웹 앱 URL(…/exec)이 앱 주소예요.
 *    응답은 내 드라이브의 '모여요 응답 데이터' 시트에 자동으로 쌓여요.
 */

var MAX_DATES = 62;
var MAX_TIMES = 48;
var MAX_RESPONSES = 300;

function doGet(e) {
  var t = HtmlService.createTemplateFromFile('index');
  var boot = { url: ScriptApp.getService().getUrl(), params: (e && e.parameter) || {} };
  t.boot = JSON.stringify(boot).replace(/</g, '\\u003c');
  return t.evaluate()
    .setTitle('모여요 · 날짜와 시간 정하기')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/* ---------- 차곡 연결 (차곡의 '일정 협의' 메뉴가 이 통로로 불러요) ---------- */

var API = {
  ping: function () { return { app: 'moyeoyo', version: 2 }; },
  createPoll: function (a) { return createPoll(a); },
  loadPoll: function (id, key) { return loadPoll(id, key); },
  summaries: function (items) { return summaries(items); },
  adminUpdate: function (id, key, patch) { return adminUpdate(id, key, patch); },
  adminDeleteResponse: function (id, key, name) { return adminDeleteResponse(id, key, name); }
};

function doPost(e) {
  var out;
  try {
    var req = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var fn = API.hasOwnProperty(req.fn) ? API[req.fn] : null;
    if (!fn) throw new Error('알 수 없는 요청이에요.');
    out = { ok: true, data: fn.apply(null, Array.isArray(req.args) ? req.args : []) };
  } catch (err) {
    out = { ok: false, error: String((err && err.message) || err) };
  }
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(ContentService.MimeType.JSON);
}

/* 여러 설문의 요약(제목·응답 수·마감)을 한 번에 — 관리키가 맞는 것만 */
function summaries(items) {
  var polls = rows_(sheet_('polls')), res = rows_(sheet_('responses')), cnt = {};
  res.forEach(function (r) { cnt[r[0]] = (cnt[r[0]] || 0) + 1; });
  return (items || []).slice(0, 200).map(function (it) {
    for (var i = 0; i < polls.length; i++) {
      if (String(polls[i][0]) === String(it.id) && String(polls[i][1]) === String(it.key)) {
        var cfg = JSON.parse(String(polls[i][3]));
        return { id: it.id, title: cfg.title, count: cnt[it.id] || 0, open: isOpen_(cfg), closed: !!cfg.closed, deadline: cfg.deadline || null, dates: cfg.dates.length, first: cfg.dates[0], last: cfg.dates[cfg.dates.length - 1] };
      }
    }
    return { id: it.id, missing: true };
  });
}

/* ---------- 저장소 ---------- */

function book_() {
  var props = PropertiesService.getScriptProperties();
  var id = props.getProperty('SHEET_ID');
  if (id) {
    try { return SpreadsheetApp.openById(id); } catch (err) { /* 시트가 지워졌으면 새로 만듦 */ }
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    id = props.getProperty('SHEET_ID');
    if (id) { try { return SpreadsheetApp.openById(id); } catch (err) {} }
    var ss = SpreadsheetApp.create('모여요 응답 데이터');
    var polls = ss.getSheets()[0];
    polls.setName('polls');
    polls.getRange(1, 1, 1, 5).setValues([['설문ID', '관리키', '제목', '설정(JSON)', '만든 시각']]);
    polls.getRange('A:E').setNumberFormat('@');
    var res = ss.insertSheet('responses');
    res.getRange(1, 1, 1, 5).setValues([['설문ID', '이름', '가능한 시간(JSON)', '고른 칸 수', '제출 시각']]);
    res.getRange('A:E').setNumberFormat('@');
    props.setProperty('SHEET_ID', ss.getId());
    return ss;
  } finally {
    lock.releaseLock();
  }
}

function sheet_(name) { return book_().getSheetByName(name); }

function rows_(sh) {
  var last = sh.getLastRow();
  if (last < 2) return [];
  return sh.getRange(2, 1, last - 1, sh.getLastColumn()).getValues();
}

function findPoll_(id) {
  var sh = sheet_('polls');
  var data = rows_(sh);
  for (var i = 0; i < data.length; i++) {
    if (String(data[i][0]) === String(id)) {
      return { row: i + 2, key: String(data[i][1]), cfg: JSON.parse(String(data[i][3])), sh: sh };
    }
  }
  throw new Error('설문을 찾을 수 없어요. 링크를 다시 확인해 주세요.');
}

function savePoll_(p) {
  p.sh.getRange(p.row, 3, 1, 2).setValues([[p.cfg.title, JSON.stringify(p.cfg)]]);
}

function responsesOf_(id) {
  var sh = sheet_('responses');
  var data = rows_(sh);
  var out = [];
  for (var i = 0; i < data.length; i++) {
    if (String(data[i][0]) === String(id)) {
      var slots = [];
      try { slots = JSON.parse(String(data[i][2])); } catch (err) {}
      out.push({ row: i + 2, name: String(data[i][1]), slots: slots, at: Number(data[i][4]) || 0 });
    }
  }
  return out;
}

/* ---------- 도우미 ---------- */

function token_(n) {
  var abc = 'abcdefghijkmnpqrstuvwxyz23456789';
  var s = '';
  for (var i = 0; i < n; i++) s += abc.charAt(Math.floor(Math.random() * abc.length));
  return s;
}

function cleanText_(v, max) {
  return String(v == null ? '' : v).replace(/[\u0000-\u001f]/g, ' ').replace(/^[=+\-@\s]+/, '').trim().slice(0, max);
}

function cleanName_(v) { return cleanText_(v, 30).replace(/\s+/g, ' '); }

function slotKeys_(cfg) {
  var keys = {};
  cfg.dates.forEach(function (d) {
    if (!cfg.times.length) keys[d] = 1;
    else cfg.times.forEach(function (t) { keys[d + 'T' + t] = 1; });
  });
  return keys;
}

function isOpen_(cfg) {
  if (cfg.closed) return false;
  if (cfg.deadline && Date.now() > cfg.deadline) return false;
  return true;
}

function publicPoll_(id, cfg) {
  return {
    id: id, title: cfg.title, note: cfg.note, dates: cfg.dates, times: cfg.times,
    interval: cfg.interval, deadline: cfg.deadline || null, highlight: !!cfg.highlight,
    share: !!cfg.share, closed: !!cfg.closed, open: isOpen_(cfg)
  };
}

/* ---------- 화면에서 부르는 함수 ---------- */

function createPoll(input) {
  input = input || {};
  var title = cleanText_(input.title, 80);
  if (!title) throw new Error('제목을 입력해 주세요.');
  var dates = (input.dates || []).filter(function (d) { return /^\d{4}-\d{2}-\d{2}$/.test(d); });
  var times = (input.times || []).filter(function (t) { return /^\d{2}:\d{2}$/.test(t); });
  if (!dates.length) throw new Error('날짜를 하나 이상 골라 주세요.');
  if (dates.length > MAX_DATES) throw new Error('날짜는 ' + MAX_DATES + '일까지 고를 수 있어요.');
  if (times.length > MAX_TIMES) throw new Error('시간 칸이 너무 많아요. 간격을 넓혀 주세요.');
  var deadline = Number(input.deadline) || null;
  if (deadline && deadline < Date.now()) throw new Error('마감 시각이 이미 지났어요.');

  var cfg = {
    title: title, note: cleanText_(input.note, 300), dates: dates, times: times,
    interval: Number(input.interval) || 0, deadline: deadline,
    highlight: !!input.highlight, share: !!input.share, closed: false, createdAt: Date.now()
  };
  var id = token_(8), key = token_(12);
  book_();
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    sheet_('polls').appendRow([id, key, title, JSON.stringify(cfg), String(cfg.createdAt)]);
  } finally { lock.releaseLock(); }
  return { id: id, key: key };
}

function loadPoll(id, key) {
  var p = findPoll_(id);
  var admin = !!key && key === p.key;
  var list = responsesOf_(id);
  var out = { poll: publicPoll_(id, p.cfg), admin: admin, count: list.length };
  if (admin || p.cfg.highlight || p.cfg.share) {
    var counts = {};
    list.forEach(function (r) { r.slots.forEach(function (k) { counts[k] = (counts[k] || 0) + 1; }); });
    out.counts = counts;
  }
  if (admin || p.cfg.share) {
    out.responses = list.map(function (r) { return { name: r.name, slots: r.slots, at: r.at }; });
  }
  return out;
}

function submitResponse(id, name, slots, overwrite) {
  book_();
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var p = findPoll_(id);
    if (!isOpen_(p.cfg)) throw new Error('마감된 설문이에요.');
    name = cleanName_(name);
    if (!name) throw new Error('이름을 입력해 주세요.');
    var valid = slotKeys_(p.cfg);
    var picked = (slots || []).filter(function (k, i, a) { return valid[k] && a.indexOf(k) === i; });
    var list = responsesOf_(id);
    var same = null;
    list.forEach(function (r) { if (r.name.toLowerCase() === name.toLowerCase()) same = r; });
    if (same && !overwrite) return { exists: true, name: same.name };
    if (!same && list.length >= MAX_RESPONSES) throw new Error('응답이 너무 많아요. 관리자에게 알려 주세요.');
    var sh = sheet_('responses');
    var row = [id, name, JSON.stringify(picked), String(picked.length), String(Date.now())];
    if (same) sh.getRange(same.row, 1, 1, 5).setValues([row]);
    else sh.appendRow(row);
    return { ok: true, updated: !!same, count: picked.length };
  } finally { lock.releaseLock(); }
}

function adminUpdate(id, key, patch) {
  book_();
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var p = findPoll_(id);
    if (key !== p.key) throw new Error('관리자 링크가 아니에요.');
    patch = patch || {};
    ['highlight', 'share', 'closed'].forEach(function (f) { if (f in patch) p.cfg[f] = !!patch[f]; });
    if ('deadline' in patch) p.cfg.deadline = Number(patch.deadline) || null;
    if ('title' in patch) { var t = cleanText_(patch.title, 80); if (t) p.cfg.title = t; }
    if ('note' in patch) p.cfg.note = cleanText_(patch.note, 300);
    savePoll_(p);
    return loadPoll(id, key);
  } finally { lock.releaseLock(); }
}

function adminDeleteResponse(id, key, name) {
  book_();
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var p = findPoll_(id);
    if (key !== p.key) throw new Error('관리자 링크가 아니에요.');
    var list = responsesOf_(id);
    for (var i = list.length - 1; i >= 0; i--) {
      if (list[i].name === name) sheet_('responses').deleteRow(list[i].row);
    }
    return loadPoll(id, key);
  } finally { lock.releaseLock(); }
}
