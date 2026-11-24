# シーンの書き方

同梱の `tunnel` `city` `core` 以外の題材を頼まれたときに読む。シーンは形とカメラだけを書くGLSLの断片で、`common.glsl` の後ろ、`main.glsl`（または `post.glsl`）の前に連結される。作業フォルダに `myscene.glsl` を作り、`config.json` の `"scene"` にそのパス（configからの相対でよい）を書く。

## 定義するもの

```glsl
#define FAR 90.0     // これより遠くは描かない
#define FOG 0.04     // 霧の濃さ。奥を暗く落として遠近を出す
#define STEPS 90     // レイマーチの反復回数。足りないと奥が欠け、多いと遅い

float map(vec3 p);                                           // 表面までの距離（内側が負）
vec3  surfEmission(vec3 p, vec3 n, float px, out vec3 hal);  // 表面の発光。halは周囲を照らす光
vec3  background(vec3 rd);                                   // 何にも当たらなかった方向の色
vec3  haze();                                                // 霧の色（ごく暗く）
void  cam(float t, out vec3 ro, out mat3 B, out float fov);  // 時刻tのカメラ
```

`cam` は時刻だけの関数にする。仕上げのモーションブラーが `cam(t)` と `cam(t-シャッター時間)` を呼び比べて流れの向きを出すので、乱数や `uTime` を直接使うとブラーが壊れる。`B` は `lookAt(ro, 注視点, 回転角)` で作る。`fov` は画面の対角の端での半画角（ラジアン）で、0.7なら普通のレンズ、1.3なら強い魚眼。`uFov` を掛けておくと設定から調整できる。

使える設定値：`uSpeed` `uWarp` `uRoll` `uFov` `uDensity` `uTime` `uBeat` `uPal[0..4]`（`uPal[0]` が主色）。

## テック面を貼る

`techHeight(uv)` が段差（0〜約1.2）、`techEmission(uv, px, hal)` が発光を返す。`uv` は1単位が回路1レーンの2次元座標で、形の表面をどう展開するかだけを決めればよい。

- 平面：`uv = p.xz / U`（Uは1レーンのワールド幅。0.15〜0.25）
- 筒：`uv = vec2((角度/TAU+0.5)*P, 軸方向の位置*P/(TAU*半径))`。一周を `P`（=112）に合わせると継ぎ目が出ない
- 球：`uv = vec2((経度/TAU+0.5)*P, 緯度*P/TAU)`。極は模様が詰まるので、カメラを赤道寄りに置く
- 箱や多面体：面ごとに支配的な軸を選んで平面の式を使う（法線 `n` の最大成分で分岐する）

`px` は1ピクセルが覆う幅で、`main.glsl` からワールド単位で渡ってくる。`techEmission` にはuvの単位に直して渡す（平面なら `px/U`、筒・球なら `px*P/(TAU*半径)`）。これを忘れると遠くの線がちらつくか、消える。

段差は `map` の中で `形の距離 - techHeight(uv)*高さ` の形で使う。段差は不連続なので、高さを大きくするとレイが突き抜けやすい。目安はレーン幅の4倍まで。

## 例：四角い回廊

```glsl
#define FAR 80.0
#define FOG 0.045
#define STEPS 100
const float W=3.0, H=2.0, U=0.2;
vec2 suv(vec3 p){
  // 壁4面を一周につなげて展開する
  float per=4.0*(W+H); float s;
  if(abs(p.x)/W>abs(p.y)/H) s=p.x>0.0? H+p.y : 3.0*H+2.0*W-p.y;
  else                      s=p.y>0.0? 2.0*H+W-p.x : 4.0*H+3.0*W+p.x;
  return vec2(s/per*P, p.z*P/per);
}
float map(vec3 p){ return min(W-abs(p.x),H-abs(p.y))-techHeight(suv(p))*0.4; }
vec3 surfEmission(vec3 p,vec3 n,float px,out vec3 hal){ return techEmission(suv(p),px*P/(4.0*(W+H)),hal); }
vec3 background(vec3 rd){ return vec3(0.0); }
vec3 haze(){ return uPal[0]*0.004; }
void cam(float t,out vec3 ro,out mat3 B,out float fov){
  ro=vec3(0.8*sin(t*0.4),0.4*cos(t*0.3),t*uSpeed);
  B=lookAt(ro,ro+vec3(0.0,0.0,5.0),uRoll*t);
  fov=1.2*uFov;
}
```

## テック面を使わない物体を混ぜる

`core.glsl` の光の輪がその例。`map` で `min()` を取り、`surfEmission` の先頭で「どの物体に当たったか」を距離で判定して、単色の発光を返す。細い発光体は半径0.02〜0.04、明るさ2〜3が扱いやすい。それ以上にするとブルームで白く潰れる。

テック面をまったく使わない題材（結晶、液体金属、粒子の雲など）でも、同じ5つを定義すれば描画と仕上げはそのまま使える。`surfEmission` で好きな発光を返し、艶は `look.reflect` に任せる。

## 題材ごとの勘どころ

- 内側を飛ぶ（トンネル、回廊、パイプ）：`fov` 1.2〜1.4、カメラを中心から少しずらして揺らすと壁の近さが出る
- 上を飛ぶ（街、基板、海）：`fov` 1.0前後、少し見下ろす。空は `background` に地平線の淡い光を入れる。真っ黒だと地平線が切れて見える
- 外から眺める（球、塔、リング、ロゴ）：`fov` 0.6〜0.8、周回カメラ。背景に星か遠景を薄く置くと動きが伝わる
- カメラの進む先に壁がある構図は、`preview` の6コマすべてで埋まっていないか確かめる

## 書いたら確かめること

1. `node scripts/render.js config.json --out work/t --frames 0 --scale 0.5`。コンパイルエラーは行番号つきで表示される（行番号は連結後のもの。`common.glsl` の行数を引く）
2. `preview` で6コマを見る。黒一色なら `map` の符号（カメラ位置で正になっているか）と `FAR` を疑う
3. 等倍で1枚描いて、線のちらつきと `px` の換算を確かめる
