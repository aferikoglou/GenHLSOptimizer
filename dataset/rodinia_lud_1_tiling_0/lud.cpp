#include"lud.h"
#include <iostream>

//Elment with the block BSIZE, diagonal
#define AA(i,j) result[(offset + i) * matrix_dim + j + offset]
//Elment with global index
#define BB(i,j) result[i * matrix_dim + j]

using namespace std;
extern "C"{
void diagonal_load(float* result, float* buffer, int offset){
    int i, j;
L1:    for(i = 0; i < BSIZE; i++){
L2:        for (j = 0; j < BSIZE; j++){
            buffer[i * BSIZE + j] = AA(i, j);
        }
    }
}

void diagonal_store(float* result, float* buffer, int offset){
    int i, j;
L3:    for(i = 0; i < BSIZE; i++){
L4:        for (j = 0; j < BSIZE; j++){
            AA(i, j) = buffer[i * BSIZE + j];
        }
    }
}
void lud_diagonal(float* result, 
                  int offset)
{ 
    int i, j, k;

L5:    float buffer[BSIZE * BSIZE];

    diagonal_load(result, buffer, offset);

L6:    for (i = 0; i < BSIZE; i++){
L7:        top:for (j = i; j < BSIZE; j++){
L8:            for (k = 0; k < BSIZE; k++){
                buffer[i * BSIZE + j] = buffer[i * BSIZE + j] - 
                buffer[i * BSIZE + k]* buffer[k * BSIZE + j];
		if(k==i) break;
            }
        }
           
           float temp = 1.f / buffer[i * BSIZE + i];

L9:           left:for (j = i + 1; j < BSIZE; j++){
L10:               for (k = 0; k < BSIZE; k++){
                   buffer[j * BSIZE + i]= buffer[j * BSIZE + i]- buffer[j * BSIZE + k] * buffer[k * BSIZE + i];
               	   if(k==i) break;
	       }
               buffer[j * BSIZE + i] = buffer[j * BSIZE + i] * temp;
           }
    }

    diagonal_store(result, buffer, offset);
}

void perimeter_load(float* result, float* top, float* left, int offset, int chunk_idx){
    int i, j;

    int i_top = offset; 
    int j_top = offset + BSIZE * (chunk_idx + 1);

    int i_left = offset + BSIZE * (chunk_idx + 1);
    int j_left = offset;

L11:    for(i = 0; i < BSIZE; i++){
L12:        for(j = 0; j < BSIZE; j++){
            top[i * BSIZE + j] = BB((i_top + i), (j_top + j));
        }
    }

L13:    for(i = 0; i < BSIZE; i++){
L14:        for(j = 0; j < BSIZE; j++){
            left[i * BSIZE + j] = BB((i_left + i), (j_left + j));
        }
    }
}

void perimeter_store(float* result, float* top, float* left, int offset, int chunk_idx){
    int i, j;

    int i_top = offset; 
    int j_top = offset + BSIZE * (chunk_idx + 1);

    int i_left = offset + BSIZE * (chunk_idx + 1);
    int j_left = offset;

L15:    for(i = 0; i < BSIZE; i++){
L16:        for(j = 0; j < BSIZE; j++){
            BB((i_top + i), (j_top + j)) = top[i * BSIZE + j];
        }
    }

L17:    for(i = 0; i < BSIZE; i++){
L18:        for(j = 0; j < BSIZE; j++){
            BB((i_left + i), (j_left + j)) = left[i * BSIZE + j];
        }
    }
}

void lud_perimeter(float* result, 
                   int    offset) {
L19:    float diagonal_buffer[BSIZE * BSIZE];
L20:    float top_buffer[BSIZE * BSIZE];
L21:    float left_buffer[BSIZE * BSIZE];

    int i, j, k;

L22:    diagonal:for (i = 0; i < BSIZE; i++){
L23:        for (j = 0; j < BSIZE; j++){
            diagonal_buffer[i * BSIZE + j] = AA(i, j);
        }
    }

    int chunk_idx, chunk_num;

    //OURS
    offset = 0;

    chunk_num = ((matrix_dim - offset) / BSIZE) - 1;

L24:    for (chunk_idx = 0; chunk_idx < 100 /*chunk_num*/; chunk_idx++){
        perimeter_load(result, top_buffer, left_buffer, offset, chunk_idx);
                
                        float sum; 
                        // processing top perimeter
L25:                        for (j = 0; j < BSIZE; j++){
L26:                            for (i = 0; i < BSIZE; i++){ 
                                sum = 0.0f; 
L27:                                for (k = 0; k < BSIZE; k++){
                                    sum += diagonal_buffer[BSIZE * i + k] * top_buffer[k * BSIZE + j];
                                    if(k==j) break;
				}

                                top_buffer[i * BSIZE + j] = top_buffer[i * BSIZE + j] - sum;
                            }
                        }


                        // processing left perimeter
L28:                        for (i = 0; i < BSIZE; i++){
L29:                            for (j = 0; j < BSIZE; j++){
                                 sum = 0.0f;
L30:                                 for (k = 0; k < BSIZE; k++){
                                     sum += left_buffer[i * BSIZE + k] * diagonal_buffer[BSIZE * k + j];
                                     if(k==j) break;
				 }

                                 left_buffer[i * BSIZE + j] = (left_buffer[i * BSIZE + j] - sum) / diagonal_buffer[j * BSIZE + j];
                            }
                        }

                        perimeter_store(result, top_buffer, left_buffer, offset, chunk_idx);

    }
    cout << "success here perimeter" << endl;
}

void internal_load(float* result, float* top, float* left, float* inner, int offset, int chunk_idx, int chunk_num){
    int i, j;
    int i_global, j_global;

    i_global = offset + BSIZE * (1 + chunk_idx / chunk_num);
    j_global = offset + BSIZE * (1 + chunk_idx % chunk_num);

L31:    for(i = 0; i < BSIZE; i++){
L32:        for(j = 0; j < BSIZE; j++){
            top[i * BSIZE + j]  = result[matrix_dim * (i + offset) + j + j_global];
        }
    }
L33:    for(i = 0; i < BSIZE; i++){
L34:        for(j = 0; j < BSIZE; j++){
            left[i * BSIZE + j] = result[matrix_dim * (i + i_global) + offset + j];
        }
    }

L35:    for(i = 0; i < BSIZE; i++){
L36:        for(j = 0; j < BSIZE; j++){
            inner[i * BSIZE + j] = result[matrix_dim * (i + i_global) + j + j_global];
        }
    }
}

void internal_store(float* result, float* inner, int offset, int chunk_idx, int chunk_num){
    int i, j;
    int i_global, j_global;

    i_global = offset + BSIZE * (1 + chunk_idx / chunk_num);
    j_global = offset + BSIZE * (1 + chunk_idx % chunk_num);

L37:    for(i = 0; i < BSIZE; i++){
L38:        for(j = 0; j < BSIZE; j++){
            result[matrix_dim * (i + i_global) + j + j_global] = inner[i * BSIZE + j];
        }
    }
}

void lud_internal( float* result, 
                    int  offset) {
    int chunk_idx, chunk_num;
    
    //OURS
    offset = 0;	
    chunk_num = ((matrix_dim - offset) / BSIZE) - 1;

L39:    float top_buffer[BSIZE * BSIZE];
L40:    float left_buffer[BSIZE * BSIZE];
L41:    float inner_buffer[BSIZE * BSIZE];

    int i, j, k, i_global, j_global;

L42:    for  (chunk_idx = 0; chunk_idx < 100 /*chunk_num * chunk_num*/; chunk_idx++){
        internal_load(result, top_buffer, left_buffer, inner_buffer, offset, chunk_idx, chunk_num);

L43:        for (i = 0; i < BSIZE; i++){
L44:            for (j = 0; j < BSIZE; j++){
                float sum = 0.0f;
                //#pragma HLS unsafemath
L45:                for (k = 0; k < BSIZE; k++){
                    sum += left_buffer[BSIZE * i + k] * top_buffer[BSIZE * k + j];
                }
                inner_buffer[i * BSIZE + j] -= sum;
            }
        }

        internal_store(result, inner_buffer, offset, chunk_idx, chunk_num);
    }

    cout << "success internal" << endl;
}

void workload(float result[GRID_ROWS * GRID_COLS]){
#pragma HLS INTERFACE m_axi port=result offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=result bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control

L46:    for(int i = 0; i < matrix_dim - BSIZE; i += BSIZE){
        lud_diagonal(result, i);
        lud_perimeter(result, i);
        lud_internal(result, i);
    }

    int i = matrix_dim - BSIZE;
    lud_diagonal(result, i);
    return;
}

}
