#include <jni.h>
#include "heartbeat_core.hpp"
extern "C" JNIEXPORT jlong JNICALL Java_org_awetzler_heartbeat_updated_MainActivity_create(JNIEnv*,jclass){return reinterpret_cast<jlong>(new HeartbeatCore);}
extern "C" JNIEXPORT void JNICALL Java_org_awetzler_heartbeat_updated_MainActivity_destroy(JNIEnv*,jclass,jlong p){delete reinterpret_cast<HeartbeatCore*>(p);}
extern "C" JNIEXPORT jdoubleArray JNICALL Java_org_awetzler_heartbeat_updated_MainActivity_step(JNIEnv*e,jclass,jlong p,jdouble g){auto t=reinterpret_cast<HeartbeatCore*>(p)->step(g);double a[]={double(t.frame),t.value,double(t.peak_index),double(t.is_peak),t.bpm_value,t.bpm_average,double(t.calibration_over),t.bpm_latest,double(t.final_determined),double(t.should_show),double(t.missed_last_peak)};auto out=e->NewDoubleArray(11);e->SetDoubleArrayRegion(out,0,11,a);return out;}
