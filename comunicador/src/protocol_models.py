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
    _read_retrys = 3#vezes que o comunicador reenvia requisição de leitura

    def __init__(self, port, baud_rate, is_debug = False):
        self._serial = serial.Serial(port, baud_rate, timeout=1)
        self._com_lock = threading.Lock()
        self._is_debug = is_debug
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
    def build_message(operation, pin_type, address, value = 0) -> str:
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

        if isinstance(operation, OperationType):
            operation = operation.value
        if isinstance(pin_type, PinType):
            pin_type = pin_type.value

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

        if self._is_debug:
            print(f"LEITURA SERIAL: ser in waiting = {self._serial.in_waiting}")

        while self._serial.in_waiting <= 0:
            if time.time() - start > ComunicadorSerial._read_timeout:
                print("Erro de leitura: timeout")
                return saida
            time.sleep(0.05) 

        while self._serial.in_waiting > 0: 
            if time.time() - start > ComunicadorSerial._read_timeout:
                print("Erro de leitura: timeout com serial cheio")
                return saida
            try:
                data = self._serial.readline().decode('utf-8').strip()
            except Exception as e:
                print(f"Erro de leitura: {e.args}")
                return saida
            saida.append(data)
        
        if self._is_debug:
            print(saida)
        return saida

    def _send_message(self, mensagem) -> bool:
        """
        Faz escrita da mensagem na porta serial

        Args:
            mensagem: string, a mensagem a ser escrita para a porta serial do ESP-32
            
        Returns:
            bool: retorna a sucesso dsa leitura
        """

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

        for i in range(0, ComunicadorSerial._read_retrys):
            with self._com_lock:
                if self._serial.in_waiting:
                    _ = self._read_serial()
                self._send_message(ComunicadorSerial.build_message(OperationType.READ,pin_type,address))    
            
            with self._com_lock:
                leitura = self._read_serial()

            for i in leitura:
                msg = ComunicadorSerial.parse_message(i)
                if msg["operation"] == OperationType.READ.value and msg["address"] == address:
                    retorno = msg
                    pass
                pass

            if len(retorno) != 0:
                return retorno
                break
            pass

        print("Erro de leitura: resposta nao encontrada")
        return {}
    
    def write_pin(self, pin_type:PinType, address,value):
        with self._com_lock:
            self._send_message( ComunicadorSerial.build_message(OperationType.WRITE, pin_type,address,value) )
        pass
    pass
