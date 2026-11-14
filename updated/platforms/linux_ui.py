#!/usr/bin/env python3
"""New Tk replay interface; every sample calls the compiled C++ state machine."""

import argparse
import csv
import ctypes
import json
import math
import os
from pathlib import Path
import tempfile
import time


def read_samples(path):
    """Reject malformed replay input before passing samples to the estimator."""
    with Path(path).open(newline="", encoding="utf-8") as stream:
        rows = csv.reader(stream)
        if next(rows, None) != ["sample"]:
            raise ValueError("Input CSV must have one column headed sample")
        values = []
        for line, row in enumerate(rows, 2):
            if len(row) != 1:
                raise ValueError(f"Input CSV line {line}: expected one sample")
            try:
                value = float(row[0])
            except ValueError as error:
                raise ValueError(f"Input CSV line {line}: invalid number") from error
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(
                    f"Input CSV line {line}: sample must be finite and in 0–1"
                )
            values.append(value)
    if not values:
        raise ValueError("Input CSV contains no samples")
    return values


def atomic_json(path, payload):
    """Atomically replace one JSON file; leave an existing file intact on failure."""
    path = Path(path)
    data = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_snapshot(output, payload, synthetic):
    """Return a checked error instead of interrupting the processing callback."""
    output = Path(output)
    stem = "synthetic84" if synthetic else "bidmc01"
    try:
        atomic_json(output, payload)
        atomic_json(output.with_name(f"{stem}-state.json"), payload)
        if payload["complete"]:
            atomic_json(output.with_name(f"{stem}-complete.json"), payload)
    except (OSError, ValueError) as error:
        return f"{type(error).__name__}: {error}"
    return None


def main():
    import tkinter as tk

    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument(
        "--data", type=Path, default=Path(__file__).parent / "data/bidmc01-ppg.csv"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    values = read_samples(args.data)
    lib = ctypes.CDLL(str(args.library.resolve()))
    lib.hb_create.argtypes = []
    lib.hb_create.restype = ctypes.c_void_p
    lib.hb_destroy.restype = None
    lib.hb_step.restype = None
    lib.hb_destroy.argtypes = [ctypes.c_void_p]
    lib.hb_step.argtypes = [
        ctypes.c_void_p,
        ctypes.c_double,
        ctypes.POINTER(ctypes.c_double),
    ]
    root = tk.Tk()
    root.title("HeartBeat — updated native replay")
    root.geometry("900x730")
    root.configure(bg="#090e17")
    frame = tk.Frame(root, bg="#090e17")
    frame.pack(fill="both", expand=True, padx=28, pady=22)

    def label(text, size, color="#f2f2f2"):
        widget = tk.Label(
            frame,
            text=text,
            font=("Sans", size),
            fg=color,
            bg="#090e17",
            anchor="w",
            justify="left",
        )
        widget.pack(fill="x", pady=5)
        return widget

    label("HeartBeat / native replay", 25)
    label("Linux · compiled C++ processing", 14, "#33d9cc")
    source = label("BIDMC01 · recorded pulse-oximeter signal", 16)
    label("30 Hz input · nominal 6× replay · no camera input", 14, "#aaaaaa")
    bpm = label("—", 58, "#33d9cc")
    label("beats / minute · recovered estimator", 14, "#aaaaaa")
    canvas = tk.Canvas(frame, bg="#121a26", highlightthickness=0, height=230)
    canvas.pack(fill="both", expand=True, pady=15)
    status = label("Calibrating", 14)
    buttons = tk.Frame(frame, bg="#090e17")
    buttons.pack(fill="x", pady=10)
    core = lib.hb_create()
    position, history = 0, []
    trace = (ctypes.c_double * 11)()
    paused = synthetic = False
    save_error = None
    completion_saved = False
    next_save_attempt = 0.0

    def reset():
        nonlocal core, position, history, paused, trace, save_error, completion_saved, next_save_attempt
        lib.hb_destroy(core)
        core = lib.hb_create()
        position, history = 0, []
        trace = (ctypes.c_double * 11)()
        paused = completion_saved = False
        save_error, next_save_attempt = None, 0.0
        pause.config(text="Pause")

    def toggle():
        nonlocal paused
        paused = not paused
        pause.config(text="Resume" if paused else "Pause")

    def change():
        nonlocal synthetic
        synthetic = not synthetic
        source.config(
            text=(
                "Synthetic waveform · known rate 84 bpm"
                if synthetic
                else "BIDMC01 · recorded pulse-oximeter signal"
            )
        )
        reset()

    for name, command in [
        ("Pause", toggle),
        ("Restart", reset),
        ("Switch input", change),
    ]:
        button = tk.Button(buttons, text=name, command=command, font=("Sans", 13))
        button.pack(side="left", expand=True, fill="x", padx=6)
        if name == "Pause":
            pause = button
    label(
        "Updated replay interface. Original authors: Or Maayan and Michael Leybovich.\nResearch prototype; not a clinical measurement. Input: BIDMC/PhysioNet 1.0.0 · ODC-By 1.0.",
        11,
        "#aaaaaa",
    )

    def save(total):
        nonlocal save_error, completion_saved, next_save_attempt
        payload = dict(
            implementation="C++ translation of recovered Algorithm.mm with bounded native filter",
            input="synthetic 84 bpm" if synthetic else "BIDMC01 recorded PPG",
            frames=position,
            total_frames=total,
            bpm=trace[7] if trace[6] else None,
            calibrated=bool(trace[6]),
            complete=position == total,
            source_hz=30,
            nominal_replay_speed=6,
        )
        save_error = save_snapshot(args.output, payload, synthetic)
        completion_saved = position == total and save_error is None
        next_save_attempt = time.monotonic() + 1.0

    def tick():
        nonlocal position
        total = 900 if synthetic else len(values)
        if not paused and position < total:
            for _ in range(min(6, total - position)):
                value = (
                    0.5 + 0.1 * math.sin(position / 30 * 2 * math.pi * 1.4)
                    if synthetic
                    else values[position]
                )
                lib.hb_step(core, value, trace)
                history.append(value)
                position += 1
            if position % 90 == 0 or position == total:
                save(total)
        elif (
            position == total
            and not completion_saved
            and time.monotonic() >= next_save_attempt
        ):
            save(total)
        bpm.config(text=f"{trace[7]:.1f}" if trace[6] else "—")
        state = (
            "Paused"
            if paused
            else (
                "Complete · results saved on host"
                if completion_saved
                else (
                    "Complete · results not saved"
                    if position == total
                    else (
                        "Estimating · legacy smoothing retained"
                        if trace[6]
                        else "Calibrating from observed input"
                    )
                )
            )
        )
        if save_error:
            state += f"\nSave error · retrying: {save_error}"
        status.config(
            text=f"Frame {position} / {total} · {position / 30:.1f} s of input\n{state}",
            fg="#ffb88c" if save_error else "#f2f2f2",
            wraplength=820,
        )
        canvas.delete("all")
        width, height = canvas.winfo_width(), canvas.winfo_height()
        for index in range(1, 4):
            canvas.create_line(
                0, index * height / 4, width, index * height / 4, fill="#263b4d"
            )
        recent = history[-240:]
        if len(recent) > 1:
            low, high = min(recent), max(recent)
            if high - low < 1e-8:
                low -= 0.1
                high += 0.1
            points = []
            for index, value in enumerate(recent):
                points.extend(
                    [
                        index / 239 * width,
                        height - 12 - (value - low) / (high - low) * (height - 24),
                    ]
                )
            canvas.create_line(*points, fill="#33d9cc", width=2)
        root.after(33, tick)

    def close():
        lib.hb_destroy(core)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close)
    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
