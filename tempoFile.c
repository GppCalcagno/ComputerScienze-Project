#include <stdio.h>

#define SIZE 16384

void main(){
    FILE *file;
    int counter=0;
    char c;
    char vett[SIZE];
    int i=0,j=0;


    printf("\n\nSTART PROGRAM TEMPOFILE\n");
    file= fopen("AES_DATA-16384","r");
    if(file){
        while (!feof(file) && counter<SIZE){
            fscanf(file,"%c",&c);
            vett[counter]=c;
            counter++;
        }
        fclose(file);
    }
    else{
        printf("ERROR: can't read AES_DATA file");
    }

    for(i=0;i<2;i++){
        file=fopen("TimeTest","w");
        j=0;

        while(j<SIZE){
            fprintf(file,"%d-",j);
            j++;
        }
        j=0;

        while(j<SIZE){
            fprintf(file,"%c",vett[j]);
            j++;
        }
        fclose(file);
    }

    printf("END PROGRAM TEMPOFILE\n");
}