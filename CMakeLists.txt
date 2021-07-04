cmake_minimum_required(VERSION 3.19)
project(AES C)

set(CMAKE_C_STANDARD 99)
find_package(Threads)
SET(CMAKE_C_FLAGS -pthread)

add_executable(AES_MAIN main.c aes.c)
add_executable(TEMPOFILE- tempoFile.c)
add_executable(conta conta.c)
add_executable(crea creafile.c)


add_executable(AES_THREAD multithread.c aes.c)