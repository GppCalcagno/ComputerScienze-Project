#include <stdio.h>

void main(){
    FILE *AES_data;
    int counter=0;
    char c;


    AES_data= fopen("AES_DATA-64","r");

    if(AES_data){
        while (!feof(AES_data)){
            fscanf(AES_data,"%c",&c);
            counter++;
        }
        printf("NUMBER OF CHARACTER: %d\n",counter);
        fclose(AES_data);
    }
    else{
        printf("ERROR: can't read AES_DATA file");
    }
}