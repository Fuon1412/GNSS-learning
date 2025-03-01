import re  # regular expression
import matplotlib.pyplot as plt # type: ignore # matplot for plot data
import os
from datetime import datetime  # date time to convert epoch-time
from collections import defaultdict # use for store data

rinex_file = r"../data/roap1810.09o"  # Use uploaded file path

output_dir = "epoch_plots"
os.makedirs(output_dir, exist_ok=True)

header_data = {}  # dictionary to store header data
types_of_obs = [] # list of observation types
obs_data = defaultdict(list)  # This will store data with the epoch time as the key and a list of tuples as values

def convert_epoch_time(epoch_time):
    parts = epoch_time.split()
    # Split time from string
    year, month, day, hour, minute = map(int, parts[:5])
    second = float(parts[5]) # Because seconds value are float so we need to convert it separately
    # Convert days, months, years, hours, minutes, seconds to new format
    formatted_time = datetime(year + 2000, month, day, hour, minute, int(second)).strftime("%H:%M:%S %d/%m/%Y")
    # Convert again for datetime type
    converted_epoch_time = datetime.strptime(formatted_time, "%H:%M:%S %d/%m/%Y")
    return converted_epoch_time 

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
# In this step, we part the data because the observable data is divided by 16 characters per value
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

# Read RINEX data
def read_rinex_data(rinex_file):
    global obs_data
    with open(rinex_file, 'r', encoding="utf-8") as f:
        # Skip header
        for line in f:
            if "END OF HEADER" in line:
                break
        
        epoch_time = None  # Initialize epoch time
        
        for line in f:
            # Detect epoch start
            if re.match(r"^\s*\d{1,4}\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\.\d+\s+\d+", line):
                epoch_time = line.strip()  # Store epoch time
                formatted_epoch_time = convert_epoch_time(epoch_time)  # Convert to datetime
                continue  # Go to next line (satellite data)
            
            # Process satellite observation data
            obs_values = parse_observation_line(line, len(types_of_obs))  # Parse correctly
            
            if idx_c1 >= len(obs_values) or idx_l1 >= len(obs_values):
                continue  # Skip if indices are out of range
            
            try:
                c1_value = obs_values[idx_c1]  # Pseudo-range value (C1)
                l1_value = obs_values[idx_l1]  # Carrier-phase value (L1)
                obs_data[formatted_epoch_time].append((l1_value, c1_value))
            except (IndexError, ValueError):
                continue  # Skip invalid lines

    return obs_data

# Get header and observation types data
header_data, types_of_obs = read_rinex_header(rinex_file)

# Get the indices of C1 and L1 from observation types
try:
    idx_c1 = types_of_obs.index("C1")
    idx_l1 = types_of_obs.index("L1")
except ValueError:
    print("Cannot find L1 or C1 index in TYPES OF OBSERV")
    exit()

# Read observation data
obs_data = read_rinex_data(rinex_file)

# Display the results for checking
print(header_data)
print(types_of_obs)
print(list(obs_data.items())[:5])

# Prepare data for plotting
epoch_times = []
pseudo_ranges = []
carrier_phases = []

# Collect data while skipping None values
for epoch, values in obs_data.items():
    for l1, c1 in values:
        if c1 is not None and l1 is not None:  # Skip if either value is None
            epoch_times.append(epoch)
            pseudo_ranges.append(c1)
            carrier_phases.append(l1)

# Plot all data on a single chart
plt.figure(figsize=(12, 6))

plt.plot(epoch_times, pseudo_ranges, linestyle='-', color='b', label="Pseudo-range (C1)")
plt.plot(epoch_times, carrier_phases, linestyle='-', color='r', label="Carrier-phase (L1)")

plt.xlabel("Epoch Time")
plt.ylabel("Observation Value")
plt.title("Observation Data Over Time")
plt.xticks(rotation=45)  # Rotate X-axis labels for better readability
plt.legend()
plt.grid(True)

# Save the plot
file_name = f"{output_dir}/all_epochs_plot.png"
plt.savefig(file_name)

print(f"Plot saved as {file_name}")
