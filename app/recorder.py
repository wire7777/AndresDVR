import datetime
import signal
import subprocess
from app import config
from app import database


class Recorder:
    def __init__(self):
        self.pidfile = config.BASE / "recording.pid"
        self.currentfile = config.BASE / "current_recording.txt"

    def is_recording(self):
        if not self.pidfile.exists():
            return False

        try:
            pid = int(self.pidfile.read_text().strip())
            subprocess.run(["kill", "-0", str(pid)], check=True)
            return True
        except Exception:
            self.pidfile.unlink(missing_ok=True)
            self.currentfile.unlink(missing_ok=True)
            return False

    def start(self, channel="17.1", tuner="tuner1", rf_channel="auto:25", program="3", title=None):
        if self.is_recording():
            return None

        start_time = datetime.datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"{channel.replace('.', '_')}_{timestamp}.ts"

        outfile = config.RECORDINGS / filename
        logfile = config.LOGS / f"{filename}.log"

        database.add_recording(
            filename=filename,
            channel=channel,
            title=title or f"Manual Recording {channel}",
            start_time=start_time.isoformat(timespec="seconds"),
            status="Recording",
        )

        subprocess.run(["hdhomerun_config", config.HDHR_DEVICE, "set", f"/{tuner}/channel", rf_channel])
        subprocess.run(["hdhomerun_config", config.HDHR_DEVICE, "set", f"/{tuner}/program", program])

        log = open(logfile, "w")

        proc = subprocess.Popen(
            ["hdhomerun_config", config.HDHR_DEVICE, "save", f"/{tuner}", str(outfile)],
            stdout=log,
            stderr=log,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
        )

        self.pidfile.write_text(str(proc.pid))
        self.currentfile.write_text(filename)

        return filename

    def start_from_channel(self, channel_row, title=None):
        if self.is_recording():
            return None

        guide_number = channel_row["guide_number"]
        guide_name = channel_row["guide_name"] or guide_number
        url = channel_row["url"]

        start_time = datetime.datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")

        safe_name = (
            (title or guide_name)
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("?", "")
            .replace('"', "")
            .replace("'", "")
        )

        filename = f"{guide_number.replace('.', '_')}_{safe_name}_{timestamp}.ts"

        outfile = config.RECORDINGS / filename
        logfile = config.LOGS / f"{filename}.log"

        database.add_recording(
            filename=filename,
            channel=guide_number,
            title=title or f"Manual Recording - {guide_name}",
            start_time=start_time.isoformat(timespec="seconds"),
            status="Recording",
        )

        log = open(logfile, "w")

        proc = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-i",
                url,
                "-c",
                "copy",
                str(outfile),
            ],
            stdout=log,
            stderr=log,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
        )

        self.pidfile.write_text(str(proc.pid))
        self.currentfile.write_text(filename)

        return filename


    def start_from_schedule(self, channel_row, schedule):
        if self.is_recording():
            return None

        guide_number = channel_row["guide_number"]
        guide_name = channel_row["guide_name"] or guide_number
        url = channel_row["url"]

        title = schedule.get("title", "") or f"Manual Recording - {guide_name}"

        start_time = datetime.datetime.now()
        timestamp = start_time.strftime("%Y%m%d_%H%M%S")

        safe_name = (
            title
            .replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("?", "")
            .replace('"', "")
            .replace("'", "")
        )

        filename = f"{guide_number.replace('.', '_')}_{safe_name}_{timestamp}.ts"

        outfile = config.RECORDINGS / filename
        logfile = config.LOGS / f"{filename}.log"

        database.add_recording_from_schedule(
            filename=filename,
            schedule=schedule,
            start_time=start_time.isoformat(timespec="seconds"),
            status="Recording",
        )

        log = open(logfile, "w")

        proc = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-i",
                url,
                "-c",
                "copy",
                str(outfile),
            ],
            stdout=log,
            stderr=log,
            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN),
        )

        self.pidfile.write_text(str(proc.pid))
        self.currentfile.write_text(filename)

        return filename

    def stop(self, tuner="tuner1"):
        filename = None

        if self.currentfile.exists():
            filename = self.currentfile.read_text().strip()

        if self.pidfile.exists():
            try:
                pid = int(self.pidfile.read_text().strip())

                subprocess.run(["kill", "-INT", str(pid)])
                try:
                    subprocess.run(["timeout", "5", "tail", "--pid", str(pid), "-f", "/dev/null"])
                except Exception:
                    pass

                subprocess.run(["kill", "-0", str(pid)], check=True)
                subprocess.run(["kill", "-TERM", str(pid)])

            except subprocess.CalledProcessError:
                pass
            except Exception:
                pass

            self.pidfile.unlink(missing_ok=True)

        subprocess.run(
            ["hdhomerun_config", config.HDHR_DEVICE, "set", f"/{tuner}/channel", "none"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if filename:
           path = config.RECORDINGS / filename
           size = path.stat().st_size if path.exists() else 0
           end_time = datetime.datetime.now().isoformat(timespec="seconds")

           database.finish_recording(filename, end_time, size)
           recording = database.get_recording(filename)

        if recording:
         rule_id = int(recording.get("recording_rule") or 0)

        if rule_id:
            rule = database.get_series_recording(rule_id)

            if rule:
                keep_last = int(rule.get("keep_last") or 0)
                old_recordings = database.get_recordings_to_prune_for_rule(rule_id, keep_last)

                for old in old_recordings:
                    old_file = old.get("filename")
                    old_path = config.RECORDINGS / old_file

                    print("Pruning old recording:", old_file, flush=True)

                    try:
                        if old_path.exists():
                            old_path.unlink()
                    except Exception as e:
                        print("Prune file delete error:", old_file, e, flush=True)

                    try:
                        database.delete_recording(old_file)
                    except Exception as e:
                        print("Prune database delete error:", old_file, e, flush=True)

        self.currentfile.unlink(missing_ok=True)