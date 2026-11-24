// 回路で覆われた球体（データコア）と、それを囲む光の輪を周回する
#define FAR 60.0
#define FOG 0.012
#define STEPS 100
const float R=4.0;
vec2 suv(vec3 p){ vec3 q=normalize(p); return vec2((atan(q.z,q.x)/TAU+0.5)*P, asin(q.y)*P/TAU); }
float torus(vec3 p,float rad,float tilt,float spin){
  float c=cos(spin),s=sin(spin); p.xz=mat2(c,-s,s,c)*p.xz;
  c=cos(tilt); s=sin(tilt); p.xy=mat2(c,-s,s,c)*p.xy;
  return length(vec2(length(p.xz)-rad,p.y))-0.022;
}
float rings(vec3 p){
  return min(min(torus(p,5.3,0.35,uTime*0.10),torus(p,5.9,-0.6,uTime*0.07+2.0)),torus(p,6.6,1.1,-uTime*0.05));
}
float map(vec3 p){ return min(length(p)-R-techHeight(suv(p))*0.5, rings(p)); }
vec3 surfEmission(vec3 p,vec3 n,float px,out vec3 hal){
  if(rings(p)<0.02){ hal=vec3(0.0); return uPal[1]*2.2; }
  return techEmission(suv(p),px*P/(TAU*R),hal);
}
vec3 background(vec3 rd){
  vec2 g=vec2(atan(rd.z,rd.x),asin(rd.y))*90.0; vec2 f=fract(g)-0.5;
  float h=h21(floor(g)); return vec3(0.9,0.95,1.0)*step(0.985,h)*smoothstep(0.12,0.0,length(f))*0.8;
}
vec3 haze(){ return vec3(0.0); }
void cam(float t,out vec3 ro,out mat3 B,out float fov){
  float a=t*uSpeed*0.035; float d=9.5-1.5*sin(t*0.15);
  ro=d*vec3(cos(a),0.28+0.2*sin(t*0.2)*uWarp,sin(a));
  B=lookAt(ro,vec3(0.0,0.3,0.0),uRoll*0.3*sin(t*0.3));
  fov=0.72*uFov;
}
