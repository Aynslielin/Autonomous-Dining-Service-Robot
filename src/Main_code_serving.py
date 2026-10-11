from ultralytics import YOLO
import cv2
import cv2.aruco as aruco
import numpy as np
import serial
import time
import torch

# ==========================================
# 1. 系統與硬體設定 (Settle Up)
# ==========================================
COM_PORT = '/dev/ttyUSB0'
BAUD_RATES = 9600
CAMERA_ID = 0

# ==========================================
# 2. 視覺與控制參數
# ==========================================
# YOLO 找盤子的目標位置
TARGET_X = 320
TARGET_Y = 380 #emptyplate:380,  
TOLERANCE_X = 10
TOLERANCE_Y = 10

# ArUco 送餐桌的觸發線 (您測試出的最佳數值)
ARUCO_THRESHOLD_Y = 100 #success_emptyplate1=110; emptyplate2 = 105； emptyplate3 = 100(best)

# P Control 參數
Kp = 0.002
MAX_DURATION = 0.5
MIN_DURATION = 0.05

# ==========================================
# 3. 狀態機定義 (State Machine)
# ==========================================
STATE_FIND_FOOD   = "FIND_FOOD"     # 階段 1: YOLO 找食物盤並夾取
STATE_ROUTE_TO_TB = "ROUTE_TO_TB"   # 階段 2: 盲走指定路線前往桌子附近
STATE_FIND_ARUCO  = "FIND_ARUCO"    # 階段 3: ArUco 視覺導航與對齊
STATE_DROP_OFF    = "DROP_OFF"      # 階段 4: 放下餐盤
STATE_RETURN_HOME = "RETURN_HOME"   # 階段 5: 回到原點

# 初始狀態：從找食物開始
robot_state = STATE_FIND_FOOD  

# ==========================================
# 4. 初始化 (GPU, Arduino, YOLO, ArUco, Camera)
# ==========================================
print("GPU 是否可用：", torch.cuda.is_available())

# Arduino
try:
    ser = serial.Serial(COM_PORT, BAUD_RATES, timeout=1)
    time.sleep(2)
    print("✅ Arduino 連線成功")
except Exception as e:
    print(f"❌ Arduino 連線失敗: {e}")
    ser = None

# YOLO
print("正在載入 YOLO 模型...")
try: 
    model = YOLO("best.engine", task='detect')
except:
    print("找不到 best.engine，改用 best.pt")
    model = YOLO("best.pt")

# ArUco
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
try:
    aruco_params = aruco.DetectorParameters_create()
    is_opencv_new = False
except AttributeError:
    aruco_params = aruco.DetectorParameters()
    is_opencv_new = True

# Camera
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("❌ 無法開啟攝影機！")
    exit()

print("✅ 系統啟動！準備開始自動送餐任務...")

# ==========================================
# 5. 馬達控制函式
# ==========================================
def move_robot(action, duration):
    if ser is not None:
        cmd_map = {
            "F": "F", 
            "B": "B", 
            "L": "L", 
            "R": "R",
            "Q": "Q", 
            "E": "E", 
            "STOP": "S",
            "GRAB": "3", 
            "RELEASE": "4"
        }
        cmd = cmd_map.get(action, "S")
        print(f"發送指令: {action} (代碼: {cmd}), 持續: {duration:.3f} 秒")
        ser.write(cmd.encode()) 
        time.sleep(duration)              
        ser.write(b"S") 
    else:
        print(f"(模擬) 執行: {action}, 時間: {duration:.3f} 秒")

def clear_buffer():
    # 動作後清空緩衝區，避免看到舊畫面
    for _ in range(5): cap.read()

# ==========================================
# 6. 主視覺迴圈 (Visual Loop)
# ==========================================
while True:
    ret, frame = cap.read()
    if not ret: break
    
    res_plotted = frame.copy()
    action = "STOP"
    dynamic_duration = 0.0

    # ----------------------------------------------------
    # 階段 1: 使用 YOLO 尋找【有食物的盤子】
    # ----------------------------------------------------
    if robot_state == STATE_FIND_FOOD:
        # UI：畫目標區
        cv2.rectangle(res_plotted, (TARGET_X - TOLERANCE_X, TARGET_Y - TOLERANCE_Y),
                      (TARGET_X + TOLERANCE_X, TARGET_Y + TOLERANCE_Y), (0, 255, 0), 2)
        cv2.putText(res_plotted, "STATE: YOLO FIND FOOD", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        results = model.predict(frame, conf=0.85, device=0, verbose=False) 
        res_plotted = results[0].plot()

        for box in results[0].boxes:
            class_name = model.names[int(box.cls[0])]
            
            # ⭐️ 鎖定食物盤
            if class_name == "food_plate":
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
                #new line
                cv2.circle(res_plotted, (cx, cy), 5, (255, 0, 0), -1) 
                cv2.line(res_plotted, (cx, cy), (TARGET_X, TARGET_Y), (0, 255, 255), 2)
                #new line(end)
                error_x, error_y = abs(TARGET_X - cx), abs(TARGET_Y - cy)

                if cx < (TARGET_X - TOLERANCE_X):
                    action, dynamic_duration = "L", min(MAX_DURATION, max(MIN_DURATION, error_x * Kp))
                elif cx > (TARGET_X + TOLERANCE_X):
                    action, dynamic_duration = "R", min(MAX_DURATION, max(MIN_DURATION, error_x * Kp))
                else:
                    if cy < (TARGET_Y - TOLERANCE_Y):
                        action, dynamic_duration = "F", min(MAX_DURATION, max(MIN_DURATION, error_y * Kp))
                    elif cy > (TARGET_Y + TOLERANCE_Y):
                        action, dynamic_duration = "B", min(MAX_DURATION, max(MIN_DURATION, error_y * Kp))
                    else:
                        print("🎉 食物盤已對齊！執行夾取！")
                        move_robot("GRAB", 1.0)
                        time.sleep(1.0)
                        
                        # 夾好後，切換到下一個狀態：前往桌子
                        robot_state = STATE_ROUTE_TO_TB
                break # 只處理第一個看到的目標

        if action != "STOP" and robot_state == STATE_FIND_FOOD:
            move_robot(action, dynamic_duration)
            clear_buffer()

    # ----------------------------------------------------
    # 階段 2: 盲走指定路線前往桌子附近
    # ----------------------------------------------------
    elif robot_state == STATE_ROUTE_TO_TB:
        print("🚚 進入指定路線導航，開往餐桌區...")
        # ⚠️ 【請在此處填寫您的路線】例如：右轉 1 秒，直走 2 秒
        # move_robot("E", 1.0) 
        # move_robot("F", 2.0)
        move_robot("E", 1.7)
        time.sleep(1)
        move_robot("F", 0.8)
        time.sleep(1)
        move_robot("Q", 0.85)
        time.sleep(1) # 暫停一下確認穩定
        
        clear_buffer()
        print("👀 抵達餐桌附近，開啟 ArUco 視覺導航！")
        robot_state = STATE_FIND_ARUCO # 切換到尋找桌子

    # ----------------------------------------------------
    # 階段 3: ArUco 視覺導航與對齊
    # ----------------------------------------------------
    elif robot_state == STATE_FIND_ARUCO:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 畫出觸發界線
        cv2.line(res_plotted, (0, ARUCO_THRESHOLD_Y), (640, ARUCO_THRESHOLD_Y), (0, 0, 255), 2)
        cv2.putText(res_plotted, f"STATE: ARUCO APPROACH", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        if is_opencv_new:
            detector = aruco.ArucoDetector(aruco_dict, aruco_params)
            corners, ids, rejected = detector.detectMarkers(gray)
        else:
            corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=aruco_params)

        if ids is not None:
            aruco.drawDetectedMarkers(res_plotted, corners, ids)
            # 取第一個標記
            c = corners[0][0]
            cx, cy = int(c[:, 0].mean()), int(c[:, 1].mean())
            error_x = abs(TARGET_X - cx)

            # 1. 左右對齊 (維持在畫面正中央 X=320)
            if cx < (TARGET_X - TOLERANCE_X):
                action, dynamic_duration = "L", min(MAX_DURATION, max(MIN_DURATION, error_x * Kp))
            elif cx > (TARGET_X + TOLERANCE_X):
                action, dynamic_duration = "R", min(MAX_DURATION, max(MIN_DURATION, error_x * Kp))
            else:
                # 2. 前後距離判斷 (判斷 Y 軸是否碰到觸發線)
                if cy < ARUCO_THRESHOLD_Y:
                    # 還沒到，繼續往前開 (給固定小步前進)
                    action, dynamic_duration = "F", 0.15 
                else:
                    # 碰到觸發線了！準備送餐
                    print(f"🎯 抵達指定餐桌 (cy={cy})！準備放下餐盤！")
                    move_robot("STOP", 0)
                    robot_state = STATE_DROP_OFF

        if action != "STOP" and robot_state == STATE_FIND_ARUCO:
            move_robot(action, dynamic_duration)
            clear_buffer()

    # ----------------------------------------------------
    # 階段 4: 抵達桌子，放下餐盤
    # ----------------------------------------------------
    elif robot_state == STATE_DROP_OFF:
        print("🍽️ 執行釋放餐盤...")
        # 稍微往前盲走一點點確保放在桌上 (請依實機微調)
        #move_robot("F", 0.3) 
        
        # 張開爪子
        ser.write(b"4")
        time.sleep(1.2)
        ser.write(b"S")
        
        # 倒退撤離
        print("🔙 倒退撤離...")
        move_robot("B", 0.4)
        
        robot_state = STATE_RETURN_HOME

    # ----------------------------------------------------
    # 階段 5: 回到原點
    # ----------------------------------------------------
    elif robot_state == STATE_RETURN_HOME:
        print("🏠 任務完成！開始返回原點...")
        # ⚠️ 【請在此處填寫您的回程路線】例如：轉 180 度，直走
        # move_robot("Q", 1.5) # 原地轉 180 度
        # move_robot("F", 3.0) # 走回原點
        move_robot("Q", 0.85)
        move_robot("F", 0.8)
        
        print("✅ 全自動送餐流程完美結束！")
        break # 結束程式

    # 顯示影像
    cv2.imshow("Jetson Delivery System", res_plotted)
    if cv2.waitKey(1) == ord("q"): break

# 釋放資源
cap.release()
cv2.destroyAllWindows()
if ser is not None: ser.close()
