#!/usr/bin/env python3
"""차곡 빠른 점검 (고친 뒤 꼭 돌려 보세요)

  pip install playwright && python -m playwright install chromium
  python tools/smoke_test.py

확인하는 것: 모든 메뉴가 오류 없이 열리는지, 공문 글에서 할 일 후보를 찾는지,
자리 배치 화면이 열리고 저장되는지, 백업 파일에 자리 배치가 들어가는지.
"""
import functools, http.server, json, pathlib, sys, threading
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
H = functools.partial(Quiet, directory=str(ROOT))
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/index.html'

SAMPLE = """[안내] 2026학년도 교원 연수 신청
- 신청 기간: 11. 24.(월) ~ 11. 28.(금) 17:00까지
- 12월 3일(수) 15:00 학년 협의회
- 생활기록부 점검은 다음 주 금요일까지 완료해 주세요."""

fails = []
def check(ok, msg):
    print(('  ✅ ' if ok else '  ❌ ') + msg)
    if not ok: fails.append(msg)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, locale='ko-KR', timezone_id='Asia/Seoul', accept_downloads=True)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(1500)
    print('버전', pg.evaluate('APP_VERSION'))
    for tab in pg.evaluate('TABS'):
        pg.evaluate(f"go('{tab}')"); pg.wait_for_timeout(350)
    check(not errs, f'모든 메뉴가 오류 없이 열려요 {errs[:2]}')

    pg.evaluate("go('input')"); pg.wait_for_timeout(300)
    pg.fill('#pasteText', SAMPLE); pg.wait_for_timeout(1200)
    n = pg.evaluate('UI.draft.cands.length')
    check(n >= 3, f'공문 글에서 할 일 후보를 찾아요 ({n}개)')

    pg.evaluate("go('seats')"); pg.wait_for_timeout(2500)
    fr = pg.frame_locator('#seatHost iframe')
    fr.locator('#welcomeDemo').click(); pg.wait_for_timeout(1000)
    raw = pg.evaluate('SEAT.raw')
    check(bool(raw) and len(json.loads(raw)['students']) == 24, '자리 배치가 열리고 예시 명단이 저장돼요')
    with pg.expect_download() as dl:
        pg.evaluate('exportBackup()')
    data = json.loads(pathlib.Path(dl.value.path()).read_text(encoding='utf-8'))
    check('seats' in data, '차곡 백업 파일에 자리 배치가 들어가요')
    check(not errs, f'끝까지 오류가 없어요 {errs[:2]}')
    b.close()

print('\n모두 통과했어요 ✅' if not fails else f'\n{len(fails)}개 실패 ❌')
sys.exit(1 if fails else 0)
