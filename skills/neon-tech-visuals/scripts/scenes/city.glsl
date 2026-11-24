// 回路基板のような街並みの上を低く飛ぶ
#define FAR 90.0
#define FOG 0.03
#define STEPS 120
const float U=0.2;      // 1レーンのワールド幅
const float HT=2.2;     // 建物の高さ倍率
float map(vec3 p){ return p.y-techHeight(p.xz/U)*HT; }
vec3 surfEmission(vec3 p,vec3 n,float px,out vec3 hal){
  vec2 uv=p.xz/U; vec3 e=techEmission(uv,px/U,hal);
  if(n.y<0.5){
    // 側面には階ごとの窓明かりを入れる
    float fl=floor(p.y/0.2); float d=(fract(p.y/0.2)-0.5)*0.2;
    float h=h21(floor(uv/2.5)+fl*0.71);
    e=e*0.2+pal(fract(h*7.7))*ln(d,0.012,px)*step(0.45,h)*1.8; hal*=0.5;
  }
  return e;
}
vec3 background(vec3 rd){ return uPal[0]*0.018*exp(-abs(rd.y)*16.0); }
vec3 haze(){ return uPal[0]*0.003; }
void cam(float t,out vec3 ro,out mat3 B,out float fov){
  ro=vec3(sin(t*0.21)*6.0*uWarp, 3.5+0.4*sin(t*0.3), t*uSpeed);
  vec3 ta=ro+vec3(cos(t*0.21)*1.3*uWarp,-1.5,5.0);
  B=lookAt(ro,ta,uRoll*0.6*sin(t*0.21));
  fov=1.05*uFov;
}
