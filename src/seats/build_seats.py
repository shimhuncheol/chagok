"""🪑 자리 배치: '우리 반 자리' 원본(original/ 의 index.html·style.css·theme.css·app.js)을
차곡 안 iframe 에서 돌아가는 한 문서로 묶어 src/assets/seatApp.txt (gzip+base64) 로 저장해요.

  python src/seats/build_seats.py      # 그다음 python tools/build.py
  python src/seats/build_seats.py --html  # 확인용 seat_bundle.html 도 함께 저장
"""
import base64, gzip, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / 'original'
html = (SRC / 'index.html').read_text(encoding='utf-8')
app = (SRC / 'app.js').read_text(encoding='utf-8')
css = subprocess.check_output([sys.executable, str(HERE / 'recolor.py'), str(SRC)]).decode('utf-8')

# 1) 저장소: 이 브라우저의 localStorage 대신 차곡 저장소(IndexedDB)에 함께 보관해요
assert app.count('localStorage') == 3, app.count('localStorage')
app = app.replace('localStorage', 'SEATLS')
# 한글 이름이 글자 단위로 끊겨 읽혀도 붙여서 찾도록 (이 도 윤 → 이도윤)
old = "map(t=>t.text).join(' ').trim();const match=raw.match"
assert app.count(old) == 1
old2 = "sort((a,b)=>a.y-b.y||a.x-b.x).map(t=>t.text)"
assert app.count(old2) == 1
app = app.replace(old2, "sort((a,b)=>Math.abs(a.y-b.y)>bh*.06?a.y-b.y:a.x-b.x).map(t=>t.text)")
app = app.replace(old, "map(t=>t.text).join('').replace(/\\s+/g,'').trim();const match=raw.match")

# 2) 사진 명부 글자 읽기: 차곡에 들어 있는 한국어 인식 엔진을 써요 (인터넷 없이)
#    원본은 window.Tesseract 가 없을 때만 CDN 에서 불러오므로 아래 부트스트랩에서 대신 만들어 둬요.

# 3) 마크업: 차곡 화면 안에서는 브랜드·바닥글이 겹치므로 숨겨요
body = re.search(r'<body>(.*)<script type="module" src="app.js"></script></body>', html, re.S).group(1)

BOOT = r"""
(function(){
  var P = window.parent && window.parent !== window ? window.parent : null;
  var H = P && P.ChagokSeat;
  /* 저장소 */
  var mem = {};
  window.SEATLS = {
    getItem: function(k){ if (H) return H.get(k); return Object.prototype.hasOwnProperty.call(mem,k) ? mem[k] : null; },
    setItem: function(k,v){ v = String(v); if (H) { H.set(k, v); return; } mem[k] = v; },
    removeItem: function(k){ if (H) { H.remove(k); return; } delete mem[k]; }
  };
  /* 한국어 글자 읽기 → 차곡 엔진 */
  if (H && H.ocr) {
    window.Tesseract = {
      createWorker: async function(){
        return {
          recognize: async function(img){
            var src = img && img.toDataURL ? img.toDataURL('image/png') : img;
            var data = await H.ocr(src);
            return { data: data };
          },
          terminate: async function(){}
        };
      }
    };
  }
  /* 디자인 → 차곡 테마 */
  window.__seatTheme = function(t){
    var r = document.documentElement;
    Object.keys(t.vars).forEach(function(k){ r.style.setProperty(k, t.vars[k]); });
    r.dataset.theme = t.id || '';
    if (t.fontCss) {
      var s = document.getElementById('chagok-fonts');
      if (!s) { s = document.createElement('style'); s.id = 'chagok-fonts'; document.head.appendChild(s); }
      if (s.textContent !== t.fontCss) s.textContent = t.fontCss;
    }
  };
  if (H && H.theme) try { window.__seatTheme(H.theme()); } catch (e) {}
})();
"""

EXTRA_CSS = """
/* ---- 차곡 안에서 보일 때 ---- */
.sidebar>.brand,main>footer{display:none!important}
.sidebar>.class-picker-label{margin-top:4px!important}
@media(min-width:921px) and (max-width:1300px){.sidebar{width:158px!important;padding:22px 12px 18px!important}main{margin-left:158px!important;padding:22px 16px 18px!important}}
"""

doc = ('<!doctype html><html lang="ko"><head><meta charset="utf-8">'
       '<meta name="viewport" content="width=device-width,initial-scale=1">'
       '<title>자리 배치</title>'
       f'<script>{BOOT}</script>'
       f'<style>{css}{EXTRA_CSS}</style></head><body>'
       f'{body}'
       f'<script type="module">{app}</script></body></html>')

if '--html' in sys.argv:
    (HERE / 'seat_bundle.html').write_text(doc, encoding='utf-8')
gz = gzip.compress(doc.encode('utf-8'), 9, mtime=0)
b64 = base64.b64encode(gz).decode()
(HERE.parent / 'assets' / 'seatApp.txt').write_text(b64, encoding='utf-8', newline='')
print(f'seatApp.txt 를 만들었어요 (문서 {len(doc):,}자 → {len(b64):,}자)')
