import argparse
import cv2
import numpy as np
import spaces

MAX_DISPLAY_W = 1280
state = {"spaces": [], "current": [], "scale": 1.0, "w": 1, "h": 1}

# معالجة تفاعل الماوس وتصحيح شكل الموقف
def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        state["current"].append((x / state["scale"] / state["w"], y / state["scale"] / state["h"]))
        if len(state["current"]) == 4:
            p0, p1, p2, p3 = state["current"]
            # تصحيح النقطة الرابعة ليصبح الشكل متوازي أضلاع متناسق
            p3_ideal = (p0[0] + (p2[0] - p1[0]), p0[1] + (p2[1] - p1[1]))
            state["current"][3] = p3_ideal
            close_polygon()
    elif event == cv2.EVENT_RBUTTONDOWN:
        undo()

# حفظ الموقف المرسوم
def close_polygon():
    if len(state["current"]) >= 3:
        state["spaces"].append(state["current"])
    state["current"] = []

# التراجع عن اخر نقطة
def undo():
    if state["current"]:
        state["current"].pop()
    elif state["spaces"]:
        state["spaces"].pop()

# تحويل الاحداثيات للعرض
def to_disp(pt):
    return int(pt[0] * state["w"] * state["scale"]), int(pt[1] * state["h"] * state["scale"])

# تشغيل واجهة الرسم
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="data/video.mp4")
    args = ap.parse_args()

    cap = cv2.VideoCapture(args.video)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        print("تأكد من وجود الفيديو في data/video.mp4")
        return

    h, w = frame.shape[:2]
    scale = min(1.0, MAX_DISPLAY_W / w)
    state.update(w=w, h=h, scale=scale)
    base = cv2.resize(frame, None, fx=scale, fy=scale) if scale != 1.0 else frame

    win = "تحديد المواقف"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)

    while True:
        img = base.copy()
        overlay = img.copy()
        for i, poly in enumerate(state["spaces"], 1):
            pts = np.array([to_disp(p) for p in poly], np.int32)
            cv2.fillPoly(overlay, [pts], (0, 200, 0))
            cv2.polylines(img, [pts], True, (0, 255, 0), 2)
        img = cv2.addWeighted(overlay, 0.25, img, 0.75, 0)

        cur = [to_disp(p) for p in state["current"]]
        for i, p in enumerate(cur):
            cv2.circle(img, p, 4, (0, 0, 255), -1)
            if i: cv2.line(img, cur[i - 1], p, (0, 0, 255), 2)

        cv2.imshow(win, img)
        k = cv2.waitKey(30) & 0xFF
        if k == 13: close_polygon()
        elif k == ord("u"): undo()
        elif k == ord("s"):
            spaces.save_spaces(state["spaces"])
            break
        elif k == 27: break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
