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

    // 피아노: 음마다 한 번만 소리(배음+두 번째 현+해머 소리)를 계산해 저장해 두고, 칠 때는 그대로 재생합니다(가볍게 돌아가도록).
    var PB = {};
    function pianoBuf(m) {
      if (PB[m]) return PB[m];
      var sr = ctx.sampleRate, f = mtof(m), life = Math.max(1.1, 4.6 - (m - 40) * 0.075);
      var len = Math.floor(sr * (life + 0.2)), buf = ctx.createBuffer(1, len, sr), d = buf.getChannelData(0);
      var bright = Math.max(0.45, 1 - (m - 60) * 0.014), T1 = life / 4.2;
      var amps = m < 64 ? [1, 0.5, 0.3, 0.17, 0.1] : [1, 0.5, 0.28, 0.15];
      var parts = [];
      for (var n = 1; n <= amps.length; n++) {
        var fn = f * n * Math.sqrt(1 + 0.00035 * n * n);
        if (fn > 7000) break;
        parts.push({ w: 2 * Math.PI * fn / sr, a: amps[n - 1] * (n > 1 ? bright : 1), k: Math.exp(-1 / (sr * T1 / (1 + 0.7 * (n - 1)))), e: 1 });
      }
      parts.push({ w: 2 * Math.PI * f * Math.pow(2, 4 / 1200) / sr, a: 0.22, k: Math.exp(-1 / (sr * T1)), e: 1 });   // 두 번째 현(살짝 어긋난 음)
      var env = 1, kEnv = Math.exp(-1 / (sr * T1)), att = Math.floor(sr * 0.005), hz = Math.floor(sr * 0.03), hy = 0, peak = 0;
      var hc = Math.min(0.95, 2 * Math.PI * Math.min(6000, f * 3) / sr);
      for (var i = 0; i < len; i++) {
        var x = 0;
        for (var j = 0; j < parts.length; j++) { var P = parts[j]; x += P.a * (0.15 + 0.85 * P.e) * Math.sin(P.w * i); P.e *= P.k; }
        if (i < hz) { hy += ((Math.random() * 2 - 1) - hy) * hc; x += hy * 0.25 * (1 - i / hz); }   // 해머가 줄을 치는 소리
        x *= env * (i < att ? i / att : 1); env *= kEnv;
        d[i] = x; if (Math.abs(x) > peak) peak = Math.abs(x);
      }
      var fade = Math.floor(sr * 0.2);
      for (var q = 0; q < fade; q++) d[len - 1 - q] *= q / fade;
      for (var r = 0; r < len; r++) d[r] *= 0.85 / (peak || 1);
      PB[m] = { buf: buf, life: life };
      return PB[m];
    }
    S.piano = function (bus, t, m, v, end, dry) {
      var pb = pianoBuf(m), off = Math.min(end || (t + pb.life), t + pb.life);
      var src = ctx.createBufferSource(); src.buffer = pb.buf;
      var g = ctx.createGain();
      g.gain.setValueAtTime(v, t);
      g.gain.setValueAtTime(v, off);
      g.gain.linearRampToValueAtTime(0, off + 0.22);   // 페달을 뗀 것처럼 잦아듦
      src.connect(g);
      if (dry) g.connect(bus); else send(g, bus, 0.42);   // dry: 잔향은 묶어서 한 번에(가볍게)
      src.start(t); src.stop(off + 0.24);
    };
    // 현악기 배경(부드럽게 들어오고 비브라토가 있는 소리)
    S.strings = function (bus, t, notes, dur, v) {
      var lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.value = 1500; lp.Q.value = 0.3;
      var hp = ctx.createBiquadFilter(); hp.type = 'highpass'; hp.frequency.value = 120;
      var g = ctx.createGain(), a = Math.min(0.9, dur * 0.4);
      g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(v, t + a);
      g.gain.setValueAtTime(v, t + Math.max(a, dur - 0.15)); g.gain.linearRampToValueAtTime(0.0001, t + dur + 0.7);
      lp.connect(hp); hp.connect(g); send(g, bus, 0.6);
      var lfo = ctx.createOscillator(); lfo.frequency.value = 5.2; var lg = ctx.createGain(); lg.gain.value = 7; lfo.connect(lg);
      notes.forEach(function (m) {
        [-9, 0, 9].forEach(function (det) {
          var o = ctx.createOscillator(); o.type = 'sawtooth'; o.frequency.value = mtof(m); o.detune.value = det;
          lg.connect(o.detune);
          var og = ctx.createGain(); og.gain.value = 1 / (notes.length * 3);
          o.connect(og); og.connect(lp); o.start(t); o.stop(t + dur + 0.8);
        });
      });
      lfo.start(t); lfo.stop(t + dur + 0.8);
    };

    // 대기 음악: 경쾌한 피아노 왈츠(창작곡, D장조 3/4박자 152bpm). A-A'-B(단조 색채)-A 32마디,
    // 두 번째 반복에는 글로켄슈필(회전목마 같은 반짝임)과 현악기를 더함 → 약 76초마다 반복
    var CH = {   // 왼손: 베이스, '짝짝' 화음
      D: [38, [57, 62, 66]], Ac: [37, [57, 61, 64]], Bm: [47, [59, 62, 66]], Fm: [42, [57, 61, 66]],
      G: [43, [59, 62, 67]], Df: [42, [57, 62, 66]], Em7: [40, [59, 62, 67]], A7: [45, [55, 61, 64]],
      D7f: [42, [57, 60, 66]], F7: [42, [58, 61, 64]], D7: [38, [57, 60, 66]], Em: [40, [59, 64, 67]]
    };
    var A1 = [
      ['D', [[0, 78, 1], [1, 76, 0.5], [1.5, 78, 0.5], [2, 81, 1]]],
      ['Ac', [[0, 79, 1.5], [1.5, 78, 0.5], [2, 76, 1]]],
      ['Bm', [[0, 74, 1], [1, 73, 0.5], [1.5, 74, 0.5], [2, 78, 1]]],
      ['Fm', [[0, 76, 2], [2, 73, 1]]],
      ['G', [[0, 74, 0.5], [0.5, 76, 0.5], [1, 78, 1], [2, 79, 1]]],
      ['Df', [[0, 81, 1], [1, 78, 1], [2, 74, 1]]],
      ['Em7', [[0, 76, 0.5], [0.5, 78, 0.5], [1, 79, 1], [2, 83, 1]]],
      ['A7', [[0, 81, 1.5], [1.5, 79, 0.5], [2, 76, 1]]]
    ];
    var A2 = A1.slice(0, 3).concat([
      ['D7f', [[0, 78, 1], [1, 76, 1], [2, 72, 1]]],
      ['G', [[0, 71, 1], [1, 74, 1], [2, 79, 1]]],
      ['A7', [[0, 79, 0.5], [0.5, 78, 0.5], [1, 76, 1], [2, 73, 1]]],
      ['D', [[0, 74, 2]]],
      ['D', [[1, 69, 0.5], [1.5, 71, 0.5], [2, 73, 0.5], [2.5, 76, 0.5]]]
    ]);
    var B1 = [
      ['Bm', [[0, 78, 1.5], [1.5, 76, 0.5], [2, 74, 1]]],
      ['F7', [[0, 76, 1], [1, 73, 1], [2, 70, 1]]],
      ['Bm', [[0, 71, 0.5], [0.5, 73, 0.5], [1, 74, 1], [2, 78, 1]]],
      ['D7', [[0, 81, 1.5], [1.5, 79, 0.5], [2, 78, 1]]],
      ['G', [[0, 79, 1], [1, 83, 1], [2, 86, 1]]],
      ['Df', [[0, 81, 1.5], [1.5, 78, 0.5], [2, 74, 1]]],
      ['Em', [[0, 79, 0.5], [0.5, 78, 0.5], [1, 76, 1], [2, 71, 1]]],
      ['A7', [[0, 73, 1], [1, 76, 1], [2, 79, 1]]]
    ];
    var TUNE = A1.concat(A2, B1, A1);
    var DYN = [];
    for (var q = 0; q < 32; q++) DYN.push(q < 16 ? 0.95 : q < 24 ? 1.06 : 1.0);
    S.waltzBar = 3 * 60 / 152;
    S.waltz = function (bus, t, i) {            // 한 마디
      var beat = S.waltzBar / 3, n = i % 32, row = TUNE[n], ch = CH[row[0]], pass = Math.floor(i / 32) % 2, d = DYN[n];
      function hum() { return (Math.random() - 0.5) * 0.012; }
      function panned(x) {                       // 왼손은 살짝 왼쪽, 오른손은 살짝 오른쪽
        var p = ctx.createStereoPanner ? ctx.createStereoPanner() : ctx.createGain();
        if (p.pan) p.pan.value = x;
        send(p, bus, 0.42);
        setTimeout(function () { try { p.disconnect(); } catch (e) {} }, (t - ctx.currentTime + S.waltzBar + 6) * 1000);
        return p;
      }
      var L = panned(-0.2), R = panned(0.16);
      // 쿵(베이스) - 짝 - 짝 : 둘째 박을 살짝 당겨 왈츠 특유의 출렁임
      S.piano(L, t, ch[0], 0.13 * d, t + beat * 1.1, 1);
      if (pass === 1) S.piano(L, t + 0.004, ch[0] + 12, 0.055 * d, t + beat * 1.1, 1);
      [0.94, 2].forEach(function (bt) {
        var at = t + bt * beat + hum();
        ch[1].forEach(function (m, k) { S.piano(L, at + k * 0.004, m, 0.05 * d * (bt === 2 ? 0.9 : 1), at + beat * 0.5, 1); });
      });
      row[1].forEach(function (x) {
        var nt = t + x[0] * beat + hum(), len = x[2] * beat;
        S.piano(R, nt, x[1], 0.19 * d * (0.94 + Math.random() * 0.12), nt + len * 0.95 + 0.12, 1);
        if (pass === 1) S.bell(R, nt, x[1] + 12, 0.038 * d, 0.9);   // 회전목마 같은 반짝임
      });
      if (pass === 1) S.strings(bus, t, [ch[1][0], ch[1][2]], S.waltzBar, 0.04 * d);
    };

    // 화면을 클릭해 소리가 켜지면, 왈츠에 쓰는 피아노 음을 조금씩 미리 만들어 둠(첫 마디가 밀리지 않게)
    S.warm = function () {
      var want = {};
      Object.keys(CH).forEach(function (k) { want[CH[k][0]] = want[CH[k][0] + 12] = 1; CH[k][1].forEach(function (m) { want[m] = 1; }); });
      TUNE.forEach(function (r) { r[1].forEach(function (x) { want[x[1]] = 1; }); });
      var list = Object.keys(want).map(Number);
      (function step() { var m = list.shift(); if (m == null) return; pianoBuf(m); setTimeout(step, 25); })();
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
    try { K.syn.warm(); } catch (e) {}
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
  // 첫 대기 화면: 경쾌한 피아노 왈츠 / 추첨 직후·축하 뒤: 기존의 잔잔한 배경음
  function lobbyMusic() { return loop(K.syn.waltz, K.syn.waltzBar, 0.9, { fadeIn: 2.5 }); }
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
      case 'lobby': stopAll(1.2); lobbyMusic(); break;
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
  // 창 제목에 지금 상태를 적어 둠 → 이 PC의 '발표화면 자동 전환' 도우미가 보고 발표자료를 띄우거나 내림
  function winTitle() {
    var el = document.querySelector('.kx-win');
    if (!el) return;
    var v = el.getAttribute('title') || 'S|', p = v.indexOf('P|') === 0;
    var want = '[KX:' + (p ? 'P:' + v.slice(2) : 'S:') + ':] ' + (p ? v.slice(2) + ' 발표 중' : '스크린');
    // Streamlit Cloud는 앱을 바깥 틀(Manage app 버튼이 있는 페이지) 안에 넣어 보여 주므로, 바깥 창 제목까지 바꿈
    var w = window;
    for (var n = 0; n < 4 && w; n++) {
      try { if (w.document.title !== want) w.document.title = want; } catch (e) { break; }
      if (w === w.parent) break;
      w = w.parent;
    }
  }
  try { new MutationObserver(winTitle).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['title'] }); } catch (e) {}
  // 자동 재생이 허용된 창(도우미가 연 스크린 창)이면 클릭 없이 소리를 켬
  var triedAuto = false;
  function autoUnlock() {
    if (triedAuto || K.unlocked) return;
    triedAuto = true;
    if (!ensure()) return;
    try { K.ctx.resume(); } catch (e) {}
    setTimeout(function () { if (K.ctx && K.ctx.state === 'running' && !K.unlocked) { K.unlocked = true; K.cur.key = ''; K.last = null; pill(''); } }, 300);
  }
  function tick() {
    winTitle();
    var m = parse();
    if (!m) return;
    autoUnlock();
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
