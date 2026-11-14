#include "heartbeat_core.hpp"
extern "C" {
void* hb_create(){return new HeartbeatCore;}
void hb_destroy(void*p){delete static_cast<HeartbeatCore*>(p);}
void hb_step(void*p,double g,double*out){auto t=static_cast<HeartbeatCore*>(p)->step(g);double v[]={double(t.frame),t.value,double(t.peak_index),double(t.is_peak),t.bpm_value,t.bpm_average,double(t.calibration_over),t.bpm_latest,double(t.final_determined),double(t.should_show),double(t.missed_last_peak)};std::copy(v,v+11,out);}
}
