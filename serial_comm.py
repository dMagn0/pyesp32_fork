import serial
import time
import threading

# op val pin
# 0  001 100

counter = 0


def read_serial(ser):
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode("utf-8").strip()
            print(f"Received: {data}")


def send_message(ser, msg, op):
    msg = f"{op}{msg}"
    ser.write(msg.encode("utf-8"))


# Replace 'COM3' with your ESP32's serial port
ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)

# Start the reading thread
threading.Thread(target=read_serial, args=(ser,), daemon=True).start()

# Wait a bit for the connection to establish
time.sleep(1)

# Keep the main thread alive
read_msg = "001101"
while True:
    operation = input("Enter operation (0 for read, 1 for write): ")
    while operation not in ["0", "1"]:
        operation = input("Invalid input. Enter operation (0 for read, 1 for write): ")

    counter += 1
    write_msg = f"00{counter % 2}100"
    if operation == "1":
        send_message(ser, write_msg, 1)
    if operation == "0":
        send_message(ser, read_msg, 0)
    time.sleep(1)
