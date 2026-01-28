from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from src.port_detect import *
from src.protocol_models import *

from threading import Thread
from time import sleep

import random

class InterfaceBase(BoxLayout):

    def __init__(self,**kwargs):
        super().__init__()
        self._comunicador:ComunicadorSerial = None
        self.ids.spinner_port.values = serial_ports()
        self.tags = kwargs.get("addrs", [])
        for val in self.tags:
            val["leitura"] = 0
            new_widget = FixedReadWidget()
            new_widget.ids.lbl_address.text = str(val.get("addr",66))
            self.ids.addrs_grid.add_widget(new_widget)
            val["widget"] = new_widget

        self._loop_ativo = False
        pass

    def conectar(self):
        porta = self.ids.spinner_port.text
        baud = self.ids.spinner_baud.text

        if porta == "Porta USB":
            print("Erro: porta não selecionada")
            return

        if baud == "Baud Rate":
            print("Erro: baud rate não selecionado")
            return

        try:
            if not self._comunicador:
                self._comunicador = ComunicadorSerial(porta,int(baud),True)
            self._comunicador.conectar()
        except Exception as e:
            self._comunicador = None
            return
        self.inicia_loop()


    def desconectar(self):
        if self._comunicador:
            self._loop_ativo = False
            self._comunicador.desconectar()
    
    def atualizar_portas(self):
        self.ids.spinner_port.values = serial_ports()

    def inicia_loop(self):
        if self._loop_ativo:
            return
        
        self._loop_ativo = True
        self._thread_loop = threading.Thread(
            target=self.atualizacao,
            daemon=True
        )
        self._thread_loop.start()

    def atualizacao(self):
        while self._loop_ativo:
            self.leitura_dados()
            self.tratamento_dados()
            self.atualiza_dados()
            time.sleep(0.1)
        pass

    def leitura_dados(self):
        for i in self.tags:
            # i["leitura"] = random.randint(0,10)
            try:
                i["leitura"] = self._comunicador.read_pin(i.get("tipo",PinType.DIGITAL),i.get("addr",0))
            except TimeoutError as e:
                print(f"Erro na leitura do {i['nome']}")

        pass
    def tratamento_dados(self):
        if self.tags[0]["leitura"] == 0:
            self._comunicador.write_pin(PinType.DIGITAL,4,1)
        elif self.tags[1]["leitura"] == 0:
            self._comunicador.write_pin(PinType.DIGITAL,4,10)
        elif self.tags[2]["leitura"] == 0:
            self._comunicador.write_pin(PinType.DIGITAL,4,100)
        pass
    def atualiza_dados(self):
        for tag in self.tags:
            tag["widget"].ids.lbl_value.text = str(tag.get("leitura",0))
        pass
    def leitura_manual(self):
        if not self._comunicador:
            print("serial desligado")
            return
        self._comunicador.read_pin(PinType(self.ids.spinner_pin_type.text),self.ids.spinner_address.text)
        # self.ids.leitura_manual.ids.label_read_value.text = f"{self.ids.leitura_manual.ids.pin_type_leitura.text} ,{self.ids.leitura_manual.ids.address_leitura.text}"
        # return
    def escrita_manual(self):
        if not self._comunicador:
            print("serial desligado")
            return
        # print(self.ids.escrita_manual.ids.spinner_pin_type.text,self.ids.escrita_manual.ids.spinner_address.text, self.ids.escrita_manual.ids.input_value.text)
        self._comunicador.write_pin(PinType(self.ids.escrita_manual.ids.spinner_pin_type.text),
                                    self.ids.escrita_manual.ids.spinner_address.text,
                                    self.ids.escrita_manual.ids.input_value.text)
    pass

class FixedReadWidget(BoxLayout):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
