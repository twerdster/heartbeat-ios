// 2026 portable translation of Algorithm.mm by Or Maayan and Michael Leybovich.
// Keeps the recovered state machine's documented quirks; original remains in source/.
#pragma once
#include <algorithm>
#include <cmath>
#include <vector>
#include <stdexcept>
#include "Butterworth.h"
struct HBTrace { int frame; double value; int peak_index,is_peak; double bpm_value,bpm_average; int calibration_over; double bpm_latest; int final_determined,should_show,missed_last_peak; };
class HeartbeatCore {
 int fc=0, first=0, num=0,last=0; bool show=false,missed=false; int window=60;
 std::vector<double> points,bpms,avgs;std::vector<int> peaks;
 double a[11]={1,-8.04234298696992,29.422399680745215,-64.5194828455958,93.95541134986065,-94.96524800144532,67.48098648876717,-33.29000463868108,10.91225271476863,-2.1463589083868864,0.19238859600117322};
 double b[11]={0.0004894360861164059,0,-0.0024471804305820294,0,0.004894360861164059,0,-0.004894360861164059,0,0.0024471804305820294,0,-0.0004894360861164059};
 bool calibrated()const{return fc>90+window&&fc>90+first+9;}
 double latest()const{return calibrated()?avgs[fc-10]:0;}
 bool final()const{return calibrated()&&std::abs(latest()-avgs[fc-55])<=1&&std::abs(latest()-avgs[fc-100])<=1.5;}
 bool local(const std::vector<double>&y,int offset)const{
   int since=fc-10-last;if(since>=0&&since<9)return false;
   for(int j=0;j<9;++j)if(y[offset+9]<=y[offset+j])return false;
   for(int j=10;j<19;++j)if(y[offset+9]<y[offset+j])return false;return true;
 }
 bool miss()const{return latest()!=0&&(fc-10-last)>1.5*(60*30/latest());}
public:
 explicit HeartbeatCore(int filter_window=60):window(filter_window){if(window!=45&&window!=60)throw std::invalid_argument("filter window must be 45 or 60");}
 HBTrace step(double green){
  ++fc;points.push_back(green*255);peaks.push_back(0);bpms.push_back(72);avgs.push_back(72);int idx=-1;
  if(fc>window){int n=window+1;std::vector<double>x(points.end()-n,points.end()),y(n);double mean=0;for(double v:x)mean+=v;mean/=n;for(double&v:x)v-=mean;filter(10,a,b,n,x.data(),y.data());idx=fc-10;
   if(!first){peaks[idx]=local(y,n-19);num+=peaks[idx];if(peaks[idx]){first=idx;bpms[idx]=avgs[idx]=0;}}
   else {
    if(fc<90+first+10){peaks[idx]=local(y,n-19);num+=peaks[idx];int frames=std::min(fc-first-1,90);bpms[idx]=std::clamp((num/(frames/30.0))*60,36.,180.);double k=fc-(first+10)-1+4.5;avgs[idx]=avgs[idx-1]*k/(k+1.5)+bpms[idx]*1.5/(k+1.5);}
    else {if(fc<90+(first+10)+75)peaks[idx]=local(y,n-19);else{bool m=miss();peaks[idx]=m?1:local(y,n-19);missed=miss();}num+=peaks[idx]-peaks[idx-90];bpms[idx]=std::clamp((num/(90/30.0))*60,36.,180.);double sum=0;for(int j=1;j<=75;++j)sum+=bpms[idx-75+j];double avg=sum/75,k=fc-(90+first+10)+2;avgs[idx]=avgs[idx-1]*k/(k+2.5)+avg*2.5/(k+2.5);}
    if(peaks[idx])last=idx;
   }
  }
  if(calibrated()&&fc>90+first+9+75&&std::abs(avgs[fc-100]-avgs[fc-101])<.083&&std::abs(avgs[fc-55]-avgs[fc-56])<.066&&std::abs(avgs[fc-10]-avgs[fc-11])<.05)show=true;
  int at=idx<0?fc-1:idx;return{fc,points.back(),idx,idx<0?0:peaks[idx],bpms[at],avgs[at],int(calibrated()),latest(),int(final()),int(show),int(missed)};
 }
};
