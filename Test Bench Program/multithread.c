#include <stdio.h>
#include <pthread.h>
#include <stdint.h>
#include "aes.h"

#define SIZE 16384

#if defined(AES256)
uint8_t key[] = { 0x60, 0x3d, 0xeb, 0x10, 0x15, 0xca, 0x71, 0xbe, 0x2b, 0x73, 0xae, 0xf0, 0x85, 0x7d, 0x77, 0x81,
                      0x1f, 0x35, 0x2c, 0x07, 0x3b, 0x61, 0x08, 0xd7, 0x2d, 0x98, 0x10, 0xa3, 0x09, 0x14, 0xdf, 0xf4 };
#elif defined(AES192)
uint8_t key[] = { 0x8e, 0x73, 0xb0, 0xf7, 0xda, 0x0e, 0x64, 0x52, 0xc8, 0x10, 0xf3, 0x2b, 0x80, 0x90, 0x79, 0xe5,
                      0x62, 0xf8, 0xea, 0xd2, 0x52, 0x2c, 0x6b, 0x7b };
#elif defined(AES128)
uint8_t key[] = { 0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c };
#endif
/* ******************** IV SELECTION ******************************* */
uint8_t iv[]  = { 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f };

uint8_t data[SIZE];


void copy(uint8_t real[],uint8_t copy[]){
    int i;
    for(i=0;i<SIZE;i++){
        copy[i]=real[i];
    }
}


void* cbc(void *arg){
    printf("\tstart \tcbc\n");

    FILE* AES_result;
    uint8_t in[SIZE];
    struct AES_ctx ctx;
    int index=0;

    AES_init_ctx_iv(&ctx, key, iv);
    copy(data,in);

    AES_CBC_encrypt_buffer(&ctx, in, SIZE);

    AES_result= fopen("AES_CBC","w");
    if(AES_result) {
        fprintf(AES_result,"ENCRYPT_CBC: \n");
        while (index<SIZE) {
            fprintf(AES_result,"%d-",in[index]);
            index++;
        }
    }
    else {
        printf("ERROR: can't create AES_CBC file");
        pthread_exit(-1);
    }

    AES_init_ctx_iv(&ctx, key, iv);
    //in already initialized
    AES_CBC_decrypt_buffer(&ctx, in, SIZE);

    fprintf(AES_result,"\n\nDECRYPT_CBC: \n");
    for(index=0;index<SIZE;index++) {
        fprintf(AES_result,"%c",(char)in[index]);
    }
    fclose(AES_result);
    printf("\tend \tcbc\n");

    pthread_exit(0);
}

void* ctr(void *arg){
    printf("\tstart \tctr\n");
    FILE* AES_result;
    uint8_t in[SIZE];
    struct AES_ctx ctx;
    int index=0;

    AES_init_ctx_iv(&ctx, key, iv);
    copy(data,in);

    AES_init_ctx_iv(&ctx, key, iv);

    //in already initialized
    AES_CTR_xcrypt_buffer(&ctx, in, SIZE);

    AES_result= fopen("AES_CTR","w");
    if(AES_result) {
        fprintf(AES_result,"ENCRYPT_CTR: \n");
        while (index<SIZE) {
            fprintf(AES_result,"%d-",in[index]);
            index++;
        }
    }
    else {
        printf("ERROR: can't create AES_CTR file");
        pthread_exit(-1);
    }


    AES_init_ctx_iv(&ctx, key, iv);
    //in already initialized
    AES_CTR_xcrypt_buffer(&ctx, in, SIZE);

    fprintf(AES_result,"\n\nDECRYPT_CTR: \n");
    for(index=0;index<SIZE;index++) {
        fprintf(AES_result,"%c",(char)in[index]);
    }
    fclose(AES_result);


    printf("\tend \tctr\n");

}



int main(){
    FILE *AES_data;
    pthread_t cbcThread, ctrThread;
    int index=0;


    printf("\n\nSTART OF AES PROGRAM.\n");

    //leggo dati
    AES_data= fopen("AES_DATA-16384","r");
    if(AES_data) {
        while(!feof(AES_data) && index < SIZE) {
            char x;
            fscanf(AES_data,"%c",&x);
            data[index]=(uint8_t) x;
            index++;
        }
        if(!feof(AES_data))printf("WARNING: can't convert all AES_DATA. (max dim: %d)",SIZE);
        fclose(AES_data);
    }
    else {
        printf("ERROR: can't read AES_DATA file");
        return -1;
    }


    pthread_create(&cbcThread,NULL,cbc,NULL);
    //pthread_create(&ctrThread,NULL,ctr,NULL);

    pthread_join(cbcThread,NULL);
    //pthread_join(ctrThread,NULL);

    printf("END OF AES PROGRAM.\n");

}

