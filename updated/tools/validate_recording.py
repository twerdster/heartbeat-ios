#!/usr/bin/env python3
"""Replay BIDMC01 pulse-oximeter PPG through the recovered processing chain.

Inputs stay outside the repository. No reference HR is used to tune processing.
PPG is already within [0,1]; it is not a camera green-channel recording.
Requires NumPy for resampling and recorded numerical summaries.
"""
import argparse
from datetime import datetime
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heartbeat_port import HeartbeatAlgorithm
from heartbeat_port.corrected import TimestampedHeartbeat


def read_csv(path):
    with path.open() as f:
        rows=list(csv.DictReader(f,skipinitialspace=True))
    return {key:np.array([float(r[key]) for r in rows]) for key in rows[0]}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('validation/2026-11-14'))
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    sp=args.data/'bidmc_01_Signals.csv';np_=args.data/'bidmc_01_Numerics.csv'
    signal=read_csv(sp);reference=read_csv(np_)
    t=signal['Time [s]'];ppg=signal['PLETH']
    if not np.all(np.isfinite(ppg)) or not 0<=ppg.min()<=ppg.max()<=1:
        raise ValueError('recording must contain finite PPG in [0,1]')
    ticks=np.arange(int(round((t[-1]-t[0])*30))+1)/30+t[0]
    resampled=np.interp(ticks,t,ppg)
    legacy=HeartbeatAlgorithm();guarded=TimestampedHeartbeat()
    legacy_bpm=[];guarded_bpm=[];statuses=[]
    for timestamp,value in zip(ticks,resampled):
        legacy.new_frame_with_green_component(float(value))
        estimate=guarded.update(float(timestamp),float(value))
        legacy_bpm.append(legacy.bpm_latest_result)
        guarded_bpm.append(estimate.bpm if estimate.bpm is not None else np.nan)
        statuses.append(estimate.status)
    rows=[]
    for ti,hr,pulse in zip(reference['Time [s]'],reference['HR'],reference['PULSE']):
        index=min(len(ticks)-1,int(round((ti-t[0])*30)))
        rows.append([float(ti),float(hr),float(pulse),legacy_bpm[index],guarded_bpm[index],statuses[index]])
    with (args.out/'bidmc01-1hz.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['time_s','reference_ecg_hr_bpm','reference_ppg_pulse_bpm','legacy_bpm','guarded_bpm','guarded_status']);w.writerows(rows)
    pairs=np.array([r[:5] for r in rows],float)
    eligible=(pairs[:,0]>=10)&np.isfinite(pairs[:,1])&(pairs[:,1]>0)
    metrics={}
    for col,name in [(3,'legacy'),(4,'guarded')]:
        valid=eligible&np.isfinite(pairs[:,col])&(pairs[:,col]>0)
        e=pairs[valid,col]-pairs[valid,1]
        metrics[name]={'pairs':int(valid.sum()),'eligible_reference_seconds':int(eligible.sum()),'coverage':float(valid.sum()/eligible.sum()),'mae_bpm':float(np.abs(e).mean()),'rmse_bpm':float(np.sqrt(np.mean(e*e))),'bias_bpm':float(e.mean()),'max_abs_error_bpm':float(np.abs(e).max())}
    result={'date':datetime.now().astimezone().date().isoformat(),'run_timestamp':datetime.now().astimezone().isoformat(),'record':'BIDMC01, entire 480 s recording; first 10 s excluded from metrics','input':'pulse-oximeter PPG, not camera video; original [0,1] amplitude retained','source':'https://physionet.org/content/bidmc/1.0.0/','license':'Open Data Commons Attribution 1.0','processing':'linear offline resampling 125 Hz to 30 Hz; recovered Butterworth/window/peak/count/smoothing chain; guarded mode disables forced peaks and gates flat/missing input','reference':'ECG-derived HR at 1 Hz, not PPG-derived PULSE; no lag fitting or rate tuning','samples_in':len(t),'samples_30hz':len(ticks),'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,'metrics':metrics,'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [sp,np_]}}
    (args.out/'bidmc01-metrics.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez(args.out/'bidmc01-render.npz',time=t,ppg=ppg,ticks=ticks,resampled=resampled,reference=pairs,legacy=np.array(legacy_bpm),guarded=np.array(guarded_bpm))
    print(json.dumps(metrics,indent=2))


if __name__=='__main__':main()
