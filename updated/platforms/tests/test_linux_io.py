"""Run 28 replay-input/IO checks, including real C++ processing with fake Tk widgets.

From updated/ after building the shared library:
    python3 platforms/tests/test_linux_io.py --library build/native/libheartbeat_core.so

No display or device is opened. These checks cover malformed CSV rejection,
atomic replacement failures and temporary-file cleanup, completion preservation,
and the actual Linux UI callbacks processing all 14,401 bundled BIDMC01 samples
through the compiled core during a blocked-output failure. They then restore
write access and verify automatic completion-save recovery and final parity.
The widgets and clock are fakes: this is not a real GUI/capture test, a clinical
accuracy check, or Android runtime coverage. --result optionally saves the JSON
assertion record. Use the bundled, unchanged BIDMC01 fixture for this check.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
from unittest.mock import patch

p = argparse.ArgumentParser()
p.add_argument(
    "--source", type=Path, default=Path(__file__).resolve().parents[1] / "linux_ui.py"
)
p.add_argument(
    "--data",
    type=Path,
    default=Path(__file__).resolve().parents[1] / "data/bidmc01-ppg.csv",
)
p.add_argument("--library", type=Path, required=True)
p.add_argument("--result", type=Path)
a = p.parse_args()
spec = importlib.util.spec_from_file_location("heartbeat_linux_ui", a.source)
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)
checks = []


def check(value, name):
    assert value, name
    checks.append(name)


with tempfile.TemporaryDirectory(prefix="heartbeat-io-qa-") as temporary:
    directory = Path(temporary)
    csv = directory / "input.csv"
    csv.write_text("sample\n0\n0.5\n1\n")
    check(ui.read_samples(csv) == [0.0, 0.5, 1.0], "valid sample header/range")
    for text in (
        "green\n0.5\n",
        "sample,other\n.5,1\n",
        "sample\n",
        "sample\nnan\n",
        "sample\ninf\n",
        "sample\n-0.1\n",
        "sample\n1.1\n",
        "sample\nword\n",
        "sample\n.5,.6\n",
    ):
        csv.write_text(text)
        try:
            ui.read_samples(csv)
            raise AssertionError("accepted malformed CSV: " + text)
        except ValueError:
            checks.append("rejected malformed CSV " + repr(text))
    target = directory / "native-state.json"
    progress = dict(frames=90, complete=False)
    complete = dict(frames=14401, complete=True)
    check(ui.save_snapshot(target, progress, False) is None, "progress write succeeds")
    check(
        not (directory / "bidmc01-complete.json").exists(),
        "progress does not create completion",
    )
    check(
        ui.save_snapshot(target, complete, False) is None, "completion write succeeds"
    )
    check(
        ui.save_snapshot(target, progress, False) is None,
        "restart progress write succeeds",
    )
    check(
        json.loads((directory / "bidmc01-complete.json").read_text()) == complete,
        "restart preserves completed result",
    )
    before = target.read_bytes()
    with patch.object(
        ui.os, "replace", side_effect=OSError("injected atomic replacement failure")
    ):
        check(
            ui.save_snapshot(target, complete, False) is not None,
            "replacement failure is checked",
        )
    check(target.read_bytes() == before, "failed replacement preserves existing JSON")
    check(
        not list(directory.glob("*.tmp")) and not list(directory.glob(".*.tmp")),
        "failed replacement cleans temporary file",
    )
    check(
        ui.save_snapshot(
            target, dict(frames=0, complete=False, bpm=float("nan")), False
        )
        is not None,
        "nonfinite JSON rejected",
    )
    check(target.read_bytes() == before, "nonfinite JSON does not alter existing file")

    # No display is opened. These widgets only drive the real UI callbacks; the
    # unchanged shared C++ library computes all 14,401 signal samples through ctypes.
    blocked = directory / "blocked-output-directory"
    blocked.write_text("a file cannot be an output directory")
    output = blocked / "native-state.json"
    clock = [0.0]
    widgets = []
    state = dict(saw_save_error=False, saw_complete_unsaved=False, recovered=False)

    class Widget:
        def __init__(self, *args, **kwargs):
            self.options = dict(kwargs)
            widgets.append(self)

        def pack(self, **kwargs):
            pass

        def config(self, **kwargs):
            self.options.update(kwargs)

        def delete(self, *args):
            pass

        def create_line(self, *args, **kwargs):
            pass

        def winfo_width(self):
            return 820

        def winfo_height(self):
            return 230

    class Root(Widget):
        def __init__(self):
            super().__init__()
            self.queue = []
            self.protocols = {}

        def title(self, value):
            pass

        def geometry(self, value):
            pass

        def configure(self, **kwargs):
            pass

        def after(self, delay, function):
            self.queue.append((delay, function))

        def protocol(self, event, function):
            self.protocols[event] = function

        def destroy(self):
            pass

        def mainloop(self):
            for tick in range(5000):
                delay, callback = self.queue.pop(0)
                clock[0] += delay / 1000
                callback()
                status = next(
                    w.options.get("text", "")
                    for w in widgets
                    if w.options.get("text", "").startswith("Frame ")
                )
                if "Save error" in status:
                    state["saw_save_error"] = True
                if (
                    "Frame 14401 / 14401" in status
                    and "Complete · results not saved" in status
                    and not state["saw_complete_unsaved"]
                ):
                    state["saw_complete_unsaved"] = True
                    check(
                        not (blocked / "bidmc01-complete.json").exists(),
                        "write failure does not claim completion file",
                    )
                    blocked.unlink()
                    blocked.mkdir()
                if "Complete · results saved on host" in status:
                    state["recovered"] = True
                    data = json.loads(output.read_text())
                    check(
                        data["frames"] == 14401 and data["complete"],
                        "live processing completes despite save failures",
                    )
                    check(
                        abs(data["bpm"] - 90.86146811423824) < 1e-9,
                        "unchanged C++ final estimate after write failure",
                    )
                    check(
                        json.loads((blocked / "bidmc01-complete.json").read_text())
                        == data,
                        "completion retry writes separate completed result",
                    )
                    self.protocols["WM_DELETE_WINDOW"]()
                    return
            raise AssertionError("UI callback loop did not recover")

    fake_tk = types.SimpleNamespace(
        Tk=Root, Frame=Widget, Label=Widget, Canvas=Widget, Button=Widget
    )
    arguments = [
        "linux_ui.py",
        "--library",
        str(a.library),
        "--data",
        str(a.data),
        "--output",
        str(output),
    ]
    with patch.dict(sys.modules, {"tkinter": fake_tk}), patch.object(
        sys, "argv", arguments
    ), patch.object(ui.time, "monotonic", lambda: clock[0]):
        ui.main()
    check(state["saw_save_error"], "UI exposes save failure while processing continues")
    check(
        state["saw_complete_unsaved"], "UI does not falsely claim saved at completion"
    )
    check(state["recovered"], "UI retries and recovers after output becomes writable")
    check(
        any("nominal 6× replay" in w.options.get("text", "") for w in widgets),
        "nominal replay label retained",
    )
result = dict(
    status="passed",
    checks=len(checks),
    assertions=checks,
    scope="Filesystem faults and headless Tk callback integration with actual C++ core; no GUI/display capture or device calls",
    frames_processed=14401,
    final_bpm=90.86146811423824,
)
if a.result is not None:
    a.result.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
