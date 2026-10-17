import json
import numpy as np
import config

# حفظ احداثيات المواقف
def save_spaces(polygons_norm, path=config.SPACES_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "spaces": polygons_norm}, f, indent=2)

# تحميل احداثيات المواقف
def load_spaces(path=config.SPACES_FILE):
    if not path.exists():
        raise FileNotFoundError("يرجى تشغيل أداة تحديد المواقف أولاً (roi_selector.py)")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["spaces"]

# تحويل الاحداثيات الى بكسل
def to_pixels(polygons_norm, width, height):
    return [np.array([[int(x * width), int(y * height)] for x, y in poly], np.int32) for poly in polygons_norm]
