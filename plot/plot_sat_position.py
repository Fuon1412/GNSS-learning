import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

# Đọc dữ liệu từ file CSV
file_path = "../data/satellite_coordinates.csv"  # Thay bằng đường dẫn file của bạn
df = pd.read_csv(file_path)

# Xử lý dữ liệu: chuyển đổi cột 'Epoch Time' thành datetime (nếu cần)
df["Epoch Time"] = pd.to_datetime(df["Epoch Time"], errors='coerce')

# Tạo thư mục lưu ảnh (nếu chưa có)
output_dir = "sat_plots"
os.makedirs(output_dir, exist_ok=True)

# Duyệt qua từng vệ tinh và vẽ biểu đồ riêng
for satellite, group in df.groupby("GPS"):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection='3d')

    # Vẽ quỹ đạo vệ tinh
    ax.plot(group["x"], group["y"], group["z"], marker="o", linestyle="-", label=satellite, color="b")

    # Đặt tên trục
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_title(f"Orbit of {satellite}")

    # Hiển thị chú thích
    ax.legend()

    # Lưu ảnh dưới dạng PNG vào thư mục sat_plots
    output_image = os.path.join(output_dir, f"{satellite}.png")
    plt.savefig(output_image, dpi=300)  # Lưu ảnh với độ phân giải cao
    plt.close(fig)  # Đóng figure để tránh tốn bộ nhớ

    print(f"Đã lưu ảnh cho {satellite}: {output_image}")

print("Tất cả các biểu đồ đã được lưu thành công vào thư mục 'sat_plots'.")
