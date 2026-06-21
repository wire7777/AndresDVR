from flask import Flask, send_from_directory, redirect, render_template, jsonify, request
from app import config
from app.recorder import Recorder
from app import database
from app import hdhr
from app import epg


import subprocess
import shutil

app = Flask(__name__)
recorder = Recorder()


# Create required folders
for folder in [
    config.RECORDINGS,
    config.LOGS,
    config.LIVEBUFFER,
    config.THUMBNAILS,
    config.GUIDE,
]:
    folder.mkdir(parents=True, exist_ok=True)


database.init_db()


@app.route("/")
def index():
    recordings = database.list_recordings()
    channels = database.get_now_next()
    status = "RECORDING" if recorder.is_recording() else "IDLE"

    return render_template(
        "index.html",
        recordings=recordings,
        channels=channels,
        status=status,
    )


@app.route("/start", methods=["POST"])
def start():
    recorder.start()
    return redirect("/")


@app.route("/stop", methods=["POST"])
def stop():
    recorder.stop()
    return redirect("/")


@app.route("/record-channel/<guide_number>", methods=["POST"])
def record_channel(guide_number):
    ch = database.get_channel(guide_number)

    if ch:
        recorder.start_from_channel(ch)

    return redirect("/")


@app.route("/play/<filename>")
def play(filename):
    return send_from_directory(
        config.RECORDINGS,
        filename,
        as_attachment=False,
    )


@app.route("/delete/<path:filename>", methods=["GET", "POST"])
def delete_recording(filename):
    path = config.RECORDINGS / filename

    if path.exists():
        path.unlink()

    database.delete_recording(filename)
    return redirect("/")


@app.route("/scan-channels", methods=["POST"])
def scan_channels():
    hdhr.import_lineup()
    return redirect("/")


@app.route("/import-epg", methods=["POST"])
def import_epg():
    epg.update_guide()
    return redirect("/")


@app.route("/guide")
def guide_page():
    channels = database.get_now_next()
    return render_template("guide.html", channels=channels)


@app.route("/guide-view/<channel>")
def guide_view_channel(channel):
    programs = database.get_programs_for_channel(channel, limit=30)
    return render_template(
        "channel_guide.html",
        channel=channel,
        programs=programs,
    )


@app.route("/guide/<channel>")
def guide_channel_json(channel):
    return jsonify(database.get_programs_for_channel(channel, limit=30))


@app.route("/api/guide")
def api_guide():
    return jsonify(database.get_now_next())


@app.route("/api/programs")
def api_programs():
    return jsonify(database.get_programs())


@app.route("/health")
def health():
    disk = shutil.disk_usage(config.RECORDINGS)

    try:
        tuner = subprocess.check_output(
            [
                "hdhomerun_config",
                config.HDHR_DEVICE,
                "get",
                "/tuner1/debug",
            ],
            text=True,
        )
    except Exception as e:
        tuner = f"HDHomeRun error: {e}"

    return f"""
<h1>AndresDVR Health</h1>

<p><a href="/">Back</a></p>

<h2>Recorder</h2>
<pre>Status: {"RECORDING" if recorder.is_recording() else "IDLE"}</pre>

<h2>Disk</h2>
<pre>
Total: {disk.total / 1024 / 1024 / 1024:.1f} GB
Used:  {disk.used / 1024 / 1024 / 1024:.1f} GB
Free:  {disk.free / 1024 / 1024 / 1024:.1f} GB
</pre>

<h2>HDHomeRun</h2>
<pre>{tuner}</pre>
"""
@app.route("/schedule-program", methods=["POST"])
def schedule_program():
    database.add_scheduled_recording(
        channel=request.form.get("channel", ""),
        title=request.form.get("title", ""),
        subtitle=request.form.get("subtitle", ""),
        start=request.form.get("start", ""),
        stop=request.form.get("stop", ""),
    )
    return redirect("/scheduled")

@app.route("/scheduled")
def scheduled_page():
    scheduled = database.list_scheduled_recordings()
    return jsonify(scheduled)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=config.PORT,
    )