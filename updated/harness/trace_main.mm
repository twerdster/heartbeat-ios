// Reference-trace driver for the ORIGINAL HeartBeat Algorithm.mm/Butterworth.cpp.
// New harness code (2026). The original files are compiled unmodified from
// ../../source/Heartbeat/. Usage:
//   heartbeat_trace coeffs OUT.csv
//   heartbeat_trace trace IN.txt OUT.csv [windowSize filterWindowSize]
// IN.txt holds one UIColor green component per line (printed with %.17g).
#import "uikit_shim.h"
#import "Algorithm.h"
#include "Butterworth.h"
#include <cstdio>
#include <cstdlib>
#include <vector>

@implementation UIColor {
    CGFloat _r, _g, _b, _a;
}
+ (instancetype)colorWithRed:(CGFloat)red green:(CGFloat)green blue:(CGFloat)blue alpha:(CGFloat)alpha {
    UIColor *c = [[UIColor alloc] init];
    c->_r = red; c->_g = green; c->_b = blue; c->_a = alpha;
    return c;
}
- (BOOL)getRed:(CGFloat *)red green:(CGFloat *)green blue:(CGFloat *)blue alpha:(CGFloat *)alpha {
    if (red) *red = _r;
    if (green) *green = _g;
    if (blue) *blue = _b;
    if (alpha) *alpha = _a;
    return YES;
}
@end

static int dumpCoeffs(const char *outPath) {
    double bands[2] = {0.04, 0.2};  // FILTER_LOWER_BAND, FILTER_UPPER_BAND in Algorithm.mm
    double **z = butter(bands, 5);  // FILTER_ORDER
    FILE *f = fopen(outPath, "w");
    if (!f) return 2;
    fprintf(f, "k,b,a\n");
    for (int k = 0; k <= 10; k++) fprintf(f, "%d,%.17g,%.17g\n", k, z[0][k], z[1][k]);
    fclose(f);
    return 0;
}

static int runTrace(const char *inPath, const char *outPath, int windowSize, int filterWindowSize) {
    FILE *in = fopen(inPath, "r");
    if (!in) return 2;
    std::vector<double> comps;
    char line[128];
    while (fgets(line, sizeof line, in)) {
        if (line[0] == '\n' || line[0] == '#') continue;
        comps.push_back(strtod(line, nullptr));
    }
    fclose(in);

    FILE *out = fopen(outPath, "w");
    if (!out) return 2;
    fprintf(out, "frame,value,peak_index,is_peak,bpm_value,bpm_average,calibration_over,bpm_latest,final_determined,should_show,missed_last_peak\n");
    @autoreleasepool {
        Algorithm *alg = [[Algorithm alloc] init];
        if (windowSize > 0) alg.windowSize = windowSize;
        if (filterWindowSize > 0) alg.filterWindowSize = filterWindowSize;
        for (double c : comps) {
            @autoreleasepool {
                [alg newFrameDetectedWithAverageColor:[UIColor colorWithRed:0 green:c blue:0 alpha:1]];
                NSUInteger fc = alg.framesCounter;
                NSInteger w = (NSInteger)alg.windowSize;
                NSInteger idx = (fc > alg.filterWindowSize) ? (NSInteger)fc - w - 1 : -1;
                NSInteger at = idx >= 0 ? idx : (NSInteger)fc - 1;
                NSArray *points = [alg valueForKey:@"points"];
                NSArray *isPeak = [alg valueForKey:@"isPeak"];
                NSArray *bpmValues = [alg valueForKey:@"bpmValues"];
                NSArray *bpmAvg = [alg valueForKey:@"bpmAverageValues"];
                BOOL calib = alg.isCalibrationOver;
                double latest = alg.bpmLatestResult;
                BOOL fin = alg.isFinalResultDetermined;
                BOOL show = alg.shouldShowLatestResult;
                fprintf(out, "%lu,%.17g,%ld,%d,%.17g,%.17g,%d,%.17g,%d,%d,%d\n",
                        (unsigned long)fc, [points[fc - 1] doubleValue], (long)idx,
                        idx >= 0 ? (int)[isPeak[idx] integerValue] : 0,
                        [bpmValues[at] doubleValue], [bpmAvg[at] doubleValue],
                        (int)calib, latest, (int)fin, (int)show, (int)alg.isMissedTheLastPeak);
            }
        }
    }
    fclose(out);
    return 0;
}

int main(int argc, const char **argv) {
    if (argc >= 3 && !strcmp(argv[1], "coeffs")) return dumpCoeffs(argv[2]);
    if (argc >= 4 && !strcmp(argv[1], "trace")) {
        int w = argc >= 6 ? atoi(argv[4]) : 0;
        int fw = argc >= 6 ? atoi(argv[5]) : 0;
        return runTrace(argv[2], argv[3], w, fw);
    }
    fprintf(stderr, "usage: %s coeffs OUT | trace IN OUT [windowSize filterWindowSize]\n", argv[0]);
    return 1;
}
