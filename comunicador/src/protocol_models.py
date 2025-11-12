from enum import Enum, auto
import serial
import sys
import time
import threading

"""
New Protocol Format:
    Position 1: Operation (r=read, w=write)
    Position 2: Type (a=analog, d=digital)
    Position 3-4: Address (2 digits, 00-99)
    Position 5-11: Value (7 digits, 0000000-9999999)

    Example: ra040000000 = read analog from GPIO4
    Example: wd050000001 = write digital to GPIO5, value 1
"""

class OperationType(Enum):
    WRITE = "w"
    READ = "r"
    pass

class PinType(Enum):
    ANALOG = "a"
    DIGITAL = "d"
    pass

class ComunicadorSerial():
    _serial:serial.Serial
    _com_lock:threading.Lock

    _read_timeout = 1 #em segundos

    def __init__(self, port, baud_rate):
        self._serial = serial.Serial(port, baud_rate, timeout=1)
        self._com_lock = threading.Lock()
        pass

    @staticmethod   
    def parse_message(msg) -> dict:
        """
        Parse a message according to the protocol.

        Args:
            msg: Message string to parse

        Returns:
            Dictionary with operation, type, address, and value
            or None if parsing fails
        """
        try:
            if len(msg) < 11:
                return None
            return {
                "operation": msg[0],
                "type": msg[1],
                "address": int(msg[2:4]),
                "value": int(msg[4:11]),
            }
        except (ValueError, IndexError):
            return None
        pass
    
    @staticmethod
    def build_message(operation, pin_type, address, value) -> str:
        """
        Build a message according to the protocol.

        Args:
            operation: 'r' for read, 'w' for write
            pin_type: 'a' for analog, 'd' for digital
            address: GPIO address (0-99)
            value: value to send (0-9999999)

        Returns:
            Formatted message string
        """
        return f"{operation}{pin_type}{address:02d}{value:07d}"
    
    def _read_serial(self) -> list:
        """
        Tenta fazer leitura da porta serial. Retorna Erro se não houver leitura em 5 segundos.

        Returns:
            lista: retorna a leitura da porta serial em formato [{"operation":,"type":,"address":,"value":},...]
        }
        """

        data = ""
        start = time.time()
        saida = []

        while self._serial.in_waiting <= 0:
            if time.time() - start > ComunicadorSerial._read_timeout:
                print("Erro de leitura: timeout")
                return saida
            time.sleep(0.05) 

        while self._serial.in_waiting >= 0: 
            try:
                data = self._serial.readline().decode('utf-8').strip()
            except Exception as e:
                print(f"Erro de leitura: {e.args}")
                return saida
            saida.append(ComunicadorSerial.parse_message(data))
            
        return saida

    def _send_message(self, operacao:OperationType, pin_type:PinType, address,value=0) -> bool:
        """
        Faz escrita da mensagem na porta serial

        Args:
            mensagem: string, a mensagem a ser escrita para a porta serial do ESP-32
            operacao: OperationType, a operacao a ser realizada
            pin_type: PinType
            address: string, valor em decimal do endereço dsa mensagem
            value: string, valor de escrita

        Returns:
            bool: retorna a sucesso dsa leitura
        """
        mensagem = ComunicadorSerial.build_message(operacao.value, pin_type.value,address,value)

        try:
            self._serial.write(mensagem.encode('utf-8'))
            return True
        except Exception as e:
            print(f"Erro de escrita: {e.args}")
            return False
        pass

    def read_pin(self, pin_type:PinType, address) -> dict:
        leitura = []
        retorno = {}

        start = time.time()
        ser_waiting = self._serial.in_waiting

        with self._com_lock:
            while ser_waiting == self._serial.in_waiting:
                if time.time() - start > ComunicadorSerial._read_timeout:
                    print("Erro de leitura: timeout")
                    return retorno
                self._send_message(OperationType.READ,pin_type,address)
                time.sleep(0.05) 

            leitura = self._read_serial()
            
        for i in leitura:
            if i["operation"] == OperationType.READ.value and i["address"] == address:
                retorno = i
                pass
            pass
        if len(retorno) == 0:
            print("Erro de leitura: resposta nao encontrada")
        return retorno

    def write_pin(self, pin_type:PinType, address,value):
        with self._com_lock:
            self._send_message(OperationType.WRITE,pin_type,address,value)
        pass
    pass
