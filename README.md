# 北京科技大学自动化生产线实训

## 📖 项目介绍
本项目为 **北京科技大学自动化生产线实训**，主要实现 **数字孪生机械臂的视觉部分**。  
 
---

## 🎥 运行效果
> 视频为 **2 倍速演示**

https://github.com/user-attachments/assets/4eaba85b-19d3-491c-b5df-446f11e7d2b1  

---

## 🖥️ 视觉上位机界面
<p align="center">
  <img src="https://github.com/user-attachments/assets/293ff6f0-baa4-4e7c-bea4-478e0bfed63e" width="800" />
</p>

---

## 📂 项目目录

```bash
.
│  communication.py     # 通讯
│  detect.py            # 识别
│  main.py              # 主函数入口
│
├─assets                # 资源文件
│  ├─captured_for_hsv   # HSV调参截图
│  ├─debug_for_angel    # 调试图片
│  └─img_angel_0        # 样例图片
│
├─config                # 相机配置参数
│      jibian.txt       # 畸变系数
│      neican.txt       # 内参
│      waican.txt       # 外参
│
├─results               # 识别结果输出
│  ├─detect             # 检测结果
│  └─original           # 原始图像
│
└─utils                 # 工具脚本
   │  get_hsv.py        # HSV颜色阈值获取
   │  pixel2world.py    # 像素坐标到世界坐标转换
