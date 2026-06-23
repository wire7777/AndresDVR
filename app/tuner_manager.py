import threading
from datetime import datetime


MAX_TUNERS = 4

_lock = threading.Lock()

_tuners = {
    0: None,
    1: None,
    2: None,
    3: None,
}


def allocate(channel, purpose="recording", title=""):
    with _lock:
        for tuner_id, job in _tuners.items():
            if job is None:
                _tuners[tuner_id] = {
                    "tuner_id": tuner_id,
                    "channel": channel,
                    "purpose": purpose,
                    "title": title,
                    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                return tuner_id

        return None


def release(tuner_id):
    with _lock:
        if tuner_id in _tuners:
            _tuners[tuner_id] = None
            return True

        return False


def release_channel(channel):
    with _lock:
        released = []

        for tuner_id, job in _tuners.items():
            if job and job.get("channel") == channel:
                _tuners[tuner_id] = None
                released.append(tuner_id)

        return released


def status():
    with _lock:
        result = []

        for tuner_id, job in _tuners.items():
            if job:
                result.append({
                    "tuner_id": tuner_id,
                    "state": "busy",
                    "channel": job.get("channel"),
                    "purpose": job.get("purpose"),
                    "title": job.get("title"),
                    "started_at": job.get("started_at"),
                })
            else:
                result.append({
                    "tuner_id": tuner_id,
                    "state": "idle",
                    "channel": "",
                    "purpose": "",
                    "title": "",
                    "started_at": "",
                })

        return result


def busy_count():
    with _lock:
        return sum(1 for job in _tuners.values() if job is not None)


def idle_count():
    return MAX_TUNERS - busy_count()


def reset():
    with _lock:
        for tuner_id in _tuners:
            _tuners[tuner_id] = None
