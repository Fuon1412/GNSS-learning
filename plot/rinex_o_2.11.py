import re
import os
import csv
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import List
import numpy as np

# Input and output file paths
rinex_file = r"../data/roap1810.09o"

def scan_header(file):
    """
    Scan RINEX header and extract relevant information.
    
    Args:
        file (str): Path to the RINEX file
    
    Returns:
        dict: Dictionary containing relevant header information
    """
    header = defaultdict(str)
    types_of_obs = []
    with open(file, 'r') as f:
        for line in f:
            if "END OF HEADER" in line:
                break
            elif "RINEX VERSION / TYPE" in line:
                header['version'] = float(line.split()[0])
                header['filetype'] = re.split(r'\s{2,}', line.strip())[1]
                header['satellite'] = re.split(r'\s{2,}', line.strip())[2]
            elif "# / TYPES OF OBSERV" in line:
                parts = line.split("# / TYPES OF OBSERV")[0].split()
                header["num_obs"] = int(parts[0])  # Number of observation types
                types_of_obs = parts[1:]  # List of observation types
            elif "APPROX POSITION XYZ" in line:
                header['position'] = [float(line[:14]), float(line[14:28]), float(line[28:42])]
            elif "TIME OF FIRST OBS" in line:
                header['first_obs'] = [int(line[:6]), int(line[6:12]), int(line[12:18]), int(line[18:24]), int(line[24:30]), float(line[30:43])]
            elif "TIME OF LAST OBS" in line:
                header['last_obs'] = [int(line[:6]), int(line[6:12]), int(line[12:18]), int(line[18:24]), int(line[24:30]), float(line[30:43])]
            elif "INTERVAL" in line:
                header['interval'] = float(line[:10])
    return header, types_of_obs

header, types_of_obs = scan_header(rinex_file)
# Get the indices of C1 and L1 from observation types
try:
    idx_c1 = types_of_obs.index("C1")
    idx_l1 = types_of_obs.index("L1")
except ValueError:
    print("Cannot find L1 or C1 index in TYPES OF OBSERV")
    exit()

def _obstime(fol: List[str]) -> datetime:
    """
    Python >= 3.7 supports nanoseconds.  https://www.python.org/dev/peps/pep-0564/
    Python < 3.7 supports microseconds.
    """
    year = int(fol[0])
    if 80 <= year <= 99:
        year += 1900
    elif year < 80:  # because we might pass in four-digit year
        year += 2000

    return datetime(year=year, month=int(fol[1]), day=int(fol[2]),
                    hour=int(fol[3]), minute=int(fol[4]),
                    second=int(float(fol[5])),
                    microsecond=int(float(fol[5]) % 1 * 1000000)
                    )
    
def extract_satellite_list(sat_list):
    """
    Extract satellite list from the Epoch line.
    
    Args:
        sat_list (str): String containing satellite data
    
    Returns:
        list: List of satellites in the format "G+number"
    """
    sat_list_cleaned = re.sub(r'\s+', '', sat_list)
    satellites = re.findall(r'G\d+', sat_list_cleaned)
    return satellites

def parse_observation_line(line, num_obs):
    obs_values = []
    for i in range(num_obs):
        raw_value = line[i * 16 : i * 16 + 14].strip()  # Take only the first 14 character data
        if raw_value:  # If the data column is not blank
            try:
                # Try converting the raw value to float, skip non-numeric values
                obs_values.append(float(raw_value))
            except ValueError:
                # If it's not numeric (like satellite ID), append None
                obs_values.append(None)
        else:
            obs_values.append(None)
    return obs_values

def scan_obs_data(file):
    with open(file, 'r') as f:
        for line in f:
            if "END OF HEADER" in line:
                break
        
        for line in f:
            if re.match(r"^\s*\d{1,4}\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\.\d+\s+\d+", line):
                epoch = _obstime([line[1:3], line[4:6], line[7:9], line[10:12], line[13:15], line[16:26]])
                num_of_sat = int(line[29:32])
                satellites = extract_satellite_list(line[32:])
            for _ in range(num_of_sat):
                line = f.readline()
                if not line:
                    break
                 # Process satellite observation data
                obs_values = parse_observation_line(line, len(types_of_obs))  # Parse correctly
                prn = satellites[_]
                c1 = obs_values[idx_c1]
                l1 = obs_values[idx_l1]
                print(f"Epoch: {epoch}, PRN: {prn}, C1: {c1}, L1: {l1}")
                
    return None

scan_obs_data(rinex_file)
# Output:
