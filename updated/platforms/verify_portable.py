#!/usr/bin/env python3
"""Compare every native trace field with the earlier faithful Python port.

Use file-backed input/output so the full recording cannot deadlock pipe buffers.
This verifies translation parity, including inherited quirks, not pulse accuracy.
"""
import argparse,csv,json,math,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from heartbeat_port.algorithm import HeartbeatAlgorithm
p=argparse.ArgumentParser();p.add_argument('executable',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
data=Path(__file__).parent/'data/bidmc01-ppg.csv'
fixtures=[('bidmc01',[float(r['sample']) for r in csv.DictReader(data.open())],60),('synthetic84',[.5+.1*math.sin(i/30*2*math.pi*1.4) for i in range(900)],60),('synthetic110',[.5+.1*math.sin(i/30*2*math.pi*110/60) for i in range(900)],45)]
results=[]
with tempfile.TemporaryDirectory() as t:
 for name,values,window in fixtures:
  inp=Path(t)/'input';out=Path(t)/'output';inp.write_text(''.join(format(x,'.17g')+'\n' for x in values))
  with inp.open() as fi,out.open('w') as fo:subprocess.run([str(a.executable.resolve()),str(window)],stdin=fi,stdout=fo,check=True,timeout=60)
  rows=list(csv.DictReader(out.open()));assert len(rows)==len(values),(name,'frame count')
  alg=HeartbeatAlgorithm(filter_window_size=window);mismatches=[]
  for row,value in zip(rows,values):
   expected_trace=vars(alg.trace_frame(value));assert set(row)==set(expected_trace),(name,'trace schema')
   for key,expected in expected_trace.items():
    if float(row[key])!=expected:mismatches.append([int(row['frame']),key,float(row[key]),expected])
  results.append(dict(fixture=name,frames=len(rows),fields=len(expected_trace),mismatches=len(mismatches),first_mismatches=mismatches[:3]))
print(json.dumps(results,indent=2))
if a.output:a.output.write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(int(any(r['mismatches'] for r in results)))
