// New regression driver for the recovered filter; no camera or UIKit dependency.
#include "Butterworth.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>

static bool check(int order, double *a, double *b) {
    for (int n : {0, 1, 2, 3, 5, 11, 61}) {
        std::vector<double> x(n), actual(n), expected(n);
        for (int i=0; i<n; ++i) x[i]=std::sin(i*0.3);
        for (int i=0; i<n; ++i) {
            for (int j=0; j<=std::min(order,i); ++j) expected[i]+=b[j]*x[i-j];
            for (int j=1; j<=std::min(order,i); ++j) expected[i]-=a[j]*expected[i-j];
        }
        filter(order, a, b, n, x.data(), actual.data());
        for (int i=0; i<n; ++i)
            if (!std::isfinite(actual[i]) || std::abs(actual[i]-expected[i])>1e-14) return false;
    }
    return true;
}

int main() {
    double a[] = {1.0, -0.2, 0.1}, b[] = {0.3, 0.2, 0.1};
    // Order-5 bandpass has order-10 transfer coefficients; saved original
    // strict fixture, independently checked by the existing coefficient test.
    double heartbeat_a[] = {1.0, -8.04234298696992, 29.422399680745215, -64.5194828455958, 93.95541134986065, -94.96524800144532, 67.48098648876717, -33.29000463868108, 10.91225271476863, -2.1463589083868864, 0.19238859600117322};
    double heartbeat_b[] = {0.0004894360861164059, 0.0, -0.0024471804305820294, 0.0, 0.004894360861164059, 0.0, -0.004894360861164059, 0.0, 0.0024471804305820294, 0.0, -0.0004894360861164059};
    if (!check(2,a,b) || !check(10,heartbeat_a,heartbeat_b)) return 1;
    std::cout << "PASS bounded native filter: orders2/10, seven lengths each, independent recurrence\n";
}
