#!/usr/bin/env python3
"""Makes STRATUM's own sounds from scratch: 808s, electronic drums, synth basses, leads, pads, keys and effects.
Nothing here is sampled. The output folder is <out>/<category>/<name>.wav; a note in a name (C2) is the pitch it plays at."""
import os, sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]
rng = np.random.default_rng(808)


def hz(note): return 440 * 2 ** ((note - 69) / 12)
def t(sec): return np.arange(int(SR * sec)) / SR
def env(x, a=0.002, r=0.01):
    n, na, nr = len(x), int(a * SR), int(r * SR)
    e = np.ones(n); e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr)
    return x * e
def osc(freq):  # sine from a frequency curve
    return np.sin(2 * np.pi * np.cumsum(freq) / SR)
def saw(freq):
    ph = np.cumsum(freq) / SR
    return 2 * (ph % 1) - 1
def square(freq): return np.sign(np.sin(2 * np.pi * np.cumsum(freq) / SR))
def lowpass(x, cut):  # one-pole, cutoff may be a curve
    c = np.broadcast_to(1 - np.exp(-2 * np.pi * np.asarray(cut) / SR), x.shape)
    y, s = np.zeros_like(x), 0.0
    for i in range(len(x)):
        s += c[i] * (x[i] - s); y[i] = s
    return y
def highpass(x, cut): return x - lowpass(x, cut)
def noise(sec): return rng.uniform(-1, 1, int(SR * sec))
def save(cat, name, x, stereo=None):
    x = np.asarray(x, float)
    x = x / max(1e-9, np.max(np.abs(x))) * 0.89
    if stereo is None: frames = np.column_stack([x, x])
    else:
        y = np.asarray(stereo, float); y = y / max(1e-9, np.max(np.abs(y))) * 0.89
        frames = np.column_stack([x, y])
    os.makedirs(os.path.join(out, cat), exist_ok=True)
    with wave.open(os.path.join(out, cat, name + ".wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((frames * 32767).astype("<i2").tobytes())


def e808(sec=2.2, decay=0.9, punch=1.0, drive=1.0, note=36, glide=0.0):
    tt = t(sec); f = hz(note) * (1 + punch * 2.5 * np.exp(-tt / 0.018))
    if glide: f = f * 2 ** (glide * np.clip(tt - 0.35, 0, 0.4) / 0.4 / 12)
    x = osc(f) * np.exp(-tt / decay)
    return env(np.tanh(x * drive) / np.tanh(drive), 0.0005, 0.03)

save("808s", "808 Long C2", e808(3.2, 1.5))
save("808s", "808 Short C2", e808(0.9, 0.28))
save("808s", "808 Punch C2", e808(1.6, 0.6, punch=2.2, drive=1.6))
save("808s", "808 Distorted C2", e808(2.2, 0.9, drive=5))
save("808s", "808 Hard Clip C2", e808(1.8, 0.8, punch=1.5, drive=12))
save("808s", "808 Drill Slide C2", e808(1.6, 0.9, drive=2.5, glide=-5))
save("808s", "808 Glide Up C2", e808(1.6, 0.9, drive=2, glide=7))
save("808s", "808 Soft Sub C2", e808(2.6, 1.1, punch=0.3))
save("808s", "808 Boom Bap C2", lowpass(e808(1.2, 0.4, punch=1.4, drive=2), 900))
save("808s", "808 Reggaeton C2", e808(0.7, 0.2, punch=1.6, drive=2))

def kick(sec, f0, f1, tau, decay, click=0.3, drive=1.5):
    tt = t(sec); x = osc(f1 + (f0 - f1) * np.exp(-tt / tau)) * np.exp(-tt / decay)
    c = highpass(noise(sec), 2000) * np.exp(-tt / 0.003) * click
    return env(np.tanh((x + c) * drive), 0.0003, 0.01)

for name, a in {"House Kick": (0.45, 220, 52, 0.03, 0.14), "Techno Kick": (0.55, 260, 46, 0.025, 0.2, 0.4, 3), "Trance Kick": (0.4, 320, 55, 0.02, 0.12, 0.5, 2.5), "DnB Kick": (0.3, 300, 62, 0.02, 0.09, 0.5, 2),
                "Hardstyle Kick": (0.6, 400, 50, 0.04, 0.2, 0.3, 8), "Trap Kick": (0.4, 240, 50, 0.025, 0.14, 0.6, 2.5), "Boom Bap Kick": (0.35, 170, 58, 0.03, 0.12, 0.2, 1.8), "Afro Kick": (0.35, 190, 70, 0.03, 0.1, 0.15, 1.3), "Soft Lo-fi Kick": (0.35, 130, 55, 0.04, 0.12, 0.05, 1.1)}.items():
    x = kick(*a); save("Kicks", name, lowpass(x, 5000) if "Lo-fi" in name else x)

def hat(sec, decay, cut=8000):
    tt = t(sec); return env(highpass(noise(sec), cut) * np.exp(-tt / decay), 0.0002, 0.005)
for name, a in {"Closed Hat Tight": (0.07, 0.012), "Closed Hat": (0.12, 0.03), "Closed Hat Dark": (0.12, 0.03, 5000), "Open Hat": (0.5, 0.14), "Open Hat Long": (0.9, 0.3), "Trap Hat": (0.09, 0.018, 9500), "Shaker Tick": (0.08, 0.02, 6000)}.items():
    save("Hats", name, hat(*a))
for name, a in {"Crash Noise": (2.5, 0.8, 5000), "Ride Noise": (1.5, 0.5, 7000)}.items():
    save("Cymbals", name, hat(*a))

def clap(sec=0.4, cut=1200, tail=0.1):
    tt = t(sec); n = highpass(lowpass(noise(sec), 5000), cut); e = np.exp(-tt / tail)
    for d in (0.0, 0.011, 0.022): e = np.maximum(e, (tt >= d) * np.exp(-np.maximum(tt - d, 0) / 0.006) * 1.2)
    return env(n * e, 0.0002, 0.01)
save("Claps", "Electronic Clap", clap()); save("Claps", "House Clap", clap(0.5, 1000, 0.14)); save("Claps", "Trap Clap", clap(0.35, 1500, 0.08)); save("Claps", "Gospel Snap Clap", clap(0.25, 2000, 0.05))

def snare(sec, f, decay, cut=1800, body=0.5):
    tt = t(sec); b = osc(f * (1 + 0.5 * np.exp(-tt / 0.01))) * np.exp(-tt / 0.06) * body
    return env(np.tanh(b + highpass(noise(sec), cut) * np.exp(-tt / decay)), 0.0002, 0.01)
for name, a in {"Electronic Snare": (0.3, 190, 0.09), "Trap Snare": (0.35, 210, 0.11, 2200), "Drill Snare": (0.25, 240, 0.07, 2500), "DnB Snare": (0.25, 230, 0.08, 1500, 0.8), "Rim Tick": (0.06, 900, 0.008, 3000, 1.0)}.items():
    save("Snares", name, snare(*a))

N = 48  # C3
def stack(f, voices=7, spread=0.012, wave_=saw):
    return sum(wave_(f * (1 + spread * (i - voices // 2) / (voices // 2))) for i in range(voices)) / voices

tt = t(2.0); f = np.full_like(tt, hz(36))
save("Bass", "Reese Bass C2", env(lowpass(stack(f, 4, 0.008), 900), 0.005, 0.05))
save("Bass", "Sub Sine C2", env(osc(f), 0.005, 0.05))
save("Bass", "Wobble Bass C2", env(lowpass(saw(f), 300 + 2400 * (0.5 + 0.5 * np.sin(2 * np.pi * 4 * tt))), 0.005, 0.05))
save("Bass", "Growl Bass C2", env(np.tanh(4 * lowpass(square(f), 500 + 1800 * (0.5 + 0.5 * np.sin(2 * np.pi * 8 * tt)))), 0.005, 0.05))
tt = t(0.5); f = np.full_like(tt, hz(36))
save("Bass", "Acid Bass C2", env(np.tanh(3 * lowpass(saw(f), 200 + 4500 * np.exp(-tt / 0.09))), 0.002, 0.03))
save("Bass", "Pluck Bass C2", env(lowpass(saw(f), 150 + 2500 * np.exp(-tt / 0.05)) * np.exp(-tt / 0.3), 0.002, 0.03))
save("Bass", "FM Bass C2", env(osc(f + 200 * np.exp(-tt / 0.1) * np.sin(2 * np.pi * 2 * f * tt)), 0.002, 0.03))

tt = t(3.0); f = np.full_like(tt, hz(N))
save("Synths", "Supersaw Lead C3", env(stack(f, 7, 0.012), 0.01, 0.1), env(stack(f * 1.001, 7, 0.014), 0.01, 0.1))
save("Synths", "Square Lead C3", env(lowpass(square(f), 3000), 0.005, 0.1))
save("Synths", "Chiptune Lead C3", env(square(f), 0.001, 0.02))
save("Synths", "Synthwave Brass C3", env(lowpass(stack(f, 4, 0.006), 600 + 3000 * (1 - np.exp(-tt / 0.2))), 0.04, 0.2))
tt = t(0.7); f = np.full_like(tt, hz(N))
save("Synths", "Pluck C3", env(lowpass(stack(f, 3, 0.005), 400 + 6000 * np.exp(-tt / 0.07)) * np.exp(-tt / 0.25), 0.001, 0.03))
save("Synths", "Trance Stab C3", env(sum(stack(f * r, 5, 0.01) for r in (1, 1.2, 1.5)) * np.exp(-tt / 0.2), 0.001, 0.03))
save("Synths", "House Chord Stab C3", env(lowpass(sum(saw(f * r) for r in (1, 1.189, 1.498, 1.782)), 2500) * np.exp(-tt / 0.15), 0.001, 0.03))
save("Synths", "Bell Pluck C3", env(osc(f * 2 + 300 * np.exp(-tt / 0.2) * np.sin(2 * np.pi * 7 * f * tt)) * np.exp(-tt / 0.3), 0.001, 0.03))

tt = t(6.0); f = np.full_like(tt, hz(N))
lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * tt)
save("Pads", "Warm Pad C3", env(lowpass(stack(f, 5, 0.006), 700 + 500 * lfo), 0.8, 1.2), env(lowpass(stack(f * 1.002, 5, 0.007), 700 + 500 * (1 - lfo)), 0.8, 1.2))
save("Pads", "Dark Pad C3", env(lowpass(stack(f / 2, 5, 0.008), 350 + 200 * lfo), 1.2, 1.5))
save("Pads", "Airy Pad C3", env(lowpass(stack(f, 3, 0.004), 1500) * 0.6 + highpass(noise(6), 5000) * 0.05, 1.0, 1.5))
save("Pads", "Vapor Pad C3", env(lowpass(sum(stack(f * r, 3, 0.01) for r in (1, 1.26, 1.5)), 1100 + 500 * lfo), 0.7, 1.5))

tt = t(3.0); f = np.full_like(tt, hz(60))
save("Piano and Keys", "Electric Piano FM C4", env(osc(f + 1.4 * f * np.exp(-tt / 0.35) * np.sin(2 * np.pi * f * tt) * 0.8) * np.exp(-tt / 1.1) + 0.2 * osc(f * 14) * np.exp(-tt / 0.03), 0.001, 0.08))
save("Piano and Keys", "Soft Keys C4", env(lowpass(osc(f) + 0.4 * osc(2 * f) + 0.15 * osc(3 * f), 2500) * np.exp(-tt / 0.9), 0.003, 0.08))
tt = t(0.8); f = np.full_like(tt, hz(60))
save("Piano and Keys", "Funk Clav C4", env(highpass(lowpass(square(f), 600 + 4500 * np.exp(-tt / 0.06)), 300) * np.exp(-tt / 0.25), 0.001, 0.02))
tt = t(3.0); f = np.full_like(tt, hz(60))
tone = sum(a * osc(f * r) for r, a in ((0.5, 0.8), (1, 1), (1.5, 0.5), (2, 0.7), (3, 0.3), (4, 0.2)))
save("Organ", "Gospel Drawbar Organ C4", env(tone * (1 + 0.15 * np.sin(2 * np.pi * 6 * tt)), 0.005, 0.03))
save("Organ", "Reggae Bubble Organ C4", env(tone[:int(0.25 * SR)], 0.003, 0.05))

tt = t(0.8); f = hz(36) * (1 + 0.6 * np.exp(-tt / 0.03))
save("World", "Amapiano Log Drum C2", env(np.tanh(2.5 * (osc(f) + 0.5 * osc(f * 2.76) * np.exp(-tt / 0.05))) * np.exp(-tt / 0.3), 0.001, 0.03))
tt = t(0.8); f = hz(48) * (1 + 0.3 * np.exp(-tt / 0.02))
save("World", "Amapiano Log Drum High C3", env((osc(f) + 0.6 * osc(f * 2.76) * np.exp(-tt / 0.04)) * np.exp(-tt / 0.2), 0.001, 0.03))

tt = t(6.0)
save("FX", "White Noise Riser", env(lowpass(noise(6), 200 + 12000 * (tt / 6) ** 2) * (tt / 6) ** 1.5, 0.01, 0.02))
save("FX", "White Noise Downlifter", env(lowpass(noise(6), 200 + 12000 * (1 - tt / 6) ** 2) * (1 - tt / 6) ** 1.5, 0.01, 0.2))
save("FX", "Synth Riser", env(saw(100 * 2 ** (4 * tt / 6)) * (tt / 6), 0.01, 0.02))
tt = t(3.0)
save("FX", "Impact Boom", env(np.tanh(3 * osc(30 + 120 * np.exp(-tt / 0.06))) * np.exp(-tt / 0.9), 0.001, 0.1))
tt = t(6.0)
crackle = (rng.uniform(0, 1, len(tt)) > 0.9995) * rng.uniform(-1, 1, len(tt))
save("FX", "Vinyl Crackle Loop", lowpass(crackle, 7000) * 6 + highpass(noise(6), 1500) * 0.01)
save("FX", "Tape Hiss Loop", highpass(noise(6), 3000) * 0.2)


# Genre kits. For every genre button in the Sounds window: drums, the sounds the genre is known for, and a two-bar drum
# loop at its usual tempo. Each sound's genres are written to genres.json; fetch-library.sh adds them to library.json so
# the genre buttons find them. Everything above this line is unchanged, so the earlier sounds come out the same.
TAGS = {}
def gsave(tags, cat, name, x, stereo=None):
    save(cat, name, x, stereo); TAGS[cat + "/" + name] = tags

try:
    from scipy.signal import lfilter
    def lp(x, cut):  # same one-pole filter as lowpass(), for a fixed cutoff, much faster
        c = 1 - np.exp(-2 * np.pi * cut / SR); return lfilter([c], [1, c - 1], x)
except ImportError:
    lp = lowpass
def hp(x, cut): return x - lp(x, cut)
def bp(x, lo, hi): return hp(lp(x, hi), lo)
def drive(x, d): return hp(np.tanh(x * d) / np.tanh(d), 25)
def const(f, sec): return np.full(int(SR * sec), float(f))
def place(x, n): y = np.zeros(n); y[:min(n, len(x))] = x[:n]; return y

_irs = {}
def verb(x, sec=1.8, mix=0.3, cut=6000, seed=0):  # reverb: an exponentially fading noise burst, convolved by FFT
    key = (sec, cut, seed)
    if key not in _irs:
        r = np.random.default_rng(1000 + seed); n = int(SR * sec)
        _irs[key] = lp(r.uniform(-1, 1, n) * np.exp(-np.arange(n) / SR / (sec / 6)), cut)
    ir = _irs[key]; n = len(x) + len(ir); N = 1 << (n - 1).bit_length()
    w = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:n]
    w *= np.max(np.abs(x)) / max(1e-9, np.max(np.abs(w)))
    return env(np.concatenate([x, np.zeros(len(ir))]) * (1 - mix) + w * mix, 0.0001, min(0.5, sec / 3))
def wide(x, sec=1.8, mix=0.3, cut=6000): return verb(x, sec, mix, cut, 0), verb(x, sec, mix, cut, 1)

def ks(note, sec, damp=0.996, bright=0.5, soft=0.0):  # plucked string (Karplus-Strong)
    n, p = int(SR * sec), max(2, int(round(SR / hz(note))))
    burst = rng.uniform(-1, 1, p)
    if soft: burst = lp(burst, 300 + 6000 * (1 - soft))
    burst = burst - burst.mean()  # no DC, so distortion stays centred
    y = list(burst) + [0.0] * (n + 1)
    a, b = damp * bright, damp * (1 - bright)
    for i in range(p + 1, n + p + 1): y[i] = a * y[i - p] + b * y[i - p - 1]
    return env(np.array(y[p + 1:]), 0.0005, 0.02)
def strum(notes, sec, gap=0.012, **k):
    x = np.zeros(int(SR * sec))
    for i, nt in enumerate(notes):
        s = ks(nt, sec - i * gap, **k); d = int(i * gap * SR); x[d:d + len(s)] += s
    return x

# Drums
def conga(note, decay=0.18):
    tt = t(0.6); f = hz(note) * (1 + 0.15 * np.exp(-tt / 0.01))
    return env((osc(f) + 0.3 * osc(f * 1.5) * np.exp(-tt / 0.03)) * np.exp(-tt / decay) + hp(noise(0.6), 3000) * np.exp(-tt / 0.004) * 0.4, 0.0005, 0.01)
def cowbell(f=587):
    tt = t(0.5); return env(bp(square(const(f, 0.5)) + square(const(f * 1.44, 0.5)), 400, 4000) * np.exp(-tt / 0.09), 0.0005, 0.01)
def timbale(note=76):
    tt = t(0.6); f = hz(note) * (1 + 0.1 * np.exp(-tt / 0.01))
    return env(osc(f) * np.exp(-tt / 0.25) + 0.5 * osc(f * 2.3) * np.exp(-tt / 0.12) + hp(noise(0.6), 2500) * np.exp(-tt / 0.02) * 0.6, 0.0003, 0.01)
def shaker(sec=0.15, decay=0.04, cut=5000):
    tt = t(sec); return env(hp(noise(sec), cut) * np.minimum(1, tt / 0.02) * np.exp(-tt / decay), 0.001, 0.01)
def clave(f=2500): tt = t(0.25); return env(osc(const(f, 0.25)) * np.exp(-tt / 0.03), 0.0002, 0.01)
def tamb():
    tt = t(0.4); return env(hp(noise(0.4), 7000) * np.exp(-tt / 0.08) + 0.3 * sum(osc(const(f, 0.4)) * np.exp(-tt / 0.06) for f in (5200, 6900, 8100)), 0.0005, 0.01)
def tom(note, decay=0.25):
    tt = t(0.8); f = hz(note) * (1 + 0.4 * np.exp(-tt / 0.03))
    return env(np.tanh(1.5 * osc(f) * np.exp(-tt / decay)) + hp(noise(0.8), 1500) * np.exp(-tt / 0.01) * 0.3, 0.0003, 0.02)
def brush(sec=0.35): tt = t(sec); return env(bp(noise(sec), 1500, 7000) * np.minimum(1, tt / 0.03) * np.exp(-tt / 0.09), 0.001, 0.02)
def ride(sec=1.6):
    tt = t(sec); m = sum(square(const(f, sec)) for f in (3150, 4280, 5400, 6740))
    return env(hp(m, 4000) * 0.3 * np.exp(-tt / 0.5) + hp(noise(sec), 7000) * np.exp(-tt / 0.35) * 0.5 + osc(const(4800, sec)) * 0.15 * np.exp(-tt / 0.08), 0.0003, 0.05)
def stomp(): tt = t(0.4); return env(np.tanh(2 * osc(60 + 60 * np.exp(-tt / 0.02)) * np.exp(-tt / 0.08)) + lp(noise(0.4), 900) * np.exp(-tt / 0.03) * 0.8, 0.0005, 0.02)
def snap(): tt = t(0.2); return env(bp(noise(0.2), 1800, 6000) * np.exp(-tt / 0.015) + osc(const(2100, 0.2)) * np.exp(-tt / 0.01) * 0.5, 0.0002, 0.01)
def gated_snare():
    s = snare(0.6, 200, 0.4, 1500, 0.6); s = verb(s, 1.2, 0.5, 7000)[:int(0.35 * SR)]; return env(s, 0.0002, 0.03)
def taiko(note=36):
    tt = t(1.6); f = hz(note) * (1 + 0.3 * np.exp(-tt / 0.02))
    return env(verb(np.tanh(2 * osc(f) * np.exp(-tt / 0.35)) + lp(noise(1.6), 1200) * np.exp(-tt / 0.03), 2.0, 0.35, 3000)[:int(2.4 * SR)], 0.0005, 0.3)
def frame_drum():
    tt = t(0.8); f = hz(45) * (1 + 0.2 * np.exp(-tt / 0.02))
    return env(osc(f) * np.exp(-tt / 0.2) + bp(noise(0.8), 600, 3000) * np.exp(-tt / 0.03) * 0.5, 0.0005, 0.02)

# Tones (one note or a chord; the name carries the root so the keys play it in tune)
def epiano(notes, sec=3.0, tine=0.8):
    tt = t(sec); x = 0
    for n_ in notes:
        f = const(hz(n_), sec); x = x + osc(f + tine * f * np.exp(-tt / 0.35) * np.sin(2 * np.pi * hz(n_) * tt)) * np.exp(-tt / 1.2)
    return env(x, 0.002, 0.1)
def piano(notes, sec=3.5):
    tt = t(sec); x = 0
    for n_ in notes:
        f = hz(n_)
        for k in range(1, 9):
            if f * k > 9000: break
            x = x + osc(const(f * k * np.sqrt(1 + 0.0004 * k * k), sec)) * np.exp(-tt / (1.6 / k ** 0.7)) / k ** 1.2
    return env(x + lp(noise(sec), 2500) * np.exp(-tt / 0.008) * 0.3 * len(notes), 0.001, 0.1)
def organ(notes, sec=2.5, perc=0.0):
    tt = t(sec); x = 0
    for n_ in notes:
        f = const(hz(n_), sec)
        x = x + sum(a * osc(f * r) for r, a in ((0.5, 0.8), (1, 1), (1.5, 0.5), (2, 0.7), (3, 0.3), (4, 0.2))) + perc * osc(f * 3) * np.exp(-tt / 0.1)
    return env(x * (1 + 0.12 * np.sin(2 * np.pi * 6 * tt)), 0.005, 0.05)
def strings(notes, sec=4.0, attack=0.35):
    tt = t(sec); vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * tt)
    x = sum(stack(const(hz(n_), sec) * vib, 5, 0.006) for n_ in notes)
    return env(lp(lp(x, 2200), 3500), attack, 0.4)
def brass(notes, sec=0.7):
    tt = t(sec); x = sum(stack(const(hz(n_), sec), 3, 0.004) for n_ in notes)
    return env(np.tanh(1.5 * lowpass(x, 500 + 4000 * (1 - np.exp(-tt / 0.04)) * np.exp(-tt / 0.5))), 0.01, 0.08)
def supersaw(notes, sec=2.0):
    x = sum(stack(const(hz(n_), sec), 7, 0.013) for n_ in notes); return env(lp(x, 7000), 0.005, 0.1)
def pluck(notes, sec=0.8, decay=0.25, open_=6000):
    tt = t(sec); x = sum(stack(const(hz(n_), sec), 3, 0.006) for n_ in notes)
    return env(lowpass(x, 300 + open_ * np.exp(-tt / 0.07)) * np.exp(-tt / decay), 0.001, 0.03)
def bell(note, sec=2.5, ratio=3.5):
    tt = t(sec); f = hz(note); return env(osc(const(f, sec) + 2 * f * np.exp(-tt / 0.4) * np.sin(2 * np.pi * ratio * f * tt)) * np.exp(-tt / 0.8), 0.001, 0.05)
def steel(note, sec=2.0):
    tt = t(sec); f = hz(note); return env((osc(const(f, sec)) + 0.5 * osc(const(2 * f, sec)) * np.exp(-tt / 0.4) + 0.3 * osc(const(3.01 * f, sec)) * np.exp(-tt / 0.15)) * np.exp(-tt / 0.7), 0.002, 0.05)
def kalimba(note, sec=1.8):
    tt = t(sec); f = hz(note); return env(osc(const(f, sec)) * np.exp(-tt / 0.6) + 0.3 * osc(const(f * 5.4, sec)) * np.exp(-tt / 0.05), 0.0008, 0.05)
def reed(note, sec=2.0, breath=0.08, cut=2200):  # harmonica-like
    tt = t(sec); f = const(hz(note), sec) * (1 + 0.006 * np.sin(2 * np.pi * 5 * tt) * np.minimum(1, tt / 0.6))
    return env(lp(0.6 * square(f) + 0.4 * saw(f), cut) + bp(noise(sec), 1000, 4000) * breath, 0.05, 0.15)
def flute(note, sec=2.0):
    tt = t(sec); f = const(hz(note), sec) * (1 + 0.005 * np.sin(2 * np.pi * 5 * tt) * np.minimum(1, tt / 0.5))
    return env(osc(f) + 0.12 * osc(2 * f) + bp(noise(sec), 1500, 6000) * 0.06, 0.06, 0.15)
def choir(notes, sec=4.0, formants=((700, 1.0), (1150, 0.5), (2600, 0.25))):  # an "ah" built from harmonics
    tt = t(sec); vib = 1 + 0.005 * np.sin(2 * np.pi * 5.5 * tt); x = 0
    for n_ in notes:
        for v in (-0.004, 0, 0.004):
            f = hz(n_) * (1 + v)
            for k in range(1, int(4000 / f)):
                a = sum(g * np.exp(-((f * k - fc) / 220) ** 2) for fc, g in formants) + 0.02
                x = x + a * osc(const(f * k, sec) * vib)
    return env(x, 0.4, 0.6)
def wobble(note, sec, rate):
    tt = t(sec); f = const(hz(note), sec); lfo = 0.5 - 0.5 * np.cos(2 * np.pi * rate * tt)
    return env(hp(np.tanh(3 * lowpass(saw(f) + square(f * 1.003), 150 + 3500 * lfo ** 2)), 25), 0.003, 0.05)
def bassline(note, sec, kind):
    tt = t(sec); f = const(hz(note), sec)
    if kind == "sub": return env(osc(f) + 0.15 * osc(2 * f), 0.004, 0.05)
    if kind == "finger": return env(lp(ks(note, sec, 0.997, 0.35, 0.6), 1500) + 0.4 * osc(f) * np.exp(-tt / 0.6), 0.002, 0.04)
    if kind == "slap": return env(ks(note, sec, 0.996, 0.75) + 0.6 * osc(f) * np.exp(-tt / 0.3) + hp(noise(sec), 2000) * np.exp(-tt / 0.004), 0.0005, 0.04)
    if kind == "upright": return env(lp(ks(note, sec, 0.994, 0.3, 0.8), 900) + 0.6 * osc(f) * np.exp(-tt / 0.5), 0.003, 0.05)
    if kind == "organ": return env(lp(osc(f) + 0.5 * osc(2 * f) + 0.3 * osc(3 * f), 1200) * np.exp(-tt / 0.4), 0.002, 0.03)
    if kind == "synth": return env(np.tanh(2 * lowpass(saw(f), 200 + 1800 * np.exp(-tt / 0.12))), 0.002, 0.03)

def loop(bpm, parts, bars=2, swing=0.0, steps=16):
    """parts: (sound, pattern, volume). A pattern has one character per step (x hit, o soft hit, . rest) for one bar
    or for every bar. swing delays every second step by that share of a step. The tail wraps to the start."""
    bar = 240 / bpm; n = int(round(SR * bar * bars)); mix = np.zeros(n + 3 * SR)
    for hit, pat, vol in parts:
        pat = pat.replace(" ", "")
        for i in range(steps * bars):
            ch = pat[i % len(pat)]
            if ch == ".": continue
            s = int(round(SR * bar / steps * (i + (swing if i % 2 else 0))))
            mix[s:s + len(hit)] += hit[:len(mix) - s] * vol * (1.0 if ch == "x" else 0.45)
    out_ = mix[:n].copy(); tail = mix[n:]; k = min(n, len(tail)); out_[:k] += tail[:k]
    return out_

C2, C3, C4, C5 = 36, 48, 60, 72
MAJ, MIN, MAJ7, MIN7, DOM9, MIN9, MAJ9 = (0, 4, 7), (0, 3, 7), (0, 4, 7, 11), (0, 3, 7, 10), (0, 4, 10, 14), (0, 3, 10, 14), (0, 4, 11, 14)
def ch(root, shape): return [root + i for i in shape]
def L(g, bpm): return f"{g} Drum Loop {bpm} BPM"

# Hip hop
G = "hip hop boom bap"
k, s, h = kick(0.4, 160, 55, 0.035, 0.16, 0.25, 2.2), lp(snare(0.32, 200, 0.12, 1400, 0.7), 6000), hat(0.1, 0.025, 6500)
gsave(G, "Kicks", "Hip hop Kick", k); gsave(G, "Snares", "Hip hop Snare", s); gsave(G, "Hats", "Hip hop Hat", h)
gsave(G + " lo-fi soul", "Piano and Keys", "Hip hop Dusty Keys Chord C4", lp(epiano(ch(C4, MIN9), 3.0, 0.5), 3000))
gsave(G, "Bass", "Hip hop Bass C2", bassline(C2, 1.2, "finger"))
gsave(G, "Drum Loops", L("Hip hop", 90), loop(90, [(k, "x......x..x.....", 1), (s, "....x.......x...", 0.9), (h, "x.x.x.x.x.x.x.xo", 0.35)], swing=0.12))

# Trap
G = "trap hip hop"
k, s, h, c = kick(0.5, 230, 48, 0.025, 0.2, 0.5, 2.5), snare(0.35, 215, 0.12, 2300), hat(0.08, 0.016, 9500), clap(0.35, 1500, 0.08)
gsave(G, "Kicks", "Trap Kick Hard", k); gsave(G, "Snares", "Trap Snare Crack", s); gsave(G, "Hats", "Trap Hat Crisp", h); gsave(G, "Claps", "Trap Clap Layer", c)
gsave(G, "Hats", "Trap Hat Roll", loop(140, [(h, "xxxxxxxxxxxxxxxx", 1)], 1, steps=32)[: int(SR * 240 / 140 / 4)])
gsave(G, "Mallets and Bells", "Trap Bell Lead C5", bell(C5, 2.0))
gsave(G, "Woodwinds", "Trap Flute C5", flute(C5, 2.0))
gsave(G, "808s", "Trap 808 Long C2", e808(3.0, 1.3, punch=1.2, drive=2.5))
gsave(G, "Drum Loops", L("Trap", 140), loop(140, [(k, "x.....x...x.....x.......x.x.....", 1), (s, "........x...............x.......", 0.9), (c, "........x...............x.......", 0.5),
                                                   (h, "x.x.x.x.x.x.xxx.x.x.x.x.x.x.x.xx", 0.35)], steps=16))

# Drill
G = "drill uk drill trap"
k, s, h = kick(0.45, 250, 50, 0.025, 0.18, 0.5, 3), snare(0.25, 245, 0.07, 2600), hat(0.08, 0.015, 9000)
gsave(G, "Kicks", "Drill Kick", k); gsave(G, "Snares", "Drill Snare Tight", s); gsave(G, "Hats", "Drill Hat", h)
gsave(G, "808s", "Drill 808 Slide C2", e808(1.8, 0.9, drive=3, glide=-7))
gsave(G, "Piano and Keys", "Drill Dark Piano Chord C4", piano(ch(C4, MIN), 3.0))
gsave(G + " cinematic", "Vocals", "Drill Choir Pad C4", *wide(choir(ch(C4, MIN), 4.0), 2.5, 0.4))
gsave(G, "Drum Loops", L("Drill", 142), loop(142, [(k, "x.........x.......x.....x.......", 1), (s, "......x.........x.....x.........", 0.85), (h, "x..x..x.x..x.x..x..x..x.x..x.xx.", 0.35)], steps=16))

# R&B
G = "r&b soul"
k, s, h = kick(0.4, 150, 52, 0.035, 0.15, 0.15, 1.6), snap(), hat(0.09, 0.02, 8000)
gsave(G, "Kicks", "R&B Kick Soft", k); gsave(G, "Snares", "R&B Finger Snap", s); gsave(G, "Hats", "R&B Hat", h)
gsave(G, "Piano and Keys", "R&B Rhodes Chord C4", *wide(epiano(ch(C4, MAJ9), 3.5, 0.6), 1.5, 0.2))
gsave(G, "Bass", "R&B Sub Bass C2", bassline(C2, 2.0, "sub"))
gsave(G + " ambient", "Pads", "R&B Silk Pad C4", *wide(strings(ch(C4, MAJ7), 5.0, 0.8), 2.5, 0.35))
gsave(G, "Drum Loops", L("R&B", 75), loop(75, [(k, "x.......x.x.....", 1), (s, "....x.......x...", 0.8), (h, "x.xxx.x.x.x.x.xx", 0.3)], swing=0.08))

# Soul
G = "soul funk r&b"
k, s, h = lp(kick(0.4, 140, 60, 0.04, 0.14, 0.2, 1.4), 4000), lp(snare(0.3, 190, 0.1, 1200, 0.8), 5000), lp(hat(0.1, 0.03, 6000), 9000)
gsave(G, "Kicks", "Soul Kick", k); gsave(G, "Snares", "Soul Snare", s); gsave(G, "Hats", "Soul Hat", h)
gsave(G + " gospel", "Organ", "Soul Organ Chord C4", organ(ch(C4, MIN7), 2.5, 0.4))
gsave(G, "Bass", "Soul Finger Bass C2", bassline(C2, 1.5, "finger"))
gsave(G + " jazz", "Brass", "Soul Horn Stab C4", brass(ch(C4, MAJ), 0.6))
gsave(G, "Drum Loops", L("Soul", 92), loop(92, [(k, "x.....x...x.....", 1), (s, "....x.......x..o", 0.85), (h, "xoxoxoxoxoxoxoxo", 0.35)], swing=0.1))

# Gospel
G = "gospel soul"
k, c = kick(0.4, 170, 55, 0.03, 0.14, 0.3, 2), clap(0.3, 1400, 0.07)
gsave(G, "Kicks", "Gospel Kick", k); gsave(G, "Claps", "Gospel Clap Stack", c + 0.6 * place(snap(), len(c)))
gsave(G, "Organ", "Gospel Organ Chord C4", organ(ch(C4, MAJ7) + [C4 + 12], 3.0, 0.5))
gsave(G, "Piano and Keys", "Gospel Piano Chord C4", piano(ch(C4, (0, 4, 7, 9, 14)), 3.5))
gsave(G, "Vocals", "Gospel Choir Ah C4", *wide(choir(ch(C4, MAJ), 4.0), 2.2, 0.35))
gsave(G, "Drum Loops", L("Gospel", 100), loop(100, [(k, "x..x..x...x..x..", 1), (c, "....x.......x...", 0.9), (hat(0.1, 0.025), "x.x.x.x.x.x.x.x.", 0.3)], swing=0.15))

# Pop
G = "pop dance"
k, s, c = kick(0.4, 200, 52, 0.03, 0.15, 0.4, 2), snare(0.3, 200, 0.1, 1800), clap(0.4, 1200, 0.12)
gsave(G, "Kicks", "Pop Kick", k); gsave(G, "Snares", "Pop Snare", s); gsave(G, "Claps", "Pop Clap", c)
gsave(G, "Synths", "Pop Pluck Chord C4", pluck(ch(C4, MAJ), 0.9))
gsave(G, "Bass", "Pop Synth Bass C2", bassline(C2, 0.6, "synth"))
gsave(G, "Piano and Keys", "Pop Piano Chord C4", piano(ch(C4, MAJ), 3.0))
gsave(G, "Drum Loops", L("Pop", 118), loop(118, [(k, "x.......x.......", 1), (s, "....x.......x...", 0.7), (c, "....x.......x...", 0.6), (hat(0.1, 0.03), "..x...x...x...x.", 0.4), (tamb(), "....x.......x...", 0.3)]))

# House
G = "house dance"
k, c, oh = kick(0.45, 220, 50, 0.03, 0.15, 0.4, 2), clap(0.5, 1000, 0.14), hat(0.4, 0.1, 7500)
gsave(G, "Kicks", "House Kick Deep", k); gsave(G, "Claps", "House Clap Wide", c); gsave(G, "Hats", "House Open Hat", oh)
gsave(G, "Bass", "House Organ Bass C2", bassline(C2, 0.8, "organ"))
gsave(G, "Piano and Keys", "House Piano Chord C4", piano(ch(C4, MIN7), 2.5))
gsave(G, "Organ", "House M-Organ Stab C4", organ(ch(C4, MIN7), 0.5, 1.0))
gsave(G, "Drum Loops", L("House", 124), loop(124, [(k, "x...x...x...x...", 1), (c, "....x.......x...", 0.8), (oh, "..x...x...x...x.", 0.4), (shaker(), "xxxxxxxxxxxxxxxx", 0.2)]))

# Techno
G = "techno dance"
k = kick(0.55, 260, 45, 0.025, 0.2, 0.4, 3)
rum = lp(verb(k, 1.6, 0.8, 400)[: int(SR * 240 / 130 / 4)], 300)
gsave(G, "Kicks", "Techno Kick Hard", k); gsave(G, "Kicks", "Techno Rumble", rum)
gsave(G, "Hats", "Techno Hat Metal", hp(hat(0.15, 0.04, 6000) + 0.3 * place(cowbell(1250), int(0.15 * SR)), 5000))
gsave(G, "Synths", "Techno Acid Stab C3", env(np.tanh(4 * lowpass(saw(const(hz(C3), 0.4)), 300 + 5000 * np.exp(-t(0.4) / 0.05))), 0.001, 0.03))
gsave(G + " ambient", "Synths", "Techno Dub Chord C3", *wide(lp(pluck(ch(C3, MIN7), 0.6, 0.2, 2500), 2000), 1.2, 0.4))
gsave(G, "Drum Loops", L("Techno", 130), loop(130, [(k, "x...x...x...x...", 1), (rum, "..x...x...x...x.", 0.6), (hat(0.12, 0.03, 7000), "..x...x...x...x.", 0.45), (clap(0.4, 1200, 0.1), "....x.......x...", 0.5)]))

# Trance
G = "trance edm dance"
k = kick(0.4, 320, 55, 0.02, 0.12, 0.5, 2.5)
gsave(G, "Kicks", "Trance Kick Punchy", k)
gsave(G, "Synths", "Trance Supersaw Chord C4", *wide(supersaw(ch(C4, MIN), 2.0), 1.5, 0.25))
gsave(G, "Synths", "Trance Pluck C4", *wide(pluck([C4, C5], 0.6, 0.18), 1.2, 0.3))
gsave(G + " ambient", "Pads", "Trance Pad C4", *wide(strings(ch(C4, MIN), 5.0, 1.0), 3.0, 0.4))
gsave(G, "Drum Loops", L("Trance", 138), loop(138, [(k, "x...x...x...x...", 1), (hat(0.3, 0.08, 8000), "..x...x...x...x.", 0.45), (clap(), "....x.......x...", 0.5), (hat(0.06, 0.012), "x.xxx.xxx.xxx.xx", 0.15)]))

# DnB
G = "dnb drum and bass jungle"
k, s = kick(0.3, 300, 62, 0.02, 0.09, 0.5, 2), snare(0.25, 230, 0.08, 1500, 0.8)
gsave(G, "Kicks", "DnB Kick Tight", k); gsave(G, "Snares", "DnB Snare Snappy", s)
gsave(G, "Bass", "DnB Reese C2", *wide(env(lp(drive(stack(const(hz(C2), 2.0), 5, 0.01), 2), 700), 0.005, 0.05), 0.6, 0.1))
gsave(G, "Bass", "DnB Sub C1", bassline(24, 1.5, "sub"))
gsave(G + " ambient", "Pads", "DnB Liquid Pad C4", *wide(strings(ch(C4, MAJ9), 5.0, 0.8), 3.0, 0.45))
gsave(G, "Drum Loops", L("DnB", 174), loop(174, [(k, "x.........x.....x.x.......x.....", 1), (s, "....x.......x.......x..o....x..o", 0.9), (hat(0.08, 0.02), "x.x.x.x.x.x.x.x.", 0.35), (ride(0.8), "..x...x...x...x.", 0.2)]))

# Dubstep
G = "dubstep edm bass"
k, s = kick(0.4, 250, 50, 0.025, 0.15, 0.5, 3), snare(0.45, 190, 0.18, 1200, 0.8)
gsave(G, "Kicks", "Dubstep Kick", k); gsave(G, "Snares", "Dubstep Snare Big", verb(s, 0.8, 0.25)[: int(0.7 * SR)])
gsave(G, "Bass", "Dubstep Wobble C1", wobble(24, 240 / 140, 140 / 60 * 2))
gsave(G, "Bass", "Dubstep Growl C1", env(np.tanh(6 * lowpass(saw(const(hz(24), 1.0)) * (1 + 0.5 * square(const(hz(24) * 2.01, 1.0))), 400 + 2500 * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * t(1.0))))), 0.003, 0.05))
gsave(G, "Drum Loops", L("Dubstep", 140), loop(140, [(k, "x.........x.....x...........x...", 1), (s, "........x...............x.......", 0.9), (hat(0.08, 0.02), "x.x.x.x.x.x.x.x.", 0.3)]))

# Synthwave
G = "synthwave retro 80s"
k, s = kick(0.4, 180, 50, 0.03, 0.15, 0.3, 2), gated_snare()
gsave(G, "Kicks", "Synthwave Kick", k); gsave(G, "Snares", "Synthwave Gated Snare", s)
gsave(G, "Toms", "Synthwave Tom C3", verb(tom(C3, 0.3), 1.0, 0.3)[: int(1.2 * SR)])
gsave(G, "Synths", "Synthwave Arp Pluck C3", pluck([C3], 0.4, 0.12, 4000))
gsave(G, "Pads", "Synthwave Pad C4", *wide(lp(supersaw(ch(C4, MAJ7), 5.0), 1800), 2.5, 0.35))
gsave(G, "Bass", "Synthwave Bass C2", bassline(C2, 0.3, "synth"))
gsave(G, "Drum Loops", L("Synthwave", 100), loop(100, [(k, "x.......x.......", 1), (s, "....x.......x...", 0.8), (hat(0.1, 0.03), "x.x.x.x.x.x.x.x.", 0.3)]))

# Reggaeton (dembow)
G = "reggaeton latin dembow"
k, s, rim = kick(0.4, 200, 52, 0.03, 0.14, 0.4, 2), snare(0.25, 220, 0.08, 1800), snare(0.06, 900, 0.008, 3000, 1.0)
gsave(G, "Kicks", "Reggaeton Kick", k); gsave(G, "Snares", "Reggaeton Snare", s); gsave(G, "Percussion", "Reggaeton Rim", rim)
gsave(G, "Synths", "Reggaeton Pluck C4", pluck(ch(C4, MIN), 0.5, 0.15))
gsave(G, "Drum Loops", L("Reggaeton", 95), loop(95, [(k, "x...x...x...x...", 1), (s, "...x..x....x..x.", 0.8), (rim, "...x..x....x..x.", 0.4), (hat(0.08, 0.02), "x.x.x.x.x.x.x.x.", 0.25)]))

# Afrobeats
G = "afrobeats afro"
k, s, sh, cg = kick(0.35, 190, 70, 0.03, 0.1, 0.15, 1.3), snare(0.08, 700, 0.012, 2500, 1.0), shaker(0.12, 0.03), conga(64)
gsave(G, "Kicks", "Afrobeats Kick", k); gsave(G, "Percussion", "Afrobeats Rim", s); gsave(G, "Percussion", "Afrobeats Shaker", sh)
gsave(G + " world", "Percussion", "Afrobeats Conga", cg)
gsave(G, "Guitar", "Afrobeats Highlife Guitar C4", ks(C4 + 7, 1.2, 0.995, 0.7))
gsave(G, "Synths", "Afrobeats Log Pluck C3", env((osc(const(hz(C3), 0.6)) + 0.4 * osc(const(hz(C3) * 3.1, 0.6)) * np.exp(-t(0.6) / 0.04)) * np.exp(-t(0.6) / 0.15), 0.001, 0.03))
gsave(G, "Drum Loops", L("Afrobeats", 105), loop(105, [(k, "x......x..x.....", 1), (s, "...x..x....x..x.", 0.6), (sh, "xoxoxoxoxoxoxoxo", 0.35), (cg, "......x.x.....x.", 0.5)], swing=0.08))

# Amapiano
G = "amapiano afro house"
k, sh, cl = kick(0.4, 180, 55, 0.03, 0.13, 0.2, 1.5), shaker(0.1, 0.025), clap(0.3, 1500, 0.06)
gsave(G, "Kicks", "Amapiano Kick", k); gsave(G, "Percussion", "Amapiano Shaker", sh); gsave(G, "Claps", "Amapiano Clap", cl)
logd = env(np.tanh(3 * (osc(hz(C2) * (1 + 0.8 * np.exp(-t(1.0) / 0.025))) + 0.5 * osc(const(hz(C2) * 2.76, 1.0)) * np.exp(-t(1.0) / 0.06))) * np.exp(-t(1.0) / 0.4), 0.001, 0.05)
gsave(G, "World", "Amapiano Log Drum Deep C2", logd)
gsave(G, "Piano and Keys", "Amapiano Piano Chord C4", piano(ch(C4, MIN9), 3.0))
gsave(G, "Drum Loops", L("Amapiano", 113), loop(113, [(k, "x...x...x...x...", 1), (sh, "xxxxxxxxxxxxxxxx", 0.25), (cl, "....x.......x...", 0.5), (logd, "......x...x..x..", 0.6)], swing=0.06))

# Dancehall
G = "dancehall reggae caribbean"
k, rim = kick(0.35, 190, 58, 0.03, 0.12, 0.3, 2), snare(0.07, 800, 0.01, 2800, 1.0)
gsave(G, "Kicks", "Dancehall Kick", k); gsave(G, "Percussion", "Dancehall Rim", rim)
gsave(G, "Synths", "Dancehall Stab C4", env(lp(sum(square(const(hz(n_), 0.3)) for n_ in ch(C4, MIN)), 3000) * np.exp(-t(0.3) / 0.08), 0.001, 0.02))
gsave(G, "Bass", "Dancehall Bass C2", bassline(C2, 0.8, "sub"))
gsave(G, "Drum Loops", L("Dancehall", 95), loop(95, [(k, "x.....x...x.....", 1), (rim, "...x..x....x..x.", 0.7), (hat(0.08, 0.02), "x.x.x.x.x.x.x.x.", 0.25)]))

# Reggae (one drop)
G = "reggae dub roots"
k, rim = lp(kick(0.4, 140, 55, 0.04, 0.16, 0.1, 1.3), 3000), snare(0.07, 750, 0.012, 2500, 1.0)
gsave(G, "Kicks", "Reggae Kick", k); gsave(G, "Percussion", "Reggae Cross Stick", rim)
gsave(G, "Guitar", "Reggae Skank Chord C4", hp(strum(ch(C4, MAJ) + [C4 + 12], 0.3, 0.006, damp=0.985, bright=0.6), 500))
gsave(G, "Bass", "Reggae Bass C2", lp(bassline(C2, 1.2, "finger"), 600))
gsave(G + " dub", "FX", "Dub Siren", env(osc(const(600, 3.0) * (1 + 0.5 * square(const(6, 3.0)) * np.linspace(1, 0.2, int(3 * SR)))), 0.01, 0.2))
gsave(G, "Drum Loops", L("Reggae", 75), loop(75, [(k, "........x.......", 1), (rim, "........x.......", 0.8), (hat(0.1, 0.03), "x.xox.xox.xox.xo", 0.3)], swing=0.15))

# Latin
G = "latin bossa world"
lo, hi, cv = conga(57, 0.22), conga(64), clave()
gsave(G, "Percussion", "Latin Conga Low", lo); gsave(G, "Percussion", "Latin Conga High", hi); gsave(G + " salsa", "Percussion", "Latin Clave", cv)
gsave(G, "Percussion", "Latin Guiro", env(bp(noise(0.35), 1500, 5000) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 40 * t(0.35)))), 0.005, 0.05))
gsave(G, "Guitar", "Latin Nylon Guitar C4", strum(ch(C3 + 12, MAJ7), 2.0, 0.02, damp=0.995, bright=0.4, soft=0.5))
gsave(G, "Drum Loops", L("Latin", 100), loop(100, [(cv, "x..x..x...x.x...", 0.6), (hi, "..x.......x..x..", 0.7), (lo, "......xx......xx", 0.7), (shaker(), "xoxoxoxoxoxoxoxo", 0.25), (kick(0.35, 150, 60, 0.03, 0.12, 0.1, 1.2), "x..x....x..x....", 0.6)]))

# Salsa
G = "salsa latin"
cb, tb = cowbell(), timbale()
gsave(G, "Percussion", "Salsa Cowbell", cb); gsave(G, "Percussion", "Salsa Timbale", tb)
gsave(G, "Brass", "Salsa Brass Stab C4", brass(ch(C4, MAJ) + [C4 + 12], 0.5))
gsave(G, "Piano and Keys", "Salsa Montuno Piano C4", piano([C4, C4 + 12], 1.5))
gsave(G, "Bass", "Salsa Tumbao Bass C2", bassline(C2, 1.0, "upright"))
gsave(G, "Drum Loops", L("Salsa", 180), loop(180, [(cb, "x.x.x.x.x.x.x.x.", 0.5), (clave(), "x.....x.....x.......x...x.......", 0.5), (conga(64), "......x.......x.", 0.7), (conga(57), "...x.....x.x....", 0.6), (tb, "............x...", 0.4)], steps=16))

# Rock
G = "rock indie"
k, s, cr = kick(0.4, 140, 60, 0.03, 0.18, 0.4, 2.5), lp(snare(0.4, 180, 0.16, 1000, 0.9), 8000), hat(2.0, 0.7, 4500)
gsave(G, "Kicks", "Rock Kick", k); gsave(G, "Snares", "Rock Snare", s); gsave(G, "Cymbals", "Rock Crash", cr)
gsave(G, "Toms", "Rock Floor Tom C2", tom(C2 + 7, 0.35))
power = lambda n_, sec, d: lp(drive(strum([n_, n_ + 7, n_ + 12], sec, 0.008, damp=0.997, bright=0.55), d), 3500)
gsave(G + " punk metal", "Guitar", "Rock Power Chord C3", power(C3, 2.0, 6))
gsave(G, "Bass", "Rock Pick Bass C2", lp(drive(ks(C2, 1.2, 0.996, 0.6), 2), 2000))
gsave(G, "Drum Loops", L("Rock", 120), loop(120, [(k, "x.......x.x.....", 1), (s, "....x.......x...", 0.9), (hat(0.12, 0.035, 6000), "x.x.x.x.x.x.x.x.", 0.4)]))

# Punk
G = "punk rock"
s = snare(0.3, 200, 0.12, 1300, 0.8)
gsave(G, "Snares", "Punk Snare", s)
gsave(G, "Guitar", "Punk Power Chord C3", power(C3, 1.2, 14))
gsave(G, "Drum Loops", L("Punk", 180), loop(180, [(kick(0.35, 150, 60, 0.03, 0.14, 0.4, 2.5), "x...x...", 1), (s, "..x...x.", 0.9), (hat(0.15, 0.05, 5000), "xxxxxxxx", 0.4)], steps=8))

# Metal
G = "metal rock"
k = hp(kick(0.25, 200, 65, 0.015, 0.08, 1.2, 3), 60)
gsave(G, "Kicks", "Metal Kick Click", k)
gsave(G, "Guitar", "Metal Chug E2", lp(drive(ks(40, 0.35, 0.97, 0.6), 20), 2500))
gsave(G, "Guitar", "Metal Chord E2", power(40, 2.0, 25))
gsave(G, "Cymbals", "Metal China", hp(hat(1.5, 0.5, 3000) + 0.4 * place(cowbell(1700), int(1.5 * SR)), 1500))
gsave(G, "Drum Loops", L("Metal", 160), loop(160, [(k, "xxxxxxxxxxxxxxxx", 0.8), (lp(snare(0.3, 190, 0.12, 1100, 0.9), 8000), "....x.......x...", 1), (ride(1.0), "x.x.x.x.x.x.x.x.", 0.3)]))

# Indie
G = "indie rock pop"
gsave(G, "Percussion", "Indie Tambourine", tamb())
gsave(G, "Guitar", "Indie Clean Guitar Chord C4", *wide(strum([C3 + 7, C3 + 12, C3 + 16, C3 + 19, C4 + 12], 2.5, 0.015, damp=0.996, bright=0.6), 1.5, 0.25))
gsave(G, "Synths", "Indie Synth Lead C4", env(lp(square(const(hz(C4), 1.5) * (1 + 0.004 * np.sin(2 * np.pi * 5 * t(1.5)))), 2500), 0.01, 0.1))
gsave(G, "Drum Loops", L("Indie", 110), loop(110, [(kick(0.35, 150, 58, 0.03, 0.15, 0.3, 1.8), "x.....x.x.......", 1), (lp(snare(0.3, 190, 0.12, 1200, 0.8), 6000), "....x.......x...", 0.8), (tamb(), "..x...x...x...x.", 0.35), (hat(0.1, 0.03, 6000), "x.x.x.x.x.x.x.x.", 0.3)]))

# Blues
G = "blues rock"
gsave(G, "Guitar", "Blues Guitar Note C4", lp(drive(ks(C4, 1.8, 0.997, 0.6), 4), 3000))
gsave(G, "Guitar", "Blues Guitar Chord C3", lp(drive(strum([C3, C3 + 7, C3 + 10, C3 + 16], 2.0, 0.015, damp=0.996, bright=0.55), 3), 3000))
gsave(G + " country folk", "Woodwinds", "Blues Harmonica C4", reed(C4, 2.0))
gsave(G, "Drum Loops", L("Blues", 90), loop(90, [(kick(0.35, 140, 58, 0.03, 0.14, 0.2, 1.5), "x.....x.....", 1), (lp(snare(0.3, 190, 0.12, 1200, 0.8), 6000), "...x.....x..", 0.8), (ride(1.2), "x.xx.xx.xx.x", 0.25)], steps=12))

# Country
G = "country folk"
gsave(G, "Guitar", "Country Twang Guitar C4", ks(C4, 1.5, 0.996, 0.8))
gsave(G, "Guitar", "Country Banjo C4", hp(ks(C4 + 12, 1.0, 0.99, 0.85), 400))
gsave(G, "Guitar", "Country Acoustic Strum C4", strum([C3, C3 + 4, C3 + 7, C3 + 12, C3 + 16, C3 + 24], 2.5, 0.012, damp=0.996, bright=0.6))
gsave(G, "Snares", "Country Brush Snare", brush())
gsave(G, "Drum Loops", L("Country", 110), loop(110, [(kick(0.35, 140, 58, 0.03, 0.14, 0.2, 1.5), "x.......x.......", 1), (brush(), "xoxoxoxoxoxoxoxo", 0.5), (snare(0.06, 900, 0.008, 3000, 1.0), "....x.......x...", 0.6)]))

# Folk
G = "folk acoustic indie"
st, cl = stomp(), clap(0.3, 1100, 0.08)
gsave(G, "Kicks", "Folk Stomp", st); gsave(G, "Claps", "Folk Hand Clap", cl)
gsave(G, "Guitar", "Folk Acoustic Strum C4", strum([C3 + 7, C3 + 12, C3 + 16, C3 + 19, C4 + 12], 2.5, 0.02, damp=0.996, bright=0.5, soft=0.3))
gsave(G, "Strings", "Folk Fiddle C4", env(lp(saw(const(hz(C4), 2.0) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t(2.0)))), 3500), 0.08, 0.2))
gsave(G, "Drum Loops", L("Folk", 100), loop(100, [(st, "x.......x.......", 1), (cl, "....x.......x...", 0.7), (tamb(), "..x...x...x...x.", 0.3)]))

# Jazz
G = "jazz swing"
br, rd = brush(), ride()
gsave(G, "Snares", "Jazz Brush Snare", br); gsave(G, "Cymbals", "Jazz Ride", rd)
gsave(G, "Bass", "Jazz Upright Bass C2", bassline(C2, 1.5, "upright"))
gsave(G, "Piano and Keys", "Jazz Piano Chord C4", piano([C3 + 10, C4 + 3, C4 + 7, C4 + 14], 3.0))
gsave(G + " soul", "Saxophone", "Jazz Sax C4", reed(C4, 2.0, 0.12, 1800))
gsave(G, "Drum Loops", L("Jazz", 120), loop(120, [(rd, "x..x.xx..x.x", 0.5), (br, "x.....x.....", 0.4), (hat(0.08, 0.02, 7000), "...x.....x..", 0.3), (kick(0.3, 120, 55, 0.03, 0.12, 0.1, 1.2), "x...........", 0.4)], steps=12))

# Funk
G = "funk soul disco"
s = snare(0.2, 230, 0.06, 2000, 0.8)
gsave(G, "Snares", "Funk Snare Tight", s)
gsave(G, "Guitar", "Funk Guitar Chank C4", hp(strum([C3 + 10, C4 + 4, C4 + 7, C4 + 14], 0.2, 0.004, damp=0.97, bright=0.7), 600))
gsave(G, "Bass", "Funk Slap Bass C2", bassline(C2, 0.8, "slap"))
gsave(G, "Brass", "Funk Horn Stab C4", brass([C4, C4 + 4, C4 + 10], 0.35))
gsave(G, "Drum Loops", L("Funk", 100), loop(100, [(kick(0.35, 170, 58, 0.03, 0.12, 0.3, 1.8), "x.x.......x..x..", 1), (s, "....x..o.o..x...", 0.85), (hat(0.08, 0.02, 7000), "xxxxxxxxxxxxxxxx", 0.3)], swing=0.05))

# Lo-fi
G = "lo-fi chill hip hop"
crk = lp((rng.uniform(0, 1, int(SR * 2)) > 0.9993) * rng.uniform(-1, 1, int(SR * 2)), 6000) * 4 + hp(noise(2), 2000) * 0.008
k, s = lp(kick(0.35, 130, 55, 0.04, 0.12, 0.05, 1.1), 3000), lp(snare(0.3, 180, 0.1, 1000, 0.7), 3500)
gsave(G, "Kicks", "Lo-fi Kick", k); gsave(G, "Snares", "Lo-fi Snare", s)
wob = 1 + 0.004 * np.sin(2 * np.pi * 0.7 * t(3.0))
gsave(G, "Piano and Keys", "Lo-fi Keys Chord C4", lp(env(sum(osc(const(hz(n_), 3.0) * wob) * np.exp(-t(3.0) / 1.0) for n_ in ch(C4, MAJ9)), 0.003, 0.1), 2200) + place(crk, int(3 * SR)) * 0.3)
gsave(G, "Guitar", "Lo-fi Guitar Chord C4", lp(strum([C3 + 7, C3 + 11, C3 + 14, C3 + 16], 2.0, 0.025, damp=0.995, bright=0.4, soft=0.5), 2500))
gsave(G, "Drum Loops", L("Lo-fi", 80), loop(80, [(k, "x.......x.x.....", 1), (s, "....x.......x...", 0.8), (lp(hat(0.1, 0.03, 6000), 8000), "x.x.x.x.x.x.x.x.", 0.3), (crk, "x...............", 0.6)], swing=0.18))

# Classical
G = "classical orchestral cinematic"
gsave(G, "Strings", "Classical String Ensemble C4", *wide(strings(ch(C3, MAJ) + [C4], 5.0), 2.5, 0.35))
gsave(G, "Strings", "Classical Pizzicato C4", verb(ks(C4, 0.6, 0.99, 0.45, 0.4), 1.5, 0.3)[: int(1.6 * SR)])
gsave(G, "Strings", "Classical Cello C3", env(lp(stack(const(hz(C3), 3.0) * (1 + 0.005 * np.sin(2 * np.pi * 5 * t(3.0))), 3, 0.004), 1500), 0.2, 0.3))
gsave(G, "Percussion", "Classical Timpani C2", verb(tom(C2 + 7, 0.6), 2.0, 0.3)[: int(2.5 * SR)])
gsave(G, "Piano and Keys", "Classical Grand Piano C4", piano([C4], 4.0))
gsave(G, "Woodwinds", "Classical Flute C5", flute(C5, 2.5))

# Cinematic
G = "cinematic trailer score"
gsave(G, "FX", "Cinematic Braam C2", *wide(env(np.tanh(3 * lowpass(stack(const(hz(C2), 4.0), 5, 0.01) + stack(const(hz(C3), 4.0), 5, 0.01), 200 + 2000 * np.minimum(1, t(4.0) / 0.5) * np.exp(-t(4.0) / 2))), 0.05, 0.8), 3.0, 0.35))
hit = taiko()
gsave(G + " world", "Percussion", "Cinematic Taiko", hit)
gsave(G, "FX", "Cinematic Hit", verb(np.tanh(3 * (kick(0.8, 120, 35, 0.05, 0.4, 0.5, 3) + lp(noise(0.8), 3000) * np.exp(-t(0.8) / 0.1))), 3.0, 0.4)[: int(3.5 * SR)])
gsave(G, "Strings", "Cinematic Staccato Strings C3", env(lp(stack(const(hz(C3), 0.25), 5, 0.006), 2500) * np.exp(-t(0.25) / 0.08), 0.005, 0.03))
gsave(G, "Drum Loops", L("Cinematic", 90), loop(90, [(hit, "x.....x...x.....", 1), (taiko(48), "....x.......x.x.", 0.6), (frame_drum(), "xx.xxx.xxx.xxx.x", 0.3)]))

# Ambient
G = "ambient chill cinematic"
gsave(G, "Pads", "Ambient Drone C3", *wide(env(lp(stack(const(hz(C3), 8.0), 3, 0.003) + stack(const(hz(C3 + 7), 8.0), 3, 0.003), 600) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t(8.0))), 1.5, 2.0), 4.0, 0.5))
gsave(G, "Pads", "Ambient Shimmer Pad C4", *wide(env(sum(osc(const(hz(n_), 8.0) * (1 + 0.002 * np.sin(2 * np.pi * (0.13 + 0.05 * i) * t(8.0)))) for i, n_ in enumerate([C4, C4 + 7, C5, C5 + 4, C5 + 12])), 2.0, 2.5), 3.5, 0.6, 9000))
gsave(G, "Mallets and Bells", "Ambient Glass Bell C5", *wide(bell(C5, 3.0, 2.0), 3.0, 0.45, 9000))
gsave(G, "FX", "Ambient Wind Texture", *wide(env(lowpass(noise(8), 400 + 600 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.15 * t(8.0)))), 1.5, 2.0), 3.0, 0.3))

# World
G = "world folk afro"
gsave(G, "World", "World Steel Drum C4", steel(C4))
gsave(G, "World", "World Kalimba C4", kalimba(C4))
fd = frame_drum()
gsave(G, "World", "World Frame Drum", fd)
gsave(G, "World", "World Udu", env(osc(hz(C2 + 12) * (1 + 0.6 * (1 - np.exp(-t(0.6) / 0.05)))) * np.exp(-t(0.6) / 0.15), 0.005, 0.03))
gsave(G, "Woodwinds", "World Pan Flute C5", flute(C5, 2.0) + bp(noise(2.0), 2000, 8000) * 0.04)
gsave(G, "Drum Loops", L("World", 100), loop(100, [(fd, "x..x..x...x.x...", 1), (conga(64), "..x...x...x...xx", 0.5), (shaker(), "xoxoxoxoxoxoxoxo", 0.25)]))

import json
json.dump(TAGS, open(os.path.join(out, "genres.json"), "w"), indent=0)
print("made", sum(len(f) for _, _, f in os.walk(out)) - 1, "sounds,", len(TAGS), "in genre kits")
