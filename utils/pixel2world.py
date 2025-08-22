import numpy as np
import cv2


def read_homography_matrix(txt_path):
    """从 txt 文件读取 3x3 外参矩阵 H"""
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        H = []
        for line in lines:
            row = list(map(float, line.strip().split()))
            H.append(row)
        H = np.array(H)
    assert H.shape == (3, 3), "Homography matrix must be 3x3"
    return H


def read_camera_matrix(txt_path):
    """读取3x3相机内参矩阵 cameraMatrix"""
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        K = []
        for line in lines:
            row = list(map(float, line.strip().split()))
            K.append(row)
        K = np.array(K)
    assert K.shape == (3, 3), "Camera intrinsic matrix must be 3x3"
    return K

def read_dist_coeffs(txt_path):
    """读取畸变参数"""
    with open(txt_path, 'r') as f:
        line = f.readline()
        coeffs = list(map(float, line.strip().replace(',', ' ').split()))
    assert len(coeffs) == 5, "Distortion coefficients must be 5 values"
    return np.array(coeffs)


def pixel_to_world_coords(u, v, H_txt_path, K_txt_path, D_txt_path):
    """
    从像素坐标(u,v) → 世界坐标(X,Y)，包含矫正与单应变换
    """
    # 加载矩阵
    H = read_homography_matrix(H_txt_path)
    K = read_camera_matrix(K_txt_path)
    D = read_dist_coeffs(D_txt_path)

    # 畸变矫正
    src = np.array([[[u, v]]], dtype=np.float32)
    undistorted = cv2.undistortPoints(src, K, D, P=K)
    u_corr, v_corr = undistorted[0][0]

    # 单应变换
    pixel = np.array([u_corr, v_corr, 1.0])
    world = H @ pixel
    world /= world[2]
    return round(world[0], 2), round(world[1], 2)



# 示例使用
if __name__ == "__main__":
    u, v = 1296, 972  # 2592与1944的一半 图像中心
    x_mm, y_mm = pixel_to_world_coords(u, v, 'config/waican.txt', 'config/neican.txt', 'config/jibian.txt')
    print(f"机械臂抓取位置 (mm): X = {x_mm:.2f}, Y = {y_mm:.2f}")
