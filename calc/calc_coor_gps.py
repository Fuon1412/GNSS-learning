import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def process_observation_json(json_file):
    """
    Process observation JSON file and convert to DataFrame.
    """
    df_obs = pd.read_json(json_file)
    df_obs['Epoch Time'] = pd.to_datetime(df_obs['Epoch Time'])
    return df_obs

def process_navigation_json(json_file):
    """
    Process navigation JSON file and convert to dictionary of satellite data.
    
    Args:
        json_file (str): Path to the input JSON file
    
    Returns:
        dict: Dictionary with satellite IDs as keys, containing navigation parameters
    """
    # Read the JSON file
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    # Convert the JSON list to a DataFrame
    df = pd.DataFrame(data)
    
    # Convert 'Epoch Time' to datetime format
    df['Epoch Time'] = pd.to_datetime(df['Epoch Time'])
    
    # Group the data by satellite
    grouped_by_satellite = df.groupby('Satellite')
    
    # Dictionary to store navigation data for each satellite
    nav_data_dict = {}
    
    # Process each satellite group
    for satellite, group in grouped_by_satellite:
        # Create a dictionary for each satellite's parameters
        satellite_data = {
            'nav_epoch': group['Epoch Time'].iloc[0],
            'GPSWeek': group['GPSWeek'].iloc[0],
            'Toe': group['Toe'].iloc[0],
            'SVclockBias': group['SVclockBias'].iloc[0],
            'SVclockDrift': group['SVclockDrift'].iloc[0],
            'SVclockDriftRate': group['SVclockDriftRate'].iloc[0],
            'IODE': group['IODE'].iloc[0],
            'Crs': group['Crs'].iloc[0],
            'DeltaN': group['DeltaN'].iloc[0],
            'M0': group['M0'].iloc[0],
            'Cuc': group['Cuc'].iloc[0],
            'Eccentricity': group['Eccentricity'].iloc[0],
            'Cus': group['Cus'].iloc[0],
            'sqrtA': group['sqrtA'].iloc[0],
            'Toe': group['Toe'].iloc[0],
            'Cic': group['Cic'].iloc[0],
            'Omega0': group['Omega0'].iloc[0],
            'Cis': group['Cis'].iloc[0],
            'Io': group['Io'].iloc[0],
            'Crc': group['Crc'].iloc[0],
            'omega': group['omega'].iloc[0],
            'OmegaDot': group['OmegaDot'].iloc[0],
            'IDOT': group['IDOT'].iloc[0],
            'CodesL2': group['CodesL2'].iloc[0],
            'L2Pflag': group['L2Pflag'].iloc[0],
            'SVacc': group['SVacc'].iloc[0],
            'health': group['health'].iloc[0],
            'TGD': group['TGD'].iloc[0],
            'IODC': group['IODC'].iloc[0],
            'TransTime': group['TransTime'].iloc[0],
            'FitIntvl': group['FitIntvl'].iloc[0],
        }
        
        # Add this satellite's data to the dictionary
        nav_data_dict[satellite] = satellite_data
    
    return nav_data_dict

def keplerian4coor(sat_nav_params, sat_obs_df, system='GPS'):
    """
    Convert Keplerian orbital elements to ECEF coordinates for multiple observation times.
    
    Args:
        sat_nav_params (dict): Navigation parameters for a satellite
        sat_obs_df (pd.DataFrame): Observation data for the satellite
        system (str): Navigation system ('GPS')
    
    Returns:
        list: List of tuples containing (epoch_time, x, y, z) for each valid observation time
    """
    # Earth gravitational constant - same for GPS and QZSS
    GM = 3.986004418e14  # [m^3 s^-2]
    
    # Earth rotation rate - same for GPS and QZSS
    omega_e = 7.292115e-5  # [rad s^-1]
    
    # Speed of light in m/s
    C = 299792458
    
    # Get reference time information
    nav_epoch = sat_nav_params['nav_epoch']
    gps_week = sat_nav_params['GPSWeek']
    toe_value = sat_nav_params['Toe']
    
    # Calculate reference time
    reference_epoch = datetime(1980, 1, 6)  # GNSS epoch start (6/1/1980)
    toe_time = reference_epoch + timedelta(weeks=int(gps_week), seconds=toe_value)
    
    # Filter observation data within 2 hours after navigation data
    filtered_obs = sat_obs_df[(sat_obs_df['Epoch Time'] > nav_epoch) & 
                          (sat_obs_df['Epoch Time'] <= nav_epoch + timedelta(hours=2))]

    if filtered_obs.empty:
        return []  # No matching observation data
    
    # Get required navigation parameters
    sqrtA = sat_nav_params['sqrtA']
    e = sat_nav_params['Eccentricity']
    M0 = sat_nav_params['M0']
    delta_n = sat_nav_params['DeltaN']
    omega = sat_nav_params['omega']
    Cus = sat_nav_params['Cus']
    Cuc = sat_nav_params['Cuc']
    Crc = sat_nav_params['Crc']
    Crs = sat_nav_params['Crs']
    Io = sat_nav_params['Io']
    IDOT = sat_nav_params['IDOT']
    Cic = sat_nav_params['Cic']
    Cis = sat_nav_params['Cis']
    Omega0 = sat_nav_params['Omega0']
    OmegaDot = sat_nav_params['OmegaDot']
    
    # Helper functions
    def solve_kepler(M, e, max_iter=10, tolerance=1e-15):
        Ek = M  # Initial guess
        for i in range(max_iter):
            delta_E = (Ek - e * np.sin(Ek) - M)
            Ek_new = Ek - delta_E / (1 - e * np.cos(Ek))  # Newton's method
            if abs(Ek_new - Ek) < tolerance:
                return Ek_new
            Ek = Ek_new
        return Ek
    
    # List to store results
    results = []
    
    # Process each observation epoch
    for _, obs_row in filtered_obs.iterrows():
        obs_epoch = obs_row['Epoch Time']
        C1C = obs_row.get('C1C', 0)  # Use 0 as default if C1C is not available

        # Calculate t (time difference between obs_epoch and reference epoch)
        t = (obs_epoch - reference_epoch).total_seconds()
        
        # Calculate toe (time difference between toe_time and reference epoch)
        toe = (toe_time - reference_epoch).total_seconds()
        
        # Now calculate the time difference in seconds for tk
        tk_seconds = t - toe
        
        # Apply the pseudorange correction if C1C is available
        if C1C > 0:
            tk_seconds -= (C1C / C)
        
        # Apply the correction as per the formula
        if tk_seconds > 302400:
            tk_seconds -= 604800
        elif tk_seconds < -302400:
            tk_seconds += 604800
        
        # Calculate mean motion
        n0 = np.sqrt(GM) / (sqrtA**3)
        n = n0 + delta_n
        
        # Calculate mean anomaly for tk
        Mk = M0 + n * tk_seconds
        
        # Solve for eccentric anomaly (Ek)
        Ek = solve_kepler(Mk, e)
        
        # Calculate true anomaly (vk)
        vk = np.arctan2(np.sqrt(1 - e**2) * np.sin(Ek), np.cos(Ek) - e)
        
        # Calculate argument of latitude (uk)
        uk = omega + vk
        
        # Apply perturbation corrections
        delta_uk = Cuc * np.cos(2*uk) + Cus * np.sin(2*uk)
        delta_rk = Crc * np.cos(2*uk) + Crs * np.sin(2*uk)
        delta_ik = Cic * np.cos(2*uk) + Cis * np.sin(2*uk)
        
        # Corrected argument of latitude
        uk = uk + delta_uk
        
        # Calculate radial distance (rk)
        A = sqrtA**2
        rk = A * (1 - e * np.cos(Ek)) + delta_rk
        
        # Calculate inclination (ik)
        ik = Io + IDOT * tk_seconds + delta_ik
        
        # Calculate longitude of ascending node (Lambda_k)
        Lambda_k = Omega0 + (OmegaDot - omega_e) * tk_seconds - omega_e * toe_value
        
        # Calculate satellite position in orbital plane
        xk_prime = rk * np.cos(uk)
        yk_prime = rk * np.sin(uk)
        
        # Calculate ECEF coordinates
        X = xk_prime * np.cos(Lambda_k) - yk_prime * np.cos(ik) * np.sin(Lambda_k)
        Y = xk_prime * np.sin(Lambda_k) + yk_prime * np.cos(ik) * np.cos(Lambda_k)
        Z = yk_prime * np.sin(ik)
        
        distance = np.sqrt(X**2 + Y**2 + Z**2)
        
        # Store results
        results.append({
            "Epoch Time": str(obs_epoch),  # Chuyển thành chuỗi để lưu JSON
            "X": X,
            "Y": Y,
            "Z": Z,
            "Distance": distance
        })
    return results

# Main Execution
def main():
    # Process observation and navigation data
    obs_file = 'G05_obs.json'
    nav_file = 'gps_output_2.json'
    
    print(f"Processing observation file: {obs_file}")
    obs_df = process_observation_json(obs_file)
    
    print(f"Processing navigation file: {nav_file}")
    nav_params_dict = process_navigation_json(nav_file)
    
    # Get unique satellite IDs from observation data
    obs_satellites = obs_df['Satellite'].unique()
    print(f"Observation satellites: {obs_satellites}")
    
    # Get satellite IDs from navigation data
    nav_satellites = list(nav_params_dict.keys())
    print(f"Navigation satellites: {nav_satellites}")
    
    # Find common satellites between observation and navigation data
    common_satellites = set(obs_satellites).intersection(set(nav_satellites))
    print(f"Common satellites: {common_satellites}")
    
    # Initialize result storage
    result_dict = {}
    
    # Process only satellites that exist in both datasets
    for satellite_id in common_satellites:
        print(f"Processing satellite: {satellite_id}")
        sat_nav_params = nav_params_dict[satellite_id]
        sat_obs_df = obs_df[obs_df['Satellite'] == satellite_id]
        
        # Call the Keplerian coordinate computation function for the satellite
        results = keplerian4coor(sat_nav_params, sat_obs_df)
        
        if results:  # Only add if there are results
            result_dict[satellite_id] = results
            print(f"  Found {len(results)} valid positions")
        else:
            print(f"  No valid positions found")
    
    # Output results to a JSON file
    output_file = 'satellite_positions.json'
    with open(output_file, 'w') as outfile:
        json.dump(result_dict, outfile, indent=4)
        print(f"Results written to {output_file}")
    
    print(f"Processed {len(common_satellites)} satellites, {len(result_dict)} with valid results")

# Run the main function
if __name__ == "__main__":
    main()