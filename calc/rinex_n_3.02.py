import re
import pandas as pd
from datetime import datetime

def extract_numbers(line):
    """
    Extract numerical values from a given line using regular expression.
    """
    return re.findall(r'[-+]?\d*\.\d+E[+-]\d+|[-+]?\d+', line.replace('D', 'E'))

def _obstime(fol):
    """
    Convert observation time components to a datetime object.
    """
    year = int(fol[0])
    if 80 <= year <= 99:
        year += 1900
    elif year < 80:
        year += 2000
    return datetime(year, int(fol[1]), int(fol[2]), int(fol[3]), int(fol[4]), int(fol[5]))

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
            if not prn_str.startswith('J'):
                continue  # Only process QZSS satellites
            
            # Parse datetime and PRN
            dt = _obstime([line[4:8], line[9:11], line[12:14], line[15:17], line[18:20], line[21:23]])
            prn = f'QZSS{prn_str[1:]}'
            
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
            for k, v in zip(fields, raw_values):
                try:
                    nav_data.append({"Satellite": prn, "Epoch Time": dt, "Parameter": k, "Value": float(v)})
                except ValueError:
                    nav_data.append({"Satellite": prn, "Epoch Time": dt, "Parameter": k, "Value": None})
    
    return nav_data

def save_to_csv(data, output_file):
    """
    Save navigation data to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

# File paths
rinex_file = "../data/30340780.21q"
output_csv = "qzss_output.csv"

# Run extraction
nav_data = read_rinex_body(rinex_file)
save_to_csv(nav_data, output_csv)
