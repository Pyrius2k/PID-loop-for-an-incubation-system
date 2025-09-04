import serial
import struct
import time
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from scipy import signal

try:
    import allantools
except ImportError:
    print("--------------------------------------------------------------------")
    print("ERROR: The 'allantools' library was not found.")
    print("Please install it with: pip install allantools")
    print("Allan Deviation plot will be skipped.")
    print("--------------------------------------------------------------------")
    allantools = None

SERIAL_PORT = 'COM6'
BAUD_RATE = 115200
MEASUREMENT_DURATION_S = 60

BETA = 3435.0
R_FIXED = 10000.0
R0_NTC = 10000.0
T0_K = 273.15 + 25.0
ADC_MAX = 1023.0
VCC = 5.0

all_timestamps = []
all_temperatures = []
all_voltages = []

def adc_to_temperature(adc_value):
    """
    Converts an ADC value to temperature (Celsius).
    Formula for: 5V --- NTC --- A0 --- R_fixed --- GND
    """
    if adc_value <= 0: return float('-inf')
    if adc_value >= ADC_MAX: return float('inf')
    try:
        r_ntc = R_FIXED * (ADC_MAX / adc_value - 1.0)
        if r_ntc <= 1e-6:
            return float('inf')

        inv_T = (1.0 / T0_K) + (1.0 / BETA) * np.log(r_ntc / R0_NTC)
        if abs(inv_T) < 1e-12:
            return float('inf')

        temp_k = 1.0 / inv_T
        temp_c = temp_k - 273.15
        return temp_c
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        print(f"Error in temperature calculation for ADC={adc_value}: {e}")
        return np.nan

def adc_to_voltage_r_fixed(adc_value):
    """
    Converts an ADC value to the voltage across the fixed resistor.
    For the circuit: 5V --- NTC --- A0 --- R_fixed --- GND
    V_A0 is the voltage across R_fixed.
    """
    if adc_value < 0 or adc_value > ADC_MAX:
        return np.nan
    return (adc_value / ADC_MAX) * VCC

ser = None
block_sample_counts = []
block_durations_micros = []
fs = 0

try:
    print(f"Connecting to Arduino on {SERIAL_PORT} at {BAUD_RATE} Baud...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
    print("Waiting for start message from Arduino...")
    start_message_found = False

    ser.timeout = 5
    for _ in range(5):
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"Arduino: {line}")
            if "Arduino ready" in line:
                start_message_found = True
                break
        except serial.SerialTimeoutException:
            print("Timeout while waiting for Arduino start message.")
            break
        except Exception as e:
            print(f"Error reading start message: {e}")
            break
    ser.timeout = 2

    if not start_message_found:
        print("Expected start message not received. Script will exit.")
        exit()

    print("Starting data acquisition for {} seconds...".format(MEASUREMENT_DURATION_S))
    script_start_time = time.monotonic()
    last_receive_time = script_start_time

    while (time.monotonic() - script_start_time) < MEASUREMENT_DURATION_S:
        if ser.in_waiting > 0:
            start_byte = ser.read(1)
            if start_byte == b'S':
                last_receive_time = time.monotonic()
                header_bytes = ser.read(6)
                if len(header_bytes) == 6:
                    num_samples, duration_micros = struct.unpack('<HL', header_bytes)
                    data_bytes_to_read = num_samples * 2
                    adc_data_bytes = ser.read(data_bytes_to_read)
                    end_byte = ser.read(1)

                    if len(adc_data_bytes) == data_bytes_to_read and end_byte == b'E':
                        block_receive_time = time.monotonic()

                        block_duration_s = duration_micros / 1_000_000.0
                        block_start_time_approx = block_receive_time - block_duration_s

                        format_string = '<' + 'H' * num_samples
                        adc_values = struct.unpack(format_string, adc_data_bytes)
                        print(f"Block received: {num_samples} samples, duration: {duration_micros} us ({block_duration_s*1000:.2f} ms)")

                        block_sample_counts.append(num_samples)
                        block_durations_micros.append(duration_micros)

                        for i, adc_val in enumerate(adc_values):
                            sample_time_s = block_start_time_approx + (i / num_samples) * block_duration_s
                            temp_c = adc_to_temperature(adc_val)
                            volt_r_fixed = adc_to_voltage_r_fixed(adc_val)

                            if not np.isnan(temp_c) and np.isfinite(temp_c) and not np.isnan(volt_r_fixed):
                                all_timestamps.append(sample_time_s)
                                all_temperatures.append(temp_c)
                                all_voltages.append(volt_r_fixed)

                    else:
                        print(f"Error: Incomplete data or wrong end byte. Expected {data_bytes_to_read} bytes, got {len(adc_data_bytes)}. End byte: {end_byte}")
                        ser.reset_input_buffer()
                else:
                    print("Error: Header not received completely.")
                    ser.reset_input_buffer()

        time.sleep(0.001)

        if (time.monotonic() - last_receive_time) > 5.0:
            print("Timeout: No data received from Arduino for 5 seconds. Aborting.")
            break

    print("Data acquisition finished.")

    if not all_timestamps:
        print("No valid data received.")
    else:
        print("\nProcessing collected data...")
        timestamps_np = np.array(all_timestamps)
        temperatures_np = np.array(all_temperatures)
        voltages_np = np.array(all_voltages)

        if block_sample_counts and block_durations_micros:
            total_samples_in_blocks = sum(block_sample_counts)
            total_duration_in_blocks_s = sum(block_durations_micros) / 1_000_000.0
            if total_duration_in_blocks_s > 0:
                fs = total_samples_in_blocks / total_duration_in_blocks_s
                print(f"Average sampling rate (fs): {fs:.2f} Hz")
            else:
                print("Warning: Total block duration is 0, sampling rate cannot be determined.")
        else:
            print("Warning: No block information available, sampling rate cannot be determined.")

        time_relative_s = timestamps_np - timestamps_np[0]
        measurement_end_time_s = time_relative_s[-1]

        bin_edges = np.arange(0, measurement_end_time_s + 1.1, 1.0)
        bin_indices = np.digitize(time_relative_s, bin_edges)

        plot_times = []
        plot_temp_means = []
        plot_temp_stds = []
        plot_volt_means = []
        plot_volt_stds = []

        for i in range(1, len(bin_edges)):
            bin_center_time = (bin_edges[i-1] + bin_edges[i]) / 2.0
            mask = (bin_indices == i)

            if np.any(mask):
                temps_in_bin = temperatures_np[mask]
                volts_in_bin = voltages_np[mask]

                plot_times.append(bin_center_time)
                plot_temp_means.append(np.mean(temps_in_bin))
                plot_temp_stds.append(np.std(temps_in_bin))
                plot_volt_means.append(np.mean(volts_in_bin))
                plot_volt_stds.append(np.std(volts_in_bin))

        if plot_times:
            print("Creating temperature time series plot...")
            plt.figure(figsize=(12, 6))
            plt.errorbar(plot_times, plot_temp_means, yerr=plot_temp_stds, fmt='-o', capsize=5, label='Temp (°C) ± Std. Dev.')
            plt.xlabel("Time since measurement start (s)")
            plt.ylabel("Temperature (°C)")
            plt.title(f"NTC Temperature Measurement ({MEASUREMENT_DURATION_S}s) - 1s Intervals")
            plt.legend()
            plt.grid(True)

            min_val_t = np.min(np.array(plot_temp_means) - np.array(plot_temp_stds))
            max_val_t = np.max(np.array(plot_temp_means) + np.array(plot_temp_stds))
            data_range_t = max_val_t - min_val_t
            padding_t = max(data_range_t * 0.1, 0.1)
            plt.ylim(min_val_t - padding_t, max_val_t + padding_t)
            plt.tight_layout()
        else:
            print("No data to plot for temperature time series after aggregation.")

        if plot_times:
            print("Creating voltage time series plot...")
            plt.figure(figsize=(12, 6))
            plt.errorbar(plot_times, plot_volt_means, yerr=plot_volt_stds, fmt='-o', capsize=5, color='green', label=f'Voltage across R_fixed ({R_FIXED:.0f}Ω) ± Std. Dev.')
            plt.xlabel("Time since measurement start (s)")
            plt.ylabel("Voltage (V)")
            plt.title(f"Voltage Measurement across Fixed Resistor ({MEASUREMENT_DURATION_S}s) - 1s Intervals (VCC={VCC}V)")
            plt.legend()
            plt.grid(True)

            min_val_v = np.min(np.array(plot_volt_means) - np.array(plot_volt_stds))
            max_val_v = np.max(np.array(plot_volt_means) + np.array(plot_volt_stds))
            data_range_v = max_val_v - min_val_v
            padding_v = max(data_range_v * 0.1, 0.05)
            plt.ylim(min_val_v - padding_v, max_val_v + padding_v)
            plt.tight_layout()
        else:
            print("No data to plot for voltage time series after aggregation.")

        print("\nPerforming frequency analysis of temperature...")
        if fs > 0 and len(temperatures_np) > 1:
            temps_detrended = signal.detrend(temperatures_np)
            n_fft = min(len(temps_detrended), 2048)

            if n_fft < 64:
                print(f"Warning: Not enough data points ({len(temps_detrended)}) for robust PSD analysis with Welch (min segment length 64).")
                frequencies, psd, asd = None, None, None
            else:
                frequencies, psd = signal.welch(
                    temps_detrended,
                    fs,
                    nperseg=n_fft,
                    noverlap=n_fft // 2,
                    scaling='density'
                )

                valid_indices = frequencies > 0
                frequencies = frequencies[valid_indices]
                psd = psd[valid_indices]

                if len(frequencies) > 0:
                    asd = np.sqrt(psd)

                    plt.figure(figsize=(10, 6))
                    plt.loglog(frequencies, psd)
                    plt.title('Power Spectral Density (PSD) of Temperature')
                    plt.xlabel('Frequency (Hz)')
                    plt.ylabel('PSD (°C$^2$/Hz)')
                    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                    plt.tight_layout()

                    plt.figure(figsize=(10, 6))
                    plt.loglog(frequencies, asd)
                    plt.title('Amplitude Spectral Density (ASD / NETD) of Temperature')
                    plt.xlabel('Frequency (Hz)')
                    plt.ylabel('ASD / NETD (°C/$\\sqrt{\mathrm{Hz}}$)')
                    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                    plt.tight_layout()

                    try:
                        low_freq_cutoff = max(1.0, frequencies[0] * 1.1)
                        high_freq_cutoff = min(fs / 2.1, 1000)
                        if low_freq_cutoff < high_freq_cutoff:
                            relevant_indices = (frequencies >= low_freq_cutoff) & (frequencies <= high_freq_cutoff)
                            if np.any(relevant_indices):
                                mean_netd = np.mean(asd[relevant_indices])
                                print(f"Mean NETD ({low_freq_cutoff:.1f}-{high_freq_cutoff:.1f} Hz): {mean_netd:.4e} °C/sqrt(Hz)")
                            else:
                                print(f"No data in the frequency range {low_freq_cutoff:.1f}-{high_freq_cutoff:.1f} Hz for mean NETD.")
                        else:
                            print("Frequency range for mean NETD is invalid.")
                    except Exception as e:
                        print(f"Could not calculate mean NETD: {e}")

                else:
                    print("No valid frequencies > 0 found after Welch method.")
        elif fs <= 0:
            print("Sampling rate could not be determined, frequency analysis skipped.")
        else:
            print("Too few data points for frequency analysis.")

        print("\nCalculating Allan Deviation of temperature...")
        if allantools is not None and fs > 0 and len(temperatures_np) > 100:
            try:
                tau0 = 1.0 / fs
                max_tau = measurement_end_time_s / 3.0
                if max_tau > tau0:
                    taus = np.logspace(np.log10(tau0), np.log10(max_tau), 50)

                    (tau_out, adev, adeverr, n) = allantools.adev(
                        temperatures_np,
                        rate=fs,
                        data_type="freq",
                        taus=taus
                    )

                    plt.figure(figsize=(10, 6))
                    plt.loglog(tau_out, adev, '-o', markersize=4)
                    plt.title('Allan Deviation of Temperature')
                    plt.xlabel('Averaging time τ (s)')
                    plt.ylabel('Allan Deviation σ(τ) (°C)')
                    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
                    plt.tight_layout()

                    min_adev_idx = np.argmin(adev)
                    min_tau = tau_out[min_adev_idx]
                    min_adev = adev[min_adev_idx]
                    print(f"Best stability (min ADEV): {min_adev:.4e} °C at τ = {min_tau:.2f} s")
                    plt.loglog(min_tau, min_adev, 'rs', markersize=8, label=f'Min ADEV @ {min_tau:.2f}s')
                    plt.legend()

                else:
                    print("Total measurement duration too short for meaningful tau values.")

            except Exception as e:
                print(f"Error calculating Allan Deviation: {e}")

        elif allantools is None:
            print("Allan Deviation skipped as 'allantools' could not be imported.")
        elif fs <= 0:
            print("Allan Deviation skipped as sampling rate is unknown.")
        else:
            print(f"Too few data points ({len(temperatures_np)}) for Allan Deviation analysis.")

        print("\nShowing all plots...")
        plt.show()

except serial.SerialException as e:
    print(f"Error with serial connection: {e}")
except KeyboardInterrupt:
    print("\nMeasurement aborted by user.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    if ser and ser.is_open:
        ser.close()
        print("Serial connection closed.")