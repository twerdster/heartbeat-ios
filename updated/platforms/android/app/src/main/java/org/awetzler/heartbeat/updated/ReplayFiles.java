package org.awetzler.heartbeat.updated;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;

/** Replay input and checked, per-file atomic result storage; no estimator changes. */
final class ReplayFiles {
    private ReplayFiles() {}

    static ArrayList<Double> readSamples(Reader source) throws IOException {
        BufferedReader input = new BufferedReader(source);
        if (!"sample".equals(input.readLine())) {
            throw new IOException("Input CSV must have one column headed sample");
        }
        ArrayList<Double> result = new ArrayList<>();
        String row;
        int line = 1;
        while ((row = input.readLine()) != null) {
            line++;
            final double value;
            try {
                value = Double.parseDouble(row);
            } catch (NumberFormatException error) {
                throw new IOException("Input CSV line " + line + ": invalid sample", error);
            }
            if (!Double.isFinite(value) || value < 0 || value > 1) {
                throw new IOException("Input CSV line " + line + ": sample must be finite and in 0–1");
            }
            result.add(value);
        }
        if (result.isEmpty()) throw new IOException("Input CSV contains no samples");
        return result;
    }

    static void atomicWrite(File target, String payload) throws IOException {
        Path parent = target.getAbsoluteFile().getParentFile().toPath();
        Files.createDirectories(parent);
        Path temporary = Files.createTempFile(parent, "." + target.getName() + ".", ".tmp");
        try {
            try (FileOutputStream stream = new FileOutputStream(temporary.toFile())) {
                stream.write((payload + "\n").getBytes(StandardCharsets.UTF_8));
                stream.flush();
                stream.getFD().sync();
            }
            // API 26+ supports java.nio.file. Report a failed replacement instead
            // of falling back to deleting and rewriting a visible result file.
            Files.move(temporary, target.toPath(), StandardCopyOption.ATOMIC_MOVE,
                       StandardCopyOption.REPLACE_EXISTING);
        } finally {
            Files.deleteIfExists(temporary);
        }
    }

    /** null means all requested writes succeeded; an error leaves processing to the UI. */
    static String saveSnapshot(File directory, String stem, String payload, boolean complete) {
        try {
            atomicWrite(new File(directory, "native-state.json"), payload);
            atomicWrite(new File(directory, stem + "-state.json"), payload);
            if (complete) atomicWrite(new File(directory, stem + "-complete.json"), payload);
            return null;
        } catch (IOException | SecurityException error) {
            return error.getClass().getSimpleName() + ": " + error.getMessage();
        }
    }
}
