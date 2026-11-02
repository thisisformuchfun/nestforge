#include <math.h>
// Orthographic, depth-tested triangle rasterizer. Input is screen x/y/depth.
void raster(int w,int h,int count,const float* tri,const unsigned char* colors,unsigned char* image,float* depth){
 for(int t=0;t<count;t++){
  const float* p=tri+9*t;const unsigned char* c=colors+3*t;
  float den=(p[4]-p[7])*(p[0]-p[6])+(p[6]-p[3])*(p[1]-p[7]);if(fabsf(den)<1e-8)continue;
  int x0=fmaxf(0,floorf(fminf(p[0],fminf(p[3],p[6])))),x1=fminf(w-1,ceilf(fmaxf(p[0],fmaxf(p[3],p[6]))));
  int y0=fmaxf(0,floorf(fminf(p[1],fminf(p[4],p[7])))),y1=fminf(h-1,ceilf(fmaxf(p[1],fmaxf(p[4],p[7]))));
  for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++){
   float a=((p[4]-p[7])*(x+.5f-p[6])+(p[6]-p[3])*(y+.5f-p[7]))/den;
   float b=((p[7]-p[1])*(x+.5f-p[6])+(p[0]-p[6])*(y+.5f-p[7]))/den;float d=1-a-b;
   if(a<0||b<0||d<0)continue;float z=a*p[2]+b*p[5]+d*p[8];int k=y*w+x;
   if(z>depth[k]){depth[k]=z;image[3*k]=c[0];image[3*k+1]=c[1];image[3*k+2]=c[2];}
  }
 }
}
