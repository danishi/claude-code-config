// うねる円筒トンネルの内側を飛ぶ
#define FAR 90.0
#define FOG 0.042
#define STEPS 90
const float R=4.6;
vec2 path(float z){
  return uWarp*vec2(sin(z*0.16)*2.6+sin(z*0.07+1.7)*3.4, cos(z*0.13)*2.3+sin(z*0.05+0.4)*3.0);
}
vec2 suv(vec3 p,out float r){
  vec2 q=p.xy-path(p.z); r=length(q);
  return vec2((atan(q.y,q.x)/TAU+0.5)*P, p.z*P/(TAU*R));
}
float map(vec3 p){ float r; vec2 uv=suv(p,r); return R-techHeight(uv)*0.75-r; }
vec3 surfEmission(vec3 p,vec3 n,float px,out vec3 hal){
  float r; vec2 uv=suv(p,r); return techEmission(uv,px*P/(TAU*R),hal);
}
vec3 background(vec3 rd){ return vec3(0.0); }
vec3 haze(){ return uPal[0]*0.004; }
void cam(float t,out vec3 ro,out mat3 B,out float fov){
  float z0=t*uSpeed;
  ro=vec3(path(z0),z0); ro.xy+=1.5*vec2(sin(t*0.5),cos(t*0.37));
  B=lookAt(ro,vec3(path(z0+6.0),z0+6.0),uRoll*t+0.3*sin(t*0.4));
  fov=1.3*uFov;
}
