import serial
import serial.tools.list_ports
import time
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import csv
# from collections import deque # Nicht mehr benötigt

# ================================================================
# 🔹 Einstellungen
# ================================================================
TARGET_TEMP = 37.0  # Soll-Temperatur (wird jetzt im Plot angezeigt)
BAUD_RATE = 9600
CSV_FILE = "temperature_data_dual_axis.csv"
MAX_DATA_POINTS = None # Keine Begrenzung, alle Daten anzeigen.

# ================================================================
# 🔍 Automatische Port-Erkennung
# ================================================================
def find_serial_port():
    ports = serial.tools.list_ports.comports()
    print("Verfügbare serielle Ports:")
    if not ports:
        print(" -> Keine Ports gefunden.")
        return None
    for port in ports:
        print(f" -> {port.device} - {port.description}")
    print(f"Verwende Port: {ports[0].device}")
    return ports[0].device

# ================================================================
# 🔌 Serielle Verbindung
# ================================================================
SERIAL_PORT = find_serial_port()
# SERIAL_PORT = "COM6" # Manuell fallback

ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Warte auf Arduino Reset ({SERIAL_PORT})...")
        time.sleep(2)
        ser.flushInput()
        print(f"✅ Verbindung zu {SERIAL_PORT} hergestellt.")
    except serial.SerialException as e:
        print(f"❌ Fehler beim Öffnen des seriellen Ports {SERIAL_PORT}: {e}")
        exit()
else:
    print("❌ Kein serieller Port zum Verbinden gefunden. Skript wird beendet.")
    exit()

# ================================================================
# 💾 Datenspeicher
# ================================================================
timestamps = []
temp_data = []
pwm_data = []

# ================================================================
# 📄 CSV-Datei Initialisierung
# ================================================================
try:
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Zeit (s)", "Temperatur (°C)", "PWM"])
    print(f"💾 CSV-Datei '{CSV_FILE}' initialisiert.")
except IOError as e:
    print(f"❌ Fehler beim Erstellen/Schreiben der CSV-Datei: {e}")

# ================================================================
# 📈 Matplotlib-Setup für Dual-Y-Achse
# ================================================================
fig, ax1 = plt.subplots(figsize=(12, 6)) # Haupt-Achse (Temperatur)

# Titel und X-Achse
fig.suptitle("Live-Temperatur & PWM Daten (PID-Regelung)")
ax1.set_xlabel("Zeit seit Start (s)")

# Linke Y-Achse (Temperatur)
ax1.set_ylabel("Temperatur (°C)", color="blue")
ax1.tick_params(axis='y', labelcolor="blue")
ax1.grid(True, axis='y', linestyle=':', color='blue', alpha=0.5)
(line_temp,) = ax1.plot([], [], label="Temperatur", color="blue", marker='.', markersize=2, linestyle='-')

# --- NEU: Horizontale Linie für Sollwert hinzufügen ---
# Füge die Linie zu ax1 hinzu (Temperaturachse)
# axhline gibt ein Line2D-Objekt zurück, das wir für die Legende brauchen
line_target = ax1.axhline(TARGET_TEMP, color="red", linestyle="--", linewidth=1.5, label=f"Sollwert ({TARGET_TEMP}°C)")
# --- Ende NEU ---

# Rechte Y-Achse (PWM), die sich die X-Achse mit ax1 teilt
ax2 = ax1.twinx()
ax2.set_ylabel("PWM (0-255)", color="green")
ax2.tick_params(axis='y', labelcolor="green")
(line_pwm,) = ax2.plot([], [], label="PWM", color="green", linestyle=':', linewidth=1.5)

# --- NEU: Kombinierte Legende mit Sollwert-Linie ---
# Sammle alle Linien-Objekte (von plot und axhline)
lines = [line_temp, line_pwm, line_target]
# Extrahiere die Labels von den Linien-Objekten
labels = [l.get_label() for l in lines]
# Erstelle die Legende mit allen gesammelten Linien und Labels
ax1.legend(lines, labels, loc='upper left')
# --- Ende NEU ---

start_time = time.time()
last_timestamp_written = -1

# ================================================================
# 📱 Funktion zum Lesen der seriellen Daten (unverändert)
# ================================================================
def read_serial():
    global last_timestamp_written
    temp_val = None
    pwm_val = None
    timestamp = time.time() - start_time

    try:
        if ser and ser.in_waiting > 0:
            line_bytes = ser.readline()
            if not line_bytes: return None, None, None
            line = line_bytes.decode("utf-8").strip()
            if not line: return None, None, None

            parts = line.split(",")
            if len(parts) == 3:
                try:
                    temp_val = float(parts[0].strip())
                    pwm_val = int(parts[2].strip())
                    current_time_rounded = round(timestamp, 2)
                    if current_time_rounded > last_timestamp_written:
                         try:
                            with open(CSV_FILE, "a", newline="") as f:
                                writer = csv.writer(f)
                                writer.writerow([current_time_rounded, temp_val, pwm_val])
                            last_timestamp_written = current_time_rounded
                         except IOError as e:
                            print(f"❌ Fehler beim Schreiben in CSV: {e}")
                except ValueError as e:
                    print(f"⚠️ Konvertierungsfehler: '{line}' -> {e}.")
                    return None, None, None
                except IndexError:
                    print(f"⚠️ Indexfehler: '{line}'.")
                    return None, None, None
            else:
                if line and not line.startswith("PID") and not line.startswith("Setpoint"):
                     print(f"⚠️ Unerwartetes Format: '{line}'.")
                return None, None, None
        else:
            return None, None, None
    except serial.SerialException as e:
        print(f"❌ Serieller Lesefehler: {e}")
        return None, None, None
    except UnicodeDecodeError as e:
        raw_bytes = line_bytes if 'line_bytes' in locals() else b''
        print(f"❌ Dekodierfehler: {raw_bytes} -> {e}")
        return None, None, None
    except Exception as e:
        print(f"❌ Unerwarteter Fehler in read_serial: {e}")
        return None, None, None

    return timestamp, temp_val, pwm_val

# ================================================================
# 📊 Update-Funktion für den Live-Plot (unverändert)
# ================================================================
def update(frame):
    timestamp, temp, pwm = read_serial()

    if timestamp is not None and temp is not None and pwm is not None:
        timestamps.append(timestamp)
        temp_data.append(temp)
        pwm_data.append(pwm)

    if timestamps:
        line_temp.set_data(timestamps, temp_data)
        line_pwm.set_data(timestamps, pwm_data)

        current_max_time = timestamps[-1] if timestamps else 1.0
        ax1.set_xlim(0, max(current_max_time * 1.05, 10))

        if temp_data:
            min_temp = min(temp_data)
            max_temp = max(temp_data)
            padding_temp = max((max_temp - min_temp) * 0.1, 1.0)
            # Stelle sicher, dass die Soll-Linie immer sichtbar ist
            ax1.set_ylim(min(min_temp - padding_temp, TARGET_TEMP - 2),
                         max(max_temp + padding_temp, TARGET_TEMP + 2))
        else:
            ax1.set_ylim(15, 45)

        ax2.set_ylim(-5, 260) # Fester PWM-Bereich

        ax1.autoscale_view(scalex=False, scaley=False) # Y-Skala manuell gesetzt
        ax2.autoscale_view(scalex=False, scaley=False) # Y-Skala manuell gesetzt

    # Die Sollwertlinie (axhline) muss nicht im return sein
    return line_temp, line_pwm

# ================================================================
# 🔄 Funktion zur PID-Steuerung über Tastatur (unverändert)
# ================================================================
def pid_control():
     while True:
        try:
            user_input = input("➡️ Drücke '1' für PID EIN, '0' für PID AUS (oder 'q' zum Beenden): ").strip().lower()
            if user_input in ["0", "1"]:
                if ser and ser.is_open:
                    ser.write(user_input.encode())
                    print(f"🔄 PID {'aktiviert' if user_input == '1' else 'deaktiviert'} gesendet.")
                else:
                    print("⚠️ Serielle Verbindung nicht offen.")
            elif user_input == 'q':
                print("Beende Tastatureingabe-Thread...")
                break
            else:
                print("⚠️ Ungültige Eingabe. Bitte '1', '0' oder 'q' eingeben.")
        except EOFError:
            print("Keine Eingabe möglich (EOF). Beende Tastatur-Thread.")
            break
        except Exception as e:
            print(f"Fehler im Eingabe-Thread: {e}")
            break

# ================================================================
# 🚀 Start (unverändert)
# ================================================================
print("Starte Live-Plot...")
print("Drücke '1' oder '0' im Terminal, um PID zu steuern.")

input_thread = threading.Thread(target=pid_control, daemon=True)
input_thread.start()

ani = animation.FuncAnimation(fig, update, interval=200, blit=False, cache_frame_data=False)

try:
    plt.show()
except KeyboardInterrupt:
    print("\nKeyboardInterrupt empfangen.")
finally:
    # ================================================================
    # 🧹 Aufräumen (unverändert)
    # ================================================================
    print("Beende Programm und schließe Ressourcen...")
    if ser and ser.is_open:
        try:
            ser.write(b'0')
            time.sleep(0.1)
            ser.close()
            print(f"✅ Serielle Verbindung {SERIAL_PORT} geschlossen.")
        except serial.SerialException as e:
            print(f"⚠️ Fehler beim Schließen der seriellen Verbindung: {e}")

    try:
        fig.savefig("temperature_pwm_plot_final.png")
        print(f"🖼️ Finaler Plot gespeichert als 'temperature_pwm_plot_final.png'")
    except Exception as e:
        print(f"❌ Fehler beim Speichern des Plots: {e}")

    print("Programm beendet.")