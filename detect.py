import cv2
import numpy as np
from utils.pixel2world import pixel_to_world_coords



def calculate_distance(p1, p2):
    return np.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))


def calculate_angle(pt1, pt2):
    # 确保 pt1 在左，pt2 在右
    if pt1[0] > pt2[0]:  # 强制从左向右
        pt1, pt2 = pt2, pt1
    
    dx = pt2[0] - pt1[0]
    dy = pt2[1] - pt1[1]
    
    angle = np.degrees(np.arctan2(dy, dx)) % 360
    return angle


def are_parallel(p1, p2, p3, p4):
    v1 = np.array([p2[0] - p1[0], p2[1] - p1[1]], dtype=np.float64)
    v2 = np.array([p4[0] - p3[0], p4[1] - p3[1]], dtype=np.float64)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 < 1e-6 or norm_v2 < 1e-6:
        return False
    cross_product = v1[0] * v2[1] - v1[1] * v2[0]
    sin_theta = cross_product / (norm_v1 * norm_v2)
    angle_tolerance_degrees = 3.0
    sin_tolerance = np.sin(np.deg2rad(angle_tolerance_degrees))
    return abs(sin_theta) < sin_tolerance

def analyze_quadrilateral(corners):
    side_lengths = [calculate_distance(corners[i], corners[(i+1)%4]) for i in range(4)]
    avg_length = sum(side_lengths) / 4
    length_tolerance_ratio = 0.15
    if all(abs(length - avg_length) < avg_length * length_tolerance_ratio for length in side_lengths):
        return "Rhombus"
    is_parallel_1 = are_parallel(corners[0], corners[1], corners[2], corners[3])
    is_parallel_2 = are_parallel(corners[1], corners[2], corners[3], corners[0])
    if is_parallel_1 or is_parallel_2:
        return "Trapezoid"
    return "Irregular Quadrilateral"

def select_reference_angle(shape, corners):
    """
    计算旋转角度
    """
    def sort_by_y(c):
        return sorted(c, key=lambda p: (p[1], p[0]))
    
    # 三角形
    if shape == "Triangle":
        # 1. 找到最上面的顶点 (y坐标最小)
        pts = sort_by_y(corners)
        top_vertex = pts[0]

        # 2. 获取另外两个顶点，形成与顶点的两条边
        other_vertices = [p for p in pts if not np.array_equal(p, top_vertex)]

        # 3. 计算每个边在x方向上的绝对变化量
        x_deltas = [abs(p[0] - top_vertex[0]) for p in other_vertices]
        
        # 4. 选择x方向变化量更大的那条边作为参考边
        #    np.argmax会找到最大值对应的索引
        reference_vertex_index = np.argmax(x_deltas)
        reference_vertex = other_vertices[reference_vertex_index]
        
        # 5. 计算参考边的角度
        ref_angle = calculate_angle(top_vertex, reference_vertex)
        base_line = [tuple(top_vertex), tuple(reference_vertex)]
        angle = (ref_angle - 60) % 120 
        return angle, base_line

    # 六边形
    elif shape == "Hexagon":
        # 1. 找到最上方的顶点（y 最小）
        pts = sort_by_y(corners)
        top = pts[0]
        # 2. 找到 top 顶点在 corners 中的索引
        top_idx = None
        for i, pt in enumerate(corners):
            if np.array_equal(pt, top):
                top_idx = i
                break
        if top_idx is None:
            return None, None
        # 3. 获取与该顶点相邻的两条边
        left_neighbor = corners[(top_idx - 1) % 6]
        right_neighbor = corners[(top_idx + 1) % 6]

        edge1 = [top, left_neighbor]
        edge2 = [top, right_neighbor]

        # 4. 计算两个边的 x 方向分量
        dx1 = left_neighbor[0] - top[0]
        dx2 = right_neighbor[0] - top[0]

        # 5. 选择更靠右的边（x 分量更大的）作为参考边
        # 选择更靠右的边作为 baseline
        base_edge_hex = edge1 if dx1 > dx2 else edge2

        ref_angle = calculate_angle(base_edge_hex[0], base_edge_hex[1])
        base_line = [tuple(base_edge_hex[0]), tuple(base_edge_hex[1])]
        angle = ref_angle % 60
        return angle, base_line


    # 菱形
    elif shape == "Rhombus":
        max_dist = 0
        pair = (corners[0], corners[2])
        for i in range(4):
            for j in range(i+1, 4):
                d = calculate_distance(corners[i], corners[j])
                if d > max_dist:
                    max_dist = d
                    pair = (corners[i], corners[j])
        ref_angle = calculate_angle(pair[0], pair[1])
        base_line = [tuple(pair[0]), tuple(pair[1])]
        return -((180 - 30 -  ref_angle) % 180), base_line
    

    # 梯形
    elif shape == "Trapezoid":
        # 找最长边（长边）
        max_len = 0
        long_edge = (corners[0], corners[1])
        long_edge_idx = 0

        for i in range(4):
            j = (i + 1) % 4
            d = calculate_distance(corners[i], corners[j])
            if d > max_len:
                max_len = d
                long_edge = (corners[i], corners[j])
                long_edge_idx = i

        # 找与长边对边的短边
        short_edge = (corners[(long_edge_idx + 2) % 4], corners[(long_edge_idx + 3) % 4])

        # 判断 y 坐标，确定朝向
        long_edge_y_avg = (long_edge[0][1] + long_edge[1][1]) / 2
        short_edge_y_avg = (short_edge[0][1] + short_edge[1][1]) / 2

        ref_angle = calculate_angle(long_edge[0], long_edge[1])
        # 如果长边在短边下方（y大） angle = ref_angle % 360
        # 如果长边在短边上方（y小） angle = (ref_angle + 180) % 
        if long_edge_y_avg > short_edge_y_avg:
            angle = ref_angle % 360
        else:
            angle = (ref_angle + 180) % 360

        base_line = [tuple(long_edge[0]), tuple(long_edge[1])]
        return angle, base_line


    return None, None


def generate_fixed_order_info(workpiece_info_dict):
    """
    将检测到的工件信息整理为带编号、顺序固定的列表。
    """
    workpiece_info_list = []
    shape_slots = {
        "Triangle": (0, 5),   # 编号1-5（索引0-4）
        "Rhombus": (5, 9),    # 编号6-9
        "Hexagon": (9, 10),   # 编号10
        "Trapezoid": (10, 11) # 编号11
    }

    for shape, (start_idx, end_idx) in shape_slots.items():
        detected_list = workpiece_info_dict.get(shape, [])
        for j, (x_mm, y_mm, angle) in enumerate(detected_list):
            global_idx = start_idx + j  # 编号索引
            if global_idx < end_idx:    # 避免多发
                info_str = f'OKOKx_{x_mm}y_{y_mm}r_{angle:.2f}b_{global_idx+1}*'
                workpiece_info_list.append(info_str)

    return workpiece_info_list


def detect_multiple_objects(image, log_callback=print):
    workpiece_info_dict = {
        "Triangle": [],
        "Rhombus": [],
        "Hexagon": [],
        "Trapezoid": []
    }

    output_image = image.copy()
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 定义颜色区间（每种颜色仅对应一种形状）
    color_definitions = {
        "Brown": ([0, 43, 30],[179, 255, 255]),     # 棕色-三角形
        "Orange": ([0, 169, 0],[179, 255, 255]),    # 橙色-六边形
        "Pink": ([14, 57, 22],[179, 255, 255]),   # 粉色-菱形
        "Green": ([23, 37, 0],[156, 255, 223])  # 绿色-梯形
    }

    # 显式绑定颜色与形状
    color_shape_map = {
        "Brown": "Triangle",
        "Orange": "Hexagon",
        "Pink": "Rhombus",
        "Green": "Trapezoid"
    }

    detected_set = set()  # 记录已识别的中心坐标和形状，避免重复

    for color_name, (lower, upper) in color_definitions.items():
        mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        expected_shape = color_shape_map[color_name]

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 900:
                continue
            perimeter = cv2.arcLength(contour, True)
            epsilon = 0.02 * perimeter
            approx_corners = cv2.approxPolyDP(contour, epsilon, True)
            num_corners = len(approx_corners)
            shape = "unknow"

            if num_corners == 3:
                shape = "Triangle"
            elif num_corners == 4:
                shape = analyze_quadrilateral(approx_corners.reshape(-1, 2))
            elif num_corners == 6:
                shape = "Hexagon"

            if shape == expected_shape:
                M = cv2.moments(approx_corners)
                if M["m00"] != 0:
                    cx, cy = int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])
                else:
                    continue

                # 去重判定
                key = (shape, cx // 10, cy // 10)  # 中心点四舍五入到10像素精度
                if key in detected_set:
                    continue
                detected_set.add(key)

                angle, base_line = select_reference_angle(shape, approx_corners.reshape(-1, 2))
                cv2.drawContours(output_image, [approx_corners], -1, (0, 255, 0), 3)
                cv2.putText(output_image, f"{shape},{angle:.1f}", (cx - 40, cy + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 255), 3)
                if base_line is not None:
                    p1, p2 = base_line
                    cv2.line(output_image, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255, 0, 0), 2)
                # log_callback(f"{color_name}: {shape}, center=({cx},{cy}) angle={angle:.2f}")

                # x 与 y 转换到机械臂坐标系
                x_mm, y_mm = pixel_to_world_coords(cx, cy, H_txt_path='config/waican.txt',
                                                   K_txt_path='config/neican.txt',
                                                   D_txt_path='config/jibian.txt'
                                                   )
                # ====补偿====
                log_callback(f"{color_name}: {shape}, center=({x_mm},{y_mm}) angle={angle:.2f}")
                 # 先存到对应形状列表
                workpiece_info_dict[shape].append((round(x_mm), round(y_mm), angle))

    workpiece_info_list = generate_fixed_order_info(workpiece_info_dict)
    return output_image, workpiece_info_list





if __name__ == "__main__":
    frame = cv2.imread(r"assets\debug_for_angel\capture_20250611_132644.jpg")
    result, workpoece_info_list = detect_multiple_objects(frame)
    print(workpoece_info_list)
    result = cv2.resize(result, (640, 512))
    cv2.imshow("Result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()



