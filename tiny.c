#include <unistd.h>  // For sleep function

char values[1024][4 * 1024] = {};

void workload()
{
    for(int i = 0; i < 1024; i++){
        for(int j = 0; j < 4 * 1024; j+= 8){
            values[i][j] = 1;
        }
        
        // printf("rdtsc page: %d %lu\n", i, rdtsc());
    }
}

int main(){
    while(1){
        workload();
        usleep(10);
        
    }
}