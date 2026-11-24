# 内部構造と改造ガイド

模様・質感・仕上げ・音を変える依頼、または不具合が出たときに読む。題材やカメラは `scenes.md`。

## ファイル

| ファイル | 役割 |
|---|---|
| `scripts/lib/common.glsl` | uniform、乱数、配色、魚眼の射影、テック面（`techHeight` / `techEmission`） |
| `scripts/lib/main.glsl` | レイマーチ、法線、遮蔽、映り込み、霧。RGBにHDRの色、Aに奥行きを書く |
| `scripts/lib/post.glsl` | モーションブラー、色収差、ブルーム、ACESトーンマップ、彩度、ビネット、粒子 |
| `scripts/scenes/*.glsl` | 題材ごとの形とカメラ |
| `scripts/render.js` | Playwright同梱のChromiumで1枚ずつPNGに描く（GPUがあれば使い、無ければSwiftShader）。`renderFrame(t)` に秒を渡すのでコマ落ちしない |
| `scripts/audio.py` | キック・ハット・クラップ・ベース・アルペジオ・パッド・ライザーを合成して48kHzのWAVにする |
| `scripts/build.py` | preview / render / finish の進行役 |
| `scripts/defaults.json` `palettes.json` | 既定値と配色 |

## 滑らかさと実在感を作っている部分

- **線の描き方**（`ln`）：1ピクセルより細くなる線は、太らせた分だけ暗くする。遠くの線がちらつかず、奥へ行くほど自然に霞む
- **照り返し**（`hal`）：線のまわりに指数的に落ちる光を足し、遮蔽（`ao`）を掛ける。線が壁を照らして見える
- **区画ごとの主色と密度**（`zoneOf`）：大きな板ごとに色を寄せ、暗い板・普通の板・密な板を混ぜる。大小の対比が出る
- **映り込み**：1回反射。当たらなければ `background` を映す。見る角度が浅いほど強くなる（フレネル）
- **モーションブラー**：1パス目がAに奥行きを書き、`post.glsl` が各画素の点をシャッターが開いた時点のカメラへ投影し直して、その向きに14回サンプルする。カメラの動きにだけ効くので、点滅や光の波はぼけない
- **ブルーム**：1パス目のテクスチャのミップマップ6段を足すだけ。ぼかし用のパスを持たないので速い
- **重ね描き**（`quality.samples`）：サブピクセルをずらして複数回描き、加算で平均する。段差の輪郭のギザギザが取れる
- **無劣化の中間フレーム**：PNGで書き出し、最後に一度だけH.264に圧縮する。細い線の多い絵は圧縮で崩れやすいので、`crf` は preset ごとに低め（20/17/16）にしてある
- **ブルームのならし**（`mipTap`）：ミップ各段を4点で読んで四角いムラを消す。解像度が変わってもにじみの幅が同じに見えるよう、段を `log2(高さ/720)` だけずらす

## よくある改造

| 依頼 | 変える場所 |
|---|---|
| 模様の層を足す | `techEmission()` にブロックを1つ追加。格子のID→`h21`で乱数→`ln()`で形→`EC()`で色→必要なら `hal` にも足す。六角格子、文字風のバー、矢印など |
| ある層を消す・弱める | 該当ブロックの最後の係数を下げる |
| 線を細く・太く | 各層の `ln(d, 幅, px)` の幅。`halo` にも同じ値を渡す |
| 照り返しを強く | 各層の `hal+=` の係数（0.04〜0.05）、広がりは `halo()` の `w*7.0` |
| 段差を大きく | シーン側の `techHeight(uv)*係数`。上げたら `march()` の歩幅係数 `0.7` を `0.55` へ |
| 板の大きさを変える | `zoneOf` の `LZ`（長さ）と `nA`（一周の分割数）、`cellOf` の `lz` と `nB` |
| 霧・奥行き感 | シーンの `FOG` と `haze()` |
| 映り込みを鏡のように | `main.glsl` の `fres` の下限 `0.07` を上げる |
| 拍の演出を変える | `main.glsl` の `wave`、`post.glsl` の `kick`。4拍ごとに切り替えるなら `floor(uBeat/4.0)` |
| ループ素材にする | 完全な継ぎ目なしは難しい。末尾1秒を先頭にクロスフェードで重ねる（ffmpeg `xfade`）か、黒フェードで割り切る |
| 文字やロゴを置く | シェーダーには入れず、finish後に ffmpeg で重ねる。黒の半透明の板を敷くと読める |
| 音のフレーズ | `audio.py` の `scale`（音階）、`prog`（小節ごとの根音）、`arp`。テンポは `bpm`、高さは `audio.root`（MIDI番号） |
| 新しい音のスタイル | `style` の分岐を足す。映像の拍と合うよう、発音は `b * beat` を基準に置く |

## 不具合の直し方

- 真っ黒：コンパイルエラーなら `render.js` がメッセージを出して終了コード2で止まる。エラーなしで黒いときは、カメラが物体の内側にいないか（`map(ro)` が負）、`FAR` が足りているかを見る
- 白っぽい：`look.bloom` を0.6へ、次に `look.exposure` を0.8へ、それでも駄目なら `look.density` を下げる
- 色が薄い：`look.saturation` を1.5まで
- 壁に筋や穴：レイの突き抜け。`march()` の歩幅係数を下げ、シーンの `STEPS` を上げる
- 遠くがちらつく：シーンの `surfEmission` で `px` をuvの単位に直しているか確かめる。合っていれば `quality.preset` を high へ
- 外周が流れすぎて読めない：`quality.shutter` を0.25へ。`post.glsl` の上限 `0.16` を下げてもよい
- 物体の輪郭にブラーのにじみ：奥行きの境目で起きる。`quality.shutter` を下げるか、カメラを遅くする
- `hdr=false` と表示される：浮動小数テクスチャが使えない環境。動きはするがブルームが弱い。`look.bloom` 1.5、`look.exposure` 1.2へ
- 遅い：`quality.preset` を standard に戻す。さらに `look.reflect`: 0 で1〜2割、シーンの `STEPS` を下げる。`renderer:` の表示が SwiftShader ならソフトウェア描画なので、GPUのあるマシンで回すのが一番効く
- GPUで描いたら絵が崩れる・真っ黒：`node scripts/render.js ... --software` でソフトウェア描画に固定する

## 環境

- Node と Playwright（グローバルにあればそれを使う）。Chromium は `/opt/pw-browsers/chromium-*/` を自動で探す。無ければ `npm i playwright`
- GPUが無いときは起動引数 `--use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist` に自動で切り替わり、WebGL2がソフトウェアで動く
- Python は numpy と scipy、あとは ffmpeg
