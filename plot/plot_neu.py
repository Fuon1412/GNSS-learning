import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Hàm chuyển từ Lat, Lon, Alt sang ECEF
def geodetic_to_ecef(lat, lon, alt):
    a = 6378137.0  # Bán kính Trái Đất (m)
    e2 = 6.69437999014e-3  # Độ dẹt bình phương
    lat, lon = np.radians(lat), np.radians(lon)

    N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2)
    X = (N + alt) * np.cos(lat) * np.cos(lon)
    Y = (N + alt) * np.cos(lat) * np.sin(lon)
    Z = ((1 - e2) * N + alt) * np.sin(lat)
    return X, Y, Z

# Hàm chuyển từ ECEF sang ENU
def ecef_to_enu(x, y, z, x_ref, y_ref, z_ref, lat_ref, lon_ref):
    lat_ref, lon_ref = np.radians(lat_ref), np.radians(lon_ref)
    
    dx, dy, dz = x - x_ref, y - y_ref, z - z_ref
    enu_matrix = np.array([
        [-np.sin(lon_ref), np.cos(lon_ref), 0],
        [-np.sin(lat_ref)*np.cos(lon_ref), -np.sin(lat_ref)*np.sin(lon_ref), np.cos(lat_ref)],
        [np.cos(lat_ref)*np.cos(lon_ref), np.cos(lat_ref)*np.sin(lon_ref), np.sin(lat_ref)]
    ])
    
    enu_coords = np.dot(enu_matrix, np.array([dx, dy, dz]))
    return enu_coords[0], enu_coords[1], enu_coords[2]

# Đọc dữ liệu từ file CSV
file_path = "../data/satellite_coordinates_v4.csv"  # Thay bằng đường dẫn thực tế
df = pd.read_csv(file_path)

# Chọn điểm tham chiếu (VD: Hà Nội, Việt Nam)
lat_ref, lon_ref, alt_ref = 21.0285, 105.8542, 10  # Hà Nội (21.0285°N, 105.8542°E, 10m)

# Chuyển đổi điểm tham chiếu sang ECEF
x_ref, y_ref, z_ref = geodetic_to_ecef(lat_ref, lon_ref, alt_ref)

# Chuyển tất cả tọa độ vệ tinh từ ECEF → ENU
df["E"], df["N"], df["U"] = zip(*df.apply(lambda row: ecef_to_enu(row["x"], row["y"], row["z"], x_ref, y_ref, z_ref, lat_ref, lon_ref), axis=1))

# Tạo thư mục lưu ảnh
output_dir = "sat_plots"
os.makedirs(output_dir, exist_ok=True)

# Vẽ tất cả quỹ đạo vệ tinh trong hệ tọa độ ENU
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

for satellite, group in df.groupby("Satellite"):
    ax.plot(group["E"], group["N"], group["U"], marker="o", linestyle="-", label=satellite)

# Đặt tên trục
ax.set_xlabel("East (m)")
ax.set_ylabel("North (m)")
ax.set_zlabel("Up (m)")
ax.set_title("Satellite Orbits in ENU Coordinate System")

# Hiển thị chú thích
ax.legend()

# Lưu ảnh vào thư mục
output_image = os.path.join(output_dir, "all_satellites_enu.png")
plt.savefig(output_image, dpi=300)  # Lưu ảnh với độ phân giải cao
plt.close(fig)

print(f"Đã lưu ảnh quỹ đạo trong hệ ENU: {output_image}")
