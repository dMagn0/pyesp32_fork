import serial
import sys
import time
import threading
from src.protocol_models import *

if __name__ == "__main__":
        
    # Replace '/dev/ttyUSB0' with your ESP32's serial port
    #ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
    com = ComunicadorSerial("COM7",115200)
    j=0
    while 1:
        i = int(input("leitura = 1, escrita = 2"))
        j += 1
        if i == 1:
            com.read_pin(PinType.DIGITAL,16)
        if i == 2:
            com.write_pin(PinType.DIGITAL,5,j%2)
        if i == 0:
            sys.exit()
        

    
