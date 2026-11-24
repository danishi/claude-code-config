---
name: live-photo
description: >
  iPhone の Live Photo（ロック画面の動く壁紙に使える JPG + MOV のペア）を Mac で作るスキル。
  手持ちの動画を Live Photo に変換するほか、題材だけ指定されたときは画像生成（nanobanana）と
  動画生成（gemini-omni）で素材から作る。「Live Photo 作って」「ライブ壁紙」「動く壁紙」
  「Live 壁紙」「この動画を Live Photo にして」「iPhone のロック画面で動くやつ」と言われたら使う。
  X などの参考ポストを渡されて「こういう壁紙作って」と言われたときにも使う。
---

# live-photo

動画を、iPhone が Live Photo として認識する JPG と MOV のペアに変換する。
macOS 標準の AVFoundation と ImageIO だけで処理するので、外部パッケージのインストールは不要。

必要なもの: macOS、`ffmpeg`、Swift（Xcode Command Line Tools）。

## 流れ

1. 素材の動画を用意する（手持ちの動画、または生成）
2. 使う区間とキー写真の時刻を決める
3. `scripts/make_live_photo.sh` でペアを作る
4. iPhone への送り方を伝える

## 1. 素材を用意する

### 手持ちの動画がある場合

そのまま 3 へ進む。横長の動画は `--portrait` で 9:16 に中央クロップできる。

### 題材から作る場合

いきなり動画を生成すると CG っぽくなりやすい。先に静止画を作り、それを動かす。

1. **静止画**: `nanobanana` スキルで `--pro --ratio 9:16 --size 2K`。できた絵を必ず目で確認し、不自然なら作り直す。
2. **動画**: `gemini-omni` スキルに静止画を `-i` で渡し、`--ratio 9:16 --resolution 1080p` で動かす。

参考ポストを渡されたときは、構図や題材の方向性だけを借りて新しく作る。元の画像や動画をそのまま使わない。

### 実写らしく作るためのプロンプトの要点

静止画のプロンプト:

- 冒頭で `Real photograph, not CGI, not an illustration.` と言い切る
- カメラの条件を具体的に書く（例: `85mm lens at f/2.8, 1/60s, ISO 1600, low angle`）
- 被写体の不揃いさを書く。大きさがばらばら、雑に積んである、ひび、欠け、汚れ、灰など。均一で左右対称なものは CG に見える
- 色を変えるときは現実の理由を添える（紫の炎なら「炎色反応の粉を入れた焚き火」）。元の色も少し残す
- 写真の癖を入れる: `subtle sensor grain`、`natural lens bloom`、`slightly clipped highlights`
- ロック画面用の構図にする。時計が上に重なるので、上 40% は暗い余白にして、主役は下半分に置く
- `No text, no people, no watermark.`

動画のプロンプト:

- `Use this photograph as the first frame` と書き、同じ場面の実写映像として動かすよう頼む
- `Continuous single shot, camera locked on a tripod, no camera movement, no zoom, no scene cuts`
- 動くものと動かないものを分けて書く（炎・火の粉・水面は動く、薪・石・地面は形も質感も変えない）
- `normal speed, never slow motion` と書く。書かないとスローで滑らかな CG 調になる
- 音は環境音だけにする: `No music, no dialogue.`

## 2. 区間とキー写真を決める

コンタクトシートを作って目で選ぶ。

```bash
ffmpeg -v error -y -i src.mp4 -vf "fps=2,scale=400:-1,tile=10x2" -frames:v 1 sheet.jpg
```

- 長さは 3〜4 秒にする。長いと iOS が壁紙のモーションを無効にしやすい
- 画像から動画を作った場合、最初の 1 秒は入力画像のまま止まっていることがあるので避ける
- **キー写真はロック画面で止まっているときに表示される絵**になる。いちばん見栄えのいいフレームを選ぶ
- 再生はキー写真に向かって収束するので、キー写真は区間の後半に置くと自然に見える

## 3. ペアを作る

```bash
bash scripts/make_live_photo.sh -i src.mp4 -n PurpleFire -s 2.0 -d 4 -k 2.5
```

| オプション | 意味 |
|---|---|
| `-i` | 元動画 |
| `-n` | 名前。`IMG_<名前>.JPG` と `IMG_<名前>.MOV` になる（英数字のみ） |
| `-o` | 出力先。省略すると `~/Desktop/LivePhoto_<名前>/` |
| `-s` | 元動画のどこから切り出すか（秒） |
| `-d` | 長さ（秒、既定 3） |
| `-k` | キー写真の時刻。**切り出した区間の先頭からの秒数** |
| `--portrait` | 1080×1920 に中央クロップ |
| `--mute` | 音声を落とす |

スクリプトは区間を H.264 で切り出し、キー写真を取り出し、`pair_live_photo.swift` で両方に同じ識別子を書き込む。

- JPG: Apple MakerNote のキー 17
- MOV: `com.apple.quicktime.content.identifier` と、キー写真の位置を示す `still-image-time` のメタデータトラック

できたかどうかは次で確かめる。両方に同じ UUID が出れば成功。

```bash
ffprobe -v error -show_entries format_tags=com.apple.quicktime.content.identifier -of csv=p=0 IMG_x.MOV
strings IMG_x.JPG | grep -m1 -E '[0-9A-F]{8}-[0-9A-F]{4}'
```

## 4. iPhone への送り方（ユーザーに伝える）

1. Finder で JPG と MOV を**2 つ同時に選択**して iPhone へ AirDrop する。片方ずつ送ると、別々の写真と動画になる
2. 写真アプリで「LIVE」マークが付いた 1 枚になっていることを確認する
3. ロック画面を長押し →「＋」→「写真」でその写真を選び、左下の Live Photo アイコンをオンにする

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| 写真と動画が別々に保存される | 2 ファイルを同時に AirDrop し直す。ファイル名の拡張子より前が同じか確認する |
| 「モーションは利用できません」と出る | 長さを 3 秒以下にして作り直す。それでも出る場合は、元動画を iPhone に送って intoLive などのアプリで変換する |
| 止まっているときの絵が気に入らない | `-k` を変えて作り直す |
| `swift` の実行でエラー | `xcode-select --install` で Command Line Tools を入れる |
