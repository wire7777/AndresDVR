import subprocess
import signal
from app import config
from app import database

PIDFILE = config.BASE / "livetv.pid"
CURRENT_CHANNEL_FILE = config.BASE / "livetv_channel.txt"

def is_live_running():
    if not PIDFILE.exists():
        return False

    try:
        pid = int(PIDFILE.read_text().strip())
        subprocess.run(["kill", "-0", str(pid)], check=True)
        return True
    except Exception:
        PIDFILE.unlink(missing_ok=True)
        return False


def stop_live():
    if PIDFILE.exists():
        try:
            pid = int(PIDFILE.read_text().strip())
            subprocess.run(["kill", "-TERM", str(pid)])
        except Exception:
            pass

        PIDFILE.unlink(missing_ok=True)


def start_live(channel_number):
    stop_live()

    ch = database.get_channel(channel_number)
    if not ch:
        CURRENT_CHANNEL_FILE.write_text(f"{ch['guide_number']} {ch['guide_name']}")
        return False

    config.LIVEBUFFER.mkdir(parents=True, exist_ok=True)

    for f in config.LIVEBUFFER.glob("*"):
        f.unlink(missing_ok=True)

    playlist = config.LIVEBUFFER / "live.m3u8"

    proc = subprocess.Popen([
        "ffmpeg",
        "-y",
        "-i", ch["url"],

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "128k",
        "-ac", "2",
        
        "-g", "60",
        "-sc_threshold", "0",
        "-f", "hls",
        "-hls_time", "2",
        "-hls_list_size", "1800",
        "-hls_flags", "delete_segments+append_list",
        str(playlist),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # proc = subprocess.Popen([
    #     "ffmpeg",
    #     "-y",
    #     "-i", ch["url"],
    #     "-c", "copy",
    #     "-f", "hls",
    #     "-hls_time", "4",
    #     "-hls_list_size", "450",
    #     "-hls_flags", "delete_segments+append_list",
    #     str(playlist),
    # ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    

    PIDFILE.write_text(str(proc.pid))
    return True

def current_channel():
    if CURRENT_CHANNEL_FILE.exists():
        return CURRENT_CHANNEL_FILE.read_text().strip()
    return ""