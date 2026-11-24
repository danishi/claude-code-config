#!/usr/bin/env python3
"""映像と同じBPMで鳴るオリジナルの電子音トラックを数式だけで合成する。
使い方: python3 audio.py config.json out.wav
style: drive（四つ打ち）/ ambient（ビートなし）
既存曲のメロディやフレーズはなぞらない。音列は seed から作る。"""
import sys, json, os
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000

def merge(a, b):
    o = dict(a)
    for k, v in (b or {}).items():
        o[k] = merge(a.get(k, {}), v) if isinstance(v, dict) else v
    return o

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def lp(x, fc, q=0.707):
    b, a = signal.iirfilter(2, min(fc, SR * 0.45) / (SR / 2), btype='low', ftype='butter'); return signal.lfilter(b, a, x)
def hp(x, fc):
    b, a = signal.iirfilter(2, fc / (SR / 2), btype='high', ftype='butter'); return signal.lfilter(b, a, x)

def saw(f, n, ph=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + ph) % 1.0) - 1

def place(buf, x, t0, gain=1.0, pan=0.0):
    i = int(round(t0 * SR))
    if i >= buf.shape[0]: return
    n = min(len(x), buf.shape[0] - i)
    buf[i:i + n, 0] += x[:n] * gain * np.sqrt(0.5 * (1 - pan))
    buf[i:i + n, 1] += x[:n] * gain * np.sqrt(0.5 * (1 + pan))

def kick():
    n = int(0.42 * SR); t = np.arange(n) / SR
    f = 46 + 110 * np.exp(-t * 34)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    x += hp(np.random.randn(n), 3000) * np.exp(-t * 240) * 0.25
    return np.tanh(x * 1.8)

def hat(open_=False):
    n = int((0.22 if open_ else 0.05) * SR); t = np.arange(n) / SR
    return hp(np.random.randn(n), 7500) * np.exp(-t * (16 if open_ else 80))

def clap():
    n = int(0.25 * SR); t = np.arange(n) / SR
    env = sum(np.exp(-np.maximum(t - d, 0) * 60) * (t >= d) for d in (0, 0.011, 0.023)) / 3
    b, a = signal.butter(2, [900 / (SR / 2), 3800 / (SR / 2)], btype='band')
    return signal.lfilter(b, a, np.random.randn(n)) * env * 3

def pluck(m, dur, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    x = saw(f, n) + saw(f * 1.006, n, 0.3) + 0.5 * np.sign(np.sin(2 * np.pi * f * 2 * t))
    x = lp(x, 900 + 4200 * bright)
    return x * np.exp(-t * 14) * 0.5

def bass(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = mtof(m)
    x = saw(f, n) * 0.7 + np.sin(2 * np.pi * f * t)
    return lp(x, 420) * np.minimum(t * 200, 1) * np.exp(-t * 5)

def pad(notes, dur):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for m in notes:
        for det in (-0.07, 0.0, 0.08):
            x += saw(mtof(m + det), n, np.random.rand())
    x = lp(x, 1400) / (len(notes) * 3)
    return x * np.minimum(t / 0.6, 1) * np.minimum((dur - t) / 0.6, 1)

def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.random.randn(n); out = np.zeros(n); blk = 2048
    for i in range(0, n, blk):   # フィルタを開きながら上がるノイズ
        fc = 300 * (40 ** (i / n))
        b, a = signal.butter(2, [fc * 0.7 / (SR / 2), min(fc * 1.4, SR * 0.45) / (SR / 2)], btype='band')
        out[i:i + blk] = signal.lfilter(b, a, x[i:i + blk])
    return out * (t / dur) ** 2

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cfg = merge(json.load(open(os.path.join(here, 'defaults.json'))), json.load(open(sys.argv[1])))
    out = sys.argv[2]
    dur, bpm, seed = float(cfg['duration']), float(cfg['bpm']), int(cfg['seed'])
    au = cfg['audio']; style = au.get('style', 'drive'); root = int(au.get('root', 41))
    rng = np.random.default_rng(seed); np.random.seed(seed)
    beat = 60.0 / bpm; nb = int(np.ceil(dur / beat))
    N = int(dur * SR)
    drums = np.zeros((N, 2)); music = np.zeros((N, 2))
    scale = [0, 3, 5, 7, 10, 12, 15]            # マイナーペンタ系
    arp = [int(rng.choice(scale)) for _ in range(16)]
    prog = [0, 0, -4, -2]                        # 小節ごとのベース音の動き
    K, H, OH, C = kick(), hat(), hat(True), clap()
    for b in range(nb):
        t0 = b * beat; bar = b // 4; r = root + prog[bar % 4]
        if style == 'drive':
            place(drums, K, t0, 0.95)
            if b % 2 == 1: place(drums, C, t0, 0.35, 0.1)
            for s in range(4):
                place(drums, H, t0 + s * beat / 4, 0.16 if s % 2 else 0.10, -0.2 if s % 2 else 0.2)
            place(drums, OH, t0 + beat / 2, 0.18, 0.15)
            place(music, bass(r - 12, beat * 0.45), t0 + beat / 2, 0.8)       # 裏拍ベース
            place(music, bass(r - 12, beat * 0.2), t0 + beat * 0.75, 0.5)
        for s in range(4):                                                    # 16分のアルペジオ
            i = (b * 4 + s) % 16
            bright = 0.25 + 0.75 * min(1.0, (t0 + s * beat / 4) / max(dur * 0.7, 1e-6))  # 終盤に向けて明るく
            g = (0.30 if style == 'drive' else 0.34) * (1.0 if s % 2 == 0 else 0.7)
            place(music, pluck(r + 24 + arp[i], beat * 0.5, bright), t0 + s * beat / 4, g, 0.5 * np.sin(i * 1.3))
        if b % 4 == 0:
            place(music, pad([r + 12, r + 15, r + 19, r + 22], min(beat * 4, dur - t0)), t0, 0.95 if style == 'ambient' else 0.30)
    # 16分付点のディレイで広げる
    d = int(beat * 0.75 * SR)
    if d < N:
        wet = np.zeros_like(music); wet[d:] = music[:-d][:, ::-1] * 0.32
        if 2 * d < N: wet[2 * d:] += music[:-2 * d] * 0.14
        music += wet
    # キックに合わせて音楽を引っ込める（サイドチェイン）
    if style == 'drive':
        t = np.arange(N) / SR
        duck = 1 - 0.6 * np.exp(-((t % beat) / beat) * 6)
        music *= duck[:, None]
    # 最後の1小節に向けて上がるノイズと、頭の一発
    rl = min(beat * 4, dur * 0.5); rz = riser(rl)
    place(music, rz, dur - rl, 0.5, 0.0)
    n = int(1.2 * SR); tt = np.arange(n) / SR
    place(music, np.sin(2 * np.pi * np.cumsum(60 - 28 * tt / 1.2) / SR) * np.exp(-tt * 3), 0, 0.7 if style == 'drive' else 0.35)
    mix = drums + music
    mix = hp(mix.T, 28).T
    mix = np.tanh(mix * 1.3)
    f = int(0.012 * SR); mix[:f] *= np.linspace(0, 1, f)[:, None]
    fo = int(0.25 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.89
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    # 耳で確かめられないので、1秒ごとのRMSを出して数値で見る
    rms = [20 * np.log10(np.sqrt(np.mean(mix[i:i + SR] ** 2)) + 1e-9) for i in range(0, N, SR)]
    print('RMS dBFS/sec:', ' '.join(f'{v:.1f}' for v in rms))
    print(f'wrote {out}  {dur:.2f}s  bpm={bpm:g} style={style}')

if __name__ == '__main__':
    main()
