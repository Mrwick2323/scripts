#!/usr/bin/env python3

import re
import time
import struct
import serial
from pathlib import Path

PORT      = "/dev/ttyUSB2"
BAUD      = 115200
COMMAND   = "md 0x0 0x8000"
OUT_FILE  = Path("~/bootrom.bin").expanduser()
TIMEOUT   = 10   # seconds of silence before assuming transfer is done

def parse_md_line(line: str) -> bytes | None:
    """Parse one U-Boot `md` output line into raw bytes."""
    m = re.match(r"[0-9a-fA-F]+:\s+((?:[0-9a-fA-F]{8}\s*)+)", line)
    if not m:
        return None
    words = m.group(1).split()
    return b"".join(struct.pack(">I", int(w, 16)) for w in words)

def main():
    print(f"Opening {PORT} at {BAUD} baud...")
    ser = serial.Serial(PORT, baudrate=BAUD, timeout=1)
    time.sleep(0.5)

    ser.reset_input_buffer()
    ser.write((COMMAND + "\n").encode())
    ser.flush()
    print(f"Sent: {COMMAND}")

    raw_lines: list[str] = []
    last_data = time.time()

    while True:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
            raw_lines.append(line)
            last_data = time.time()
        elif time.time() - last_data > TIMEOUT:
            print("No data received — transfer complete.")
            break

    ser.close()

    chunks: list[bytes] = []
    for line in raw_lines:
        data = parse_md_line(line)
        if data:
            chunks.append(data)

    if not chunks:
        print("No parseable hex data found in output.")
        return

    binary = b"".join(chunks)
    OUT_FILE.write_bytes(binary)
    print(f"Saved {len(binary):,} bytes to {OUT_FILE}")

if __name__ == "__main__":
    main()