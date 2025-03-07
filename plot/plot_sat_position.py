import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import os

# Hàm chuyển đổi từ ECEF (x, y, z) sang Azimuth và Elevation
def ecef_to_az_el(x, y, z):
    # Tọa độ của người quan sát (x = 0, y = 0, z = 0 tức là ở trung tâm Trái Đất)
    observer_x = 0
    observer_y = 0
    observer_z = 0

    # Tính toán sự khác biệt giữa tọa độ vệ tinh và người quan sát
    dx = x - observer_x
    dy = y - observer_y
    dz = z - observer_z

    # Tính toán khoảng cách từ vệ tinh đến người quan sát
    r = np.sqrt(dx**2 + dy**2 + dz**2)

    # Tính toán góc Elevation (góc với trục z)
    elevation = np.arcsin(dz / r)
    
    # Tính toán góc Azimuth (góc trong mặt phẳng xy)
    azimuth = np.arctan2(dy, dx)

    # Chuyển đổi sang độ
    elevation = np.degrees(elevation)
    azimuth = np.degrees(azimuth)

    return azimuth, elevation

# Đọc dữ liệu từ file CSV
file_path = "../data/satellite_coordinates_v4.csv"  # Đường dẫn file CSV của bạn
df = pd.read_csv(file_path)

# Khởi tạo danh sách lưu các tọa độ Azimuth và Elevation
azimuths = []
elevations = []
satellite_ids = []

# Chuyển đổi tất cả các tọa độ ECEF sang Azimuth, Elevation
for index, row in df.iterrows():
    x, y, z = row['x'], row['y'], row['z']
    azimuth, elevation = ecef_to_az_el(x, y, z)
    azimuths.append(azimuth)
    elevations.append(elevation)
    satellite_ids.append(row['Satellite'])

# Vẽ sky-satellite plot với yếu tố đặc trưng của QZSS
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_aspect('equal')

# Vẽ các vệ tinh theo góc Azimuth và Elevation
scatter = ax.scatter(azimuths, elevations, c=elevations, cmap=cm.viridis, s=20, alpha=0.7)

# Phân loại vệ tinh QZSS (theo tên hoặc mã)
for i, sat_id in enumerate(satellite_ids):
    if "QZSS" in sat_id:
        ax.text(azimuths[i], elevations[i], sat_id, fontsize=8, color='red', ha='center')

# Thiết lập giới hạn và tiêu đề
ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)
ax.set_xlabel("Azimuth (degrees)")
ax.set_ylabel("Elevation (degrees)")
ax.set_title("Sky-Satellite Plot - QZSS System")

# Thêm thanh màu sắc
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label("Elevation (degrees)")

# Lưu ảnh vào thư mục
output_dir = "sky_sat_plots"
os.makedirs(output_dir, exist_ok=True)
output_image = os.path.join(output_dir, "sky_satellite_qzss_plot.png")
plt.savefig(output_image, dpi=300)  # Lưu ảnh với độ phân giải cao
plt.close(fig)  # Đóng figure để tiết kiệm bộ nhớ

print(f"Đã lưu ảnh sky-satellite plot với QZSS: {output_image}")
