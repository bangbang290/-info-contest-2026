"""정보분석 경진대회 현장 심사 시스템 (Streamlit)

주소 하나로 세 화면을 씁니다.
  /                 → 심사위원(휴대폰). QR로 접속해 본인 관실을 한 번 선택
  /?view=screen     → 대강당 스크린(프로젝터)
  /?view=admin      → 기획팀 진행·관리 (PIN 필요)
"""
from __future__ import annotations

import time

import pandas as pd
import streamlit as st

import core
import screens

st.set_page_config(page_title="정보분석 경진대회 심사", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")
core.init()

BASE_CSS = """<style>
header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"],#MainMenu,footer{display:none!important}
[data-stale="true"],.stale-element{opacity:1!important;transition:none!important}
</style>"""

JUDGE_CSS = """<style>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
.block-container{max-width:560px!important;padding-top:1.2rem!important;padding-bottom:5rem!important}
.jx{font-family:"Pretendard Variable",Pretendard,"Noto Sans KR","Apple SD Gothic Neo",sans-serif;letter-spacing:-.02em}
.jx-head{padding:.2rem 0 1rem;border-bottom:1px solid rgba(255,255,255,.12);margin-bottom:1rem}
.jx-head small{display:block;color:#8ea3cf;font-size:.9rem}
.jx-head b{display:block;font-size:1.35rem;font-weight:800;color:#fff;margin-top:.15rem}
.jx-who{display:inline-block;margin-top:.55rem;padding:.25rem .7rem;border-radius:99px;background:rgba(79,139,255,.18);color:#cfe0ff;font-size:.95rem;font-weight:600}
.jx-card{border-radius:16px;padding:1.1rem 1.2rem;background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.12);margin:.4rem 0 1rem}
.jx-card .ey{color:#7fb0ff;font-weight:700;font-size:.95rem}
.jx-card .tm{font-size:2rem;font-weight:900;color:#fff;margin-top:.2rem;line-height:1.2;word-break:keep-all}
.jx-card .mt{color:#b9c6e4;font-size:1rem;margin-top:.35rem;word-break:keep-all}
.jx-msg{font-size:1.15rem;line-height:1.6;color:#dfe7f7;word-break:keep-all}
.jx-msg b{color:#fff}
.jx-crit{font-size:1.12rem;font-weight:700;color:#fff;margin:1.1rem 0 .1rem}
.jx-crit span{color:#8ea3cf;font-weight:500;font-size:.95rem;margin-left:.35rem}
.jx-total{display:flex;justify-content:space-between;align-items:baseline;margin:1.3rem 0 .6rem;padding:.9rem 1.1rem;border-radius:14px;background:rgba(79,139,255,.14);border:1px solid rgba(79,139,255,.35)}
.jx-total span{color:#cfe0ff;font-weight:600}
.jx-total b{font-size:1.9rem;color:#fff;font-weight:900}
.jx-total b small{font-size:1rem;color:#9fb3dc;font-weight:600;margin-left:.2rem}
.jx-order{margin:.6rem 0 0;padding:0;list-style:none}
.jx-order li{padding:.55rem 0;border-bottom:1px solid rgba(255,255,255,.08);font-size:1.05rem;color:#dfe7f7}
.jx-order li em{font-style:normal;display:inline-block;width:1.6rem;color:#7fb0ff;font-weight:800}
div[data-testid="stButton"] button{min-height:3.3rem;font-size:1.1rem!important;font-weight:700;border-radius:12px}
div[data-testid="stButton"] button p{font-size:1.1rem!important}
div[data-testid="stButtonGroup"]>div,div[data-testid="stButtonGroup"] div:has(> button){flex-wrap:wrap!important;gap:.5rem!important;width:100%}
div[data-testid="stButtonGroup"] button{flex:1 1 100%!important;min-height:3.5rem;border-radius:12px!important;margin:0!important}
div[data-testid="stButtonGroup"] button p{font-size:1.15rem!important;font-weight:700}
.jx-note{color:#b9c6e4;font-size:1rem;margin:.2rem 0 .4rem;word-break:keep-all}
.jx-guide .gd{padding:.6rem 0;border-bottom:1px solid rgba(255,255,255,.08)}
.jx-guide .gd:last-child{border-bottom:0}
.jx-guide .gd b{display:block;color:#fff;font-size:1.05rem}
.jx-guide .gd b span{color:#7fb0ff;font-weight:700;margin-left:.35rem}
.jx-guide .gd div{color:#c9d4ec;font-size:.98rem;line-height:1.55;padding-left:.6rem;word-break:keep-all}
div[data-testid="stNumberInput"] input{font-size:1.3rem;min-height:3rem}
</style>"""

ADMIN_CSS = """<style>
.block-container{max-width:1180px!important;padding-top:1.5rem!important}
.ad-h{font-size:1.6rem;font-weight:800;margin:0 0 .2rem}
.ad-sub{color:#8ea3cf;margin:0 0 1rem}
.ad-big{font-size:2.2rem;font-weight:900;line-height:1.2}
.ad-pill{display:inline-block;padding:.2rem .7rem;border-radius:99px;font-size:.85rem;font-weight:700;margin-right:.35rem}
.ad-pill.on{background:rgba(61,220,151,.18);color:#6ff0b3}.ad-pill.off{background:rgba(255,255,255,.08);color:#9aa8c7}
.ad-pill.now{background:rgba(79,139,255,.25);color:#cfe0ff}.ad-pill.done{background:rgba(95,224,228,.15);color:#8ff0f2}
</style>"""

PHASE_KO = {"lobby": "추첨 전 (접속 대기)", "order": "순서 추첨 완료", "running": "발표 진행 중",
            "done": "모든 평가 마감 · 결과 발표 대기", "reveal": "최우수 발표 완료"}


def md(html: str):
    st.markdown(html, unsafe_allow_html=True)


def base_url() -> str:
    S = core.get_settings()
    if S["public_url"]:
        return S["public_url"]
    try:
        h = {k.lower(): v for k, v in st.context.headers.items()}
        host = h.get("x-forwarded-host") or h.get("host") or ""
        if host:
            proto = h.get("x-forwarded-proto") or ("https" if "streamlit.app" in host else "http")
            return f"{proto}://{host}"
    except Exception:
        pass
    return ""


def is_local(url: str) -> bool:
    return any(x in url for x in ("localhost", "127.0.0.1", "0.0.0.0")) or not url


def judge_url() -> str:
    b = base_url()
    return f"{b}/" if b else ""


def who(dept: str) -> str:
    """심사위원 호칭. '심사2국장님'처럼 이미 '님'으로 끝나면 그대로,
    '심사2국장'처럼 '장'으로 끝나면 '님'만, 나머지(관실 이름)는 '과장님'을 붙입니다."""
    d = str(dept or "").strip()
    if d.endswith("님"):
        return d
    if d.endswith("장"):
        return d + "님"
    return f"{d} 과장님"


def autofill(S, team) -> int:
    """리허설용: 아직 제출하지 않은 심사위원의 점수를 무작위로 채웁니다."""
    import random
    rng = random.Random()
    n = 0
    for s_ in core.seats():
        if not core.eligible(S, s_["idx"], team) or core.my_score(s_["token"], team):
            continue
        vals = []
        for c in S["criteria"]:
            opts = grade_options(S, c)
            weights = [.3, .4, .2, .07, .03][:len(opts)] if len(opts) <= 5 else None
            vals.append(rng.choices(opts, weights=weights)[0])
        core.submit(s_["token"], team, vals, proxy=True)
        n += 1
    return n


def grade_options(S, crit):
    return [round(crit["max"] * r, 4) for r in S["grade_ratio"]]


def grade_label(S, crit, v):
    for lab, r in zip(S["grade_labels"], S["grade_ratio"]):
        if abs(crit["max"] * r - v) < 1e-6:
            return lab
    return ""


# ───────────────────────── 스크린
def screen_view():
    md(screens.SCREEN_CSS)

    @st.fragment(run_every=1)
    def live():
        snap = core.snapshot()
        url = judge_url()
        md(screens.render(snap, url, local_warn=is_local(url)))

    live()


# ───────────────────────── 심사위원
def score_inputs(S, team, key_prefix, existing=None):
    """항목별 입력 위젯. 값 목록(미선택은 None)을 돌려줍니다."""
    vals = []
    for k, crit in enumerate(S["criteria"]):
        key = f"{key_prefix}_{team}_{k}"
        if existing and key not in st.session_state:
            st.session_state[key] = existing["vals"][k]
        md(f'<div class="jx jx-crit">{screens.esc(crit["name"])}<span>{core.fmt(crit["max"])}점 만점</span></div>')
        if S["input_mode"] == "grade":
            opts = grade_options(S, crit)
            if key in st.session_state and st.session_state[key] not in opts:
                st.session_state[key] = None
            fmt_fn = (lambda v, c=crit: f"{core.fmt(v)}점 · {grade_label(S, c, v)}")
            if hasattr(st, "segmented_control"):
                v = st.segmented_control(crit["name"], opts, format_func=fmt_fn, key=key,
                                         label_visibility="collapsed")
            else:
                v = st.radio(crit["name"], opts, format_func=fmt_fn, key=key, index=None, horizontal=True,
                             label_visibility="collapsed")
        else:
            v = st.number_input(crit["name"], min_value=0.0, max_value=float(crit["max"]), step=1.0, value=None,
                                key=key, placeholder=f"0 ~ {core.fmt(crit['max'])}", label_visibility="collapsed")
        vals.append(v)
    return vals


def seat_picker():
    S = core.get_settings()
    md(JUDGE_CSS)
    md(f'<div class="jx jx-head"><small>{screens.esc(S["title_top"])}</small><b>{screens.esc(S["title_main"])} 심사</b></div>')
    pending = st.session_state.get("pick")
    seats = core.seats()
    if pending is not None and pending < len(seats):
        s = seats[pending]
        md(f'<div class="jx jx-card"><div class="jx-msg"><b>{screens.esc(who(s["dept"]))}</b>으로 접속합니다.<br>맞으시면 아래 버튼을 눌러 주세요.</div></div>')
        if s["online"]:
            st.warning("이 자리는 다른 휴대폰에서 이미 접속 중입니다. 본인이 맞을 때만 계속해 주세요.")
        code = judge_code()
        typed = ""
        if code:
            typed = st.text_input("심사위원 확인 코드", type="password", key="pick_code",
                                  placeholder="심사 자료에 적힌 숫자를 입력해 주세요")
        if st.button("네, 맞습니다", type="primary", use_container_width=True, key="pick_yes"):
            if code and typed.strip() != code:
                st.error("확인 코드가 맞지 않습니다. 심사 자료에 적힌 숫자를 다시 확인해 주세요.")
                return
            token = core.claim(s["idx"])
            st.session_state.pop("pick", None)
            st.query_params["j"] = token
            st.rerun()
        if st.button("다시 선택", use_container_width=True, key="pick_no"):
            st.session_state.pop("pick", None)
            st.rerun()
        return
    md('<div class="jx jx-msg" style="margin-bottom:.8rem">본인 <b>소속 관실</b>을 눌러 주세요.<br>'
       '<span style="color:#8ea3cf;font-size:.95rem">한 번만 선택하면 이 휴대폰에서 계속 유지됩니다.</span></div>')
    for s in seats:
        label = who(s["dept"]) + ("  · 접속 중" if s["online"] else "")
        if st.button(label, key=f"seat_{s['idx']}", use_container_width=True):
            st.session_state["pick"] = s["idx"]
            st.rerun()


def judge_view():
    token = st.query_params.get("j")
    judge = core.judge_by_token(token)
    if not judge:
        if token:
            st.query_params.clear()
        seat_picker()
        return
    md(JUDGE_CSS)

    @st.fragment(run_every=3)
    def live():
        core.touch(judge["token"])
        S, stt = core.get_settings(), core.get_state()
        md(f'<div class="jx jx-head"><small>{screens.esc(S["title_top"])} {screens.esc(S["title_main"])}</small>'
           f'<b>심사위원 화면</b><span class="jx-who">{screens.esc(who(judge["dept"]))}</span></div>')
        ph = stt["phase"]
        order_html = ""
        if stt["order"]:
            items = "".join(f'<li><em>{i + 1}</em>{screens.esc(S["teams"][t]["name"])}'
                            f'{" · 평가 제외(본인 관실)" if not core.eligible(S, judge["idx"], t) else ""}</li>'
                            for i, t in enumerate(stt["order"]))
            order_html = f'<ul class="jx-order">{items}</ul>'
        if ph == "lobby":
            md('<div class="jx jx-card"><div class="jx-msg">접속되었습니다. 감사합니다.<br>'
               '곧 <b>발표 순서 추첨</b>이 진행됩니다. 이 화면을 켜 두시면 발표마다 평가 화면이 자동으로 나타납니다.</div></div>')
            return
        if ph == "order":
            md(f'<div class="jx jx-card"><div class="ey">발표 순서</div>{order_html}</div>'
               '<div class="jx jx-msg">첫 발표가 시작되면 평가 화면이 자동으로 나타납니다.</div>')
            return
        if ph in ("done", "reveal"):
            msg = "모든 평가가 끝났습니다. 수고 많으셨습니다."
            if ph == "reveal":
                snap = core.snapshot()
                if snap["winner"] is not None:
                    msg += f'<br><br>최우수상: <b>{screens.esc(S["teams"][snap["winner"]]["name"])}</b>'
            md(f'<div class="jx jx-card"><div class="jx-msg">{msg}</div></div>')
            return
        team = core.current_team(stt)
        if team is None:
            return
        tinfo = S["teams"][team]
        meta = " · ".join(x for x in [tinfo["dept"], tinfo["topic"]] if x)
        md(f'<div class="jx jx-card"><div class="ey">발표 {stt["cur"] + 1} / {len(stt["order"])}'
           f'{" · 평가 요청" if stt["step"] == "scoring" else " · 발표 중"}</div>'
           f'<div class="tm">{screens.esc(tinfo["name"])}</div>'
           f'{f"<div class=mt>{screens.esc(meta)}</div>" if meta else ""}</div>')
        if not core.eligible(S, judge["idx"], team):
            md('<div class="jx jx-card"><div class="jx-msg"><b>본인 관실 팀</b>이라 이번 발표는 평가하지 않습니다.<br>'
               '다음 발표가 시작되면 화면이 자동으로 바뀝니다.</div></div>')
            return
        mine = core.my_score(judge["token"], team)
        if team in stt["closed"]:
            md('<div class="jx jx-card"><div class="jx-msg">이 팀의 평가는 마감되었습니다.</div></div>')
            return
        if S["guide"]:
            summary = " · ".join(f'{g["name"]} {g["weight"]}' for g in S["guide"])
            with st.expander(f"평가기준 보기 ({summary})"):
                md('<div class="jx jx-guide">' + "".join(
                    f'<div class="gd"><b>{screens.esc(g["name"])}<span>{screens.esc(g["weight"])}</span></b>'
                    + "".join(f"<div>· {screens.esc(x)}</div>" for x in g["items"]) + "</div>"
                    for g in S["guide"]) + "</div>")
        if S["guide_note"]:
            md(f'<div class="jx jx-note">{screens.esc(S["guide_note"])}</div>')
        vals = score_inputs(S, team, "s", existing=mine)
        picked = [v for v in vals if v is not None]
        max_total = sum(c["max"] for c in S["criteria"])
        total_label = "선택한 점수" if len(S["criteria"]) == 1 else "합계"
        md(f'<div class="jx jx-total"><span>{total_label}</span><b>{core.fmt(sum(picked)) if picked else "–"}'
           f'<small>/ {core.fmt(max_total)}점</small></b></div>')
        if mine:
            st.success(f"제출 완료 ({core.fmt(mine['total'])}점) · 마감 전까지 수정해서 다시 제출할 수 있습니다.")
        label = "수정해서 다시 제출" if mine else "점수 제출하기"
        if st.button(label, type="primary", use_container_width=True, key=f"submit_{team}"):
            if any(v is None for v in vals):
                missing = [c["name"] for c, v in zip(S["criteria"], vals) if v is None]
                st.error(f"아직 선택하지 않은 항목이 있습니다: {', '.join(missing)}")
            else:
                try:
                    core.submit(judge["token"], team, vals)
                    st.toast("제출되었습니다")
                    st.rerun(scope="fragment")
                except core.FlowError as e:
                    st.error(str(e))

    live()
    st.write("")
    with st.expander("다른 분이 이 휴대폰을 쓰시나요?"):
        st.caption("심사위원 선택 화면으로 돌아갑니다. 지금까지 제출한 점수는 그대로 남습니다.")
        if st.button("심사위원 다시 선택", key="reset_me"):
            st.query_params.clear()
            st.rerun()


# ───────────────────────── 관리
def _secret(name: str):
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return None


def admin_pin() -> str:
    return _secret("admin_pin") or core.get_settings()["admin_pin"]


def judge_code() -> str:
    """심사위원 확인 코드. 비어 있으면 코드 없이 접속(권장하지 않음)."""
    v = _secret("judge_code")
    return v if v is not None else core.get_settings()["judge_code"]


def confirm_button(label, key, warn, kind="secondary"):
    """두 번 눌러야 실행되는 버튼(실수 방지)."""
    if st.session_state.get(f"cf_{key}"):
        st.warning(warn)
        c1, c2 = st.columns(2)
        ok = c1.button("실행", key=f"{key}_ok", type="primary", use_container_width=True)
        if c2.button("취소", key=f"{key}_no", use_container_width=True):
            st.session_state.pop(f"cf_{key}", None)
            st.rerun()
        if ok:
            st.session_state.pop(f"cf_{key}", None)
        return ok
    if st.button(label, key=key, type=kind, use_container_width=True):
        st.session_state[f"cf_{key}"] = True
        st.rerun()
    return False


def act(fn, *a):
    try:
        fn(*a)
        return True
    except core.FlowError as e:
        st.error(str(e))
        return False


def admin_view():
    md(ADMIN_CSS)
    if not st.session_state.get("admin_ok"):
        md('<div class="ad-h">관리 화면</div><div class="ad-sub">기획팀 전용입니다.</div>')
        with st.form("pin"):
            pin = st.text_input("관리자 PIN", type="password")
            if st.form_submit_button("들어가기", type="primary"):
                if pin.strip() == admin_pin():
                    st.session_state["admin_ok"] = True
                    st.rerun()
                else:
                    st.error("PIN이 맞지 않습니다.")
        return
    S = core.get_settings()
    md(f'<div class="ad-h">{screens.esc(S["title_top"])} {screens.esc(S["title_main"])} · 관리</div>')
    url = base_url()
    if is_local(url):
        st.warning("휴대폰이 접속할 주소를 아직 알 수 없습니다. [설정] 탭의 '접속 주소'에 실제 주소를 넣어 주세요.")
    if S.get("rehearsal"):
        st.error("🧪 리허설 모드가 켜져 있습니다. 행사 전에 [설정] 탭에서 끄고, [데이터] 탭에서 '점수·진행 초기화'를 눌러 주세요.")
    if not judge_code():
        st.warning("심사위원 확인 코드가 설정되지 않았습니다. 스크린의 QR을 찍은 누구나 심사위원으로 들어올 수 있으니 "
                   "[설정] 탭이나 Secrets에서 코드를 정해 주세요.")
    tabs = st.tabs(["진행", "결과", "대리 입력", "QR · 링크", "설정", "데이터"])
    with tabs[0]:
        progress_panel()
    with tabs[1]:
        results_panel()
    with tabs[2]:
        proxy_panel()
    with tabs[3]:
        links_panel()
    with tabs[4]:
        settings_panel()
    with tabs[5]:
        data_panel()


def progress_panel():
    @st.fragment(run_every=2)
    def live():
        snap = core.snapshot()
        S, stt = snap["S"], snap["st"]
        c1, c2 = st.columns([3, 2])
        with c1:
            st.caption("현재 단계")
            md(f'<div class="ad-big">{PHASE_KO.get(stt["phase"], stt["phase"])}</div>')
            if stt["order"]:
                chips = []
                for i, t in enumerate(stt["order"]):
                    cls = "done" if t in stt["closed"] else ("now" if stt["phase"] == "running" and i == stt["cur"] else "off")
                    chips.append(f'<span class="ad-pill {cls}">{i + 1}. {screens.esc(S["teams"][t]["name"])}</span>')
                md('<div style="margin-top:.6rem">' + "".join(chips) + "</div>")
        with c2:
            st.caption(f"심사위원 접속 {snap['online']} / {snap['judges']}")
            md("".join(f'<span class="ad-pill {"on" if s["online"] else "off"}">{screens.esc(s["dept"])}</span>'
                       for s in snap["seats"]))
        st.divider()
        ph = stt["phase"]
        if ph == "lobby":
            st.write("심사위원들이 접속하면 발표 순서를 추첨하세요. 스크린에 추첨 장면이 나옵니다.")
            if st.button("🎲 발표 순서 추첨", type="primary", use_container_width=True, key="draw"):
                if act(core.draw_order):
                    st.rerun(scope="fragment")
        elif ph == "order":
            st.write("스크린에 추첨 결과가 나와 있습니다. 첫 팀이 준비되면 발표를 시작하세요.")
            if st.button("▶ 첫 발표 시작", type="primary", use_container_width=True, key="start"):
                if act(core.start):
                    st.rerun(scope="fragment")
            if confirm_button("순서 다시 추첨", "redraw", "지금 순서를 버리고 다시 추첨합니다."):
                if act(core.draw_order):
                    st.rerun(scope="fragment")
        elif ph == "running":
            t = snap["cur"]
            sub = snap["sub"]
            md(f'<div class="ad-big">{stt["cur"] + 1}번째 · {screens.esc(S["teams"][t]["name"])}</div>')
            st.write(f"제출 {sub['submitted']} / {sub['eligible']}"
                     + (f" · 미제출: {', '.join(sub['missing'])}" if sub["missing"] else " · 모두 제출"))
            last = stt["cur"] == len(stt["order"]) - 1
            if stt["step"] == "presenting":
                st.caption("발표 중에도 심사위원은 점수를 입력할 수 있습니다. 발표가 끝나면 아래 버튼을 누르세요.")
                if st.button("발표 종료 · 평가 요청", type="primary", use_container_width=True, key="req"):
                    if act(core.request_scoring):
                        st.rerun(scope="fragment")
            else:
                label = "평가 마감 · 결과 집계로" if last else "평가 마감 · 다음 발표로"
                if sub["missing"]:
                    if confirm_button(label, f"close_{t}", f"아직 제출하지 않은 분이 있습니다: {', '.join(sub['missing'])}. "
                                                         "그래도 마감할까요? (마감 후에는 '대리 입력'으로만 넣을 수 있습니다)", "primary"):
                        if act(core.close_current):
                            st.rerun(scope="fragment")
                elif st.button(label, type="primary", use_container_width=True, key=f"close_ok_{t}"):
                    if act(core.close_current):
                        st.rerun(scope="fragment")
        elif ph in ("done", "reveal"):
            R = core.ranking()
            if R["top_tied"]:
                names = {t: S["teams"][t]["name"] for t in R["top_tied"]}
                st.warning(f"평균과 {core.top_label(S)} 받은 수까지 같은 팀이 있습니다. 심사위원장 결정에 따라 최우수 팀을 골라 주세요.")
                pick = st.radio("최우수 팀", R["top_tied"], format_func=lambda x: names[x], horizontal=True,
                                index=R["top_tied"].index(R["winner"]) if R["winner"] in R["top_tied"] else None,
                                key="tie_pick")
                if pick is not None and pick != R["winner"]:
                    core.set_winner_override(pick)
                    st.rerun(scope="fragment")
            if ph == "done":
                st.write("모든 평가가 마감되었습니다. 준비되면 스크린에 최우수 팀을 발표하세요. (스크린에는 최우수 팀만 나옵니다)")
                if st.button("🏆 최우수 발표", type="primary", use_container_width=True, key="reveal",
                             disabled=R["winner"] is None):
                    if act(core.reveal):
                        st.rerun(scope="fragment")
            else:
                st.success(f"발표 완료 · 최우수: {S['teams'][R['winner']]['name']}" if R["winner"] is not None else "발표 완료")
                if st.button("발표 장면 다시 재생", use_container_width=True, key="replay"):
                    if act(core.reveal):
                        st.rerun(scope="fragment")
        if ph == "running" and S.get("rehearsal"):
            st.write("")
            if st.button("🧪 남은 심사위원 점수 자동 채우기 (리허설용)", use_container_width=True, key=f"autofill_{snap['cur']}"):
                k = autofill(S, snap["cur"])
                st.toast(f"{k}명 점수를 자동으로 채웠습니다")
                st.rerun(scope="fragment")
        if ph != "lobby":
            st.write("")
            if confirm_button("◀ 한 단계 되돌리기", "back", "직전 단계로 돌아갑니다. 마감한 팀은 다시 입력할 수 있게 열립니다."):
                if act(core.back):
                    st.rerun(scope="fragment")

    live()
    url = base_url()
    if url:
        st.link_button("스크린 화면 열기 (새 창 → 프로젝터로)", f"{url}/?view=screen", use_container_width=True)


def results_panel():
    st.caption("기획팀 확인용입니다. 스크린과 심사위원 화면에는 최우수 팀만 나옵니다. 심사위원별 점수는 어디에도 표시하지 않습니다.")
    S = core.get_settings()
    st.button("새로고침", key="res_refresh")
    R = core.ranking()
    if not any(r["n"] for r in R["rows"]):
        st.info("아직 입력된 점수가 없습니다.")
        return
    df = pd.DataFrame([{
        "순위": r["rank"], "팀": r["name"], "소속": r["dept"], "발표 순서": r["order_no"],
        "평가 인원": f'{r["n"]} / {r["eligible"]}',
        "평균": r["score"], f"{core.top_label(S)} 받은 수": r["top_count"],
        "수상": ("최우수" if r["team"] == R["winner"] else "우수") if r["score"] is not None else "",
    } for r in R["rows"]])
    st.dataframe(df, hide_index=True, use_container_width=True)
    if R["top_tied"]:
        st.warning("1위 동점이 있습니다. [진행] 탭에서 최우수 팀을 정해 주세요.")
    st.download_button("결과 엑셀 내려받기 (익명)", core.export_excel(),
                       file_name=f"정보분석경진대회_심사결과_{time.strftime('%Y%m%d_%H%M')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
    st.caption(f"집계: 팀별 평균 → 같으면 {core.top_label(S)}을 더 많이 받은 팀 → 그래도 같으면 심사위원장 결정")


def proxy_panel():
    st.caption("휴대폰 입력이 어려운 분의 종이 심의표를 대신 입력할 때 씁니다. 마감된 팀도 입력할 수 있습니다.")
    S = core.get_settings()
    seats = core.seats()
    j = st.selectbox("심사위원", [s["idx"] for s in seats], format_func=lambda i: who(seats[i]["dept"]), key="px_j")
    teams = [t for t in range(len(S["teams"])) if core.eligible(S, j, t)]
    t = st.selectbox("팀", teams, format_func=lambda x: S["teams"][x]["name"], key="px_t")
    if t is None:
        return
    tok = seats[j]["token"]
    mine = core.my_score(tok, t)
    if mine:
        st.info(f"이미 입력된 점수: {core.fmt(mine['total'])}점" + (" (대리 입력)" if mine["proxy"] else ""))
    vals = []
    cols = st.columns(len(S["criteria"]))
    for k, (c, col) in enumerate(zip(S["criteria"], cols)):
        with col:
            v = st.number_input(f'{c["name"]} ({core.fmt(c["max"])})', min_value=0.0, max_value=float(c["max"]),
                                step=1.0, value=(float(mine["vals"][k]) if mine else None), key=f"px_{j}_{t}_{k}")
            vals.append(v)
    c1, c2 = st.columns(2)
    if c1.button("대리 입력 저장", type="primary", use_container_width=True, key="px_save"):
        if any(v is None for v in vals):
            st.error("모든 항목을 입력해 주세요.")
        else:
            try:
                tot = core.submit(tok, t, vals, proxy=True)
                st.success(f"저장했습니다 ({core.fmt(tot)}점)")
            except core.FlowError as e:
                st.error(str(e))
    if mine and c2.button("이 점수 삭제", use_container_width=True, key="px_del"):
        core.delete_score(tok, t)
        st.rerun()


def qr_cards_html(url: str, S: dict) -> str:
    """인쇄용 개인 QR 카드(A4 한 장에 2장, 흰 바탕). 브라우저에서 열어 Ctrl+P로 인쇄합니다."""
    import segno
    cards = []
    for s_ in core.seats():
        link = f"{url}/?j={s_['token']}"
        qr = segno.make(link, error="m").svg_data_uri(scale=8, border=2, dark="#000000", light="#ffffff")
        name = screens.esc(who(s_["dept"]))
        cards.append(f'''<section class="card">
<div class="ev">{screens.esc(S["title_top"])} {screens.esc(S["title_main"])} · 심사위원 전용</div>
<div class="nm">{name}</div>
<img class="qr" src="{qr}" alt="QR">
<ol><li>휴대폰 <b>카메라</b>를 켜고 QR 코드를 비춥니다.</li>
<li>화면에 뜨는 <b>주소(링크)</b>를 누릅니다.</li>
<li>발표가 시작되면 <b>평가 화면이 자동으로</b> 나타납니다.</li></ol>
<div class="ft">이 QR은 <b>{name}</b> 전용입니다. 다른 분과 바꿔 쓰지 마세요.</div>
</section>''')
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>심사위원 개인 QR 카드</title>
<style>
@page{{size:A4;margin:12mm}}
body{{margin:0;font-family:"Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",sans-serif;color:#111;background:#fff}}
.tip{{padding:10px 14px;margin:0 0 10px;background:#eef3ff;border:1px solid #c9d6f5;border-radius:8px;font-size:14px}}
@media print{{.tip{{display:none}}}}
.card{{height:128mm;box-sizing:border-box;border:1.5px dashed #9aa4b8;border-radius:6mm;padding:9mm 12mm;margin:0 0 8mm;
display:grid;grid-template-columns:1fr 62mm;grid-template-rows:auto auto 1fr auto;column-gap:10mm;break-inside:avoid;page-break-inside:avoid}}
.card:nth-of-type(2n){{break-after:page;page-break-after:always}}
.ev{{grid-column:1/3;font-size:13pt;color:#3b4a6b;font-weight:700}}
.nm{{grid-column:1/2;font-size:30pt;font-weight:800;margin-top:6mm;letter-spacing:-.5px}}
.qr{{grid-column:2/3;grid-row:2/4;width:62mm;height:62mm;align-self:center}}
ol{{grid-column:1/2;margin:6mm 0 0;padding-left:6mm;font-size:14pt;line-height:1.75;word-break:keep-all}}
.ft{{grid-column:1/3;font-size:11.5pt;color:#555;border-top:1px solid #dde3ee;padding-top:3mm;margin-top:4mm}}
</style></head><body>
<div class="tip">이 파일을 연 상태에서 <b>Ctrl + P</b>를 눌러 인쇄하세요. 한 장에 두 분씩 나오고, 점선을 따라 자르면 됩니다. (이 안내 문구는 인쇄되지 않습니다)</div>
{"".join(cards)}
</body></html>'''


def links_panel():
    url = base_url()
    S = core.get_settings()
    if not url:
        st.warning("접속 주소를 [설정] 탭에서 입력해 주세요.")
        return
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**심사위원 공통 주소** — 개인 QR을 잃어버린 분은 이 QR로 들어와 관실을 고르고 확인 코드를 입력하면 됩니다")
        st.code(f"{url}/", language=None)
        uri = screens.qr_data_uri(f"{url}/")
        if uri:
            md(f'<img src="{uri}" style="width:220px;border-radius:12px;background:#fff;padding:8px">')
    with c2:
        st.markdown("**스크린(프로젝터) 주소**")
        st.code(f"{url}/?view=screen", language=None)
        st.markdown("**관리 화면 주소**")
        st.code(f"{url}/?view=admin", language=None)
    st.divider()
    code = judge_code()
    st.markdown(f"**심사위원 확인 코드:** `{code}` — 심사 자료에만 적어 두세요." if code else
                "**심사위원 확인 코드:** 없음 ([설정] 탭에서 정해 주세요)")
    st.markdown("**개인별 QR** — 관실 선택과 코드 입력 없이 바로 들어가는 QR입니다. "
                "해당 심사위원 자리에만 두세요. 다른 사람이 찍으면 그분 자리로 들어가니 공개하면 안 됩니다.")
    st.download_button("🖨 인쇄용 개인 QR 카드 내려받기 (흰 바탕 · A4 한 장에 2명)",
                       qr_cards_html(url, S).encode("utf-8"), file_name="심사위원_개인QR카드.html", mime="text/html",
                       use_container_width=True, type="primary")
    st.caption("받은 파일을 열고 Ctrl+P로 인쇄하세요. ⚠️ 인쇄한 뒤에는 [데이터] 탭의 '심사위원 접속 정보 새로 발급'을 누르지 마세요. "
               "카드의 QR이 모두 바뀝니다. 서버가 다시 켜졌을 때도 백업으로 되살리면 카드 QR이 그대로 다시 작동합니다.")
    cols = st.columns(3)
    for i, s in enumerate(core.seats()):
        with cols[i % 3]:
            u = screens.qr_data_uri(f"{url}/?j={s['token']}")
            md(f'<div style="text-align:center;padding:12px;margin-bottom:12px;border:1px solid rgba(255,255,255,.12);'
               f'border-radius:14px"><img src="{u}" style="width:150px;background:#fff;border-radius:8px;padding:6px">'
               f'<div style="margin-top:6px;font-weight:700">{screens.esc(who(s["dept"]))}</div>'
               f'<div style="font-size:.8rem;color:#8ea3cf">{screens.esc(S["title_main"])} 심사</div></div>')
            with st.expander("링크 주소 보기"):
                st.code(f"{url}/?j={s['token']}", language=None)


def settings_panel():
    S = core.get_settings()
    st.caption("팀·심사위원·평가 항목을 바꿀 수 있습니다. 점수가 입력된 뒤 팀 수, 심사위원 수, 배점을 바꾸면 점수가 초기화됩니다.")
    with st.form("settings"):
        c1, c2 = st.columns(2)
        title_top = c1.text_input("제목 윗줄", S["title_top"])
        title_main = c2.text_input("제목", S["title_main"])
        date_line = st.text_input("일시·장소", S["date_line"])
        public_url = st.text_input("접속 주소 (예: https://○○○.streamlit.app)", S["public_url"],
                                   help="비워 두면 지금 브라우저 주소를 씁니다. QR에 들어가는 주소입니다.")
        st.markdown("**발표팀**")
        teams = st.data_editor(pd.DataFrame(S["teams"]).rename(columns={"name": "팀명", "dept": "소속 관실", "topic": "정보분석명"}),
                               num_rows="dynamic", hide_index=True, use_container_width=True, key="ed_teams")
        st.markdown("**심사위원** (소속 관실이 발표팀의 소속 관실과 같으면 그 팀은 자동으로 평가 제외)")
        judges = st.data_editor(pd.DataFrame(S["judges"]).rename(columns={"dept": "소속 관실"}),
                                num_rows="dynamic", hide_index=True, use_container_width=True, key="ed_judges")
        st.markdown("**평가 항목**")
        crit = st.data_editor(pd.DataFrame(S["criteria"]).rename(columns={"name": "항목", "max": "배점"}),
                              num_rows="dynamic", hide_index=True, use_container_width=True, key="ed_crit")
        c3, c4 = st.columns(2)
        mode = c3.radio("입력 방식", ["grade", "number"], index=0 if S["input_mode"] == "grade" else 1,
                        format_func=lambda m: "등급 버튼 (매우우수~매우미흡)" if m == "grade" else "점수 직접 입력", horizontal=True)
        grades = c4.text_input("등급 (이름:비율, 쉼표로 구분)",
                               ", ".join(f"{l}:{r:g}" for l, r in zip(S["grade_labels"], S["grade_ratio"])))
        guide_note = st.text_input("심사위원 화면 안내 문구", S["guide_note"])
        guide_txt = st.text_area(
            "평가기준 (한 줄에 한 지표: 지표명 | 배점 | 내용1 / 내용2 / …)",
            "\n".join(f'{g["name"]} | {g["weight"]} | ' + " / ".join(g["items"]) for g in S["guide"]),
            height=130, help="심사위원 휴대폰의 '평가기준 보기'에 그대로 나옵니다. 점수 계산에는 쓰이지 않습니다.")
        runners = st.checkbox("최우수 발표 화면에 우수상 팀도 함께 표시", S["show_runner_ups"])
        rehearsal = st.checkbox("🧪 리허설 모드 (진행 탭에 '남은 심사위원 점수 자동 채우기' 버튼 표시)",
                                bool(S.get("rehearsal", False)),
                                help="휴대폰 9대 없이 혼자 시험할 때 씁니다. 행사 당일에는 반드시 끄세요.")
        c5, c6 = st.columns(2)
        pin = c5.text_input("관리자 PIN", S["admin_pin"],
                            help="Streamlit Secrets에 admin_pin을 넣으면 그 값이 우선합니다.")
        jcode = c6.text_input("심사위원 확인 코드 (숫자 4자리 권장)", S["judge_code"],
                              help="관실을 고를 때 입력하는 코드입니다. 심사 자료에만 적어 두세요. "
                                   "Secrets에 judge_code를 넣으면 그 값이 우선합니다.")
        reset_ok = st.checkbox("구조가 바뀌어 초기화가 필요하면 점수·진행을 초기화하고 저장")
        saved = st.form_submit_button("설정 저장", type="primary")
    if saved:
        try:
            labels, ratios = [], []
            for part in grades.split(","):
                if ":" in part:
                    a, b = part.split(":", 1)
                    labels.append(a.strip())
                    ratios.append(float(b))
            guide = []
            for line in guide_txt.splitlines():
                parts = [x.strip() for x in line.split("|")]
                if parts and parts[0]:
                    guide.append({"name": parts[0], "weight": parts[1] if len(parts) > 1 else "",
                                  "items": [x.strip() for x in (parts[2] if len(parts) > 2 else "").split("/") if x.strip()]})
            new = dict(S, guide=guide, guide_note=guide_note, title_top=title_top, title_main=title_main, date_line=date_line, public_url=public_url,
                       input_mode=mode, trim_high_low=False, show_runner_ups=runners, rehearsal=rehearsal, admin_pin=pin, judge_code=jcode,
                       grade_labels=labels or S["grade_labels"], grade_ratio=ratios or S["grade_ratio"],
                       teams=[{"name": r.get("팀명", ""), "dept": r.get("소속 관실", ""), "topic": r.get("정보분석명", "")}
                              for r in teams.fillna("").to_dict("records") if str(r.get("팀명", "")).strip()],
                       judges=[{"dept": r.get("소속 관실", "")} for r in judges.fillna("").to_dict("records")
                               if str(r.get("소속 관실", "")).strip()],
                       criteria=[{"name": r.get("항목", ""), "max": r.get("배점", 0)}
                                 for r in crit.fillna("").to_dict("records") if str(r.get("항목", "")).strip()])
            core.save_settings(new, reset_if_needed=reset_ok)
            st.success("저장했습니다.")
            time.sleep(.6)
            st.rerun()
        except (core.FlowError, ValueError) as e:
            st.error(str(e))


def data_panel():
    st.markdown("**백업** — 행사 중간중간 내려받아 두면, 서버가 재시작되어도 그대로 되살릴 수 있습니다.")
    st.download_button("현재 상태 백업 파일 내려받기", core.backup(),
                       file_name=f"심사_백업_{time.strftime('%H%M%S')}.json", mime="application/json",
                       use_container_width=True)
    up = st.file_uploader("백업 파일로 되살리기", type=["json"], key="restore")
    if up is not None and st.button("이 백업으로 되살리기", type="primary", key="do_restore"):
        try:
            core.restore(up.getvalue())
            st.success("되살렸습니다.")
        except Exception as e:
            st.error(f"되살리지 못했습니다: {e}")
    st.divider()
    st.markdown("**초기화** — 리허설이 끝나면 '점수·진행 초기화'를 눌러 주세요.")
    if confirm_button("점수·진행 초기화 (설정·접속 유지)", "rp", "입력된 점수와 진행 상황을 모두 지웁니다."):
        core.reset_progress()
        st.rerun()
    if confirm_button("심사위원 접속 정보 새로 발급", "rs", "모든 심사위원이 QR로 다시 접속해야 합니다. 개인 QR도 바뀝니다."):
        core.reset_seats()
        st.rerun()
    if confirm_button("전체 초기화 (settings.json 기준)", "fr", "설정·점수·접속 정보를 모두 처음 상태로 되돌립니다."):
        core.factory_reset()
        st.rerun()
    st.divider()
    st.markdown("**심사위원 접속 해제** — 엉뚱한 관실을 선택했을 때")
    for s in core.seats():
        c1, c2 = st.columns([3, 1])
        c1.write(f'{who(s["dept"])} — {"접속 중" if s["online"] else ("접속했었음" if s["claimed"] else "미접속")}')
        if s["claimed"] and c2.button("해제", key=f"rel_{s['idx']}"):
            core.release_seat(s["idx"])
            st.rerun()


# ───────────────────────── 라우팅
md(BASE_CSS)
view = st.query_params.get("view", "")
if view == "screen":
    screen_view()
elif view == "admin":
    admin_view()
else:
    judge_view()
