package org.awetzler.heartbeat.updated;

import java.io.File;
import java.io.IOException;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;

/** Plain-JVM filesystem checks; no Android device or estimator required. */
public final class ReplayFilesTest {
    static int checks;

    static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
        checks++;
    }

    static String read(Path path) throws IOException {
        return new String(Files.readAllBytes(path), StandardCharsets.UTF_8).trim();
    }

    public static void main(String[] args) throws Exception {
        check(ReplayFiles.readSamples(new StringReader("sample\n0\n0.5\n1\n")).size() == 3,
              "Accept valid sample range");
        for (String input : Arrays.asList("green\n0.5\n", "sample,other\n0.5,1\n", "sample\n",
                "sample\nNaN\n", "sample\nInfinity\n", "sample\n-0.1\n", "sample\n1.1\n",
                "sample\nnot-a-number\n", "sample\n0.5,0.6\n")) {
            try {
                ReplayFiles.readSamples(new StringReader(input));
                throw new AssertionError("Malformed CSV was accepted: " + input);
            } catch (IOException expected) {
                checks++;
            }
        }
        Path directory = Files.createTempDirectory("heartbeat-replay-io-");
        try {
            File root = directory.toFile();
            String progress = "{\"frames\":90,\"complete\":false}";
            String complete = "{\"frames\":14401,\"complete\":true}";
            check(ReplayFiles.saveSnapshot(root, "bidmc01", progress, false) == null, "Save progress");
            check(!Files.exists(directory.resolve("bidmc01-complete.json")), "Progress never creates completion");
            check(ReplayFiles.saveSnapshot(root, "bidmc01", complete, true) == null, "Save completion");
            check(read(directory.resolve("bidmc01-complete.json")).equals(complete), "Completion content");
            check(ReplayFiles.saveSnapshot(root, "bidmc01", progress, false) == null, "Save restart progress");
            check(read(directory.resolve("bidmc01-complete.json")).equals(complete), "Restart preserves completion");
            check(read(directory.resolve("native-state.json")).equals(progress), "Progress advances separately");

            Path blocked = directory.resolve("blocked-parent");
            Files.write(blocked, new byte[] {42});
            int processed = 0;
            for (; processed < 300; processed++) {
                if (processed % 90 == 0) {
                    check(ReplayFiles.saveSnapshot(blocked.toFile(), "bidmc01", progress, false) != null,
                          "A blocked output returns a checked error instead of throwing");
                }
            }
            check(processed == 300, "Caller can continue processing after write errors");

            Path cannotReplace = directory.resolve("cannot-replace.json");
            Files.createDirectory(cannotReplace);
            Path keep = cannotReplace.resolve("keep");
            Files.write(keep, new byte[] {23});
            try {
                ReplayFiles.atomicWrite(cannotReplace.toFile(), complete);
                throw new AssertionError("Replacing a nonempty directory unexpectedly succeeded");
            } catch (IOException expected) {
                check(Files.readAllBytes(keep)[0] == 23, "Failed replacement preserves existing target");
            }
            try (java.util.stream.Stream<Path> files = Files.list(directory)) {
                check(files.noneMatch(path -> path.getFileName().toString().endsWith(".tmp")),
                      "Failed replacement removes temporary file");
            }
            Path failedComplete = directory.resolve("synthetic84-complete.json");
            Files.createDirectory(failedComplete);
            Files.write(failedComplete.resolve("keep"), new byte[] {23});
            check(ReplayFiles.saveSnapshot(root, "synthetic84", complete, true) != null,
                  "Completion write failure is reported even if progress writes succeeded");
            check(read(directory.resolve("synthetic84-state.json")).equals(complete),
                  "Progress snapshots remain distinct from completion success");
        } finally {
            try (java.util.stream.Stream<Path> files = Files.walk(directory)) {
                files.sorted(java.util.Comparator.reverseOrder()).forEach(path -> {
                    try { Files.delete(path); } catch (IOException error) { throw new RuntimeException(error); }
                });
            }
        }
        System.out.println("ReplayFiles: " + checks + " input/filesystem checks passed");
    }
}
