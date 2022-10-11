/*
Based on algorithm described here:
http://www.cs.berkeley.edu/~mhoemmen/matrix-seminar/slides/UCB_sparse_tutorial_1.pdf
*/

#include "spmv.h"

void ellpack(TYPE nzval[N*L], int32_t cols[N*L], TYPE vec[N], TYPE out[N])
{
    int i, j;
    TYPE Si;

L1:    ellpack_1 : for (i=0; i<N; i++) {
        TYPE sum = out[i];
L2:        ellpack_2 : for (j=0; j<L; j++) {
                Si = nzval[j + i*L] * vec[cols[j + i*L]];
                sum += Si;
        }
        out[i] = sum;
    }
}
