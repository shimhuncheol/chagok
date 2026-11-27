#!/usr/bin/env python3
"""모여요 코드(src/meet/Code.gs, index.html)를 차곡 안 '코드 복사' 버튼용 자산(base64)으로 만들어요.

  python src/meet/build_meet.py   →  src/assets/meetGs.txt, src/assets/meetPage.txt
그다음  python tools/build.py  로 index.html 을 다시 만드세요.
"""
import base64, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ASSETS = HERE.parent / 'assets'
for name, src in [('meetGs', 'Code.gs'), ('meetPage', 'index.html')]:
    (ASSETS / f'{name}.txt').write_text(base64.b64encode((HERE / src).read_bytes()).decode(), encoding='utf-8')
    print(f'{name}.txt 를 만들었어요')
