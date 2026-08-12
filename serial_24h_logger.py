# -*- coding: utf-8 -*-
"""
serial_24h_logger.py
BrewXOS - 24h serial stability test.

Parses Mind+ format from program.ino (t7.txt=... + 0xFF 0xFF 0xFF) and writes
to CSV. Designed to run for 24h unattended.

Output columns:
  timestamp_iso, time_s, ds18b20_C, scd4x_temp_C, DO_pct, CO2_ppm, pH

Mind+ field mapping (from program.ino):
  t7.txt  = DS18B20 temperature (pin 47)
  t8.txt  = SCD4X temperature
  t9.txt  = Dissolved Oxygen (%)
  t10.txt = SCD4X CO2 (ppm)
  t11.txt = pH (A6)

Usage:
  python serial_24h_logger.py --port COM5 --out data/run_20260812.csv
  python serial_24h_logger.py --port COM5 --out data/run.csv --duration 24h
"""

import argparse
import csv
import re
import sys
import time
from datetime import datetime, timedelta


def open_serial(port, baud=115200):
    try:
        import serial
    except ImportError:
        print("ERROR: pyserial not installed. Run: pip install pyserial")
        sys.exit(1)
    ser = serial.Serial(port, baud, timeout=1.0)
    time.sleep(2)  # wait for Arduino reset after open
    ser.reset_input_buffer()
    print(f"Connected to {port} at {baud} baud.")
    return ser


# Mind+ format: "t7.txt=23.45" or "t11.txt=OFFLINE"
FIELD_RE = re.compile(rb't(\d+)\.txt=([\d\.\-]+|OFFLINE|-127)')


def parse_mindplus_payload(payload: bytes):
    """Extract dict {field_num: value} from a 0xFF-terminated payload."""
    out = {}
    for m in FIELD_RE.finditer(payload):
        field_num = int(m.group(1))
        raw = m.group(2)
        if raw == b'OFFLINE' or raw == b'-127':
            out[field_num] = 'OFFLINE'
        else:
            try:
                out[field_num] = float(raw)
            except ValueError:
                out[field_num] = 'OFFLINE'
    return out


def make_row(t_start, fields):
    """Build a CSV row from a {field_num: value} dict."""
    elapsed = (datetime.now() - t_start).total_seconds()
    ts = datetime.now().isoformat(timespec='seconds')

    def val(num):
        return fields.get(num, 'OFFLINE')

    return [
        ts,
        f"{elapsed:.1f}",
        val(7),    # DS18B20
        val(8),    # SCD4X temp
        val(9),    # DO %
        val(10),   # CO2 ppm
        val(11),   # pH
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='COM5', help='Serial port (e.g. COM5)')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--out', default='data/serial_24h.csv', help='Output CSV path')
    ap.add_argument('--duration', default='24h', help='Run duration (e.g. 24h, 1h, 30m)')
    args = ap.parse_args()

    # Parse duration
    m = re.match(r'^(\d+)([hm])$', args.duration)
    if not m:
        print("ERROR: --duration must be like '24h' or '30m'")
        sys.exit(1)
    n, unit = int(m.group(1)), m.group(2)
    total_seconds = n * 3600 if unit == 'h' else n * 60
    end_time = datetime.now() + timedelta(seconds=total_seconds)
    print(f"Will run for {args.duration} (until {end_time.strftime('%H:%M:%S')})")

    ser = open_serial(args.port, args.baud)
    t_start = datetime.now()

    buf = bytearray()
    n_cycles = 0
    n_rows = 0
    last_print = time.time()

    header = [
        'timestamp_iso', 'time_s',
        'ds18b20_C', 'scd4x_temp_C',
        'DO_pct', 'CO2_ppm', 'pH'
    ]

    with open(args.out, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        writer.writerow(header)
        print(f"Logging to {args.out}  (Ctrl+C to stop)")
        print(f"{'time':>10} {'T(DS)':>8} {'T(SC)':>8} {'DO%':>6} {'CO2':>6} {'pH':>5}")

        try:
            while datetime.now() < end_time:
                byte = ser.read(1)
                if not byte:
                    continue
                buf.extend(byte)

                # 0xFF 0xFF 0xFF = end of Mind+ payload
                if len(buf) >= 3 and buf[-3:] == b'\xff\xff\xff':
                    payload = bytes(buf[:-3])
                    buf.clear()

                    if not payload:
                        continue

                    fields = parse_mindplus_payload(payload)
                    if not fields:
                        continue

                    # We have all 5 fields → write a row
                    if all(k in fields for k in (7, 8, 9, 10, 11)):
                        row = make_row(t_start, fields)
                        writer.writerow(row)
                        n_rows += 1
                        n_cycles += 1

                        # Print every 5s
                        if time.time() - last_print > 5:
                            print(
                                f"{row[1]:>10} "
                                f"{str(row[2]):>8} "
                                f"{str(row[3]):>8} "
                                f"{str(row[4]):>6} "
                                f"{str(row[5]):>6} "
                                f"{str(row[6]):>5}"
                            )
                            last_print = time.time()
                            fout.flush()

        except KeyboardInterrupt:
            print(f"\nStopped by user. {n_rows} rows logged.")
        except Exception as e:
            print(f"\nERROR: {e}")
            print(f"Saving {n_rows} rows before exit...")
        finally:
            ser.close()
            print(f"Done. {n_rows} rows saved to {args.out}")
            print(f"Run: python day2_serial_fit.py --refit {args.out}")


if __name__ == '__main__':
    main()
