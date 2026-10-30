"""스크린 효과음·배경음악.

음원 파일 없이 브라우저(Web Audio)에서 직접 소리를 만들어 저작권 걱정이 없습니다.
스크린 화면에 숨겨 둔 표시(.kx-sc)를 읽어서 장면이 바뀔 때마다 알맞은 소리를 냅니다.
브라우저 정책상 스크린 화면을 한 번 클릭해야 소리가 켜집니다.
"""
from __future__ import annotations

import json

ENGINE_JS = r"""
(function () {
  'use strict';
  var W = window;
  if (W.__kxSound) return;
  var K = W.__kxSound = { ctx: null, master: null, fx: null, syn: null, unlocked: false, muted: false,
                          snd: false, vol: 0.7, lastVol: -1, last: null, cur: { key: '', loops: [], timers: [] } };

  function mtof(m) { return 440 * Math.pow(2, (m - 69) / 12); }

  // ───────────── 악기 (시각 t에 소리를 예약하는 함수들)
  function Synth(ctx, out) {
    var S = {}, nb = null;
    function noise() {
      if (nb) return nb;
      nb = ctx.createBuffer(1, Math.floor(ctx.sampleRate * 2), ctx.sampleRate);
      var d = nb.getChannelData(0);
      for (var i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      return nb;
    }
    var rv = ctx.createConvolver();
    (function () {
      var len = Math.floor(ctx.sampleRate * 2.4), b = ctx.createBuffer(2, len, ctx.sampleRate);
      for (var c = 0; c < 2; c++) {
        var d = b.getChannelData(c), y = 0;
        for (var i = 0; i < len; i++) { var x = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.6); y += (x - y) * 0.45; d[i] = y; }
      }
      rv.buffer = b;
    })();
    var rvIn = ctx.createGain(); rvIn.gain.value = 0.9; rvIn.connect(rv); rv.connect(out);
    function send(node, bus, wet) {
      node.connect(bus);
      if (wet) { var g = ctx.createGain(); g.gain.value = wet; node.connect(g); g.connect(rvIn); }
    }
    function envExp(g, t, peak, attack, decay) {
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0002), t + attack);
      g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
    }
    S.snare = function (bus, t, v) {
      var s = ctx.createBufferSource(); s.buffer = noise();
      var bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1900; bp.Q.value = 0.6;
      var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 650;
      var g = ctx.createGain(); envExp(g, t, v, 0.003, 0.11);
      s.connect(bp); bp.connect(hp); hp.connect(g); send(g, bus, 0.22);
      s.start(t, Math.random() * 1.6); s.stop(t + 0.15);
    };
    S.kick = function (bus, t, v) {
      var o = ctx.createOscillator(); o.frequency.setValueAtTime(130, t); o.frequency.exponentialRampToValueAtTime(42, t + 0.16);
      var g = ctx.createGain(); envExp(g, t, v, 0.004, 0.42);
      o.connect(g); send(g, bus, 0.04); o.start(t); o.stop(t + 0.5);
    };
    S.tom = function (bus, t, v, f) {
      var o = ctx.createOscillator(); o.frequency.setValueAtTime(f * 1.25, t); o.frequency.exponentialRampToValueAtTime(f, t + 0.08);
      var g = ctx.createGain(); envExp(g, t, v, 0.004, 0.32);
      o.connect(g); send(g, bus, 0.15); o.start(t); o.stop(t + 0.4);
    };
    S.crash = function (bus, t, v, dur) {
      dur = dur || 2.2;
      var s = ctx.createBufferSource(); s.buffer = noise(); s.loop = true;
      var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 3200;
      var pk = ctx.createBiquadFilter(); pk.type = 'peaking'; pk.frequency.value = 7000; pk.gain.value = 6;
      var g = ctx.createGain(); envExp(g, t, v, 0.005, dur);
      s.connect(hp); hp.connect(pk); pk.connect(g); send(g, bus, 0.35); s.start(t); s.stop(t + dur + 0.1);
    };
    S.hat = function (bus, t, v) {
      var s = ctx.createBufferSource(); s.buffer = noise();
      var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 8000;
      var g = ctx.createGain(); envExp(g, t, v, 0.002, 0.045);
      s.connect(hp); hp.connect(g); send(g, bus, 0); s.start(t, Math.random()); s.stop(t + 0.07);
    };
    S.clap = function (bus, t, v) {
      [0, 0.011, 0.023].forEach(function (d, i) {
        var s = ctx.createBufferSource(); s.buffer = noise();
        var bp = ctx.createBiquadFilter(); bp.type = 'bandpass'; bp.frequency.value = 1400; bp.Q.value = 0.9;
        var g = ctx.createGain(); envExp(g, t + d, v * (i === 2 ? 1 : 0.7), 0.002, i === 2 ? 0.14 : 0.02);
        s.connect(bp); bp.connect(g); send(g, bus, 0.2); s.start(t + d, Math.random()); s.stop(t + d + 0.2);
      });
    };
    S.tick = function (bus, t, v, f) {
      var o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = f || 2200;
      var g = ctx.createGain(); envExp(g, t, v, 0.001, 0.035);
      o.connect(g); send(g, bus, 0.1); o.start(t); o.stop(t + 0.06);
    };
    S.bell = function (bus, t, m, v, dur) {
      dur = dur || 2.4; var f = mtof(m);
      [[1, 1], [2.756, 0.35], [5.404, 0.12]].forEach(function (p) {
        var o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = f * p[0];
        var g = ctx.createGain(); envExp(g, t, v * p[1], 0.006, p[0] > 2 ? dur / 2 : dur);
        o.connect(g); send(g, bus, 0.5); o.start(t); o.stop(t + dur + 0.1);
      });
    };
    S.pluck = function (bus, t, m, v) {
      var f = mtof(m);
      [[1, 1, 0.5], [4, 0.22, 0.1]].forEach(function (p) {
        var o = ctx.createOscillator(); o.type = 'sine'; o.frequency.value = f * p[0];
        var g = ctx.createGain(); envExp(g, t, v * p[1], 0.004, p[2]);
        o.connect(g); send(g, bus, 0.3); o.start(t); o.stop(t + p[2] + 0.06);
      });
    };
    S.pad = function (bus, t, notes, dur, v, cutoff) {
      var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = cutoff || 1100; lp.Q.value = 0.5;
      var g = ctx.createGain(), a = Math.min(1.2, dur * 0.35);
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(v, t + a);
      g.gain.setValueAtTime(v, t + Math.max(a, dur - 0.2)); g.gain.linearRampToValueAtTime(0.0001, t + dur + 1.2);
      lp.connect(g); send(g, bus, 0.45);
      notes.forEach(function (m, i) {
        [-7, 7].forEach(function (det) {
          var o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = mtof(m); o.detune.value = det + (i % 2 ? 2 : -2);
          var og = ctx.createGain(); og.gain.value = 1 / (notes.length * 2);
          o.connect(og); og.connect(lp); o.start(t); o.stop(t + dur + 1.3);
        });
      });
    };
    S.brass = function (bus, t, notes, dur, v) {
      var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 1.2;
      lp.frequency.setValueAtTime(500, t); lp.frequency.exponentialRampToValueAtTime(3200, t + 0.07);
      lp.frequency.exponentialRampToValueAtTime(1600, t + dur + 0.1);
      var g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.03);
      g.gain.setValueAtTime(v * 0.8, t + Math.max(0.04, dur * 0.7)); g.gain.exponentialRampToValueAtTime(0.0001, t + dur + 0.35);
      lp.connect(g); send(g, bus, 0.35);
      notes.forEach(function (m) {
        [-6, 0, 6].forEach(function (det) {
          var o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = mtof(m); o.detune.value = det;
          var og = ctx.createGain(); og.gain.value = 0.9 / (notes.length * 3);
          o.connect(og); og.connect(lp); o.start(t); o.stop(t + dur + 0.4);
        });
      });
    };

    // 장면별 음악 조각 (일정 주기마다 반복)
    var PROG = [[50, 54, 57, 61, 64], [47, 50, 54, 57, 61], [43, 47, 50, 54, 57], [45, 49, 52, 55, 59]];
    var PENTA = [74, 76, 78, 81, 83, 86, 88];
    S.ambient = function (bus, t, i) {          // 4초
      var ch = PROG[i % 4];
      S.pad(bus, t, ch, 4.0, 0.22, 1000);
      S.pad(bus, t, [ch[0] - 12], 4.0, 0.12, 300);
      for (var k = 0; k < 1 + (i % 2); k++) S.bell(bus, t + 0.6 + k * 1.7, PENTA[(i * 3 + k * 2) % PENTA.length], 0.05, 3);
    };
    S.roll = function (bus, t, p) {            // 0.25초 (스네어 6번)
      for (var k = 0; k < 6; k++) S.snare(bus, t + k * 0.0417, (0.16 + 0.5 * p) * (0.75 + Math.random() * 0.35));
    };
    S.timp = function (bus, t, p) {            // 0.25초 (팀파니 4번)
      for (var k = 0; k < 4; k++) S.tom(bus, t + k * 0.0625, (0.1 + 0.45 * p) * (0.8 + Math.random() * 0.3), 62);
    };
    var THINK = [[69, 72, 76, 72], [67, 71, 74, 71], [65, 69, 72, 69], [67, 71, 74, 79]];
    S.thinkPeriod = 8 * 60 / 112 / 2;
    S.think = function (bus, t, i) {           // 한 마디
      var e = 60 / 112 / 2, row = THINK[i % 4];
      S.pad(bus, t, [row[0] - 24, row[0] - 12], 8 * e, 0.07, 500);
      for (var k = 0; k < 8; k++) {
        S.pluck(bus, t + k * e, row[k % 4], 0.15 * (k % 2 ? 0.7 : 1));
        if (k % 2) S.hat(bus, t + k * e, 0.035);
      }
    };
    S.tense = function (bus, t, i) {           // 2초 (심장 소리 + 낮은 긴장음)
      S.pad(bus, t, [33, 40, 45], 2.0, 0.2, 260 + 120 * Math.sin(i * 0.7));
      S.kick(bus, t, 0.35); S.kick(bus, t + 0.26, 0.22); S.kick(bus, t + 1, 0.3); S.kick(bus, t + 1.26, 0.18);
      S.tick(bus, t + 0.5, 0.05, 2400); S.tick(bus, t + 1.5, 0.05, 2000);
    };
    var CEL = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]];
    S.celebrate = function (bus, t, i) {       // 2초 (120bpm 한 마디)
      var b = 0.5, ch = CEL[i % 4];
      for (var k = 0; k < 4; k++) S.kick(bus, t + k * b, 0.5);
      S.clap(bus, t + b, 0.3); S.clap(bus, t + 3 * b, 0.3);
      for (var h = 0; h < 8; h++) S.hat(bus, t + h * b / 2, h % 2 ? 0.05 : 0.08);
      S.brass(bus, t, ch, 0.32, 0.22); S.brass(bus, t + 1.5 * b, ch, 0.22, 0.16); S.brass(bus, t + 2.5 * b, ch, 0.32, 0.18);
      S.pad(bus, t, [ch[0] - 12], 2.0, 0.12, 400);
    };
    // 한 번만 나는 효과음
    S.hit = function (bus, t, k) {
      S.kick(bus, t, 0.62); S.crash(bus, t, 0.2, 1.4); S.bell(bus, t + 0.01, PENTA[Math.min(k, PENTA.length - 1)], 0.2, 2.2);
    };
    S.finalHit = function (bus, t) {
      S.kick(bus, t, 0.7); S.crash(bus, t, 0.36, 2.6); S.brass(bus, t, [50, 57, 62, 66, 69], 1.4, 0.24);
    };
    S.chime = function (bus, t) { S.bell(bus, t, 88, 0.16, 2.4); S.bell(bus, t + 0.16, 93, 0.16, 2.8); };
    S.win = function (bus, t) {
      S.kick(bus, t, 0.7); S.crash(bus, t, 0.42, 3); S.brass(bus, t, [48, 55, 60, 64, 67], 0.5, 0.27);
      [[0.55, 67], [0.72, 72], [0.89, 76]].forEach(function (x) { S.brass(bus, t + x[0], [x[1]], 0.15, 0.24); });
      S.brass(bus, t + 1.06, [60, 64, 67, 72, 79], 1.6, 0.3); S.crash(bus, t + 1.06, 0.34, 3); S.kick(bus, t + 1.06, 0.62);
      S.bell(bus, t + 1.1, 96, 0.08, 3);
    };
    return S;
  }
  K.Synth = Synth;

  // ───────────── 재생 엔진
  function ensure() {
    if (K.ctx) return true;
    var AC = W.AudioContext || W.webkitAudioContext;
    if (!AC) return false;
    var ctx = K.ctx = new AC();
    var comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14; comp.ratio.value = 3; comp.attack.value = 0.005; comp.release.value = 0.3;
    var lim = ctx.createDynamicsCompressor();
    lim.threshold.value = -4; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.001; lim.release.value = 0.12;
    K.master = ctx.createGain(); K.master.gain.value = 0; K.master.connect(comp); comp.connect(lim); lim.connect(ctx.destination);
    K.fx = ctx.createGain(); K.fx.gain.value = 1; K.fx.connect(K.master);
    K.syn = Synth(ctx, K.master);
    return true;
  }
  function applyVol(force) {
    if (!K.ctx) return;
    var v = (K.muted || !K.snd) ? 0 : K.vol;
    if (!force && Math.abs(v - K.lastVol) < 0.001) return;
    K.lastVol = v;
    var g = K.master.gain, n = K.ctx.currentTime;
    g.cancelScheduledValues(n); g.setValueAtTime(g.value, n); g.linearRampToValueAtTime(v, n + 0.25);
  }
  function loop(seg, period, level, opts) {
    opts = opts || {};
    var ctx = K.ctx, bus = ctx.createGain(), now = ctx.currentTime;
    bus.gain.setValueAtTime(0.0001, now); bus.gain.linearRampToValueAtTime(level, now + (opts.fadeIn || 0.8));
    bus.connect(K.master);
    var start = now + 0.05, next = start, i = 0, id = null, done = false;
    function stop(f) {
      if (done) return; done = true; clearInterval(id);
      f = (f == null) ? 0.6 : f;
      var n = ctx.currentTime;
      bus.gain.cancelScheduledValues(n); bus.gain.setValueAtTime(Math.max(bus.gain.value, 0.0001), n);
      bus.gain.linearRampToValueAtTime(0.0001, n + f);
      setTimeout(function () { try { bus.disconnect(); } catch (e) {} }, (f + 3) * 1000);
    }
    id = setInterval(function () {
      while (next < ctx.currentTime + 0.4) {
        if (opts.dur && next - start >= opts.dur) { stop(1.5); return; }
        try { seg(bus, next, i, next - start); } catch (e) {}
        i++; next += period;
      }
    }, 70);
    var L = { stop: stop };
    K.cur.loops.push(L);
    return L;
  }
  function stopAll(f) {
    K.cur.loops.forEach(function (l) { l.stop(f); });
    K.cur.loops = [];
    K.cur.timers.forEach(clearTimeout);
    K.cur.timers = [];
    K.roll = K.timp = null;
  }
  function later(sec, fn) { K.cur.timers.push(setTimeout(fn, sec * 1000)); }
  function ambient(level) { return loop(K.syn.ambient, 4, level == null ? 0.9 : level, { fadeIn: 2 }); }
  function winSeq() {
    var S = K.syn;
    S.win(K.fx, K.ctx.currentTime + 0.03);
    later(1.9, function () { loop(S.celebrate, 2, 0.85, { fadeIn: 0.3, dur: 16 }); });
    later(19.5, function () { ambient(0.6); });
  }
  function enter(m) {
    var S = K.syn;
    switch (m.scene) {
      case 'lobby': stopAll(1.2); ambient(0.9); break;
      case 'order':
        stopAll(0.6);
        if (m.a >= m.b) { ambient(0.7); break; }
        K.roll = loop(function (bus, t, i, el) { S.roll(bus, t, Math.min(1, el / 10)); }, 0.25, 0.8, { fadeIn: 0.4 });
        K.timp = loop(function (bus, t, i, el) { S.timp(bus, t, Math.min(1, el / 10) * 0.6); }, 0.25, 0.6, { fadeIn: 0.8 });
        break;
      case 'present': stopAll(1.5); break;
      case 'scoring': stopAll(0.8); loop(S.think, S.thinkPeriod, 0.9, { fadeIn: 1.2 }); break;
      case 'done': stopAll(0.8); loop(S.tense, 2, 0.9, { fadeIn: 1.5 }); break;
      case 'reveal':
        stopAll(0.4);
        if (m.a === 'sus') {
          K.roll = loop(function (bus, t, i, el) { S.roll(bus, t, Math.min(1, 0.25 + el / 3.6)); }, 0.25, 1, { fadeIn: 0.2 });
          K.timp = loop(function (bus, t, i, el) { S.timp(bus, t, Math.min(1, 0.2 + el / 3.6)); }, 0.25, 0.8, { fadeIn: 0.3 });
        } else if (m.e < 25) { winSeq(); } else { ambient(0.6); }
        break;
      default: stopAll(1);
    }
  }
  function update(m, prev) {
    var S = K.syn, t = K.ctx.currentTime + 0.03;
    if (m.scene === 'order') {
      if (m.a > prev.a) for (var k = prev.a; k < m.a; k++) S.hit(K.fx, t + (k - prev.a) * 0.25, k);
      if (m.a >= m.b && prev.a < m.b) {
        if (K.roll) K.roll.stop(0.15);
        if (K.timp) K.timp.stop(0.15);
        S.finalHit(K.fx, t + 0.35);
        later(3, function () { ambient(0.7); });
      }
    } else if (m.scene === 'scoring') {
      if (m.b > 0 && m.a >= m.b && prev.a < m.b) S.chime(K.fx, t);
    } else if (m.scene === 'reveal') {
      if (prev.a === 'sus' && m.a === 'win') {
        if (K.roll) K.roll.stop(0.08);
        if (K.timp) K.timp.stop(0.08);
        winSeq();
      }
    }
  }

  // ───────────── 안내 표시 (화면 왼쪽 아래 작은 알림)
  var pillEl = null, pillTimer = null;
  function pill(text, ms) {
    if (!document.body) return;
    if (!pillEl) {
      pillEl = document.createElement('div');
      pillEl.setAttribute('style', 'position:fixed;left:24px;bottom:20px;z-index:2147483000;padding:10px 16px;' +
        'border-radius:999px;background:rgba(8,14,32,.82);border:1px solid rgba(255,255,255,.18);color:#e8eefc;' +
        'font:600 15px/1.2 "Pretendard Variable",Pretendard,"Noto Sans KR","Malgun Gothic",sans-serif;' +
        'pointer-events:none;transition:opacity .5s;opacity:0');
      document.body.appendChild(pillEl);
    }
    if (!text) { pillEl.style.opacity = '0'; return; }
    if (pillEl.textContent !== text) pillEl.textContent = text;
    pillEl.style.opacity = '1';
    clearTimeout(pillTimer);
    if (ms) pillTimer = setTimeout(function () { pillEl.style.opacity = '0'; }, ms);
  }

  function parse() {
    var el = document.querySelector('.kx-sc');
    if (!el) return null;
    var p = (el.getAttribute('title') || '').split('|');
    var a = p[2];
    return { scene: p[0], key: p[1], a: (a === 'sus' || a === 'win') ? a : (+a || 0), b: +p[3] || 0,
             e: +p[4] || 0, snd: p[5] === '1', vol: Math.max(0, Math.min(100, +p[6] || 0)) / 100 };
  }
  function tick() {
    var m = parse();
    if (!m) return;
    K.snd = m.snd; K.vol = m.vol;
    if (!m.snd) {
      if (K.ctx) { applyVol(); stopAll(0.5); }
      K.cur.key = ''; K.last = null;
      if (!K.unlocked) pill('');
      return;
    }
    if (!K.unlocked) { pill('🔈 화면을 한 번 클릭하면 효과음이 켜집니다'); return; }
    applyVol();
    var key = m.scene + '|' + m.key;
    if (key !== K.cur.key) { K.cur.key = key; enter(m); }
    else if (K.last) update(m, K.last);
    K.last = m;
  }
  function unlock() {
    if (!ensure()) return;
    try { K.ctx.resume(); } catch (e) {}
    if (!K.unlocked) {
      K.unlocked = true; K.cur.key = ''; K.last = null;
      if (K.snd) pill('🔊 효과음이 켜졌습니다 · M 키로 끄기/켜기', 3500);
    }
  }
  document.addEventListener('pointerdown', unlock, true);
  document.addEventListener('keydown', function (e) {
    var k = e.key;
    if (k === 'm' || k === 'M' || k === 'ㅡ') {
      if (!K.unlocked) { unlock(); return; }
      K.muted = !K.muted; applyVol(true);
      pill(K.muted ? '🔇 효과음 꺼짐 · M 키로 다시 켜기' : '🔊 효과음 켜짐', 2500);
    } else { unlock(); }
  }, true);
  setInterval(tick, 250);
})();
"""


def component_html() -> str:
    """스크린 화면에 넣는 보이지 않는 부품. 소리 엔진을 화면 본문(부모 문서)에 한 번만 심습니다."""
    code = json.dumps(ENGINE_JS).replace("</", "<\\/")
    return ("<script>(function(){var code=" + code + ";"
            "try{var P=window.parent;if(P&&P!==window&&P.document){"
            "if(!P.__kxSoundLoaded){P.__kxSoundLoaded=true;var s=P.document.createElement('script');"
            "s.textContent=code;P.document.head.appendChild(s);}return;}}catch(e){}"
            "})();</script>")
