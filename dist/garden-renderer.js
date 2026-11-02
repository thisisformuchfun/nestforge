import * as THREE from 'three';

// A transparent, depth-aware finishing pass: retain the real garden behind
// the canvas while shading cavities in the actual CAD, then tone-map once.
export class GardenRenderer {
  constructor(renderer) {
    this.renderer=renderer;
    this.target=new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter});
    this.target.depthTexture=new THREE.DepthTexture(1,1,THREE.UnsignedIntType);
    this.target.samples=Math.min(4,renderer.capabilities.maxSamples||0);
    this.material=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,blending:THREE.NoBlending,uniforms:{
      tColor:{value:this.target.texture},tDepth:{value:this.target.depthTexture},resolution:{value:new THREE.Vector2(1,1)},inverseProjection:{value:new THREE.Matrix4()},strength:{value:.55}
    },vertexShader:`varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}`,
    fragmentShader:`
      uniform sampler2D tColor,tDepth;uniform vec2 resolution;uniform mat4 inverseProjection;uniform float strength;varying vec2 vUv;
      vec3 viewPoint(vec2 uv,float depth){vec4 p=inverseProjection*vec4(uv*2.-1.,depth*2.-1.,1.);return p.xyz/p.w;}
      void main(){
        vec4 color=texture2D(tColor,vUv);float depth=texture2D(tDepth,vUv).r;
        if(color.a<.001||depth>=.999999){gl_FragColor=color;return;}
        vec3 p=viewPoint(vUv,depth);vec3 normal=normalize(cross(dFdx(p),dFdy(p)));
        if(normal.z<0.)normal=-normal;
        float occlusion=0.;float weight=0.;
        for(int i=0;i<12;i++){
          float a=float(i)*2.399963;float radius=3.+float(i%4)*3.;
          vec2 uv=vUv+vec2(cos(a),sin(a))*radius/resolution;
          float z=texture2D(tDepth,uv).r;
          if(z<.999999){
            vec3 delta=viewPoint(uv,z)-p;float distance=length(delta);
            float nearWeight=1.-smoothstep(4.,18.,distance);
            float horizon=max(dot(normal,delta/max(distance,.001))-.13,0.);
            occlusion+=horizon*nearWeight;weight+=1.;
          }
        }
        float ao=1.-strength*clamp(occlusion/max(weight,1.)*2.3,0.,.75);
        color.rgb*=ao;
        gl_FragColor=color;
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`});
    this.scene=new THREE.Scene();this.camera=new THREE.Camera();
    this.quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2),this.material);this.quad.frustumCulled=false;this.scene.add(this.quad);
  }
  setSize(width,height){const ratio=this.renderer.getPixelRatio();this.target.setSize(Math.round(width*ratio),Math.round(height*ratio));this.material.uniforms.resolution.value.set(this.target.width,this.target.height);}
  render(scene,camera){
    this.material.uniforms.inverseProjection.value.copy(camera.projectionMatrixInverse);
    this.renderer.setRenderTarget(this.target);this.renderer.clear();this.renderer.render(scene,camera);
    this.renderer.setRenderTarget(null);this.renderer.render(this.scene,this.camera);
  }
  dispose(){this.target.dispose();this.material.dispose();this.quad.geometry.dispose();}
}
