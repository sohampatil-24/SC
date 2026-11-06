"""Synthesize a 15 s festive soundtrack synced to the fireworks in schedule.json.

Layers: tanpura drone, santoor-like plucked melody (raag Bhupali, pentatonic),
dholki groove, temple bell at the logo reveal, and firework whooshes/booms/crackles.
"""
import json, os, wave
import numpy as np

SR = 44100
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(1020)
HERE = os.path.dirname(os.path.abspath(__file__))
sched = json.load(open(os.path.join(HERE, "diwali.schedule.json")))

L = np.zeros(N); Rr = np.zeros(N)


def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * l
    Rr[i:i + len(sig)] += sig * r


def env(n, a=0.005, d=1.0):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / d)


def lowpass(x, cutoff):
    # simple one-pole, run twice
    a = np.exp(-2 * np.pi * cutoff / SR)
    for _ in range(2):
        y = np.empty_like(x); acc = 0.0
        for i in range(len(x)):
            acc = (1 - a) * x[i] + a * acc; y[i] = acc
        x = y
    return x


def lp_fast(x, cutoff):
    # FFT brick-ish lowpass with soft rolloff (fast for long buffers)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / cutoff) ** 4)
    return np.fft.irfft(X, len(x))


def bp_fast(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (1 / (1 + (lo / np.maximum(f, 1)) ** 4)) * (1 / (1 + (f / hi) ** 4))
    return np.fft.irfft(X, len(x))


def pluck(freq, dur=1.6, bright=0.5):
    """Karplus-Strong string — a santoor-ish hammered pluck."""
    n = int(dur * SR); p = int(SR / freq)
    buf = rng.uniform(-1, 1, p) * 0.8
    buf = lp_fast(np.concatenate([buf, np.zeros(1)]), 2000 + 6000 * bright)[:p]
    out = np.empty(n)
    decay = 0.996
    for i in range(n):
        v = buf[i % p]
        out[i] = v
        buf[i % p] = decay * 0.5 * (v + buf[(i + 1) % p])
    return out * env(n, 0.001, dur * 0.5)


# ---- tanpura drone (Sa = D3, Pa = A3) ----
SA = 146.83
t = np.arange(N) / SR
drone = np.zeros(N)
for base, ph in [(SA * 1.5 / 2 * 2, 0.0), (SA, 0.7), (SA * 2, 1.3), (SA, 2.1)]:
    for k, amp in enumerate([1, .5, .35, .25, .18, .12], start=1):
        drone += amp * np.sin(2 * np.pi * base * k * t + ph * k) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * t + ph))
drone = lp_fast(drone, 1800) * 0.018
drone *= np.minimum(1, t / 1.5)
add(drone, 0, 0.0)

# ---- melody: Bhupali (S R G P D) on santoor ----
BPM = 112
beat = 60 / BPM
scale = {"S": 0, "R": 2, "G": 4, "P": 7, "D": 9}
def note(n, octv=1):
    return SA * 2 ** octv * 2 ** (scale[n] / 12)
phrase = [("G", .5), ("P", .5), ("D", 1), ("S'", .5), ("D", .5), ("P", 1),
          ("G", .5), ("R", .5), ("G", .5), ("P", .5), ("G", 1), ("R", .5), ("S", .5),
          ("R", .5), ("G", .5), ("P", .5), ("D", .5), ("S'", 1), ("D", .5), ("P", .5),
          ("G", .5), ("P", .5), ("D", .5), ("S'", .5), ("R'", 1), ("S'", 2)]
tt = 0.6
for rep in range(2):
    for n, d in phrase:
        if tt > 14.2:
            break
        hi = n.endswith("'")
        f = note(n[0], 2 if hi else 1)
        s = pluck(f, 1.4, 0.6)
        add(s, tt, pan=-0.25, gain=0.20)
        add(s * 0.5, tt + 0.012, pan=0.3, gain=0.20)  # double-strike, santoor style
        tt += d * beat

# ---- dholki groove ----
def dha(t0, g=1.0):
    n = int(0.35 * SR); tl = np.arange(n) / SR
    f = 95 * np.exp(-tl * 9) + 60
    add(np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, .12), t0, 0, 0.32 * g)
def ta(t0, g=1.0):
    n = int(0.12 * SR)
    s = bp_fast(rng.uniform(-1, 1, n), 1800, 6000) * env(n, .001, .03)
    s += np.sin(2 * np.pi * 660 * np.arange(n) / SR) * env(n, .001, .05) * .5
    add(s, t0, 0.15, 0.16 * g)
bt = 0.6 + 8 * beat * 0  # start with melody
k = 0
while bt < 14.4:
    pos = k % 8
    if pos in (0, 3, 6): dha(bt)
    if pos in (2, 4, 7): ta(bt)
    if pos in (1, 5): ta(bt, 0.5)
    bt += beat / 2; k += 1

# ---- temple bell + shimmer at the card reveal ----
def bell(t0, f0=520, g=1.0):
    n = int(3.5 * SR); tl = np.arange(n) / SR
    s = np.zeros(n)
    for ratio, amp, dec in [(1, 1, 2.2), (2.76, .5, 1.2), (5.4, .3, .6), (8.9, .15, .3), (0.5, .4, 2.8)]:
        s += amp * np.sin(2 * np.pi * f0 * ratio * tl) * np.exp(-tl / dec)
    add(s * np.minimum(1, tl / .002), t0, 0, 0.12 * g)
bell(sched["events"]["card"] + 0.1)
bell(sched["events"]["title"] + 0.0, 660, 0.7)

def shimmer(t0, dur=1.2, g=1.0):
    n = int(dur * SR); tl = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(18):
        f = 2000 + 300 * k
        on = rng.uniform(0, dur * .7)
        s += np.sin(2 * np.pi * f * tl) * np.exp(-np.maximum(0, tl - on) * 7) * (tl > on) * 0.12
    add(s * np.sin(np.pi * tl / dur), t0, 0.2, 0.18 * g)
for key in ("shimmer", "message", "cardShine"):
    shimmer(sched["events"][key])
for i, pt in enumerate(sched["events"]["sweetsPop"]):
    n = int(.15 * SR); tl = np.arange(n) / SR
    add(np.sin(2 * np.pi * (700 + 90 * i) * tl * (1 + tl * 3)) * env(n, .002, .05), pt, (i - 3) / 5, 0.09)

# ---- fireworks ----
for l in sched["launches"]:
    n = int(0.9 * SR); tl = np.arange(n) / SR
    noise = rng.uniform(-1, 1, n)
    wh = bp_fast(noise, 1500, 7000) * (tl / 0.9) ** 1.5 * np.exp(-np.maximum(0, tl - .8) * 30)
    whistle = np.sin(2 * np.pi * np.cumsum(1200 + 1600 * tl / .9) / SR) * 0.05 * (tl / .9)
    add(wh * 0.5 + whistle, l["t"], pan=(l["x"] - .5) * 1.4, gain=0.10)
for b in sched["bursts"]:
    pan = (b["x"] - .5) * 1.4
    n = int(2.2 * SR); tl = np.arange(n) / SR
    boom = lp_fast(rng.uniform(-1, 1, n), 380) * env(n, .003, .35) * 2.2
    boom += np.sin(2 * np.pi * np.cumsum(70 * np.exp(-tl * 4) + 38) / SR) * env(n, .002, .3)
    add(boom, b["t"], pan, 0.34)
    # crackle tail
    dur = 1.8 if b["type"] == "willow" else 1.1
    m = int(dur * SR)
    cr = np.zeros(m)
    cnt = 140 if b["type"] == "willow" else 70
    for _ in range(cnt):
        i = int(rng.uniform(0.15, dur) * SR * rng.uniform(.5, 1)) % (m - 400)
        c = rng.uniform(-1, 1, 300) * np.exp(-np.arange(300) / 40)
        cr[i:i + 300] += c * rng.uniform(.3, 1)
    cr = bp_fast(cr, 1500, 9000)
    add(cr, b["t"] + 0.1, pan + rng.uniform(-.3, .3), 0.12)

# ---- master ----
mix = np.stack([L, Rr], 1)
fade = np.ones(N); fo = int(0.6 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 2
fi = int(0.05 * SR); fade[:fi] = np.linspace(0, 1, fi)
mix *= fade[:, None]
mix = np.tanh(mix * 1.6) / np.tanh(1.6)  # gentle saturation / limiter
mix *= 0.89 / np.max(np.abs(mix))
pcm = (mix * 32767).astype(np.int16)
out = os.path.join(HERE, "soundtrack.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("wrote", out)
