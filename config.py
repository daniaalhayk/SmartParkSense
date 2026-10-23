from pathlib import Path

# إعدادات النظام الأساسية
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

SPACES_FILE = DATA_DIR / "parking_spaces.json"
DB_FILE = DATA_DIR / "parksense.db"
LATEST_FRAME = DATA_DIR / "latest.jpg"

MODEL_NAME = "yolov8n.pt"
CONFIDENCE = 0.18
VEHICLE_CLASSES = [2, 3, 5, 7]
IMG_SIZE = 960

SAMPLE_EVERY_SEC = 1.0
OVERLAP_THRESHOLD = 0.20
BOX_BOTTOM_FRACTION = 1.0
SMOOTH_WINDOW = 3
