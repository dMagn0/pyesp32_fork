import serial
import sys
import glob
import time
import threading
from src.protocol_models import *
from src.port_detect import *

BAUD_RATE = 115200 

if __name__ == "__main__":
    serial_p = serial_ports()
    if len(serial_p) == 0 :
        print("nenhuma porta indentificada")
        sys.exit()
        
    print("Portas disponíveis: \n   ",serial_p)

    # Replace '/dev/ttyUSB0' with your ESP32's serial port
    #ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
    
    porta = input("Digite a porta de comunicacao serial ("" para a primeira): ")
    if porta == "":
        porta = serial_p[0]

    com = ComunicadorSerial(porta,BAUD_RATE)

    # print(ComunicadorSerial.build_message(OperationType.READ,PinType.ANALOG,55,15))
    # j=0
    # while 1:
    #     i = int(input("leitura = 1, escrita = 2\n"))
    #     j += 1
    #     if i == 1:
    #         com.read_pin(PinType.DIGITAL,16)
    #     if i == 2:
    #         com.write_pin(PinType.DIGITAL,5,j%2)
    #     if i == 0:
    #         sys.exit()
        

    
