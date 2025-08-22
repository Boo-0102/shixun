# 北京科技大学自动化生产线实训
## 介绍
北京科技大学自动化生产线实训-数字孪生机械臂-视觉部分
## 运行效果
https://github.com/user-attachments/assets/4eaba85b-19d3-491c-b5df-446f11e7d2b1
视频为2倍速
## 视觉上位机
<img width="1002" height="639" alt="image" src="https://github.com/user-attachments/assets/293ff6f0-baa4-4e7c-bea4-478e0bfed63e" />

## 项目目录
```bash
.
│  communication.py # 通讯
│  detect.py # 识别
│  main.py # 主函数
│
├─assets 
│  ├─captured_for_hsv
│  ├─debug_for_angel
│  └─img_angel_0
│
├─config # 相机内外参与畸变系数
│      jibian.txt
│      neican.txt
│      waican.txt
│
├─results # 识别结果
│  ├─detect
│  └─original
│
└─utils
   │  get_hsv.py # 获取颜色阈值
   │  pixel2world.py # 坐标转换



