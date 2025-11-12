import serial
import sys
import time
import threading
from src.protocol_models import *

"""
New Protocol Format:
    Position 1: Operation (r=read, w=write)
    Position 2: Type (a=analog, d=digital)
    Position 3-4: Address (2 digits, 00-99)
    Position 5-11: Value (7 digits, 0000000-9999999)

    Example: ra040000000 = read analog from GPIO4
    Example: wd050000001 = write digital to GPIO5, value 1
"""

# Configuration
THRESHOLD = 3000  # Threshold for analog reading (adjust as needed)
READ_INTERVAL = 0.5  # Seconds between reads
GPIO_READ_PIN = 4  # GPIO4 for analog reading
GPIO_WRITE_PIN = 5  # GPIO5 for digital writing

last_read_time = 0

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
    
    def _read_serial(self) -> dict:
        """
        Tenta fazer leitura da porta serial. Retorna Erro se não houver leitura em 5 segundos.

        Returns:
            dicionario: retorna a leitura da porta serial em formato {"operation":,"type":,"address":,"value":}
        }
        """
        data = ""
        start = time.time()
        while self._serial.in_waiting <= 0:
            if time.time() - start > ComunicadorSerial._read_timeout:
                print("Erro de leitura: timeout")
                return ComunicadorSerial.parse_message("")
            time.sleep(0.05) 


        try:
            data = self._serial.readline().decode('utf-8').strip()
        except Exception as e:
            print(f"Erro de leitura: {e.args}")
            return ComunicadorSerial.parse_message("")
        
        return data

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
        with self._com_lock:
            self._send_message(OperationType.READ,pin_type,address)
            retorno = self._read_serial()
        print(retorno)

        pass
    def write_pin(self, pin_type:PinType, address,value):
        with self._com_lock:
            self._send_message(OperationType.WRITE,pin_type,address,value)
        pass
    pass


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
        

    
