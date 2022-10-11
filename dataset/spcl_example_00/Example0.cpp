constexpr int N = 1024000;

void InitiationInterval(float const *a_mem, float const *b_mem, float *c_mem) {
L1:  for (int i = 0; i < N; ++i) {
    const auto a = a_mem[i];
    const auto b = b_mem[i];
    // -------------------------
    // Try changing the target initiation interval (II) and re-running HLS.
    // Notice what happens to the total number of cycles to completion, and to
    // the number of adders instantiated.
    float c = (a + b) * (a - b);
    // -------------------------
    c_mem[i] = c;
  }
}
