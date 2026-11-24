#!/usr/bin/env python3
"""ネオン・テック映像の一連の作業をまとめる。
  python3 build.py preview CONFIG WORK        6コマを半解像度で描いて WORK/preview.jpg にする（約20秒）
  python3 build.py render  CONFIG WORK        全フレームを描く。240秒で区切って終了するので「完了」と出るまで繰り返す
                                             （--budget 秒 で区切りを変えられる。描画済みのコマは飛ばす）
  python3 build.py finish  CONFIG WORK OUT    音を作り、MP4にまとめ、確認用の一覧画像と数値を出す
"""
import sys, os, json, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))

def merge(a, b):
    o = dict(a)
    for k, v in (b or {}).items():
        o[k] = merge(a.get(k, {}), v) if isinstance(v, dict) else v
    return o

def load(p):
    cfg = merge(json.load(open(os.path.join(HERE, 'defaults.json'))), json.load(open(p)))
    q = cfg['quality']; pre = cfg['presets'][q.get('preset', 'standard')]
    cfg['fps'] = cfg.get('fps') or q.get('fps') or pre['fps']   # render.js と同じ決め方
    return cfg
def sh(cmd, **kw): return subprocess.run(cmd, check=True, **kw)

def main():
    if len(sys.argv) < 4: print(__doc__); sys.exit(1)
    mode, cfgp, work = sys.argv[1:4]
    cfg = load(cfgp); os.makedirs(work, exist_ok=True)
    total = round(cfg['duration'] * cfg['fps']); frames = os.path.join(work, 'frames')
    extra = sys.argv[5:] if mode == 'finish' else sys.argv[4:]   # --scene / --post をrender.jsへ渡せる
    if mode == 'preview':
        prev = os.path.join(work, 'preview'); subprocess.run(['rm', '-rf', prev])
        ids = ','.join(str(int(i * (total - 1) / 5)) for i in range(6))
        sh(['node', os.path.join(HERE, 'render.js'), cfgp, '--out', prev, '--frames', ids, '--scale', '0.5'] + extra)
        sh(['ffmpeg', '-v', 'error', '-y', '-pattern_type', 'glob', '-i', prev + '/*.png', '-vf', 'tile=3x2', os.path.join(work, 'preview.jpg')])
        print('preview:', os.path.join(work, 'preview.jpg'))
    elif mode == 'render':
        # 裏実行は呼び出しが終わると止められる環境があるので、時間で区切って前面で描く。終わるまで繰り返し呼ぶ
        budget = '240'
        if '--budget' in extra: i = extra.index('--budget'); budget = extra[i + 1]; del extra[i:i + 2]
        sh(['node', os.path.join(HERE, 'render.js'), cfgp, '--out', frames, '--budget', budget] + extra)
        n = len(glob.glob(frames + '/f_*.png'))
        print(f'{n}/{total} frames' + ('  全フレーム完了。finish へ' if n >= total else '  まだ残りあり。同じコマンドをもう一度'))
    elif mode == 'finish':
        out = sys.argv[4]
        n = len(glob.glob(frames + '/f_*.png'))
        if n < total: print(f'まだ {n}/{total} フレーム。描画が終わってから実行する'); sys.exit(2)
        cmd = ['ffmpeg', '-v', 'error', '-y', '-framerate', str(cfg['fps']), '-i', frames + '/f_%05d.png']
        if cfg['audio'].get('enabled', True):
            wav = os.path.join(work, 'audio.wav'); sh(['python3', os.path.join(HERE, 'audio.py'), cfgp, wav])
            cmd += ['-i', wav, '-c:a', 'aac', '-b:a', '192k', '-shortest']
        crf = cfg.get('crf', cfg['presets'][cfg['quality'].get('preset', 'standard')]['crf'])
        vf = f"fade=t=in:st=0:d=0.15,fade=t=out:st={cfg['duration'] - 0.25:.2f}:d=0.25"
        cmd += ['-vf', vf, '-c:v', 'libx264', '-crf', str(crf), '-preset', 'slow', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart', out]
        sh(cmd)
        sheet = os.path.join(work, 'sheet.jpg')
        step = max(cfg['duration'] / 10.0, 0.1)
        sh(['ffmpeg', '-v', 'error', '-y', '-i', out, '-vf', f'fps=1/{step:.3f},scale=270:-1,tile=5x2', '-frames:v', '1', sheet])
        # 白飛び・真っ暗の検出：平均輝度が飛び抜けたフレームがないかを数値で見る
        r = subprocess.run(['ffmpeg', '-v', 'error', '-i', out, '-vf', 'signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-', '-an', '-f', 'null', '-'], capture_output=True, text=True)
        ys = [float(l.split('=')[1]) for l in r.stdout.splitlines() if 'YAVG' in l]
        if ys:
            print(f'平均輝度 min={min(ys):.1f} max={max(ys):.1f} mean={sum(ys) / len(ys):.1f}（目安: 25〜90。100超は白飛び気味、15未満は暗すぎ）')
        if os.path.getsize(out) > 30e6: print(f'30MBを超えた（crf={crf}）。渡せないときは config に "crf": {crf + 4} を足して finish をやり直す')
        print(f'video: {out}  ({os.path.getsize(out) / 1e6:.1f} MB)\nsheet: {sheet}')
    else:
        print(__doc__); sys.exit(1)

if __name__ == '__main__':
    main()
