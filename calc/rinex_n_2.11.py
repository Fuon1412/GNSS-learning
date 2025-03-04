import re
import json
import numpy as np
from datetime import datetime
from collections import defaultdict
from typing import List

rinex_file = "../data/brdc1810.09n"  # Đường dẫn đến file RINEX
output_file = "rinex_output.json"  # File JSON đầu ra

header_data = {}
nav_data = defaultdict(list)
fields = ['SVclockBias', 'SVclockDrift', 'SVclockDriftRate', 'IODE', 'Crs', 'DeltaN',
          'M0', 'Cuc', 'Eccentricity', 'Cus', 'sqrtA', 'Toe', 'Cic', 'Omega0', 'Cis', 'Io',
          'Crc', 'omega', 'OmegaDot', 'IDOT', 'CodesL2', 'GPSWeek', 'L2Pflag', 'SVacc',
          'health', 'TGD', 'IODC', 'TransTime', 'FitIntvl', 'unknown1', 'unknown2']


def extract_numbers(line: str) -> List[str]:
    """Tách các số từ một dòng văn bản, kể cả số khoa học"""
    return re.findall(r'[-+]?\d*\.\d+E[+-]\d+|[-+]?\d+', line)


def _obstime(fol: List[str]) -> datetime:
    """Chuyển đổi thời gian từ danh sách số sang đối tượng datetime"""
    year = int(fol[0])
    if 80 <= year <= 99:
        year += 1900
    elif year < 80:
        year += 2000

    return datetime(year=year, month=int(fol[1]), day=int(fol[2]),
                    hour=int(fol[3]), minute=int(fol[4]),
                    second=int(float(fol[5])),
                    microsecond=int(float(fol[5]) % 1 * 1000000))


def read_rinex_header(rinex_file):
    header_data = {}
    with open(rinex_file, 'r', encoding="utf-8") as f:
        for line in f:
            if "RINEX VERSION / TYPE" in line:
                header_data["version"] = float(line.split()[0])
                header_data["filetype"] = re.split(r'\s{2,}', line.strip())[1]
            elif "ION ALPHA" in line:
                header_data["ion_alpha"] = extract_numbers(line)
            elif "ION BETA" in line:
                header_data["ion_beta"] = extract_numbers(line)
            elif "DELTA-UTC" in line:
                header_data["delta_utc"] = {
                    "A0": line[:22].strip(),
                    "A1": line[22:41].strip(),
                    "T": line[41:50].strip(),
                    "W": line[51:60].strip()
                }
            elif "LEAP SECONDS" in line:
                header_data["leap_seconds"] = int(line[0:6].strip())
            elif "END OF HEADER" in line:
                break
    return header_data


def read_rinex_body(rinex_file):
    nav_data = defaultdict(list)
    with open(rinex_file, 'r', encoding="utf-8") as f:
        for line in f:
            if "END OF HEADER" in line:
                break

        for line in f:
            prn_str = line[:3].strip()
            if not prn_str.isdigit():
                continue
            
            dt = _obstime([line[3:5], line[6:8], line[9:11], line[12:14], line[15:17], line[17:22]])
            prn = f'GPS{int(prn_str):02d}'

            raw_data = [line[22:].strip()]
            for _ in range(7):
                extra_line = f.readline()
                if not extra_line:
                    break
                raw_data.append(extra_line.strip())
            
            raw_values = extract_numbers(" ".join(raw_data))
            if len(raw_values) == len(fields):
                nav_data[str(dt)].append(dict(zip(fields, map(float, raw_values))))
    
    return nav_data


def save_to_json(output_file, header_data, nav_data):
    data = {
        "header": header_data,
        "navigation": nav_data
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


header_data = read_rinex_header(rinex_file)
nav_data = read_rinex_body(rinex_file)

save_to_json(output_file, header_data, nav_data)
print(f"Data saved to {output_file}")
