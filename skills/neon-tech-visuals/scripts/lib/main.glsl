// 共通の描画本体。シーン側が map / surfEmission / background / cam と FAR・FOG・STEPS を定義する
out vec4 o;

float march(vec3 ro,vec3 rd,int steps,out bool hit){
  float t=0.02,tp=0.0; hit=false;
  for(int i=0;i<160;i++){
    if(i>=steps) break;
    float d=map(ro+rd*t);
    if(d<0.0012*(1.0+t)){
      // 段差を踏み越えたときは二分探索で表面まで戻す
      if(d<0.0){ float a=tp,b=t; for(int k=0;k<5;k++){ float m=0.5*(a+b); if(map(ro+rd*m)<0.0) b=m; else a=m; } t=a; }
      hit=true; break;
    }
    tp=t; t+=min(d*0.7,0.30+t*0.05);
    if(t>FAR) break;
  }
  return t;
}
vec3 normalAt(vec3 p,float e){
  vec2 k=vec2(e,0.0);
  return normalize(vec3(map(p+k.xyy)-map(p-k.xyy),map(p+k.yxy)-map(p-k.yxy),map(p+k.yyx)-map(p-k.yyx)));
}

void main(){
  float hd=length(0.5*uRes);
  vec2 uv=(gl_FragCoord.xy+uJitter-0.5*uRes)/hd;
  vec3 ro; mat3 B; float fov; cam(uTime,ro,B,fov);
  vec3 rd=rayDir(uv,B,fov);
  float pix=fov/hd;                      // 1ピクセルの見込み角
  bool hit; float t=march(ro,rd,STEPS,hit);
  vec3 col; float depth=FAR;
  if(hit){
    depth=t;
    vec3 p=ro+rd*t; vec3 n=normalAt(p,0.003+0.0015*t);
    float ndv=max(dot(n,-rd),0.0);
    float px=t*pix/max(ndv,0.25);
    vec3 hal; vec3 e=surfEmission(p,n,px,hal);
    float ao=clamp(map(p+n*0.15)/0.15,0.0,1.0); ao=0.25+0.75*ao;
    // 拍に合わせて手前から奥へ走る光の波
    float bf=fract(uBeat);
    float wave=1.0+uPulse*2.2*exp(-abs(t-bf*FAR*0.6)*0.5)*exp(-bf*2.0);
    col=e*wave+(hal*wave+vec3(0.006)*(0.4+0.6*ndv))*ao;
    // 艶のある壁への映り込み（1回反射）
    if(uReflect>0.01){
      vec3 r2=reflect(rd,n); vec3 p1=p+n*0.02; bool h2;
      float t2=march(p1,r2,STEPS/2,h2);
      float fres=0.07+0.93*pow(1.0-ndv,4.0);
      vec3 rc;
      if(h2){
        vec3 p2=p1+r2*t2; vec3 n2=normalAt(p2,0.006+0.002*(t+t2)); vec3 hal2;
        rc=surfEmission(p2,n2,(t+t2)*pix*1.5,hal2); rc=(rc+hal2)*exp(-t2*FOG);
      } else rc=background(r2);
      col+=rc*fres*0.7*uReflect*ao;
    }
    float fog=exp(-t*FOG);
    col=col*fog+haze()*(1.0-fog);
  } else col=background(rd)+haze();
  o=vec4(max(col,0.0),depth)*uWeight;
}
