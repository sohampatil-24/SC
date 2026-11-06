"""Soundtracks for the Dhanteras and Diwali Padwa videos, synced to <kind>.schedule.json.

usage: python3 festival_audio.py dhanteras|padwa
  dhanteras: santoor melody in raag Durga, tanpura, dholki, brass bells, coin clinks, gold fireworks
  padwa:     shehnai melody in raag Bhairav (a morning raag), tanpura, birdsong, page turn, bells, fireworks
"""
import json, os, sys, wave
import numpy as np

KIND = sys.argv[1]
SR = 44100
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(2026)
HERE = os.path.dirname(os.path.abspath(__file__))
sched = json.load(open(os.path.join(HERE, f"{KIND}.schedule.json")))
ev = sched["events"]
L = np.zeros(N); Rr = np.zeros(N)


def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i] * gain
    pan = max(-1, min(1, pan))
    L[i:i + len(sig)] += sig * np.cos((pan + 1) * np.pi / 4)
    Rr[i:i + len(sig)] += sig * np.sin((pan + 1) * np.pi / 4)


def env(n, a=0.005, d=1.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def filt(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    if lo: X *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi: X *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X, len(x))


def pluck(freq, dur=1.4):
    n = int(dur * SR); p = int(SR / freq)
    buf = filt(np.concatenate([rng.uniform(-1, 1, p) * .8, [0]]), hi=5000)[:p].copy()
    out = np.empty(n)
    for i in range(n):
        v = buf[i % p]; out[i] = v; buf[i % p] = 0.996 * 0.5 * (v + buf[(i + 1) % p])
    return out * env(n, .001, dur * .5)


SA = 146.83  # D3
t_all = np.arange(N) / SR


def tanpura(gain=0.018):
    d = np.zeros(N)
    for base, ph in [(SA * 1.5, 0.0), (SA, .7), (SA * 2, 1.3), (SA, 2.1)]:
        for k, amp in enumerate([1, .5, .35, .25, .18, .12], start=1):
            d += amp * np.sin(2 * np.pi * base * k * t_all + ph * k) * (.6 + .4 * np.sin(2 * np.pi * .25 * t_all + ph))
    add(filt(d, hi=1800) * gain * np.minimum(1, t_all / 1.5), 0)


def dholki(start, end, beat, g=1.0):
    def dha(t0):
        n = int(.35 * SR); tl = np.arange(n) / SR
        add(np.sin(2 * np.pi * np.cumsum(95 * np.exp(-tl * 9) + 60) / SR) * env(n, .002, .12), t0, 0, .3 * g)
    def ta(t0, k=1.0):
        n = int(.12 * SR); tl = np.arange(n) / SR
        s = filt(rng.uniform(-1, 1, n), 1800, 6000) * env(n, .001, .03) + np.sin(2 * np.pi * 660 * tl) * env(n, .001, .05) * .5
        add(s, t0, .15, .15 * g * k)
    bt, k = start, 0
    while bt < end:
        pos = k % 8
        if pos in (0, 3, 6): dha(bt)
        if pos in (2, 4, 7): ta(bt)
        if pos in (1, 5): ta(bt, .5)
        bt += beat / 2; k += 1


def bell(t0, f0=520, g=1.0, pan=0):
    n = int(3.5 * SR); tl = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f0 * r * tl) * np.exp(-tl / d) for r, a, d in [(1, 1, 2.2), (2.76, .5, 1.2), (5.4, .3, .6), (8.9, .15, .3), (.5, .4, 2.8)])
    add(s * np.minimum(1, tl / .002), t0, pan, .12 * g)


def shimmer(t0, dur=1.2, g=1.0):
    n = int(dur * SR); tl = np.arange(n) / SR; s = np.zeros(n)
    for k in range(18):
        on = rng.uniform(0, dur * .7)
        s += np.sin(2 * np.pi * (2000 + 300 * k) * tl) * np.exp(-np.maximum(0, tl - on) * 7) * (tl > on) * .12
    add(s * np.sin(np.pi * tl / dur), t0, .2, .18 * g)


def clink(t0, pan=0, g=1.0):
    n = int(.4 * SR); tl = np.arange(n) / SR
    f = rng.uniform(2600, 4200)
    s = sum(a * np.sin(2 * np.pi * f * r * tl) * np.exp(-tl / d) for r, a, d in [(1, 1, .09), (1.51, .6, .06), (2.73, .4, .04)])
    add(s * np.minimum(1, tl / .0005), t0, pan, .05 * g)


def fireworks(g=1.0):
    for l in sched["launches"]:
        n = int(.9 * SR); tl = np.arange(n) / SR
        wh = filt(rng.uniform(-1, 1, n), 1500, 7000) * (tl / .9) ** 1.5 * np.exp(-np.maximum(0, tl - .8) * 30)
        add(wh * .5 + np.sin(2 * np.pi * np.cumsum(1200 + 1600 * tl / .9) / SR) * .05 * (tl / .9), l["t"], (l["x"] - .5) * 1.4, .09 * g)
    for b in sched["bursts"]:
        pan = (b["x"] - .5) * 1.4
        n = int(2.2 * SR); tl = np.arange(n) / SR
        boom = filt(rng.uniform(-1, 1, n), hi=380) * env(n, .003, .35) * 2.2
        boom += np.sin(2 * np.pi * np.cumsum(70 * np.exp(-tl * 4) + 38) / SR) * env(n, .002, .3)
        add(boom, b["t"], pan, .3 * g)
        dur = 1.8 if b["type"] == "willow" else 1.1; m = int(dur * SR); cr = np.zeros(m)
        for _ in range(140 if b["type"] == "willow" else 70):
            i = int(rng.uniform(.15, dur) * SR * rng.uniform(.5, 1)) % (m - 400)
            cr[i:i + 300] += rng.uniform(-1, 1, 300) * np.exp(-np.arange(300) / 40) * rng.uniform(.3, 1)
        add(filt(cr, 1500, 9000), b["t"] + .1, pan, .1 * g)


def santoor(phrase, scale, start, beat, end=14.2, gain=.2):
    tt = start
    while tt < end:
        for n, d in phrase:
            if tt > end: break
            hi = n.endswith("'")
            f = SA * 2 ** (2 if hi else 1) * 2 ** (scale[n[0]] / 12)
            s = pluck(f)
            add(s, tt, -.25, gain); add(s * .5, tt + .012, .3, gain)
            tt += d * beat


def shehnai(phrase, scale, start, beat, end=14.3, gain=.11):
    """Reed-like lead: harmonic-rich tone with glides, vibrato and breath."""
    notes = []
    tt = start
    while tt < end:
        for n, d in phrase:
            if tt > end: break
            hi = n.endswith("'")
            notes.append((tt, d * beat, SA * 2 ** (2 if hi else 1) * 2 ** (scale[n[0]] / 12)))
            tt += d * beat
    t0, t1 = notes[0][0], min(end + .6, DUR)
    n = int((t1 - t0) * SR); tl = np.arange(n) / SR + t0
    f = np.full(n, notes[0][2]); amp = np.zeros(n)
    for (a, d, fr), nxt in zip(notes, notes[1:] + [None]):
        i0 = int((a - t0) * SR); i1 = min(n, int((a + d - t0) * SR))
        f[i0:i1] = fr
        k = np.arange(i1 - i0) / SR
        amp[i0:i1] = np.minimum(1, k / .04) * (1 - .25 * np.exp(-k / .08))  # soft tongue at each note
    # glide between notes (portamento)
    gl = int(.05 * SR); f = np.convolve(np.pad(f, (gl, gl), mode="edge"), np.ones(gl) / gl, "same")[gl:-gl]
    f *= 1 + .006 * np.sin(2 * np.pi * 5.6 * tl) * np.minimum(1, (tl - t0) / .5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k ** .7) * np.sin(k * ph) for k in range(1, 16))
    s = filt(s, 500, 3600) + filt(rng.normal(0, 1, n), 1500, 5000) * .05
    tail = np.ones(n); tf = int(.6 * SR); tail[-tf:] = np.linspace(1, 0, tf)
    s *= amp * tail
    add(s / np.max(np.abs(s)), t0, .1, gain)


def birds(a, b):
    tt = a
    while tt < b:
        n = int(rng.uniform(.06, .14) * SR); tl = np.arange(n) / SR
        f0 = rng.uniform(3000, 5200)
        f = f0 + rng.uniform(-1500, 1500) * tl / tl[-1] + 300 * np.sin(2 * np.pi * 40 * tl)
        add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tl / tl[-1]), tt, rng.uniform(-.8, .8), .03)
        tt += rng.uniform(.08, .5)


def page_turn(a, b):
    n = int((b - a + .3) * SR); tl = np.arange(n) / SR
    s = filt(rng.uniform(-1, 1, n), 600, 7000) * np.sin(np.pi * np.minimum(1, tl / (b - a + .3))) ** 2
    s *= 1 + .6 * (rng.uniform(0, 1, n) > .997)  # paper crackle
    add(s, a, 0, .08)


if KIND == "dhanteras":
    tanpura()
    beat = 60 / 104
    durga = {"S": 0, "R": 2, "M": 5, "P": 7, "D": 9}
    santoor([("S", .5), ("R", .5), ("M", 1), ("P", .5), ("D", .5), ("P", 1), ("M", .5), ("R", .5), ("M", .5), ("P", .5),
             ("D", 1), ("S'", 1), ("D", .5), ("P", .5), ("M", .5), ("R", .5), ("S", 1), ("R", .5), ("M", .5), ("P", 2)],
            durga, .6, beat)
    dholki(.6 + 4 * beat, 14.4, beat, .9)
    for i, b in enumerate(ev["bells"]): bell(b, 480, 1.1, -.6); bell(b + .35, 560, .8, -.3)
    bell(ev["card"] + .1, 520, 1.0)
    for s in ev["shimmer"] + [ev["cardShine"]]: shimmer(s)
    a, b = ev["fountain"]
    for k in range(40): clink(rng.uniform(a, b + .9), rng.uniform(-.7, .7), 1.2)
    for _ in range(45): clink(rng.uniform(.8, 14.3), rng.uniform(-.9, .9), .45)
    for s in ev["steps"]: clink(s, 0, .9); clink(s + .03, 0, .4)
    fireworks(.8)
else:
    tanpura(.016)
    beat = 60 / 96
    bhairav = {"S": 0, "r": 1, "G": 4, "m": 5, "P": 7, "d": 8, "N": 11}
    shehnai([("S", 1), ("r", .5), ("G", .5), ("m", 1), ("P", 1.5), ("d", .5), ("P", 1), ("m", .5), ("G", .5),
              ("r", 1), ("S", 1), ("G", .5), ("m", .5), ("P", .5), ("d", .5), ("N", .5), ("S'", 1.5), ("N", .5), ("d", .5),
              ("P", 1), ("m", .5), ("G", .5), ("m", .5), ("r", .5), ("S", 2)], bhairav, .7, beat)
    dholki(.7 + 8 * beat, 14.4, beat, .75)
    birds(.2, 5.0)
    bell(ev["bells"][0], 500, 1.0); bell(ev["card"] + .1, 540, 1.0)
    for s in ev["shimmer"] + [ev["cardShine"]]: shimmer(s)
    page_turn(*ev["bookOpen"])
    shimmer(ev["bookOpen"][1], 1.6, 1.2)
    fireworks(.8)

mix = np.stack([L, Rr], 1)
fade = np.ones(N); fo = int(.6 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 2; fade[:int(.05 * SR)] = np.linspace(0, 1, int(.05 * SR))
mix *= fade[:, None]
mix = np.tanh(mix * 1.6) / np.tanh(1.6)
mix *= .89 / np.max(np.abs(mix))
out = os.path.join(HERE, f"{KIND}.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out)
