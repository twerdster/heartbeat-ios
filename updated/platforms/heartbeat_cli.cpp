#include "heartbeat_core.hpp"
#include <iostream>
#include <iomanip>
#include <string>
#include <cmath>
int main(int argc,char**argv){std::ios::sync_with_stdio(false);std::cin.tie(nullptr);if(argc>2||(argc==2&&std::string(argv[1])!="45"&&std::string(argv[1])!="60")){std::cerr<<"usage: heartbeat_cli [45|60] < numeric-green-samples\n";return 2;}HeartbeatCore core(argc>1?std::stoi(argv[1]):60);double g;std::cout<<"frame,value,peak_index,is_peak,bpm_value,bpm_average,calibration_over,bpm_latest,final_determined,should_show,missed_last_peak\n"<<std::setprecision(17);while(std::cin>>g){if(!std::isfinite(g)||g<0||g>1){std::cerr<<"Expected finite green components in [0,1]\n";return 2;}auto t=core.step(g);std::cout<<t.frame<<','<<t.value<<','<<t.peak_index<<','<<t.is_peak<<','<<t.bpm_value<<','<<t.bpm_average<<','<<t.calibration_over<<','<<t.bpm_latest<<','<<t.final_determined<<','<<t.should_show<<','<<t.missed_last_peak<<'\n';}if(!std::cin.eof()){std::cerr<<"Invalid numeric input\n";return 2;}}
