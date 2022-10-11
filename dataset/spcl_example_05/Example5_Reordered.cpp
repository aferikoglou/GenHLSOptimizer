#include "Example5.h"

void MatrixMultiplication(const double A[], const double B[], double C[]) {
L1:  for (int n = 0; n < N; ++n) {
L2:    double acc[M];  // Buffer an output row of C

L3:    for (int k = 0; k < K; ++k) {  // Collapsed dimension moved out

      const auto a = A[n * K + k];  // We only need to read A once per row of B

L4:      for (int m = 0; m < M; ++m) {
        const double prev = (k == 0) ? 0 : acc[m];  // Automatic "reset" during
        acc[m] = prev + a * B[k * M + m];           // first iteration of M-loop
        #pragma HLS DEPENDENCE variable=acc false
      }
    }

    // Write out resulting row of C
L5:    for (int m = 0; m < M; ++m) {
      C[n * M + m] = acc[m];
    }
  }
}
