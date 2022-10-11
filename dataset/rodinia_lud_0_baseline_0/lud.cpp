#include"lud.h"
extern "C"{
void lud(float result[GRID_ROWS * GRID_COLS])
	{
		int i, j, k; 
		float sum;
	 
L1:		for (i=0; i<SIZE; i++){
L2:		     for (j=i; j<SIZE; j++){
		         sum=result[i*SIZE+j];
L3:			 for (k=0; k<SIZE /*i*/; k++) { if(k==i) break; sum -= result[i*SIZE+k]*result[k*SIZE+j]; }
			 result[i*SIZE+j]=sum;
		     }

L4:		     for (j=i+1;j<SIZE; j++){
		         sum=result[j*SIZE+i];
L5:			 for (k=0; k<SIZE /*i*/; k++) { if(k==i) break; sum -= result[j*SIZE+k]*result[k*SIZE+i]; }
		         result[j*SIZE+i]=sum/result[i*SIZE+i];
		     }
		 }
		
		 return;
	}

	void workload(float result[GRID_ROWS * GRID_COLS])
	{

		#pragma HLS INTERFACE m_axi port=result offset=slave bundle=gmem		
		#pragma HLS INTERFACE s_axilite port=result bundle=control
		#pragma HLS INTERFACE s_axilite port=return bundle=control

		lud(result);

		return;

	}
}
