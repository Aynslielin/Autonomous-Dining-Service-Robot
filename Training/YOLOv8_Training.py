# Self-Annotated Data Training
from ultralytics import YOLO
import os
import torch

# 1. 解決環境報錯問題
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

def train_model():
    # 2. 檢測 GPU 狀態
    print("="*30)
    gpu_available = torch.cuda.is_available()
    print(f"是否有抓到獨顯: {gpu_available}")
    
    if gpu_available:
        device_name = torch.cuda.get_device_name(0)
        print(f"正在使用的顯卡型號: {device_name}")
        device = 0  # 使用第一張顯卡
    else:
        print("警告: 未抓到 GPU，將使用 CPU 進行訓練 (速度會很慢)")
        device = 'cpu'
    print("="*30)

    # 3. 載入模型 (yolov8n.pt 是最輕量、速度最快的版本)
    model = YOLO("yolov8n.pt") 

    # 4. 指向資料庫路徑 (請再次確認 data.yaml 檔案位置)
    data_path = r"D:\python\NTSC\PythonProject\pycharm\Plate_Detection.v5i.yolov8\data.yaml"

    # 5. 開始訓練
    model.train(
        data=data_path, 
        epochs=300,     # 訓練 300 次
        imgsz=640, 
        batch=32,       # 使用獨顯時，batch 調整到 16 或 32 可以提高穩定度
        lr0=0.0015,
        device=device,  # 強制使用顯卡
        workers=0,      # 避免多執行緒權限報錯
        name="plate_model_v5" # 給訓練結果取個名字，方便找檔案
    )

    # 6. 驗證與匯出
    metrics = model.val()
    path = model.export(format="onnx")
    print(f"模型訓練完成並已匯出為 ONNX 格式，路徑: {path}")

if __name__ == '__main__':
    train_model()
