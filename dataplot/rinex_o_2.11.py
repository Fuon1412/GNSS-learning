# Description: Read RINEX observation file (version 2.11) and extract header data and observation data, focus on
# pseudo-range and carrier-phase observation types.

import re  # regular expression
import matplotlib.pyplot as plt 
rinex_file = r"C:\gLAB\win\GNSS_TUTBOOK_MASTER\FILES\TUT0\roap1810.09o"  # Use uploaded file path

header_data = {}  # dictionary to store header data
types_of_obs = []  # list of observation types
obs_data = []  # list of observation data

# Read the RINEX file
# Header data
def read_rinex_header(rinex_file):
    global types_of_obs
    with open(rinex_file, 'r', encoding="utf-8") as f:
        for line in f:
            if "RINEX VERSION / TYPE" in line:
                header_data["version"] = float(line.split()[0])
                header_data["filetype"] = re.split(r'\s{2,}', line.strip())[1]
                header_data["sat_sys"] = re.split(r'\s{2,}', line.strip())[2]
            if header_data["version"] != 2.11:
                print("Only RINEX version 2.11 is supported")
                break
            elif "# / TYPES OF OBSERV" in line:
                parts = line.split("# / TYPES OF OBSERV")[0].split()
                header_data["num_obs"] = int(parts[0])  # Number of observation types
                types_of_obs = parts[1:]  # List of observation types
            elif "END OF HEADER" in line:
                break
    return header_data, types_of_obs

# Observation data
def read_rinex_data(rinex_file):
    global obs_data
    with open(rinex_file, 'r', encoding="utf-8") as f:
        # Skip header
        for line in f:
            if "END OF HEADER" in line:
                break
        
        epoch_time = None  # Store current epoch timestamp

        for line in f:
            # Detect epoch start
            if re.match(r"^\s*\d{1,4}\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\.\d+\s+\d+", line):
                epoch_time = line.strip()  # Store epoch time
                continue  # Go to the next line (satellite data)
            
            # Process satellite observation data
            parts = line.split()
            if len(parts) < max(idx_c1, idx_l1) + 1:
                continue  # Skip lines that don't have enough data
            
            try:
                c1_value = parts[2*idx_c1]  # pseudo-range value(C1)
                l1_value = parts[2*idx_l1]  # carrier-phase value(L1)
                obs_data.append((epoch_time, c1_value, l1_value))
            except IndexError:
                continue  # Skip invalid lines

    return obs_data

# Execute functions
header_data, types_of_obs = read_rinex_header(rinex_file)

try:
    idx_c1 = types_of_obs.index("C1")
    idx_l1 = types_of_obs.index("L1")
except ValueError:
    print("Cannot find L1 or C1 index in TYPES OF OBSERV")
    exit()

obs_data = read_rinex_data(rinex_file)

# Display the results
print(header_data)
print(types_of_obs)
print(obs_data[:10])  # Print first 10 observations for checking
