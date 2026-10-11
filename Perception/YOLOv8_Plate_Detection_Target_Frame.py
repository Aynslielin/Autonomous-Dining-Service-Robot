from ultralytics import YOLO
import cv2
import time
import torch
print("GPU 是否可用：", torch.cuda.is_available())
print("GPU 型號：", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "沒抓到")
# ==========================================
# 1. 模型載入
# ==========================================
print("正在載入模型")
# 不需要先載入 yaml，可以用.engine替代.pt
try:
    #model = YOLO("best.pt") 
    model = YOLO("best.engine", task='detect')

except:
    print("找不到 best.pt，改用預設 yolov8n.pt 測試")
    model = YOLO("yolov8n.pt")


# ==========================================
# 2. 設定攝影機 (Jetson 修改重點)
# ==========================================
# Windows 用 CAP_DSHOW，但在 Jetson (Linux) 要用 CAP_V4L2
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# 設定解析度
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# 檢查是否成功開啟
if not cap.isOpened():
    print("無法開啟攝影機，檢查device ID(0或1)")
    exit()

print("程式啟動，請按'q'鍵離開")

# ==========================================
# 3. 主迴圈
# ==========================================
while True:
    ret, frame = cap.read()
    if not ret:
        print("讀取影像失敗")
        break

    # 執行預測
    # device=0: 強制使用 GPU (如果是 Jetson Orin Nano 很重要)
    # verbose=False: 隱藏雜亂的 log
    results = model.predict(frame, conf=0.8, device=0, verbose=False) 
    
    # 取得 YOLO 幫你畫好框的圖 (當作基底)
    res_plotted = results[0].plot()

    # --- 計算面積邏輯 ---
    for box in results[0].boxes:
        # 1. 取得座標
        # box.xyxy[0] 是 Tensor 格式，先轉到 cpu 再轉 numpy
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)

        # 2. 計算面積
        w = x2 - x1
        h = y2 - y1
        area = w * h

        # 3. 印出資訊
        # print(f"偵測到: {model.names[int(box.cls[0])]} | 面積: {area}")

        # 4. 畫在畫面上 (畫在 res_plotted 上)
        # 在框框上方顯示面積數值
        cv2.putText(res_plotted, f"Area: {area}", (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    # --- 結束 ---

    # 顯示畫面
    cv2.imshow("Jetson YOLO Vision", res_plotted)

    # 按 'q' 離開 (waitKey(1) 比較適合即時串流)
    if cv2.waitKey(1) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("程式結束")
