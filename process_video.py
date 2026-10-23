import argparse
from datetime import datetime, timedelta
import cv2
import config
import database
import spaces
from detector import VehicleDetector, OccupancyAnalyzer

# معالجة الفيديو واستخراج البيانات بشكل مباشر (Real-Time)
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="data/video.mp4", help="مسار الفيديو")
    args = ap.parse_args()

    database.init_db()
    database.clear("video")

    start = datetime.now()
    polys_norm = spaces.load_spaces()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print("تأكد من وضع الفيديو في المجلد data/video.mp4")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w, h = int(cap.get(3)), int(cap.get(4))
    step = max(1, int(round(fps * config.SAMPLE_EVERY_SEC)))

    analyzer = OccupancyAnalyzer(spaces.to_pixels(polys_norm, w, h), (h, w))
    detector = VehicleDetector()
    n_spaces = len(polys_norm)

    idx = 0
    print("جاري المعالجة وعرض النتائج ...")
    print("اضغط على حرف 'q' في نافذة العرض لإيقاف المعالجة.")
    
    cv2.namedWindow("المراقبة المباشرة (Real-Time)", cv2.WINDOW_NORMAL)
    
    while True:
        ok = cap.grab()
        if not ok:
            break
            
        if idx % step == 0:
            ok, frame = cap.retrieve()
            if not ok: break
            
            ts = (start + timedelta(seconds=idx / fps)).isoformat(timespec="seconds")
            boxes = detector.detect(frame)
            states = analyzer.update(boxes)
            occupied = sum(states)
            
            # حفظ البيانات فورياً لعرضها في لوحة التحكم بشكل مباشر
            database.insert_snapshots([(ts, occupied, n_spaces, "video")])
            database.insert_space_states([(ts, i + 1, int(s), "video") for i, s in enumerate(states)])
            
            annotated = analyzer.draw(frame, states, boxes)
            cv2.imwrite(str(config.LATEST_FRAME), annotated)
            
            # عرض الفيديو والنتائج بشكل مباشر
            cv2.imshow("المراقبة المباشرة (Real-Time)", annotated)
            
            # الانتظار 1 ملي ثانية لتحديث النافذة، وإيقاف التشغيل عند ضغط q
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        idx += 1

    cap.release()
    cv2.destroyAllWindows()
    print("انتهت المعالجة  بنجاح.")

if __name__ == "__main__":
    main()
