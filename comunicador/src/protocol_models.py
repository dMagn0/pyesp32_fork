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
    CORRENTE = "c"
    TEMPERATURA = "t"
    pass

class ComunicadorSerial():
    _serial:serial.Serial
    _com_lock:threading.Lock

    _read_timeout = 1 #em segundos
    _read_retrys = 20#vezes que o comunicador reenvia requisição de leitura

    def __init__(self, port, baud_rate, is_debug = False):
        self._serial = serial.Serial(port, baud_rate, timeout=ComunicadorSerial._read_timeout)
        self._com_lock = threading.Lock()
        self._is_debug = is_debug
        # self._clear_serial()
        pass

    def conectar(self):
        """
        Abre a porta serial.
        Se port/baud_rate forem informados, recria a conexão.
        """
        with self._com_lock:
            if self._serial and self._serial.is_open:
                return  
            self._serial.open()
            if self._is_debug:
                print("Serial conectada")

    def desconectar(self):
        """
        Fecha a porta serial com segurança.
        """
        with self._com_lock:
            if self._serial and self._serial.is_open:
                self._serial.close()
                if self._is_debug:
                    print("Serial desconectada")

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
        except Exception as e:
            raise Exception(f"Erro no parse da mensagem: {msg}") from e
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
    
    def _read_serial(self) -> str:
        """
        Faz leitura da porta serial até o próximo '\n'.

        Returns:
            string: retorna a leitura da porta serial

        Raises:
            ValueError, TimeoutError
        }
        """
        data = self._serial.readline()
        
        if not data:
            raise TimeoutError("Timeout aguardando resposta da serial")

        try:
            return data.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError("Erro de decodificação da serial") from exc
        pass

    def _clear_serial(self):
        print(self._serial.in_waiting)
        with self._com_lock:
            while self._serial.in_waiting > 0:
                data = self._serial.read(self._serial.in_waiting)
                print(self._serial.in_waiting, data)
        pass

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
            return
        except Exception as e:
            raise Exception(f"Erro de escrita da mensagen {mensagem}: {e}") from e
        pass

    def read_pin(self, pin_type:PinType, address) -> dict:
        """
        Envia um comando de leitura para o pino especificado e aguarda a
        resposta correspondente do dispositivo via comunicação serial.

        Args:
            pin_type (PinType): Tipo do pino a ser lido.
            address: Endereço do pino no dispositivo.

        Returns:
            dict: Dicionário no modelo {"operation":,"type":,"address":,"value":}.

        Raises:
            TimeoutError
        """
        leitura = ""

        for i in range(0, ComunicadorSerial._read_retrys):
            try:
                with self._com_lock:
                    self._send_message(ComunicadorSerial.build_message(OperationType.READ,pin_type,address))
                    leitura = self._read_serial()
                msg = ComunicadorSerial.parse_message(leitura)
                if msg["operation"] == OperationType.READ.value and msg["address"] == address:
                    return msg
                    
            except Exception as e:
                print("Erro: ", e)
            pass

        raise TimeoutError("Tentativas de leitura sem sucesso")
    
    def write_pin(self, pin_type:PinType, address,value):
        with self._com_lock:
            self._send_message( ComunicadorSerial.build_message(OperationType.WRITE, pin_type,address,value) )
        pass
    pass
