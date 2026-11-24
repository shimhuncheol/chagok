#!/usr/bin/env python3
"""차곡 빌드: src/chagok.html 의 {{asset:이름}} 자리에 src/assets/이름.txt 를 채워 index.html 을 만들어요.

  python tools/build.py           # index.html 만들기
  python tools/build.py --check   # index.html 이 소스와 같은지만 확인 (다르면 종료 코드 1)

자리 배치(우리 반 자리)를 고쳤다면 먼저  python src/seats/build_seats.py  를 실행하세요.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'chagok.html'
ASSETS = ROOT / 'src' / 'assets'
OUT = ROOT / 'index.html'
MARK = re.compile(r'\{\{asset:([A-Za-z0-9_.-]+)\}\}')


def build():
    src = SRC.read_text(encoding='utf-8')
    missing = [n for n in MARK.findall(src) if not (ASSETS / f'{n}.txt').exists()]
    if missing:
        sys.exit(f'없는 자산 파일: {missing}')
    return MARK.sub(lambda m: (ASSETS / f'{m.group(1)}.txt').read_text(encoding='utf-8'), src)


if __name__ == '__main__':
    html = build()
    if '--check' in sys.argv:
        same = OUT.exists() and OUT.read_text(encoding='utf-8') == html
        print('index.html 이 소스와 같아요.' if same else 'index.html 이 소스와 달라요. python tools/build.py 를 실행하세요.')
        sys.exit(0 if same else 1)
    OUT.write_text(html, encoding='utf-8', newline='')
    print(f'index.html 을 만들었어요 ({len(html.encode("utf-8")):,} bytes)')
