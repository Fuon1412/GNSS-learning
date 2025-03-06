import pandas as pd
import xarray as xr
import numpy as np
from datetime import datetime, timedelta

def process_rinex_csv(csv_file):
    """
    Process RINEX CSV file and convert to XArray Dataset.
    
    Args:
        csv_file (str): Path to the input CSV file
    
    Returns:
        xr.Dataset: Processed navigation data as an XArray Dataset
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Convert 'Epoch Time' to datetime format
    df['Epoch Time'] = pd.to_datetime(df['Epoch Time'])
    
    # Convert 'Value' column to numeric, handling the case where 'F' is present
    df['Value'] = pd.to_numeric(df['Value'].apply(lambda x: str(x).replace('F', '')), errors='coerce')
    
    # Group the data by GPS and Epoch Time
    grouped = df.groupby(['GPS', 'Epoch Time'])
    
    # Prepare list to store navigation data
    nav_data = []
    
    # Process each group (each satellite at a specific epoch)
    for (gps, epoch), group in grouped:
        # Create a dictionary for this satellite at this epoch
        sv_data = {'GPS': gps, 'time': np.datetime64(epoch)}
        
        # Convert group to dictionary of parameter-value pairs
        for _, row in group.iterrows():
            sv_data[row['Parameter']] = row['Value']
        
        nav_data.append(sv_data)
    
    # Convert to DataFrame
    df_nav = pd.DataFrame(nav_data)
    
    # Set time as index and convert to XArray Dataset
    ds = xr.Dataset.from_dataframe(df_nav.set_index('time'))
    
    return ds

def save_processed_data_to_txt(ds, output_file):
    """
    Save processed XArray dataset to a txt file.
    
    Args:
        ds (xr.Dataset): The processed dataset.
        output_file (str): The path to the output txt file.
    """
    # Convert the XArray dataset to a pandas DataFrame
    df = ds.to_dataframe().reset_index()

    # Save the DataFrame to a txt file (or CSV)
    df.to_csv(output_file, sep='\t', index=False)
    print(f"Data saved to {output_file}")
    

def keplerian4coor(sv: xr.DataArray) -> tuple:
    """
    Convert Keplerian orbital elements to ECEF coordinates.
    
    Args:
        sv (xr.DataArray): Satellite navigation data
    
    Returns:
        tuple: Satellite coordinates in ECEF
    """
    sv = sv.dropna(dim='time', how='all')
    
    # Add a name to the DataArray before converting to DataFrame
    sv.name = 'satellite_data'
    
    # Convert the DataArray to DataFrame
    sv_df = sv.to_dataframe().reset_index()
    
    # Earth gravitational constant
    GM = 3.986005e14  # [m^3 s^-2]
    
    # Earth rotation rate
    omega_e = 7.292115e-5  # [rad s^-1]
    
    # Get GPS Week
    gps_week = sv_df[sv_df['variable'] == 'GPSWeek']['satellite_data'].values[0]
    
    # Get reference epoch Toe
    toe_value = sv_df[sv_df['variable'] == 'Toe']['satellite_data'].values[0]
    
    # Calculate tk (time from ephemerides reference epoch)
    t = datetime(1980, 1, 6) + timedelta(weeks=int(gps_week))
    toe_time = datetime(1980, 1, 6) + timedelta(weeks=int(gps_week), seconds=toe_value)
    tk_seconds = (t - toe_time).total_seconds()
    
    # Apply the correction as per the formula in the image
    if tk_seconds > 302400:
        tk_seconds -= 604800
    elif tk_seconds < -302400:
        tk_seconds += 604800
    
    # Get required parameters
    sqrtA = sv_df[sv_df['variable'] == 'sqrtA']['satellite_data'].values[0]
    e = sv_df[sv_df['variable'] == 'Eccentricity']['satellite_data'].values[0]
    M0 = sv_df[sv_df['variable'] == 'M0']['satellite_data'].values[0]
    delta_n = sv_df[sv_df['variable'] == 'DeltaN']['satellite_data'].values[0]
    
    # Compute mean anomaly for tk
    n0 = np.sqrt(GM) / (sqrtA**3)
    n = n0 + delta_n
    Mk = M0 + n * tk_seconds
    
    # Solve Kepler's equation to get the eccentric anomaly (Ek)
    def solve_kepler(M, e, max_iter=100, tolerance=1e-8):
        Ek = M  # Initial guess
        for i in range(max_iter):
            delta_E = Ek - e * np.sin(Ek) - M
            Ek_new = Ek - delta_E / (1 - e * np.cos(Ek))  # Newton's method
            if abs(Ek_new - Ek) < tolerance:
                return Ek_new
            Ek = Ek_new
        return Ek
    
    # Solve for eccentric anomaly (Ek)
    Ek = solve_kepler(Mk, e)
    
    # Compute true anomaly (vk)
    vk = np.arctan2(np.sqrt(1 - e**2) * np.sin(Ek), np.cos(Ek) - e)
    
    # Get correction terms
    omega = sv_df[sv_df['variable'] == 'omega']['satellite_data'].values[0]
    Cus = sv_df[sv_df['variable'] == 'Cus']['satellite_data'].values[0]
    Cuc = sv_df[sv_df['variable'] == 'Cuc']['satellite_data'].values[0]
    
    # Compute argument of latitude (uk)
    uk = omega + vk + Cuc * np.cos(2*(omega + vk)) + Cus * np.sin(2*(omega + vk))
    
    # Get radial correction terms
    Crc = sv_df[sv_df['variable'] == 'Crc']['satellite_data'].values[0]
    Crs = sv_df[sv_df['variable'] == 'Crs']['satellite_data'].values[0]
    
    # Compute radial distance (rk)
    A = sqrtA**2
    rk = A * (1 - e * np.cos(Ek)) + Crc * np.cos(2*(omega + vk)) + Crs * np.sin(2*(omega + vk))
    
    # Get inclination parameters
    Io = sv_df[sv_df['variable'] == 'Io']['satellite_data'].values[0]
    IDOT = sv_df[sv_df['variable'] == 'IDOT']['satellite_data'].values[0]
    Cic = sv_df[sv_df['variable'] == 'Cic']['satellite_data'].values[0]
    Cis = sv_df[sv_df['variable'] == 'Cis']['satellite_data'].values[0]
    
    # Compute inclination (ik)
    ik = Io + IDOT * tk_seconds + Cic * np.cos(2*(omega + vk)) + Cis * np.sin(2*(omega + vk))
    
    # Get longitude parameters
    Omega0 = sv_df[sv_df['variable'] == 'Omega0']['satellite_data'].values[0]
    OmegaDot = sv_df[sv_df['variable'] == 'OmegaDot']['satellite_data'].values[0]
    
    # Compute longitude of ascending node (Lambda_k)
    Lambda_k = Omega0 + (OmegaDot - omega_e) * tk_seconds - omega_e * toe_value
    
    # Rotation matrices
    def calc_R3(angle):
        return np.array([[np.cos(angle), -np.sin(angle), 0],
                         [np.sin(angle), np.cos(angle), 0],
                         [0, 0, 1]])
        
    def calc_R1(angle):
        return np.array([[1, 0, 0],
                         [0, np.cos(angle), -np.sin(angle)],
                         [0, -np.sin(angle), np.cos(angle)]])
    
    # Calculate satellite position in orbital plane
    r_orb_plane = np.array([rk, 0, 0])
    
    # Apply rotations to get ECEF coordinates
    r_lambda_k = calc_R3(-Lambda_k)
    r_i_k = calc_R1(-ik)
    r_u_k = calc_R3(-uk)
    
    r_orb = np.dot(r_lambda_k, np.dot(r_i_k, np.dot(r_u_k, r_orb_plane)))
    
    x = r_orb[0]
    y = r_orb[1]
    z = r_orb[2]
    
    return x, y, z

# Save the coordinates to a CSV file
def save_coordinates_to_csv(gps_id, epoch, coords, output_file):
    """
    Save satellite coordinates, time, and GPS ID to a CSV file.
    
    Args:
        gps_id (str): The GPS satellite ID.
        epoch (datetime): The epoch time of the data point.
        coords (tuple): The satellite coordinates (x, y, z).
        output_file (str): The path to the output CSV file.
    """
    # Prepare the data as a DataFrame
    df_coords = pd.DataFrame([{
        'GPS': gps_id,
        'Epoch Time': epoch,
        'x': coords[0],
        'y': coords[1],
        'z': coords[2]
    }])
    
    # Save to CSV, append mode
    df_coords.to_csv(output_file, mode='a', header=not pd.io.common.file_exists(output_file), index=False)

# Main execution
csv_file = r"rinex_output.csv"
ds = process_rinex_csv(csv_file)
output_file = "processed_data.txt"
save_processed_data_to_txt(ds, output_file)

# CSV file to save coordinates
coordinates_output_file = "satellite_coordinates.csv"  # File to save coordinates

# Process each satellite data and calculate its position
for gps_id, group in ds.groupby('GPS'):
    for epoch, sv_data in group.groupby('time'):
        # Extract satellite data for this time and GPS
        sv = sv_data.to_array()
        
        # Calculate the position in ECEF coordinates
        x, y, z = keplerian4coor(sv)
        
        # Save the coordinates along with time and GPS ID to CSV
        save_coordinates_to_csv(gps_id, epoch, (x, y, z), coordinates_output_file)