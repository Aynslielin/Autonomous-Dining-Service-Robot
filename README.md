# Automated-Plate-Delivery-Machine
## Project Overview  
![Project Overview](https://github.com/Aynslielin/Autonomous-Dining-Service-Robot/blob/main/figures/Project%20Overview.png)  
This project presents the design, fabrication, and implementation of an **Automated Plate Delivery Machine**. The system integrates computer vision, robotic manipulation, and mobile mobility to achieve autonomous service tasks.  
Originally developed on a Raspberry Pi 4, the computing core has been successfully migrated to the **NVIDIA Jetson Orin Nano** to overcome the latency bottlenecks and enable real-time processing for the object detection and kinematic control.  
### Funding & Recognition
* **Program:** Undergraduate Research Project
* **Grant:** Funded by the **National Science and Technology Council (NSTC)**.  
* **Institution**: Department of Electrical Engineering, National Taiwan Ocean University
* **Advisor**: Prof. Chih-Yung Cheng
* **Researcher**: Hsin-Wei Lin
---
<!---**Current Status:** Focusing on integrating plate serving mobility.
**Future Roadmap / Challenges:** Planned implementation of LiDAR for dynamic obstacle avoidance and SLAM algorithm.
* Validated mechanical design and YOLOv8 model performance.
* Transitioned the computing core from **Raspberry Pi 4** to **NVIDIA Jetson Orin Nano** to address computational bottlenecks encountered during YOLOv8-based object detection.
* Achieved precise plate-grabbing action by implementing visual servoing algorithms, enabling the robot to autonomously align its chassis with the target using real-time YOLOv8 feedback .--->

## Project Demo
> **Watch the final demonstration video on YouTube:**  
[![](https://img.youtube.com/vi/sNF4TxTJK3E/0.jpg)](https://youtu.be/sNF4TxTJK3E?si=VH2IiI8ZEKtDzknI)

> **Watch the first demonstration video on YouTube:**  
[![](https://img.youtube.com/vi/ru0SwnUDgf8/0.jpg)](https://youtu.be/ru0SwnUDgf8)
---

## System Architecture
![](https://github.com/Aynslielin/Autonomous-Dining-Service-Robot/blob/main/figures/System%20Overview.png)
### 1. Hardware Specifications
| Component | Specification | Function |
| :--- | :--- | :--- |
| **Computing Core** | NVIDIA Jetson Orin Nano | Deep learning inference (YOLOv8) & High-level control |  
| **Vision Sensor** | USB / CSI Camera | Real-time video stream acquisition |
| **Microcontroller** | Arduino Mega 2560 | Low-level motor control & command execution |  
| **Manipulator** | Custom 2-DOF Robotic Arm | 3D printed structure designed in **SolidWorks** |  
| **Motor Driver** | L298N Module | H-Bridge driver for DC motors and arm actuation |  
| **Actuators** | DC Motors | Chassis movement control and Arm movement control |  
### 2. Software Stack
* **Language:** Python 3.9+, C++
* **Computer Vision:** OpenCV, Ultralytics YOLOv8  
* **Communication:** UART(Jetson ↔ Arduino) / I2C Protocols
---
## Engineering Techniques
### 1. Ｍechanical Design & Control
To pickup the plate, I initially designed the lift-based gripper and arm by SolidWorks. However, the arm-extension design shifted the robot's center of mass and caused chassis instability, which decreased the accuracy of plate-pickup. To solve this problem, I removed arm design and fixed the gripper on the front chassis of the robot to lighten the load. Under this circumstance, the gripper is stationary.  
![](https://github.com/Aynslielin/Autonomous-Dining-Service-Robot/blob/main/figures/gripper_design.png)  
As the robot could not rely on the extension arm to pickup the plate in the distant environment, I figured out another method - Controlling the wheel motion to adjust the gripping distance between the plate and the robot. To achieve this method, I used plate position in the camera view as feedback for P-Control, adjusting Mecanum wheel motion during the final approach for more reliable plate positioning.  
![](https://github.com/Aynslielin/Autonomous-Dining-Service-Robot/blob/main/figures/P_Control.png)
### 2. Perception
In this project, I initially utilized existing plate dataset for YOLOv8 model training. However, this model performed poorly on plate recognition as the camera is fixed in angle. Hence, I collected and annotated a custom plate dataset for identifying empty plate and food-filled plate. With new custom dataset, I retrained a new YOLOv8 model and received well-recognized performance.
### 3. ArUco Marker Delivery
---
## Challenges
