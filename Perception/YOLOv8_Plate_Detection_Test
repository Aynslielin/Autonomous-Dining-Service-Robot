from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.yaml")
model._load(r"D:\python\NTSC\PythonProject\pycharm\runs\detect\train4\weights\best.pt")

cap = cv2.VideoCapture(0)                     #Use Camera0(default) 使用攝影機0(預設)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) #Set Up Resolution 設定像素
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) #Set Up Resolution 設定像素

while cap.isOpened():
    ret,frame = cap.read()                    #Read Image讀取影像
    if not ret:
        print("無法讀取影像")
        break

    result = model.predict(frame, conf=0.8)   #When the similarity between the detected object and the training item reaches 80% or more, it is considered the result to be displayed,  當偵測到的物體與訓練物品相似度達到80%以上便視為要顯示的結果

    res_plotted = result[0].plot()            #Draw the frames to the detected objects 繪製辨識出的物體框架
    cv2.imshow("YOLOv8 Result", res_plotted) #Show Result 顯示辨識結果

    if cv2.waitKey(10) == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
