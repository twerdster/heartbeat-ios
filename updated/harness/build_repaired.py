#!/usr/bin/env python3
"""Build the original Objective-C++ algorithm with the separately repaired filter.

The only substituted numerical source is updated/native/Butterworth.cpp.
Original source and the existing original-code comparison remain unchanged.
"""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_original import HERE, UPDATED, SOURCE, BUILD, VARIANTS, compiler


def build(variant='strict'):
    cxx = compiler()
    if not cxx:
        raise RuntimeError('clang++ is required')
    BUILD.mkdir(exist_ok=True)
    flags = VARIANTS[variant]
    common = ['-std=c++17', '-w', f'-I{SOURCE}', f'-I{HERE}', *flags]
    jobs = [(UPDATED/'native/Butterworth.cpp', ['-x', 'c++']),
            (SOURCE/'Algorithm.mm', ['-x', 'objective-c++', '-fobjc-arc', '-include', str(HERE/'uikit_shim.h')]),
            (HERE/'trace_main.mm', ['-x', 'objective-c++', '-fobjc-arc'])]
    objects = []
    for source, language in jobs:
        obj = BUILD/f'{source.stem}_repaired_{variant}.o'
        subprocess.run([cxx, *language, *common, '-c', str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    exe = BUILD/f'heartbeat_trace_repaired_{variant}'
    subprocess.run([cxx, *flags, *objects, '-framework', 'Foundation', '-o', str(exe)], check=True)
    return exe


if __name__ == '__main__':
    print(build(sys.argv[1] if len(sys.argv)>1 else 'strict'))
