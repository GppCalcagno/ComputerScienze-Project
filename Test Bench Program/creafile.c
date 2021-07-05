#include <stdio.h>
#include <stdlib.h>

#define DIM 16384

void main(){
    FILE *file;
    int x;



    file= fopen("AES_DATA-16384","w");

    if(file){
        for(int i=0;i<DIM-1;i++){
            x= rand()%94;
            x=x+32;
            fprintf(file,"%c",(char)x);
        }
    }
    else{
        printf("ERROR: can't open AES_DATA file");
    }
}