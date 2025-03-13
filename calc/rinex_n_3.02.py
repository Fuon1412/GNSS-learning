import re
import pandas as pd
import json
from datetime import datetime

def extract_numbers(line):
    """
    Extract numerical values from a given line using regular expression.
    """
    return re.findall(r'[-+]?\d*\.\d+E[+-]\d+|[-+]?\d+', line.replace('D', 'E'))

def _obstime(fol):
    return datetime(year=int(fol[0]), month=int(fol[1]), day=int(fol[2]),
                    hour=int(fol[3]), minute=int(fol[4]),
                    second=int(float(fol[5])))

def read_rinex_body(file):
    """
    Read the RINEX 3.02 navigation message file and extract navigation data for QZSS satellites.
    """
    fields = [
        'SVclockBias', 'SVclockDrift', 'SVclockDriftRate', 'IODE', 'Crs', 'DeltaN', 'M0',
        'Cuc', 'Eccentricity', 'Cus', 'sqrtA', 'Toe', 'Cic', 'Omega0', 'Cis',
        'Io', 'Crc', 'omega', 'OmegaDot', 'IDOT', 'CodesL2', 'GPSWeek', 'L2Pflag',
        'SVacc', 'health', 'TGD', 'IODC', 'TransTime', 'FitIntvl'
    ]
    
    nav_data = []
    with open(file, 'r', encoding='utf-8') as f:
        # Skip header
        for line in f:
            if "END OF HEADER" in line:
                break
        
        # Process navigation data
        for line in f:
            prn_str = line[:3].strip()
            
            # Parse datetime and PRN
            dt = _obstime([line[4:8], line[9:11], line[12:14], line[15:17], line[18:20], line[21:23]])
            prn = f'G{prn_str[1:]}'
            
            if prn != "G05":
                continue
            
            # Collect raw data across multiple lines
            raw_data = [line[23:].strip()]
            for _ in range(7):
                extra_line = f.readline()
                if not extra_line:
                    break
                raw_data.append(extra_line.strip())
            
            # Extract numerical values
            raw_values = extract_numbers(" ".join(raw_data))
            
            # Ensure correct field-value mapping
            entry = {"Satellite": prn, "Epoch Time": dt.strftime('%Y-%m-%d %H:%M:%S')}
            for k, v in zip(fields, raw_values):
                try:
                    entry[k] = float(v)
                except ValueError:
                    entry[k] = None
            nav_data.append(entry)
    
    return nav_data

def save_to_json(data, output_file):
    """
    Save navigation data to a JSON file.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {output_file}")

# File paths
rinex_file = "../data/GPS_nav_3.02.rnx"
output_json = "gps_output_2.json"

# Run extraction
nav_data = read_rinex_body(rinex_file)
save_to_json(nav_data, output_json)
