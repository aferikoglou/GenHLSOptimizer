#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// #define DEBUG

#define MEMORY_REORG 0
#define PADDED 1

#define TYPE float
#define UNROLL_SIZE 20
#define FULL_NEIGHBOR_COUNT 27
#define NUMBER_PAR_PER_BOX 100

#define DIMENSION_1D 2   //User defined
#define DIMENSION_2D (DIMENSION_1D * DIMENSION_1D)
#define DIMENSION_3D (DIMENSION_1D * DIMENSION_1D * DIMENSION_1D)

#define DIMENSION_1D_PADDED (1+DIMENSION_1D+1) 
#define DIMENSION_2D_PADDED (DIMENSION_1D_PADDED * DIMENSION_1D_PADDED)
#define DIMENSION_3D_PADDED (DIMENSION_1D_PADDED * DIMENSION_1D_PADDED * DIMENSION_1D_PADDED)

#define ALPHA 0.5
#define A2 (ALPHA * ALPHA * 2.0)

#define N (DIMENSION_3D * NUMBER_PAR_PER_BOX)
#define N_PADDED (DIMENSION_3D_PADDED * NUMBER_PAR_PER_BOX)

#define POS_DIM 4
#define V 0
#define X 1
#define Y 2
#define Z 3

#define POS_DATA_SIZE_FLATTEN (N * POS_DIM)
#define POS_DATA_SIZE_FLATTEN_PADDED (N_PADDED * POS_DIM)

#define DOT(A, B) ((A.x) * (B.x) + (A.y) * (B.y) + (A.z) * (B.z))

typedef struct { TYPE v, x, y, z; } FOUR_VECTOR;

struct bench_args_t {
  TYPE pos_i[N*POS_DIM];
  TYPE q_i[N];
  TYPE pos_o[N*POS_DIM];
};
