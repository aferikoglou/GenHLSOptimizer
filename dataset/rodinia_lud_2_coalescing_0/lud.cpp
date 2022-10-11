#include "lud.h"
#include "mc.h"
#define coalescing

#ifdef coalescing 
extern "C" {
void internal_load(int flag, float buffer[BSIZE][matrix_dim - BSIZE], class ap_uint<512> * src, int k, int idx){
	if(flag){
L1:		for(int i = 0; i < BSIZE; i++){ //16 
			memcpy_wide_bus_read_float(buffer[i], src + ((idx + BSIZE) * GRID_COLS + idx + BSIZE + k * BSIZE * GRID_COLS + i * GRID_COLS) / (512 / 32), 0, sizeof(float) * (matrix_dim - BSIZE)); //sizeof(float) * (matrix_dim - idx - BSIZE));
			// memcpy(buffer[i], src + (idx + BSIZE) * GRID_COLS + idx + BSIZE + k * BSIZE * GRID_COLS + i * GRID_COLS, sizeof(float) * (matrix_dim - idx - BSIZE));
		}
	}
}

void internal_store(int flag, float buffer[BSIZE][matrix_dim - BSIZE], class ap_uint<512> * dst, int k, int idx){
	if(flag){
L2:		for(int i = 0; i < BSIZE; i++){
			memcpy_wide_bus_write_float((class ap_uint<512> *)dst + ((idx + BSIZE) * GRID_COLS + idx + BSIZE + k * BSIZE * GRID_COLS + i * GRID_COLS) / (512 /32), buffer[i], 0, sizeof(float) * (matrix_dim - BSIZE));// sizeof(float) * (matrix_dim - idx - BSIZE));
			// memcpy(dst + (idx + BSIZE) * GRID_COLS + idx + BSIZE + k * BSIZE * GRID_COLS + i * GRID_COLS, buffer[i], sizeof(float) * (matrix_dim - idx - BSIZE));
		}
	}
}

#else

void internal_load(int flag, float buffer[BSIZE][matrix_dim - BSIZE], float * src, int k, int idx){
	if(flag){
		for(int i = 0; i < BSIZE; i++){ //16 
			memcpy(buffer[i], src + (idx + BSIZE) * GRID_COLS + idx + BSIZE + k * BSIZE * GRID_COLS + i * GRID_COLS, sizeof(float) * (matrix_dim - idx - BSIZE));
		}
	}
}

void internal_store(int flag, float buffer[BSIZE][matrix_dim - BSIZE], float * dst, int k, int idx){
	if(flag){
		for(int i = 0; i < BSIZE; i++){
			memcpy(dst + (idx + BSIZE) * GRID_COLS + idx + BSIZE + k * BSIZE * GRID_COLS + i * GRID_COLS, buffer[i], sizeof(float) * (matrix_dim - idx - BSIZE));
		}
	}
}

#endif

void internal_compute(int flag, float buffer_inner[BSIZE][matrix_dim - BSIZE], float buffer_left[GRID_ROWS][BSIZE], float buffer_up[BSIZE][GRID_COLS], int k, int idx){
	if(flag){
		
L3:		for(int j = 0; j < matrix_dim - 10 /*idx*/ - BSIZE; j++){
L4:			for(int i = 0; i < BSIZE; i++){
				float tmp = buffer_inner[i][j];
L5:				for(int m = 0; m < BSIZE; m++){
					tmp -= buffer_left[i + k * BSIZE][m] * 
							buffer_up[m][j + BSIZE];
				}
				buffer_inner[i][j] = tmp;
			}
		}
	}
}

void workload(class ap_uint<512> * result){
	#pragma HLS INTERFACE m_axi port=result offset=slave bundle=gmem		
	#pragma HLS INTERFACE s_axilite port=result bundle=control
	#pragma HLS INTERFACE s_axilite port=return bundle=control

L6:	float buffer_up[BSIZE][GRID_COLS]; //16 * 256
L7:	float buffer_up_2[BSIZE][GRID_COLS];
L8:	float buffer_left[GRID_ROWS][BSIZE];
L9:	float buffer_left_2[GRID_ROWS][BSIZE];

L10:	outmost:for(int i = 0; i < matrix_dim; i += BSIZE){

		//load up and left
#ifdef coalescing
L11:		l_dup:for(int j = 0; j < BSIZE; j++){
			memcpy_wide_bus_read_float(buffer_up[j], result + ((i + j) * GRID_COLS + i) / (512 / 32), 0,
				sizeof(float) * (GRID_COLS - i));
			memcpy_wide_bus_read_float(buffer_up_2[j], result + ((i + j) * GRID_COLS + i) / (512 / 32), 0,
				sizeof(float) * (GRID_COLS - i));
			// memcpy(buffer_up[j], result + (i + j) * GRID_COLS + i, 
			// 	sizeof(float) * (GRID_COLS - i));
		}

L12:		l_dleft:for(int j = 0; j < GRID_ROWS - BSIZE; j++){
			if(j == GRID_ROWS - BSIZE - i) break;
			memcpy_wide_bus_read_float(buffer_left[j], result + ((i + BSIZE) * GRID_COLS + j * GRID_COLS + i)/(512/32), 0,
				sizeof(float) * BSIZE); 
			memcpy_wide_bus_read_float(buffer_left_2[j], result + ((i + BSIZE) * GRID_COLS + j * GRID_COLS + i)/(512/32), 0,
				sizeof(float) * BSIZE);
			// memcpy(buffer_left[j], result + (i + BSIZE) * GRID_COLS + j * GRID_COLS + i,
			// 	sizeof(float) * BSIZE);
		}
#else
		l_dup:for(int j = 0; j < BSIZE; j++){
			memcpy(buffer_up[j], result + (i + j) * GRID_COLS + i, 
				sizeof(float) * (GRID_COLS - i));
			memcpy(buffer_up_2[j], result + (i + j) * GRID_COLS + i, 
				sizeof(float) * (GRID_COLS - i));
		}

		l_dleft:for(int j = 0; j < GRID_ROWS - BSIZE; j++){
			if(j == GRID_ROWS - BSIZE - i) break;
			memcpy(buffer_left[j], result + (i + BSIZE) * GRID_COLS + j * GRID_COLS + i,
				sizeof(float) * BSIZE);
			memcpy(buffer_left_2[j], result + (i + BSIZE) * GRID_COLS + j * GRID_COLS + i,
				sizeof(float) * BSIZE);
		}
#endif
		//Process diagonal and store
L13:		diagonal:for(int m = 0; m < BSIZE; m++){
			//#pragma HLS dependence
L14:			p_dup:for(int n = m; n < BSIZE; n++){
				float tmp = buffer_up[m][n];
L15:				for(int k = 0; k < BSIZE; k++){                      //2. k<BSIZE  //1. pipeline]
					if(k < m)
						tmp -= buffer_up_2[m][k] * buffer_up[k][n];  //2. buffer_up_1 / 2
				}

				buffer_up[m][n] = tmp;
				buffer_up_2[m][n] = tmp;
			}

			float temp = 1.f / buffer_up[m][m];
L16:			p_dleft:for(int n = m + 1; n < BSIZE; n++){
				float tmp = buffer_up[n][m];
L17:				for(int k = 0; k < BSIZE; k++){                      //pipeline
					if(k < m)
						tmp -= buffer_up_2[n][k] * buffer_up[k][m];
				}
				tmp = tmp * temp;
				buffer_up[n][m] = tmp;
				buffer_up_2[n][m] = tmp;

			}
		}

#ifdef coalescing
		if(i == matrix_dim - BSIZE){
L18:			innermost:for(int j = 0; j < BSIZE; j++){
				memcpy_wide_bus_write_float(result + (i * GRID_COLS + j * GRID_COLS + i)/(512/32), buffer_up[j], 0,
					sizeof(float) * BSIZE);
				// memcpy(result + i * GRID_COLS + j * GRID_COLS + i, buffer_up[j],
					// sizeof(float) * BSIZE);
			}
		}
#else
		if(i == matrix_dim - BSIZE){
			innermost:for(int j = 0; j < BSIZE; j++){
				memcpy(result + i * GRID_COLS + j * GRID_COLS + i, buffer_up[j],
					sizeof(float) * BSIZE);
			}
		}
#endif

		//process perimeters
		int chunk_idx, chunk_num;

		chunk_num = (matrix_dim - (i + BSIZE)) / BSIZE;

L19:		perimeters:for(chunk_idx = 0; chunk_idx < 100 /*chunk_num*/; chunk_idx++){
			// p_up:for(int n = 0; n < BSIZE; n++){
			// 	for(int m = 0; m < BSIZE; m++){
			// 		for(int k = 0; k < m; k++){
			// 			buffer_up[m][n + chunk_idx * BSIZE + BSIZE] -= buffer_up[m][k] * buffer_up[k][n + chunk_idx * BSIZE + BSIZE];
			// 		}
			// 	}
			// }

			// Move m loop inward
			// p_left:for(int m = 0; m < BSIZE; m++){
			// 	for(int n = 0; n < BSIZE; n++){
			// 		float tmp = buffer_left[m + chunk_idx * BSIZE][n];
			// 		for(int k = 0; k < BSIZE; k++){
			// 			if(k < n)
			// 				tmp -= buffer_left[m + chunk_idx * BSIZE][k] * buffer_up[k][n];
			// 			//tmp -= buffer_left[m + chunk_idx * BSIZE][k] * buffer_up[k][n];
			// 		}
			// 		float temp = buffer_up[n][n];
			// 		buffer_left[m + chunk_idx * BSIZE ][n] = tmp / temp;
			// 	}
			// }

L20:			p_up:for(int m = 0; m < BSIZE; m++){

L21:				for(int k = 0; k < BSIZE/*m*/; k++){
					if(k==m) break;
					float tmp = buffer_up[m][k];

L22:					for(int n = 0; n < BSIZE; n++){
						buffer_up_2[m][n + chunk_idx * BSIZE + BSIZE] -= tmp * buffer_up_2[k][n + chunk_idx * BSIZE + BSIZE];
						//buffer_up[m][n + chunk_idx * BSIZE + BSIZE] = buffer_up_2[m][n + chunk_idx * BSIZE + BSIZE];
						//buffer_up[m][n + chunk_idx * BSIZE + BSIZE] -= tmp * buffer_up_2[k][n + chunk_idx * BSIZE + BSIZE];
					}
				}

L23:				for(int n = 0; n < BSIZE; n++){
						buffer_up[m][n + chunk_idx * BSIZE + BSIZE] = buffer_up_2[m][n + chunk_idx * BSIZE + BSIZE];
				}
			}

L24:			p_left:for(int n = 0; n < BSIZE; n++){
				// float tmp = buffer_left[m + chunk_idx * BSIZE][n];
				//#pragma HLS dependence
L25:				p_left_c:for(int k = 0; k < BSIZE/*n*/; k++){
					if(k==n) break;
L26:					for(int m = 0; m < BSIZE; m++){
						buffer_left_2[m + chunk_idx * BSIZE][n] -= 
							buffer_left_2[m + chunk_idx * BSIZE][k] * buffer_up[k][n];
					}
					
				}

L27:				p_left_s:for(int m = 0; m < BSIZE; m++){
					float temp = buffer_left_2[m + chunk_idx * BSIZE][n] / buffer_up[n][n];
					buffer_left[m + chunk_idx * BSIZE ][n] = temp;
					buffer_left_2[m + chunk_idx * BSIZE ][n] = temp;
				}
			}
		}

		//Store up and left
#ifdef coalescing
L28:		s_up:for(int j = 0; j < BSIZE; j++){
			memcpy_wide_bus_write_float(result + (i * GRID_COLS + j * GRID_COLS + i)/(512/32), buffer_up[j], 0, sizeof(float) * (matrix_dim - i));
			// memcpy(result + (i + j) * GRID_COLS + i, buffer_up[j], sizeof(float) * (matrix_dim - i));
		}

L29:		s_load:for(int j = 0; j < matrix_dim - BSIZE; j++){
			if(j == matrix_dim - BSIZE - i) break;
			memcpy_wide_bus_write_float(result + ((i + BSIZE + j) * GRID_COLS + i) /(512/32), buffer_left[j], 0, sizeof(float) * BSIZE);
			// memcpy(result + (i + BSIZE + j) * GRID_COLS + i, buffer_left[j], sizeof(float) * BSIZE); 
		}
#else
		s_up:for(int j = 0; j < BSIZE; j++){
			memcpy(result + (i + j) * GRID_COLS + i, buffer_up[j], sizeof(float) * (matrix_dim - i));
		}

		s_load:for(int j = 0; j < matrix_dim - BSIZE; j++){
			if(j == matrix_dim - BSIZE - i) break;
			memcpy(result + (i + BSIZE + j) * GRID_COLS + i, buffer_left[j], sizeof(float) * BSIZE); 
		}
#endif
		//Process internal part
L30:		float buffer_inner_0[BSIZE][matrix_dim - BSIZE];
L31:		float buffer_inner_1[BSIZE][matrix_dim - BSIZE];
L32:		float buffer_inner_2[BSIZE][matrix_dim - BSIZE];

L33:		internal:for(int k = 0; k < 102 /*chunk_num + 2*/; k++){
			int load_flag = k >=0 && k < chunk_num;
			int compute_flag = k >= 1 && k < chunk_num + 1;
			int store_flag = k >= 2 && k < chunk_num + 2;

			if(k % 3 == 0){
				internal_load(load_flag, buffer_inner_0, result, k, i);
				internal_compute(compute_flag, buffer_inner_2, buffer_left, buffer_up, k - 1, i);
				internal_store(store_flag, buffer_inner_1, result, k - 2, i);
			} else if(k % 3 == 1){
				internal_load(load_flag, buffer_inner_1, result, k, i);
				internal_compute(compute_flag, buffer_inner_0, buffer_left, buffer_up, k - 1, i);
				internal_store(store_flag, buffer_inner_2, result, k - 2, i);
			} else {
				internal_load(load_flag, buffer_inner_2, result, k, i);
				internal_compute(compute_flag, buffer_inner_1, buffer_left, buffer_up, k - 1, i);
				internal_store(store_flag, buffer_inner_0, result, k - 2, i);
			}
		} 

	}

	return;
}
}
