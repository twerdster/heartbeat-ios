package org.awetzler.heartbeat.updated;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Locale;
import org.json.JSONObject;

public class MainActivity extends Activity {
    static { System.loadLibrary("heartbeat_jni"); }
    static native long create();
    static native void destroy(long handle);
    static native double[] step(long handle, double sample);

    long core;
    ArrayList<Double> values = new ArrayList<>(), history = new ArrayList<>();
    int position;
    boolean paused, synthetic, completionSaved;
    String inputError, saveError;
    long nextSaveAttempt;
    double[] trace = new double[11];
    Handler handler = new Handler();
    Plot plot;
    TextView status, bpm, source;
    Button pause;

    public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        try (InputStreamReader input = new InputStreamReader(
                getAssets().open("bidmc01-ppg.csv"), StandardCharsets.UTF_8)) {
            values = ReplayFiles.readSamples(input);
        } catch (Exception error) {
            inputError = error.getMessage();
        }
        core = create();
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(22, 24, 22, 14);
        root.setBackgroundColor(Color.rgb(9, 14, 23));
        setContentView(root);
        label(root, "HeartBeat / native replay", 25, Color.WHITE);
        label(root, "Android · computed on this device", 14, Color.rgb(51, 217, 204));
        source = label(root, "BIDMC01 · recorded pulse-oximeter signal", 16, Color.WHITE);
        label(root, "30 Hz input · nominal 6× replay · no camera input", 14, Color.LTGRAY);
        bpm = label(root, "—", 62, Color.rgb(51, 217, 204));
        label(root, "beats / minute · recovered estimator", 14, Color.LTGRAY);
        plot = new Plot();
        root.addView(plot, new LinearLayout.LayoutParams(-1, 0, 1));
        status = label(root, "Calibrating", 14, Color.WHITE);
        LinearLayout buttons = new LinearLayout(this);
        root.addView(buttons);
        pause = button(buttons, "Pause");
        pause.setOnClickListener(view -> {
            paused = !paused;
            pause.setText(paused ? "Resume" : "Pause");
        });
        button(buttons, "Restart").setOnClickListener(view -> reset());
        button(buttons, "Switch input").setOnClickListener(view -> {
            synthetic = !synthetic;
            reset();
        });
        label(root, "Updated replay interface. Original authors: Or Maayan and Michael Leybovich. "
                + "Research prototype; not a clinical measurement. Input: BIDMC / PhysioNet 1.0.0 · ODC-By 1.0.",
                12, Color.LTGRAY);
    }

    TextView label(LinearLayout root, String text, int size, int color) {
        TextView widget = new TextView(this);
        widget.setText(text);
        widget.setTextSize(size);
        widget.setTextColor(color);
        widget.setPadding(0, 8, 0, 8);
        root.addView(widget);
        return widget;
    }

    Button button(LinearLayout root, String text) {
        Button widget = new Button(this);
        widget.setText(text);
        root.addView(widget, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        return widget;
    }

    void reset() {
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        destroy(core);
        core = create();
        position = 0;
        history.clear();
        trace = new double[11];
        paused = completionSaved = false;
        saveError = null;
        nextSaveAttempt = 0;
        pause.setText("Pause");
        source.setText(synthetic ? "Synthetic waveform · known rate 84 bpm"
                                 : "BIDMC01 · recorded pulse-oximeter signal");
        handler.removeCallbacks(tick);
        handler.post(tick);
    }

    final Runnable tick = new Runnable() {
        public void run() {
            if (!synthetic && inputError != null) {
                status.setText("Input error · " + inputError);
                status.setTextColor(Color.rgb(255, 184, 140));
                getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                return;
            }
            int total = synthetic ? 900 : values.size();
            if (!paused && position < total) {
                for (int index = 0; index < 6 && position < total; index++) {
                    double sample = synthetic ? .5 + .1 * Math.sin(position / 30. * 2 * Math.PI * 1.4)
                                              : values.get(position);
                    trace = step(core, sample);
                    history.add(sample);
                    position++;
                }
                if (position % 90 == 0 || position == total) save(total);
            } else if (position == total && !completionSaved
                       && SystemClock.uptimeMillis() >= nextSaveAttempt) {
                save(total);
            }
            bpm.setText(trace[6] > 0 ? String.format(Locale.US, "%.1f", trace[7]) : "—");
            String state = paused ? "Paused" : completionSaved ? "Complete · results saved on device"
                    : position == total ? "Complete · results not saved"
                    : trace[6] > 0 ? "Estimating · legacy smoothing retained" : "Calibrating from observed input";
            if (saveError != null) state += "\nSave error · retrying: " + saveError;
            status.setText(String.format(Locale.US, "Frame %d / %d · %.1f s\n%s", position, total, position / 30., state));
            status.setTextColor(saveError == null ? Color.WHITE : Color.rgb(255, 184, 140));
            plot.invalidate();
            if (position < total || !completionSaved) handler.postDelayed(this, 33);
            else getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        }
    };

    void save(int total) {
        try {
            JSONObject data = new JSONObject();
            data.put("implementation", "C++ translation of recovered Algorithm.mm with bounded native filter");
            data.put("input", synthetic ? "synthetic 84 bpm" : "BIDMC01 recorded PPG");
            data.put("frames", position);
            data.put("total_frames", total);
            data.put("bpm", trace[6] > 0 ? trace[7] : JSONObject.NULL);
            data.put("complete", position == total);
            data.put("source_hz", 30);
            data.put("nominal_replay_speed", 6);
            data.put("calibrated", trace[6] > 0);
            saveError = ReplayFiles.saveSnapshot(getFilesDir(), synthetic ? "synthetic84" : "bidmc01",
                                                data.toString(2), position == total);
        } catch (Exception error) {
            saveError = error.getClass().getSimpleName() + ": " + error.getMessage();
        }
        completionSaved = position == total && saveError == null;
        nextSaveAttempt = SystemClock.uptimeMillis() + 1000;
    }

    protected void onResume() {
        super.onResume();
        handler.removeCallbacks(tick);
        if (plot != null) handler.post(tick);
    }

    protected void onPause() {
        handler.removeCallbacks(tick);
        super.onPause();
    }

    protected void onDestroy() {
        handler.removeCallbacks(tick);
        destroy(core);
        super.onDestroy();
    }

    class Plot extends View {
        Paint paint = new Paint(3);
        Plot() { super(MainActivity.this); }

        protected void onDraw(Canvas canvas) {
            canvas.drawColor(Color.rgb(18, 26, 38));
            int begin = Math.max(0, history.size() - 240);
            double low = 1, high = 0;
            for (int index = begin; index < history.size(); index++) {
                low = Math.min(low, history.get(index));
                high = Math.max(high, history.get(index));
            }
            if (high - low < 1e-8) { low -= .1; high += .1; }
            paint.setColor(Color.rgb(51, 217, 204));
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(3);
            Path path = new Path();
            for (int index = begin; index < history.size(); index++) {
                float x = (float)((index - begin) / 239. * getWidth());
                float y = (float)(getHeight() - 16 - (history.get(index) - low) / (high - low) * (getHeight() - 32));
                if (index == begin) path.moveTo(x, y); else path.lineTo(x, y);
            }
            canvas.drawPath(path, paint);
        }
    }
}
