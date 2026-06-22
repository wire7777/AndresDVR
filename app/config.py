from pathlib import Path

BASE = Path.home() / "signaldvr"

RECORDINGS = BASE / "recordings"
LIVEBUFFER = BASE / "livebuffer"
LOGS = BASE / "logs"
THUMBNAILS = BASE / "thumbnails"
GUIDE = BASE / "guide"
GUIDE_XML = GUIDE / "guide.xml"
GUIDE_URL = "http://192.168.2.13:8089/api/xmltv"
HDHR_DEVICE = "1077144F"
START_PADDING_SECONDS = 120
STOP_PADDING_SECONDS = 300

PORT = 8088