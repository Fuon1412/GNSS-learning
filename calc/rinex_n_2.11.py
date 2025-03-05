import re
import pandas as pd
from datetime import datetime
from collections import defaultdict

# Input and output file paths
rinex_file = "../data/brdc1810.09n"
output_csv = "rinex_output.csv"

# Mapping of original field names to their symbolic representations
fields =['SVclockBias', 'SVclockDrift', 'SVclockDriftRate', 'IODE', 'Crs', 'DeltaN',
          'M0', 'Cuc', 'Eccentricity', 'Cus', 'sqrtA', 'Toe', 'Cic', 'Omega0', 'Cis', 'Io',
          'Crc', 'omega', 'OmegaDot', 'IDOT', 'CodesL2', 'GPSWeek', 'L2Pflag', 'SVacc',
          'health', 'TGD', 'IODC', 'TransTime', 'FitIntvl', 'dontknow', 'dontknow2']

def extract_numbers(line):
    """
    Extract numerical values from a given line using regular expression.
    
    Args:
        line (str): Input line containing numerical values
    
    Returns:
        list: Extracted numerical values
    """
    return re.findall(r'[-+]?\d*\.\d+E[+-]\d+|[-+]?\d+', line)

def _obstime(fol):
    """
    Convert observation time components to a datetime object.
    
    Args:
        fol (list): List of time components [year, month, day, hour, minute, second]
    
    Returns:
        datetime: Parsed datetime object
    """
    year = int(fol[0])
    if 80 <= year <= 99:
        year += 1900
    elif year < 80:
        year += 2000
    return datetime(year, int(fol[1]), int(fol[2]), int(fol[3]), int(fol[4]), int(float(fol[5])))

def read_rinex_body(file):
    """
    Read RINEX navigation message file and extract navigation data.
    
    Args:
        file (str): Path to the RINEX navigation message file
    
    Returns:
        list: List of dictionaries containing navigation data
    """
    nav_data = []
    with open(file, 'r', encoding="utf-8") as f:
        # Skip header
        for line in f:
            if "END OF HEADER" in line:
                break

        # Process navigation message body
        for line in f:
            prn_str = line[:3].strip()
            if not prn_str.isdigit():
                continue
            
            # Parse datetime and PRN
            dt = _obstime([line[3:5], line[6:8], line[9:11], line[12:14], line[15:17], line[17:22]])
            prn = f'GPS{int(prn_str):02d}'

            # Collect raw data across multiple lines
            raw_data = [line[22:].strip()]
            for _ in range(7):
                extra_line = f.readline()
                if not extra_line:
                    break
                raw_data.append(extra_line.strip())
            
            # Extract numerical values
            raw_values = extract_numbers(" ".join(raw_data))
            
            # Create navigation data entries, skipping 'dontknow' fields
            for k, v in zip(fields, raw_values):
                if k not in ['dontknow', 'dontknow2']:
                    nav_data.append({
                        "GPS": prn, 
                        "Epoch Time": dt, 
                        "Parameter": k, 
                        "Value": float(v)
                    })
    return nav_data

def save_to_csv(data, output_file):
    """
    Save navigation data to a CSV file.
    
    Args:
        data (list): List of navigation data dictionaries
        output_file (str): Path to output CSV file
    """
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    print(f"Data saved to {output_file}")

# Main execution
nav_data = read_rinex_body(rinex_file)
save_to_csv(nav_data, output_csv)