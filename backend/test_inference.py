from ultralytics import YOLO
import sys

img_path = "/Users/srujangowda/Downloads/naval-ai/backend/uploads/fb66751b9d1f415fa6669f14da9e47d3.jpg"

print("--- Testing best.pt ---")
model_standard = YOLO("../models/weights/best.pt")
results = model_standard.predict(source=img_path, conf=0.01, verbose=False)
for box in results[0].boxes:
    print(f"Standard Model Detection - Class: {int(box.cls.item())}, Conf: {float(box.conf.item()):.4f}")

print("\n--- Testing all_weather_best.pt ---")
model_all_weather = YOLO("../models/weights/all_weather_best.pt")
results2 = model_all_weather.predict(source=img_path, conf=0.01, verbose=False)
for box in results2[0].boxes:
    print(f"All-Weather Model Detection - Class: {int(box.cls.item())}, Conf: {float(box.conf.item()):.4f}")

