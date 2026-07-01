import sys
import json
import urllib.parse
import urllib.request

import xbmcgui
import xbmcplugin
import xbmcaddon


ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = ADDON.getSetting("server_url").rstrip("/")


def build_url(query):
    return sys.argv[0] + "?" + urllib.parse.urlencode(query)


def fetch_json(path):
    url = BASE_URL + path
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def add_dir(name, mode):
    item = xbmcgui.ListItem(label=name)
    url = build_url({"mode": mode})
    xbmcplugin.addDirectoryItem(HANDLE, url, item, True)


def add_play_item(name, url):
    item = xbmcgui.ListItem(label=name)
    item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, url, item, False)


def main_menu():
    add_dir("Live TV", "live")
    add_dir("Recordings", "recordings")
    xbmcplugin.endOfDirectory(HANDLE)


def live_tv():
    channels = fetch_json("/api/kodi/live")

    for ch in channels:
     name = "{} {}  |  NOW: {}  |  NEXT: {}".format(
      ch.get("channel", ""),
      ch.get("name", ""),
      ch.get("now_title") or "No guide data",
      ch.get("next_title") or "No guide data",
)
    play_url = BASE_URL + ch.get("play_url", "")
    add_play_item(name, play_url)

    xbmcplugin.endOfDirectory(HANDLE)


def recordings():
    items = fetch_json("/api/kodi/recordings")

    for r in items:
        title = r.get("title") or r.get("filename") or "Recording"
        channel = r.get("channel", "")
        recorded = r.get("start_time", "")
        label = "{}  [{} {}]".format(title, channel, recorded)

        play_url = BASE_URL + r.get("download_url", "")
        add_play_item(label, play_url)

    xbmcplugin.endOfDirectory(HANDLE)


def router():
    params = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    mode = params.get("mode", "")

    if mode == "live":
        live_tv()
    elif mode == "recordings":
        recordings()
    else:
        main_menu()


if __name__ == "__main__":
    router()
