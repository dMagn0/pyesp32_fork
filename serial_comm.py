import serial
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

# Configuration
THRESHOLD = 3000  # Threshold for analog reading (adjust as needed)
READ_INTERVAL = 0.5  # Seconds between reads
GPIO_READ_PIN = 4  # GPIO4 for analog reading
GPIO_WRITE_PIN = 5  # GPIO5 for digital writing

last_read_time = 0


def build_message(operation, pin_type, address, value):
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


def parse_message(msg):
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


def read_serial(ser):
    """Thread function to continuously read from serial port."""
    while True:
        if ser.in_waiting > 0:
            try:
                data = ser.readline().decode("utf-8").strip()
            except Exception as ex:
                print(ex)
                continue

            # Parse the message
            parsed = parse_message(data)
            if parsed:
                print(f"Address: {parsed['address']}, Value: {parsed['value']}")

                # Check if it's a read response from GPIO4
                if parsed["operation"] == "r" and parsed["address"] == GPIO_READ_PIN:
                    value = parsed["value"]

                    # Check threshold
                    if value >= THRESHOLD:
                        write_msg = build_message("w", "d", GPIO_WRITE_PIN, 1)
                        ser.write(write_msg.encode("utf-8"))
                    else:
                        write_msg = build_message("w", "d", GPIO_WRITE_PIN, 0)
                        ser.write(write_msg.encode("utf-8"))


def send_periodic_read(ser):
    """Send periodic read requests for GPIO4."""
    global last_read_time

    current_time = time.time()
    if current_time - last_read_time >= READ_INTERVAL:
        read_msg = build_message("r", "a", GPIO_READ_PIN, 0)
        ser.write(read_msg.encode("utf-8"))
        last_read_time = current_time


# Replace '/dev/ttyUSB0' with your ESP32's serial port
ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)

# Start the reading thread
threading.Thread(target=read_serial, args=(ser,), daemon=True).start()

# Wait a bit for the connection to establish
time.sleep(1)

print("Serial communication started on /dev/ttyUSB0")
print(f"Reading GPIO{GPIO_READ_PIN} (analog) every {READ_INTERVAL} seconds")
print(f"Threshold: {THRESHOLD} - Will set GPIO{GPIO_WRITE_PIN} HIGH when exceeded")
print("Press Ctrl+C to exit\n")

# Main loop - send periodic reads
try:
    while True:
        send_periodic_read(ser)
        time.sleep(0.1)  # Small sleep to prevent CPU spinning
except KeyboardInterrupt:
    print("\nExiting...")
    ser.close()
