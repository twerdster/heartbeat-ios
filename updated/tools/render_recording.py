#!/usr/bin/env python3
"""Render measured BIDMC01 traces, not an invented app interface.

Requires NumPy, Matplotlib, Pillow and ffmpeg. Metrics come from the saved replay.
"""
import argparse
import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=Path('assets'))
    ap.add_argument('--frames',type=Path,default=Path('build/heartbeat-frames'))
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True);args.frames.mkdir(parents=True,exist_ok=True)
    data=np.load(args.results/'bidmc01-render.npz');metrics=json.loads((args.results/'bidmc01-metrics.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#34495e','xtick.color':'#566573','ytick.color':'#566573'})
    fig=plt.figure(figsize=(10,6),dpi=100,facecolor='#f5f8fa')
    fig.text(.07,.94,'Heartbeat · recorded pulse replay',fontsize=22,weight='bold',color='#102a43')
    fig.text(.07,.895,'BIDMC01 pulse-oximeter PPG · offline 30 Hz replay · not phone-camera data',fontsize=11,color='#52697f')
    m=metrics['metrics'];fig.text(.07,.828,f"Legacy chain   {m['legacy']['mae_bpm']:.2f} bpm MAE",fontsize=15,color='#087e8b',weight='bold')
    fig.text(.51,.828,f"Guarded mode   {m['guarded']['mae_bpm']:.2f} bpm MAE",fontsize=15,color='#a85b18',weight='bold')
    fig.text(.07,.79,'All 471 eligible 1 Hz samples, 10–480 s; ECG-derived HR reference; no fitted time lag.',fontsize=10,color='#52697f')
    ax=fig.add_axes([.08,.47,.86,.25],facecolor='white')
    r=data['reference'];ax.plot(r[:,0],r[:,1],color='#263746',lw=2,label='Recorded ECG HR')
    ax.plot(data['ticks'],data['legacy'],color='#087e8b',lw=1.2,label='Legacy chain')
    ax.plot(data['ticks'],data['guarded'],color='#d7843e',lw=1,alpha=.8,label='Guarded mode')
    ax.set(xlim=(0,480),ylim=(80,102),ylabel='Heart rate (bpm)',xlabel='Full recording (s)');ax.grid(alpha=.15)
    ax.legend(loc='lower right',fontsize=9,ncol=3,frameon=False)
    playhead=ax.axvline(0,color='#b63054',lw=1.5)
    bx=fig.add_axes([.08,.14,.86,.17],facecolor='white');wave,=bx.plot([],[],color='#087e8b',lw=1.8)
    bx.set(ylim=(.2,.72),ylabel='PPG (sensor units)',xlabel='Recording time (s)');bx.grid(alpha=.15)
    label=fig.text(.08,.355,'',fontsize=11,color='#b63054')
    fig.text(.07,.025,'Source: PhysioNet BIDMC v1.0.0 (Pimentel et al.) · ODC Attribution 1.0 · Filter bounds repaired; original preserved.',fontsize=9,color='#52697f')
    for i,end in enumerate(np.linspace(10,70,72)):
        mask=(data['time']>=end-10)&(data['time']<=end)
        wave.set_data(data['time'][mask],data['ppg'][mask]);bx.set_xlim(end-10,end)
        playhead.set_xdata([end,end]);label.set_text(f'10–70 s excerpt · 10× saved playback · t = {end:.1f} s')
        fig.savefig(args.frames/f'{i:04d}.png',dpi=100,facecolor=fig.get_facecolor())
    fig.savefig(args.out/'heartbeat-recording.png',dpi=150,facecolor=fig.get_facecolor())
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(args.frames/'%04d.png'),'-c:v','libx264','-crf','24','-pix_fmt','yuv420p','-movflags','+faststart',str(args.out/'heartbeat-recording.mp4')],check=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(args.out/'heartbeat-recording.mp4'),'-filter_complex','fps=8,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer:bayer_scale=3','-loop','0',str(args.out/'heartbeat-recording.gif')],check=True)


if __name__=='__main__':main()
