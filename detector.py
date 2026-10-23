from collections import deque
import cv2
import numpy as np
from ultralytics import YOLO
import config

class VehicleDetector:
    # تهيئة نموذج الكشف
    def __init__(self):
        self.model = YOLO(config.MODEL_NAME)

    # كشف المركبات في الصورة
    def detect(self, frame):
        res = self.model.predict(frame, conf=config.CONFIDENCE, classes=config.VEHICLE_CLASSES, imgsz=config.IMG_SIZE, verbose=False)[0]
        boxes = []
        for b in res.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            boxes.append((x1, y1, x2, y2, float(b.conf[0])))
        return boxes

class OccupancyAnalyzer:
    # تهيئة محلل المواقف
    def __init__(self, polygons_px, frame_shape):
        self.polys = polygons_px
        h, w = frame_shape[:2]
        self.shape = (h, w)
        self.masks, self.areas = [], []
        for p in polygons_px:
            m = np.zeros((h, w), np.uint8)
            cv2.fillPoly(m, [p], 255)
            self.masks.append(m)
            self.areas.append(max(1, cv2.countNonZero(m)))
        self.history = [deque(maxlen=config.SMOOTH_WINDOW) for _ in polygons_px]

    # تحديث حالة الإشغال للمواقف
    def update(self, boxes):
        car_mask = np.zeros(self.shape, np.uint8)
        for x1, y1, x2, y2, _ in boxes:
            top = y1 + (y2 - y1) * (1 - config.BOX_BOTTOM_FRACTION)
            cv2.rectangle(car_mask, (int(x1), int(top)), (int(x2), int(y2)), 255, -1)

        states = []
        for i, m in enumerate(self.masks):
            overlap = cv2.countNonZero(cv2.bitwise_and(m, car_mask)) / self.areas[i]
            is_overlap = overlap >= config.OVERLAP_THRESHOLD
            self.history[i].append(is_overlap)
            h = self.history[i]
            # مشغول إذا كان التداخل كافياً في معظم الإطارات أو قوي ومباشر في الإطار الحالي
            is_occ = (sum(h) > len(h) / 2) or (overlap >= config.OVERLAP_THRESHOLD * 1.5)
            states.append(bool(is_occ))
        return states

    # رسم النتائج على الصورة
    def draw(self, frame, states, boxes=()):
        out = frame.copy()
        overlay = out.copy()
        for i, (p, occ) in enumerate(zip(self.polys, states), 1):
            color = (0, 0, 230) if occ else (0, 200, 0)
            cv2.fillPoly(overlay, [p], color)
            cv2.polylines(out, [p], True, color, 2)
            cx, cy = p.mean(axis=0).astype(int)
            cv2.putText(out, str(i), (cx - 8, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        out = cv2.addWeighted(overlay, 0.30, out, 0.70, 0)
        for x1, y1, x2, y2, _ in boxes:
            cv2.rectangle(out, (int(x1), int(y1)), (int(x2), int(y2)), (255, 180, 0), 1)
        return out
