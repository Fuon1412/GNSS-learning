import re
import json
from datetime import datetime
from collections import defaultdict

rinex_file = r"../data/GPS_obs_3_02.rnx"
json_output = r"../data/output.json"

def _obstime(fol):
    return datetime(year=int(fol[0]), month=int(fol[1]), day=int(fol[2]),
                    hour=int(fol[3]), minute=int(fol[4]),
                    second=int(float(fol[5])),
                    microsecond=int(float(fol[5]) % 1 * 1000000))

def scan_header(file):
    with open(file, 'r') as f:
        header = defaultdict(list)
        for line in f:
            if "RINEX VERSION / TYPE" in line:
                header['version'] = float(line.split()[0])
                header['filetype'] = re.split(r'\s{2,}', line.strip())[1]
                header['satellite'] = re.split(r'\s{2,}', line.strip())[2]
            elif "SYS / # / OBS TYPES" in line:
                header['sys'] = line[0]  
                header['num_obs'] = int(line[3:6])  
                obs_types = []
                for i in range(header['num_obs']):
                    start_pos = 7 + i * 4  
                    if start_pos + 3 <= len(line):
                        obs_type = line[start_pos:start_pos+3].strip()
                        if obs_type:
                            obs_types.append(obs_type)
                header['type_of_obs'] = obs_types
            elif "END OF HEADER " in line:
                break
    return header 

header = scan_header(rinex_file)
try:
    idx_c1 = header['type_of_obs'].index("C1C") #pseudorange
    idx_l1 = header['type_of_obs'].index("L1C") #carrier phase
except ValueError:
    print("Cannot find L1C or C1C index in TYPES OF OBSERV")
    exit()

def scan_body(file, output_json):
    data = []
    
    with open(file, 'r') as f:
        for line in f:
            if "END OF HEADER " in line:
                break
        
        for line in f:
            if ">" in line:
                epoch = _obstime([line[2:6], line[7:9], line[10:12], line[13:15], line[16:18], line[19:29]])
                num_of_sats_in_epoch = int(line[33:35]) 
                for _ in range(num_of_sats_in_epoch):
                    line = f.readline()
                    prn = line[0:3].strip()
                    if prn != "G05":
                        continue
                    
                    try:
                        C1C = float(line[4 + idx_c1 * 16: 4 + idx_c1 * 16 + 14].strip())
                    except ValueError:
                        C1C = None
                    
                    try:
                        L1C = float(line[4 + idx_l1 * 16: 4 + idx_l1 * 16 + 14].strip())
                    except ValueError:
                        L1C = None
                    
                    data.append({
                        "Satellite": prn,
                        "Epoch Time": epoch.strftime('%Y-%m-%d %H:%M:%S.%f'),
                        "C1C": C1C,
                        "L1C": L1C
                    })
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"Data saved to {output_json}")

scan_body(rinex_file, json_output)
