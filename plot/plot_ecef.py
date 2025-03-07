import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

# Đọc dữ liệu từ file CSV
file_path = "../data/satellite_coordinates.csv"  # Đường dẫn file CSV của bạn
df = pd.read_csv(file_path)

# Khởi tạo các danh sách lưu tọa độ ECEF
x_coords = []
y_coords = []
z_coords = []
satellite_ids = []

# Lấy tọa độ ECEF của các vệ tinh
for index, row in df.iterrows():
    x, y, z = row['x'], row['y'], row['z']
    x_coords.append(x)
    y_coords.append(y)
    z_coords.append(z)
    satellite_ids.append(row['Satellite'])

# Tạo figure cho biểu đồ 3D
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')

# Vẽ các vệ tinh trong không gian ECEF
sc = ax.scatter(x_coords, y_coords, z_coords, c=z_coords, cmap='viridis', s=50, alpha=0.7)

# Phân loại vệ tinh QZSS (theo tên hoặc mã)
for i, sat_id in enumerate(satellite_ids):
    if "QZSS" in sat_id:
        ax.text(x_coords[i], y_coords[i], z_coords[i], sat_id, fontsize=8, color='red')

# Thiết lập tiêu đề và nhãn cho các trục
ax.set_xlabel("X (meters)")
ax.set_ylabel("Y (meters)")
ax.set_zlabel("Z (meters)")
ax.set_title("ECEF Coordinates - Satellite Positions")

# Thêm thanh màu sắc
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label("Z (meters)")

# Hiển thị biểu đồ
plt.show()

# Lưu ảnh vào thư mục
output_dir = "ecef_sat_plots"
os.makedirs(output_dir, exist_ok=True)
output_image = os.path.join(output_dir, "ecef_satellite_plot.png")
fig.savefig(output_image, dpi=300)  # Lưu ảnh với độ phân giải cao
plt.close(fig)  # Đóng figure để tiết kiệm bộ nhớ

print(f"Đã lưu ảnh ECEF satellite plot: {output_image}")
