// 全シーン共通：uniform、乱数、配色、魚眼の射影、「テック面」（段差と発光模様）
precision highp float;
uniform vec2  uRes, uJitter;
uniform float uTime, uBeat, uSeed, uWeight;
uniform float uSpeed, uWarp, uFov, uRoll, uDensity, uReflect, uPulse;
uniform vec3  uPal[5];
uniform float uPalW[5];   // 累積の重み（最後が1.0）

#define TAU 6.2831853
#define P 112.0           // テック面のx方向の周期（レーン単位）。筒や球に巻くときは一周をPに合わせる

float h11(float n){ return fract(sin(n*127.1+uSeed*1.37)*43758.5453); }
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)+uSeed*0.137); p+=dot(p,p+45.32); return fract(p.x*p.y); }
vec3 pal(float h){ for(int i=0;i<4;i++) if(h<uPalW[i]) return uPal[i]; return uPal[4]; }

// 等距離射影の魚眼。uvは画面中心0・対角の端で長さ1、fovは対角端での半画角（ラジアン）
vec3 rayDir(vec2 uv, mat3 B, float fov){
  float r=length(uv); float th=r*fov;
  vec2 d=r>1e-5?uv/r*sin(th):vec2(0.0);
  return normalize(B*vec3(d,cos(th)));
}
vec2 project(vec3 d, mat3 B, float fov){
  vec3 l=d*B; float s=length(l.xy);
  return s>1e-5?l.xy/s*acos(clamp(l.z,-1.0,1.0))/fov:vec2(0.0);
}
mat3 lookAt(vec3 ro, vec3 ta, float roll){
  vec3 f=normalize(ta-ro); vec3 up=vec3(sin(roll),cos(roll),0.0);
  vec3 r=normalize(cross(up,f)); return mat3(r,cross(f,r),f);
}

// 線の描画。d=中心からの距離, w=半幅, px=1ピクセルが覆う幅（同じ単位）。
// ピクセルより細い線は太らせた分だけ暗くするので、遠くでもちらつかない
float ln(float d,float w,float px){ float a=max(w,px*0.6); return clamp((a-abs(d))/max(px,1e-4)+0.5,0.0,1.0)*(w/a); }
// 線のまわりの壁を照らす光
float halo(float d,float w){ return exp(-abs(d)/(w*7.0)); }

// ---- テック面：2次元座標uv（1単位=回路1レーン）から段差と発光を作る ----
void zoneOf(vec2 uv,out vec2 zid,out vec2 zf){
  float LZ=14.0; float iz=floor(uv.y/LZ); float nA=floor(3.0+h11(iz)*4.0);
  float sx=fract(uv.x/P+h11(iz+9.1));
  zid=vec2(floor(sx*nA),iz); zf=vec2(fract(sx*nA),fract(uv.y/LZ));
}
void cellOf(vec2 uv,out vec2 cid,out vec2 cf,out vec2 cs){
  float lz=2.5; float jz=floor(uv.y/lz); float nB=floor(24.0+h11(jz*0.37+2.0)*40.0);
  float sx=fract(uv.x/P+h11(jz+5.7));
  cid=vec2(floor(sx*nB)+31.0,jz); cf=vec2(fract(sx*nB),fract(uv.y/lz)); cs=vec2(P/nB,lz);
}
// 段差の高さ（0〜約1.2）。大きな板、張り出す枠、細かいブロックの3層
float techHeight(vec2 uv){
  vec2 zid,zf,cid,cf,cs; zoneOf(uv,zid,zf); cellOf(uv,cid,cf,cs);
  float big=floor(h21(zid)*4.0)/3.0*0.55;
  float rib=step(0.75,h11(zid.y+3.3))*step(zf.y,0.10);
  float hs=h21(cid); float small=step(0.6,hs)*floor(hs*5.0)/5.0*0.18;
  return max(big,rib)+small;
}
// 発光。戻り値=線そのものの光、hal=線が周囲の壁を照らす光（遮蔽を掛けられるよう分けて返す）
vec3 techEmission(vec2 uv,float px,out vec3 hal){
  vec2 zid,zf,cid,cf,cs; zoneOf(uv,zid,zf); cellOf(uv,cid,cf,cs);
  // 区画ごとに主色と密度を決める。暗い板と密な板が混ざると大きさの対比が出る
  float zh=h21(zid+7.7); vec3 zcol=pal(h21(zid+3.1));
  float zd=(zh<0.22?0.12:(zh<0.7?0.6:1.0))*uDensity;
  vec3 e=vec3(0.0); hal=vec3(0.0);
  #define EC(h) ((h)<0.72?zcol:pal(fract((h)*13.7)))
  // 1) 横に走るアーク（端は丸める）
  {
    float ir=floor(uv.y); float fy=fract(uv.y)-0.5; float hr=h11(ir+1.3);
    float n=floor(4.0+hr*14.0); float sx=fract(uv.x/P+h11(ir+4.4));
    float is=floor(sx*n); float fs=fract(sx*n); float hs=h21(vec2(is,ir));
    float on=step(1.0-0.55*zd,hs); float len=0.3+0.65*h21(vec2(is+7.0,ir));
    float d=length(vec2(fy,max(fs-len,0.0)*P/n));
    vec3 c=EC(fract(hs*7.13)); float br=1.2+3.5*step(0.9,h21(vec2(is,ir+0.5)));
    e+=c*ln(d,0.036,px)*on*br; hal+=c*halo(d,0.036)*on*0.05*br;
  }
  // 1b) 細い目盛り線
  {
    float ir=floor(uv.y*3.0); float fy=(fract(uv.y*3.0)-0.5)/3.0;
    vec2 blk=vec2(floor(uv.x/P*16.0),floor(uv.y/6.0));
    float on=step(1.0-0.45*zd,h21(blk+1.9))*step(0.3,h11(ir+8.8));
    e+=zcol*ln(fy,0.022,px)*on*0.4;
  }
  // 2) 縦に走る回路トレース（区間の後半で斜めに段を変える）とパッド
  {
    float il=floor(uv.x); float u=fract(uv.x)-0.5; float L=4.0;
    float is=floor(uv.y/L); float fz=fract(uv.y/L);
    float run=step(1.0-0.5*zd,h21(vec2(il,floor(uv.y/30.0)+3.0)));
    float o0=floor(h21(vec2(il,is))*3.0-1.0)*0.28;
    float o1=floor(h21(vec2(il,is+1.0))*3.0-1.0)*0.28;
    float d=u-mix(o0,o1,smoothstep(0.62,0.92,fz));
    float hl=h21(vec2(il,9.0)); vec3 c=EC(hl);
    float pulse=1.0+uPulse*3.0*smoothstep(0.92,1.0,fract(uv.y*0.012-uTime*0.5+hl));
    e+=c*ln(d,0.036,px)*run*0.9*pulse; hal+=c*halo(d,0.036)*run*0.04*pulse;
    float pad=step(0.82,h21(vec2(il,is+50.0)))*run;
    e+=EC(fract(hl*5.3))*ln(max(abs(d),abs((fz-0.5)*L)),0.15,px)*pad*2.0;
  }
  // 3) 細かいブロックの輪郭線
  {
    float d=min(min(cf.y,1.0-cf.y)*cs.y,min(cf.x,1.0-cf.x)*cs.x)-0.12;
    float hc=h21(cid+11.0); float on=step(1.0-0.3*zd,hc); vec3 c=EC(fract(hc*3.9));
    e+=c*ln(d,0.03,px)*on; hal+=c*halo(d,0.03)*on*0.04;
  }
  // 4) ゆっくり明滅する点の群れ
  {
    vec2 g=uv*2.0; vec2 id=floor(g); vec2 f=fract(g)-0.5; float hd=h21(id);
    float cl=step(1.0-0.45*zd,h21(floor(id/vec2(8.0,12.0))+2.0));
    float tw=0.5+0.5*sin(uTime*(1.5+4.0*hd)+hd*50.0);
    e+=pal(fract(hd*9.7))*step(0.8,hd)*cl*ln(max(abs(f.x),abs(f.y))*0.5,0.14,px)*(0.3+0.7*tw*tw)*1.6;
  }
  hal+=zcol*zd*0.004;
  return e;
}
