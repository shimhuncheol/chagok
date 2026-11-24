"""우리 반 자리 CSS의 고정 색을 차곡 테마 변수(--surface, --bg, --text, --primary ...)로 바꿔요.
- 무채색: 밝기에 맞춰 --text 와 --surface/--bg 를 섞어요 (기본 모습은 거의 그대로, 테마에 따라 물듦)
- 초록·라임(포인트색): --primary 와 섞어요
- 남/여 학생 색(파랑·분홍), 갈색 경고색, 반투명 그림자: 그대로 둬요
"""
import re, colorsys, sys

INK_L = 0.15   # 원래 글자색(#20252c)의 밝기


def parse(c):
    c = c.lower()
    if c == 'white':
        return (1, 1, 1), 1
    if c == 'black':
        return (0, 0, 0), 1
    h = c[1:]
    if len(h) in (3, 4):
        h = ''.join(x * 2 for x in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1
    return (r, g, b), a


def pct(x):
    return max(1, min(100, round(x)))


def mapc(c, prop, sel):
    (r, g, b), a = parse(c)
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    hue = hh * 360
    chroma = max(r, g, b) - min(r, g, b)
    is_text = prop in ('color', 'fill', 'stroke', '-webkit-text-fill-color', 'caret-color')
    primary_sel = re.search(r'primary|confirm|\.selected|is-selected|active|\.on\b', sel or '')
    if a < 1:
        if l > 0.9 and chroma < 0.1:
            return c                                   # 흰색 반투명 (유리 효과)
        if chroma < 0.12:
            return c                                   # 그림자
        if 60 <= hue <= 175:                            # 포인트색 반투명 (예: 초점 테두리)
            return f'color-mix(in srgb, var(--primary) {pct(a * 100)}%, transparent)'
        return c
    if chroma >= 0.12:
        if 60 <= hue <= 175:                            # 초록·라임 → 테마 주 색
            if l >= 0.6:
                q = pct((1 - l) * 85)
                return f'color-mix(in srgb, var(--primary) {q}%, var(--surface))'
            k = pct(100 - (0.5 - min(l, 0.5)) * 120)
            return f'color-mix(in srgb, var(--primary) {k}%, var(--text))'
        return c                                       # 남/여, 경고, 갈색 — 의미가 있는 색은 그대로
    # 무채색
    if is_text and l >= 0.97:
        return 'var(--on-primary)' if primary_sel else 'var(--surface)'
    if primary_sel and l < 0.42 and not is_text:
        return 'var(--primary)' if l < 0.25 else 'color-mix(in srgb, var(--primary) 82%, var(--surface))'
    if l >= 0.985:
        return 'var(--surface)'
    if l >= 0.955:
        p = pct((0.985 - l) / (0.985 - 0.955) * 35)
        return f'color-mix(in srgb, var(--bg) {100 - p}%, var(--surface))' if p < 100 else 'var(--bg)'
    if is_text:
        p = pct((0.985 - l) / (0.985 - INK_L) * 100)
        if p >= 88:
            return 'var(--text)'
        if p >= 60:
            return 'var(--text2)'
        return 'var(--text3)'
    p = pct((0.985 - l) / (0.985 - INK_L) * 100)
    return f'color-mix(in srgb, var(--text) {p}%, var(--surface))'


COLOR = re.compile(r'#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b|\bwhite\b|\bblack\b')


def transform(css):
    css = re.sub(r"@import url\([^)]*\);?", '', css)
    css = re.sub(r"font-family:\s*'Noto Sans KR'[^;}]*", 'font-family:var(--font)', css)
    css = re.sub(r"font:\s*14px 'Noto Sans KR',sans-serif", 'font:14px var(--font)', css)
    out = []
    # 규칙 단위로: 선택자 { 선언들 }
    pos = 0
    for m in re.finditer(r'([^{}]*)\{([^{}]*)\}', css):
        out.append(css[pos:m.start()])
        sel, body = m.group(1), m.group(2)

        def decl(dm):
            prop, val = dm.group(1).strip().lower(), dm.group(2)
            if prop.startswith('--'):
                return dm.group(0)                     # 변수 정의는 아래 :root 에서 따로 정해요
            return dm.group(1) + ':' + COLOR.sub(lambda cm: mapc(cm.group(0), prop, sel), val)

        body = re.sub(r'([a-zA-Z-]+)\s*:([^;]+)', decl, body)
        out.append(sel + '{' + body + '}')
        pos = m.end()
    out.append(css[pos:])
    return ''.join(out)


ROOT = """
/* ---- 차곡 디자인 연결 ---- */
:root{--green:var(--primary);--ink:var(--text);--line:var(--border);--canvas:var(--bg);--muted:var(--text3);
--lime:color-mix(in srgb, var(--primary) 22%, var(--surface));--lime-ink:color-mix(in srgb, var(--primary) 80%, var(--text))}
html,body{background:var(--bg)}
body{font-family:var(--font)}
"""

if __name__ == '__main__':
    src = sys.argv[1]
    a = open(f'{src}/style.css', encoding='utf-8').read()
    b = open(f'{src}/theme.css', encoding='utf-8').read()
    sys.stdout.write(transform(a) + '\n' + transform(b) + ROOT)
