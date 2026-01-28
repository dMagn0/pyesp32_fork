import os
import serial
import sys
import glob
import time
import threading
from time import sleep

from src.protocol_models import *
from src.port_detect import *
BAUD_RATE = 115200 

import logging
logging.getLogger("pyModbusTCP").setLevel(logging.WARNING)
import kivy
from kivy.app import App
from kivy.core.window import Window
from src.interface_base import InterfaceBase
from ui import builder




class BasicApp(App):
    def build(self):
        """
        Método para construção do aplicativo com base no widget criado
        """
        self._widget = InterfaceBase(addrs = [
            {'addr':1, 'tipo': PinType.DIGITAL, 'nome': "botao 1:"},
            {'addr':2, 'tipo': PinType.DIGITAL, 'nome': "botao 2:"},
            {'addr':3, 'tipo': PinType.DIGITAL, 'nome': "botao 3:"},
            {'addr':1, 'tipo': PinType.ANALOG, 'nome': "corrente"},
            {'addr':0, 'tipo': PinType.TEMPERATURA, 'nome': "temperatura:"},
            # {'addr':0, 'tipo': PinType.CORRENTE, 'nome': "corrente:"},
        ])
        return self._widget
    
    def on_stop(self):
        """
        Chamado automaticamente quando o app é fechado
        """
        self._widget.desconectar()
       

    # def on_stop(self):
    #     sself._widget.stopRefresh()


if __name__ == '__main__':

    Window.size = (800,600)
    Window.fullscreen = False
    builder.build_strings()

    BasicApp().run()


# if __name__ == "__main__":
#     serial_p = serial_ports()
#     if len(serial_p) == 0 :
#         print("nenhuma porta indentificada")
#         sys.exit()
        
#     print("Portas disponíveis: \n   ",serial_p)
    
#     porta = input("Digite a porta de comunicacao serial ("" para a primeira): ")
#     if porta == "":
#         porta = serial_p[0]

#     if len(porta) == 1:
#         val = int(porta)
#         if val >= len(serial_p):
#             print("PORTA INVALIDA")
#             sys.exit()
#         porta = serial_p[val]

#     if not (porta in serial_p):
#         print("PORTA INVALIDA")
#         sys.exit()

    
#     com = ComunicadorSerial(porta,BAUD_RATE, is_debug = True)

#     while(1):
#         op = input("Digite a operacao (leitura = 1, escrita = 2): ")
#         try:
#             if op == "1":
#                 pin_t = PinType(input("digite o tipo do pino (a, d, c, t): "))
#                 addr = int(input("digite a porta: "))
#                 print(com.read_pin(pin_t,addr))
#             elif op == "2":
#                 pin_t = PinType(input("digite o tipo do pino (a, d): "))
#                 addr = int(input("digite a porta: "))
#                 escr = int(input("digite o valor: "))
#                 com.write_pin(pin_t,addr,escr)
#             elif op == "0":
#                 break
#         except Exception as e:
#             print(e.args)
#         pass

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
        

    
