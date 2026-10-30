"""대강당 스크린(프로젝터)용 화면. 전부 HTML/CSS로 그려서 st.markdown 한 번으로 출력합니다.

같은 상태에서는 같은 HTML이 나오도록 만들어서, 2초마다 새로고침되어도 애니메이션이 끊기지 않습니다.
"""
from __future__ import annotations

import html
import random
from functools import lru_cache
from urllib.parse import quote

from core import fmt

# 연출 타이밍(초). 화면은 서버 시계 기준으로 그려서, 새로고침되어도 순서가 꼬이지 않습니다.
DRAW_FIRST = 1.5        # 추첨 후 첫 팀이 공개되는 시점
DRAW_STEP = 2.0         # 다음 팀까지 간격
POP_SEC = 1.0           # 공개 직후 강조 효과 시간
REVEAL_SUSPENSE = 3.6   # '최우수상 발표합니다' 대기 시간
REVEAL_ENTER = 1.0      # 팀명 등장 효과 시간
CONFETTI_SEC = 9.0      # 꽃가루를 보여 주는 시간


def esc(s) -> str:
    return html.escape(str(s or ""))


@lru_cache(maxsize=32)
def qr_data_uri(url: str) -> str:
    if not url:
        return ""
    try:
        import segno
        return segno.make(url, error="m").png_data_uri(scale=10, border=1, dark="#0b1534", light="#ffffff")
    except Exception:
        return ""


def _trend_svg() -> str:
    pts = [(-.02, .90), (.08, .86), (.17, .885), (.27, .83), (.37, .855), (.47, .79), (.57, .815), (.66, .74),
           (.745, .76), (.82, .62), (.885, .55), (.925, .40), (.962, .29)]
    P = [(u * 1920, v * 1080) for u, v in pts]
    d = f"M{P[0][0]:.1f},{P[0][1]:.1f}"
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
        d += (f" C{p1[0] + (p2[0] - p0[0]) / 6:.1f},{p1[1] + (p2[1] - p0[1]) / 6:.1f}"
              f" {p2[0] - (p3[0] - p1[0]) / 6:.1f},{p2[1] - (p3[1] - p1[1]) / 6:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    nodes = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#0b1534" stroke="#5f9bff" stroke-width="2.5" '
                    f'opacity="{.35 + .55 * (x / 1920):.2f}"/>' for x, y in P[1:])
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" preserveAspectRatio="xMidYMid slice">'
           '<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#4f8bff" stop-opacity=".25"/>'
           '<stop offset=".65" stop-color="#4f8bff" stop-opacity=".5"/><stop offset="1" stop-color="#5fe0e4" stop-opacity=".85"/>'
           '</linearGradient><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4f8bff" stop-opacity=".14"/>'
           '<stop offset="1" stop-color="#4f8bff" stop-opacity="0"/></linearGradient></defs>'
           f'<path d="{d} L1847,1080 L-38,1080 Z" fill="url(#a)"/>'
           f'<path d="{d}" fill="none" stroke="url(#g)" stroke-width="2.5"/>{nodes}</svg>')
    return "data:image/svg+xml;utf8," + quote(svg)


FONT = '"Pretendard Variable",Pretendard,"Noto Sans KR","Noto Sans CJK KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif'

SCREEN_CSS = """<style>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
html{font-size:min(1vw,1.7778vh)!important}
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],#MainMenu,footer{display:none!important}
[data-stale="true"],.stale-element{opacity:1!important;transition:none!important}
.kx{position:fixed;inset:0;z-index:999990;overflow:hidden;color:#fff;font-family:FONT;letter-spacing:-.02em;background:#070d20;-webkit-font-smoothing:antialiased;line-height:1.2}
.kx *{box-sizing:border-box}
.kx .bg{position:absolute;inset:0;background:radial-gradient(70rem 45rem at 80% 38%,rgba(79,139,255,.22),transparent 62%),radial-gradient(45rem 32rem at 100% 100%,rgba(95,224,228,.10),transparent 62%),linear-gradient(135deg,#060b1c 0%,#0b1534 100%)}
.kx .bg::before{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(120,160,255,.22) .08rem,transparent .1rem);background-size:1.25rem 1.25rem;-webkit-mask-image:linear-gradient(100deg,transparent 28%,#000 88%);mask-image:linear-gradient(100deg,transparent 28%,#000 88%)}
.kx .bg::after{content:"";position:absolute;inset:0;background:url("TREND") center/cover no-repeat;opacity:.7}
.kx .top{position:absolute;left:7rem;right:7rem;top:3.6rem;display:flex;justify-content:space-between;align-items:center;gap:2rem}
.kx .brand{font-size:1.3rem;font-weight:600;color:rgba(214,224,245,.78);display:flex;align-items:center;gap:.8rem;white-space:nowrap}
.kx .brand i{width:.7rem;height:.7rem;border-radius:.15rem;background:linear-gradient(135deg,#4f8bff,#5fe0e4)}
.kx .brand{flex:none}
.kx .chips{display:flex;gap:.6rem;flex-wrap:nowrap;overflow:hidden;min-width:0;flex:1;justify-content:flex-end}
.kx .chip{flex:0 1 auto;min-width:0;display:flex;align-items:center;gap:.55rem;padding:.5rem 1.1rem .5rem .55rem;border-radius:99rem;border:1px solid rgba(255,255,255,.14);font-size:1.1rem;color:rgba(214,224,245,.55);white-space:nowrap;max-width:15rem;overflow:hidden;text-overflow:ellipsis}
.kx .chip em{font-style:normal;flex:none;width:1.7rem;height:1.7rem;border-radius:50%;display:grid;place-items:center;font-size:.9rem;font-weight:700;background:rgba(255,255,255,.08)}
.kx .chip.done{color:rgba(214,224,245,.85)}
.kx .chip.done em{background:rgba(95,224,228,.18);color:#5fe0e4}
.kx .chip.now{border-color:#4f8bff;color:#fff;background:rgba(79,139,255,.18)}
.kx .chip.now em{background:#4f8bff;color:#fff}
.kx .lobby{position:absolute;inset:0;display:flex;align-items:center;justify-content:space-between;padding:0 7rem;gap:4rem}
.kx .t1{font-weight:300;font-size:4.6rem;color:rgba(214,224,245,.74);letter-spacing:-.035em;line-height:1.1}
.kx .t2{font-weight:900;font-size:7rem;letter-spacing:-.045em;line-height:1.1;margin-top:.5rem;text-shadow:0 0 3rem #070d20}
.kx .rule{width:5.4rem;height:.28rem;border-radius:.2rem;background:linear-gradient(90deg,#4f8bff,#5fe0e4);margin:3.2rem 0 2.4rem}
.kx .date{font-size:2.3rem;font-weight:700}
.kx .qrbox{flex:none;display:flex;flex-direction:column;align-items:center}
.kx .qrcard{background:#fff;border-radius:1.5rem;padding:1.5rem 1.5rem 1.3rem;width:21rem;box-shadow:0 2.4rem 6rem rgba(0,0,0,.5)}
.kx .qrcard img{width:100%;display:block}
.kx .qcap{color:#0c1730;text-align:center;margin-top:.9rem}
.kx .qcap b{display:block;font-size:1.75rem;font-weight:800;letter-spacing:-.03em}
.kx .qcap span{display:block;font-size:1.05rem;color:#52607d;margin-top:.35rem}
.kx .conn{margin-top:1.8rem;display:flex;align-items:center;gap:1.1rem;font-size:1.45rem;color:rgba(214,224,245,.8)}
.kx .conn b{color:#fff;font-size:1.9rem}
.kx .pips{display:flex;gap:.45rem}
.kx .pip{width:.85rem;height:.85rem;border-radius:50%;background:rgba(255,255,255,.18)}
.kx .pip.on{background:#5fe0e4;box-shadow:0 0 .8rem rgba(95,224,228,.8)}
.kx .warn{position:absolute;left:7rem;bottom:2.4rem;font-size:1.05rem;color:#ffb4a8}
.kx .ord-h{position:absolute;left:7rem;right:7rem;top:7.8rem}
.kx .ord-h h2{font-size:4rem;font-weight:900;margin:0;letter-spacing:-.045em}
.kx .ord-h p{font-size:1.5rem;color:rgba(214,224,245,.72);margin:.6rem 0 0}
.kx .rows{position:absolute;left:7rem;right:7rem;top:16.2rem;display:flex;flex-direction:column;gap:.7rem}
.kx .row{display:flex;align-items:center;gap:2.2rem;height:6.4rem;padding:0 2.6rem 0 1.1rem;border-radius:1.2rem;background:linear-gradient(90deg,rgba(255,255,255,.09),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.13);position:relative;overflow:hidden}
.kx .row .no{flex:none;width:3.6rem;height:3.6rem;border-radius:50%;display:grid;place-items:center;font-size:1.8rem;font-weight:900;background:linear-gradient(135deg,#4f8bff,#5fe0e4);color:#fff}
.kx .row .mid{flex:1;min-width:0}
.kx .row .nm{font-size:2.7rem;font-weight:800;line-height:3.5rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.04em}
.kx .row .tp{font-size:1.45rem;font-weight:500;color:rgba(214,224,245,.78);margin-top:.15rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;letter-spacing:-.02em}
.kx .row .dp{flex:none;font-size:1.6rem;color:rgba(214,224,245,.72);max-width:24rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kx .row.wait{background:rgba(255,255,255,.025);border-color:rgba(255,255,255,.07)}
.kx .row.wait .no{background:rgba(255,255,255,.08);color:rgba(255,255,255,.4)}
.kx .sk{height:2.4rem;width:24rem;max-width:100%;border-radius:.7rem;background:linear-gradient(90deg,rgba(255,255,255,.04) 0%,rgba(255,255,255,.10) 50%,rgba(255,255,255,.04) 100%);background-size:200% 100%;animation:shim 1.6s linear infinite}
.kx .row.next{border-color:rgba(95,224,228,.45);background:rgba(95,224,228,.06)}
.kx .row.next .no{background:rgba(95,224,228,.25);color:#fff}
.kx .row.next .sk{width:30rem;background:linear-gradient(90deg,rgba(95,224,228,.08) 0%,rgba(95,224,228,.28) 50%,rgba(95,224,228,.08) 100%);background-size:200% 100%;animation:shim .9s linear infinite;display:flex;align-items:center;padding-left:1.2rem;font-size:1.5rem;font-weight:700;color:#bff6f7;letter-spacing:.02em}
.kx .row.pop{animation:pop .95s cubic-bezier(.2,.8,.2,1) both}
.kx .row.pop .nm,.kx .row.pop .tp,.kx .row.pop .dp{animation:fadeup .6s ease-out both}
.kx .row.pop .tp{animation-delay:.15s}.kx .row.pop .dp{animation-delay:.25s}
.kx .run{position:absolute;left:7rem;right:7rem;top:14rem}
.kx .eyebrow{font-size:1.6rem;font-weight:700;color:#7fb0ff;letter-spacing:.04em}
.kx .team{font-size:8.6rem;font-weight:900;letter-spacing:-.055em;line-height:1.08;margin-top:1.2rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 0 3rem #070d20}
.kx .meta{font-size:2.1rem;color:rgba(214,224,245,.75);margin-top:1.5rem;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:80rem}
.kx .meta b{color:#fff;font-weight:700}
.kx .stat{position:absolute;left:7rem;bottom:5.6rem}
.kx .live{display:inline-flex;align-items:center;gap:1rem;font-size:1.9rem;font-weight:700;padding:1rem 2rem 1rem 1.6rem;border-radius:99rem;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16)}
.kx .live i{width:1rem;height:1rem;border-radius:50%;background:#ff5a5f;animation:pulse 1.6s infinite}
.kx .sc-label{font-size:1.7rem;font-weight:600;color:rgba(214,224,245,.82);display:flex;align-items:center;gap:.8rem}
.kx .sc-label i{width:.9rem;height:.9rem;border-radius:50%;background:#5fe0e4;animation:pulse2 1.6s infinite}
.kx .sc-num{font-size:6.4rem;font-weight:900;line-height:1;margin-top:1rem;letter-spacing:-.04em;font-variant-numeric:tabular-nums}
.kx .sc-num small{font-size:2.8rem;color:rgba(214,224,245,.55);font-weight:600;margin-left:.4rem}
.kx .sc-num span{font-size:1.7rem;color:rgba(214,224,245,.75);font-weight:600;margin-left:1.2rem;letter-spacing:0}
.kx .bar{height:.75rem;background:rgba(255,255,255,.1);border-radius:99rem;overflow:hidden;margin-top:1.5rem;width:42rem}
.kx .bar i{display:block;height:100%;background:linear-gradient(90deg,#4f8bff,#5fe0e4);border-radius:99rem}
.kx .bar i.full{background:linear-gradient(90deg,#3ddc97,#5fe0e4)}
.kx .mini{position:absolute;right:7rem;bottom:5rem;display:flex;align-items:center;gap:1.2rem;color:rgba(214,224,245,.75);font-size:1.15rem;text-align:right;line-height:1.5}
.kx .mini img{width:8.6rem;border-radius:.7rem;background:#fff;padding:.45rem;display:block}
.kx .mini b{display:block;color:#fff;font-size:1.35rem}
.kx .center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.kx .center h2{font-size:5.2rem;font-weight:900;margin:0;letter-spacing:-.045em}
.kx .center p{font-size:2rem;color:rgba(214,224,245,.78);margin:1.6rem 0 0}
.kx .dots3 span{display:inline-block;animation:blink 1.4s infinite both}
.kx .dots3 span:nth-child(2){animation-delay:.2s}.kx .dots3 span:nth-child(3){animation-delay:.4s}
.kx .rays{position:absolute;left:50%;top:47%;width:84rem;height:84rem;margin:-42rem 0 0 -42rem;background:repeating-conic-gradient(from 0deg,rgba(255,214,120,.11) 0deg 5deg,transparent 5deg 15deg);-webkit-mask-image:radial-gradient(circle,#000 0%,transparent 60%);mask-image:radial-gradient(circle,#000 0%,transparent 60%);animation:spin 60s linear infinite}
.kx .glow{position:absolute;left:50%;top:47%;width:70rem;height:40rem;margin:-20rem 0 0 -35rem;background:radial-gradient(closest-side,rgba(255,196,90,.24),transparent)}
.kx .award{font-size:2.2rem;font-weight:800;letter-spacing:.55em;padding-left:.55em;background:linear-gradient(90deg,#c8923a,#ffe7a3 50%,#c8923a);-webkit-background-clip:text;background-clip:text;color:transparent}
.kx .wname{font-size:10rem;font-weight:900;letter-spacing:-.055em;line-height:1.1;margin-top:2rem;max-width:88rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 .4rem 3rem rgba(0,0,0,.35)}
.kx .wmeta{font-size:2.2rem;color:rgba(232,238,250,.82);margin-top:1.6rem;font-weight:500;max-width:80rem}
.kx .congrats{margin-top:3.2rem;font-size:1.6rem;color:#f3d27a;letter-spacing:.4em;padding-left:.4em;font-weight:600}
.kx .others{position:absolute;left:0;right:0;bottom:4.6rem;text-align:center;font-size:1.5rem;color:rgba(214,224,245,.72)}
.kx .others b{color:#fff;margin:0 .7rem;font-weight:700}
.kx .sus{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;animation:fadein .5s ease-out both}
.kx .sus h2{font-size:6.4rem;font-weight:900;margin:2rem 0 0;letter-spacing:-.045em;animation:breathe 1.2s ease-in-out infinite}
.kx .ring{width:9rem;height:9rem;border-radius:50%;border:.4rem solid rgba(255,255,255,.12);border-top-color:#f3d27a;animation:spin 1s linear infinite;margin-top:3.4rem}
.kx .enter .wl{animation:winin 1s cubic-bezier(.2,.8,.2,1) both}
.kx .enter .rays{animation:fadein 1.6s ease-out both,spin 60s linear infinite}
.kx .enter .glow{animation:fadein 1.6s ease-out both}
.kx .enter .others{animation:fadein 1s ease-out .8s both}
.kx .cf{position:absolute;top:-3rem;width:.7rem;height:1.25rem;border-radius:.15rem;opacity:0;animation:fall var(--t) cubic-bezier(.3,.2,.6,1) both;animation-delay:var(--d)}
@keyframes shim{from{background-position:200% 0}to{background-position:-200% 0}}
@keyframes pop{0%{transform:scale(.975);border-color:#5fe0e4;box-shadow:0 0 0 0 rgba(95,224,228,0)}35%{border-color:#5fe0e4;box-shadow:0 0 2.6rem .2rem rgba(95,224,228,.35)}100%{transform:none;box-shadow:0 0 0 0 rgba(95,224,228,0)}}
@keyframes fadeup{from{opacity:0;transform:translateY(.7rem)}to{opacity:1;transform:none}}
@keyframes cardin{from{opacity:0;transform:translateY(1.6rem)}to{opacity:1;transform:none}}
@keyframes land{0%{opacity:0}18%{opacity:1}100%{opacity:0}}
@keyframes fadein{from{opacity:0}to{opacity:1}}
@keyframes fadeout{from{opacity:1}to{opacity:0;visibility:hidden}}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(255,90,95,.6)}70%{box-shadow:0 0 0 1.1rem rgba(255,90,95,0)}100%{box-shadow:0 0 0 0 rgba(255,90,95,0)}}
@keyframes pulse2{0%{box-shadow:0 0 0 0 rgba(95,224,228,.6)}70%{box-shadow:0 0 0 1rem rgba(95,224,228,0)}100%{box-shadow:0 0 0 0 rgba(95,224,228,0)}}
@keyframes blink{0%,80%,100%{opacity:.2}40%{opacity:1}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes breathe{0%,100%{opacity:.75;transform:scale(1)}50%{opacity:1;transform:scale(1.04)}}
@keyframes winin{from{opacity:0;transform:scale(.86);filter:blur(1rem)}to{opacity:1;transform:none;filter:none}}
@keyframes fall{0%{opacity:0;transform:translate3d(0,0,0) rotate(0)}6%{opacity:1}85%{opacity:1}100%{opacity:0;transform:translate3d(var(--x),64rem,0) rotate(var(--r))}}
</style>""".replace("FONT", FONT).replace("TREND", _trend_svg())


def fit(text: str, base: float, avail: float) -> str:
    """글자 수에 맞춰 큰 제목 크기를 줄여 한 줄에 들어가게 합니다(rem 단위)."""
    w = 0.0
    for ch in str(text or ""):
        if "\uac00" <= ch <= "\ud7a3":
            w += 0.92
        elif ch == " ":
            w += 0.3
        elif ch.isascii():
            w += 0.6
        else:
            w += 0.8
    size = base if w <= 0 else min(base, avail / w)
    return f"font-size:{size:.2f}rem"


def _one(s: str) -> str:
    """st.markdown이 HTML을 그대로 쓰도록 한 줄로 만듭니다(빈 줄·들여쓰기 제거)."""
    return " ".join(line.strip() for line in s.splitlines() if line.strip())


def _top(snap, chips=True) -> str:
    S, st = snap["S"], snap["st"]
    brand = f'<div class="brand"><i></i>{esc(S["title_top"])} {esc(S["title_main"])}</div>'
    if not chips or not st["order"]:
        return f'<div class="top">{brand}</div>'
    out = []
    for i, t in enumerate(st["order"]):
        cls = "done" if t in st["closed"] else ("now" if st["phase"] == "running" and i == st["cur"] else "")
        out.append(f'<div class="chip {cls}"><em>{"✓" if cls == "done" else i + 1}</em>{esc(S["teams"][t]["name"])}</div>')
    return f'<div class="top">{brand}<div class="chips">{"".join(out)}</div></div>'


def _lobby(snap, judge_url, local_warn) -> str:
    S = snap["S"]
    qr = qr_data_uri(judge_url)
    pips = "".join(f'<div class="pip{" on" if s["online"] else ""}"></div>' for s in snap["seats"])
    qr_html = (f'<img src="{qr}" alt="심사위원 접속 QR">' if qr else
               '<div style="color:#0c1730;padding:3rem 1rem;text-align:center;font-size:1.2rem">관리 화면의 설정에서<br>접속 주소를 입력해 주세요</div>')
    warn = (f'<div class="warn">QR 주소가 {esc(judge_url)} 입니다. 휴대폰에서 열리지 않는 주소면 관리 화면 설정에서 접속 주소를 입력해 주세요.</div>'
            if local_warn else "")
    return f'''
<div class="lobby">
<div><div class="t1">{esc(S["title_top"])}</div><div class="t2">{esc(S["title_main"])}</div>
<div class="rule"></div><div class="date">{esc(S["date_line"])}</div></div>
<div class="qrbox"><div class="qrcard">{qr_html}<div class="qcap"><b>심사위원 접속</b><span>휴대폰 카메라로 QR 코드를 비춰 주세요</span></div></div>
<div class="conn"><div class="pips">{pips}</div><div>접속 <b>{snap["online"]}</b> / {snap["judges"]}</div></div></div>
</div>{warn}'''


def _order(snap) -> str:
    """추첨 결과를 한 팀씩 공개합니다. 공개 전 줄에는 팀 이름을 절대 보여 주지 않습니다."""
    S, st = snap["S"], snap["st"]
    e = snap["now"] - st["drawn_at"]
    rows, nxt = [], None
    for i, t in enumerate(st["order"]):
        at = DRAW_FIRST + DRAW_STEP * i
        team = S["teams"][t]
        if e >= at:
            cls = "row pop" if e - at < POP_SEC else "row"
            tp = f'<div class="tp">{esc(team["topic"])}</div>' if team["topic"] else ""
            body = (f'<div class="mid"><div class="nm">{esc(team["name"])}</div>{tp}</div>'
                    f'<div class="dp">{esc(team["dept"])}</div>')
        else:
            if nxt is None:
                nxt = i
            cls = "row wait next" if nxt == i else "row wait"
            body = f'<div class="mid"><div class="sk">{"추첨 중" if nxt == i else ""}</div></div>'
        rows.append(f'<div class="{cls}"><div class="no">{i + 1}</div>{body}</div>')
    sub = "추첨하고 있습니다" if nxt is not None else "현장에서 무작위로 추첨한 순서입니다"
    return f'''{_top(snap, chips=False)}
<div class="ord-h"><h2>발표 순서</h2><p>{sub}</p></div>
<div class="rows">{"".join(rows)}</div>'''


def _running(snap, judge_url) -> str:
    S, st = snap["S"], snap["st"]
    t = snap["cur"]
    team = S["teams"][t]
    meta = " · ".join(x for x in [f'<b>{esc(team["dept"])}</b>' if team["dept"] else "", esc(team["topic"])] if x)
    if st["step"] == "scoring":
        sub = snap["sub"] or {"submitted": 0, "eligible": 0}
        pct = 100 * sub["submitted"] / max(1, sub["eligible"])
        full = sub["submitted"] >= sub["eligible"] > 0
        stat = (f'<div class="sc-label"><i></i>심사위원 평가 입력 중</div>'
                f'<div class="sc-num">{sub["submitted"]}<small>/ {sub["eligible"]}</small>'
                f'<span>{"모두 제출했습니다" if full else "제출"}</span></div>'
                f'<div class="bar"><i class="{"full" if full else ""}" style="width:{pct:.1f}%"></i></div>')
    else:
        stat = '<div class="live"><i></i>발표 중</div>'
    qr = qr_data_uri(judge_url)
    mini = (f'<div class="mini"><div><b>심사 접속</b>화면이 꺼졌다면<br>다시 찍어 주세요</div><img src="{qr}" alt=""></div>'
            if qr else "")
    return f'''{_top(snap)}
<div class="run"><div class="eyebrow">발표 {st["cur"] + 1} / {len(st["order"])}</div>
<div class="team" style="{fit(team["name"], 8.6, 84)}">{esc(team["name"])}</div>{f'<div class="meta">{meta}</div>' if meta else ""}</div>
<div class="stat">{stat}</div>{mini}'''


def _done(snap) -> str:
    return f'''{_top(snap)}
<div class="center"><h2>모든 발표가 끝났습니다</h2>
<p>심사 결과를 집계하고 있습니다<span class="dots3"><span>.</span><span>.</span><span>.</span></span></p></div>'''


def _reveal(snap) -> str:
    S, st = snap["S"], snap["st"]
    w = snap["winner"]
    if w is None:
        return _done(snap)
    e = snap["now"] - st["revealed_at"]
    if e < REVEAL_SUSPENSE:
        return ('<div style="position:absolute;inset:0"><div class="sus"><div class="award">최우수상</div>'
                '<h2>발표합니다</h2><div class="ring"></div></div></div>')
    team = S["teams"][w]
    meta = " · ".join(x for x in [esc(team["dept"]), esc(team["topic"])] if x)
    others = ""
    if S["show_runner_ups"]:
        names = "".join(f"<b>{esc(S['teams'][t]['name'])}</b>" for t in st["order"] if t != w)
        others = f'<div class="others">우수상 {names}</div>'
    conf = ""
    if e < REVEAL_SUSPENSE + CONFETTI_SEC:
        rng = random.Random(int(st["revealed_at"] * 1000) or 3)
        cols = ["#f3d27a", "#ffe7a3", "#4f8bff", "#5fe0e4", "#ffffff", "#c8923a"]
        conf = "".join(
            f'<i class="cf" style="left:{rng.uniform(2, 98):.1f}%;background:{rng.choice(cols)};'
            f'--d:{0.15 + rng.uniform(0, 2.0):.2f}s;--t:{rng.uniform(3.4, 5.8):.2f}s;'
            f'--x:{rng.uniform(-8, 8):.1f}rem;--r:{rng.choice([-1, 1]) * rng.randint(240, 900)}deg;'
            f'width:{rng.uniform(.45, .8):.2f}rem;height:{rng.uniform(.8, 1.4):.2f}rem"></i>' for _ in range(70))
    enter = "enter" if e < REVEAL_SUSPENSE + REVEAL_ENTER else ""
    return f'''<div class="{enter}" style="position:absolute;inset:0">
<div class="glow"></div><div class="rays"></div>
<div class="center wl"><div class="award">최우수상</div><div class="wname" style="{fit(team["name"], 10, 82)}">{esc(team["name"])}</div>
{f'<div class="wmeta">{meta}</div>' if meta else ""}<div class="congrats">축하합니다</div></div>{others}{conf}</div>'''


def render(snap: dict, judge_url: str, local_warn: bool = False) -> str:
    st = snap["st"]
    ph, now = st["phase"], snap["now"]
    if ph == "order":
        body = _order(snap)
    elif ph == "running" and snap["cur"] is not None:
        body = _running(snap, judge_url)
    elif ph == "done":
        body = _done(snap)
    elif ph == "reveal":
        body = _reveal(snap)
    else:
        body = _lobby(snap, judge_url, local_warn)
    return _one(f'<div class="kx"><div class="bg"></div>{body}</div>')
