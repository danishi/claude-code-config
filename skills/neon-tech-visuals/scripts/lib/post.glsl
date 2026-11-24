// 仕上げ：カメラの動きに沿ったモーションブラー、色収差、ブルーム、トーンマップ、ビネット、粒子
uniform sampler2D uScene;
uniform float uExposure, uBloom, uAberr, uSat, uShutter, uFps, uGrain, uTaps;
out vec4 o;

float ign(vec2 p){ return fract(52.9829189*fract(dot(p,vec2(0.06711056,0.00583715)))); }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.0,1.0); }
// ミップマップを重ねるブルーム。各段を4点でならして、拡大時の四角いムラを消す
vec3 mipTap(vec2 tc,float lod){
  vec2 d=exp2(lod)*0.5/uRes;
  return 0.25*(textureLod(uScene,tc+d*vec2(1.0,1.0),lod).rgb+textureLod(uScene,tc+d*vec2(-1.0,1.0),lod).rgb
              +textureLod(uScene,tc+d*vec2(1.0,-1.0),lod).rgb+textureLod(uScene,tc+d*vec2(-1.0,-1.0),lod).rgb);
}
vec3 bloomAt(vec2 tc){
  float k=log2(uRes.y/720.0);            // 解像度が変わってもにじみの見かけの幅を保つ
  vec3 b=mipTap(tc,1.5+k)*0.20;
  b+=mipTap(tc,2.5+k)*0.22; b+=mipTap(tc,3.5+k)*0.20;
  b+=mipTap(tc,4.5+k)*0.16; b+=mipTap(tc,5.5+k)*0.12;
  b+=mipTap(tc,6.5+k)*0.10;
  return b;
}

void main(){
  float hd=length(0.5*uRes); vec2 sc=hd/uRes;          // uv→テクスチャ座標の倍率
  vec2 uv=(gl_FragCoord.xy-0.5*uRes)/hd;
  // この画素に写っている点が、シャッターが開いた時点では画面のどこにあったかを求める
  float depth=texture(uScene,gl_FragCoord.xy/uRes).a;
  vec3 ro; mat3 B; float fov; cam(uTime,ro,B,fov);
  vec3 wp=ro+rayDir(uv,B,fov)*depth;
  vec3 ro1; mat3 B1; float fov1; cam(uTime-uShutter/uFps,ro1,B1,fov1);
  vec2 vel=uv-project(normalize(wp-ro1),B1,fov1);
  float vl=length(vel); if(vl>0.16) vel*=0.16/vl;
  float r2=dot(uv,uv);
  float kick=exp(-fract(uBeat)*6.0)*uPulse;
  float ab=(0.010+0.006*kick)*uAberr*r2;                // 外周ほど色がずれる
  float j=ign(gl_FragCoord.xy+uTime*60.0);
  vec3 col=vec3(0.0); float N=max(uTaps,1.0);
  for(int i=0;i<48;i++){
    if(float(i)>=N) break;
    vec2 q=uv-vel*((float(i)+j)/N-0.5);
    col.r+=texture(uScene,0.5+q*(1.0+ab)*sc).r;
    col.g+=texture(uScene,0.5+q*sc).g;
    col.b+=texture(uScene,0.5+q*(1.0-ab)*sc).b;
  }
  col/=N;
  vec3 bl=vec3(bloomAt(0.5+uv*(1.0+ab*1.5)*sc).r,bloomAt(0.5+uv*sc).g,bloomAt(0.5+uv*(1.0-ab*1.5)*sc).b);
  col+=bl*uBloom*0.9;
  col*=uExposure*(1.0+0.10*kick);
  col=aces(max(col,0.0));
  float l=dot(col,vec3(0.2126,0.7152,0.0722));
  col=clamp(mix(vec3(l),col,uSat),0.0,1.0);            // 彩度はトーンマップ後（明るい線の色を残す）
  col=pow(col,vec3(1.0/2.2));
  col*=1.0-0.38*smoothstep(0.55,1.05,sqrt(r2));
  col+=(ign(gl_FragCoord.xy+uTime*113.0)-0.5)*uGrain;
  o=vec4(col,1.0);
}
