import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# 🎯 Target temperature
TARGET_TEMP = 37.0

# 🔍 Automatic port detection
def find_serial_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Found port: {port.device}")
    return ports[0].device if ports else None

# 🎯 Set the port (automatic or manual)
SERIAL_PORT = find_serial_port() or "COM6"  # Set to "COM3" manually if needed
BAUD_RATE = 9600

# Establish serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to be ready
    print(f"✅ Connection to {SERIAL_PORT} established.")
except serial.SerialException as e:
    print(f"❌ Error: {e}")
    exit()

# 🔄 FIFO storage for the last 100 measurements
data = deque(maxlen=100)

# 📊 Matplotlib setup
fig, ax = plt.subplots()
ax.set_title("Live Temperature Data")
ax.set_xlabel("Measurement Point")
ax.set_ylabel("Temperature (°C)")
line, = ax.plot([], [], label="Temperature")
ax.legend()
ax.grid()

# 📡 Read data from serial port
def read_serial():
    try:
        line = ser.readline().decode("utf-8").strip()
        return float(line) if line else None
    except ValueError:
        return None

# 📈 Update plot
def update(frame):
    temp = read_serial()
    if temp is not None:
        data.append(temp)
    line.set_data(range(len(data)), list(data))
    ax.set_xlim(0, len(data))  # Automatically adjust X-axis
    ax.set_ylim(min(data, default=20) - 1, max(data, default=30) + 1)  # Scale Y-axis
    return line,

# 🚀 Start animation
ani = animation.FuncAnimation(fig, update, interval=500)
plt.show()

# 🔌 Close serial connection when window is closed
ser.close()
plt.show(block=True)