#ifndef KNN_H
#define KNN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

const int NUM_FEATURE = 2;
const int NUM_PT_IN_SEARCHSPACE = 1024*1024;
const int NUM_PT_IN_BUFFER = 512;
const int NUM_TILES = NUM_PT_IN_SEARCHSPACE / NUM_PT_IN_BUFFER;
const int UNROLL_FACTOR = 2;

struct bench_args_t {
    float input_query[NUM_FEATURE];
    float search_space_data[NUM_PT_IN_SEARCHSPACE*NUM_FEATURE];
    float distance[NUM_PT_IN_SEARCHSPACE];
};

#endif
