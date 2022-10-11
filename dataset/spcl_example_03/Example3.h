#pragma once

constexpr int N = 1000;
constexpr int M = 1000;
constexpr int T = 1000;

void Stencil2D(float const memory_in[N * M], float memory_out[N * M]);

void Example3(float const *in, float *out);
