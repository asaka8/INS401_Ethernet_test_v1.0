#!/bin/sh


CFLAGS := 
CFLAGS += -O3 -lm -DRTK330LA_UART


SRC := -c cJSON.c DateTime.c uart_test_rtk330la.c
INC := -I ./ -fpic 
OBJ := $(SRC:.c=.o)

CC := gcc

TARGET := uart_test_rtk330la_static

all:
	${CC} -c ${CFLAGS} ${LFLAGS} ${SRC} ${INC}
	${CC} -o ${TARGET}.exe *.o

zip:
	rm *.o
 
show:
	@echo "all source file -------------->"
	@echo ${SRC}
	@echo "all .o file--------------->"
	@echo ${OBJ}

clean:
	rm ${TARGET}.exe *.o
