from app.database import connect
import xml.etree.ElementTree as ET


def import_xmltv(filename):

    tree = ET.parse(filename)
    root = tree.getroot()

    with connect() as db:

        db.execute("DELETE FROM programs")

        for p in root.findall("programme"):

            db.execute("""
                INSERT INTO programs
                (
                    channel,
                    title,
                    description,
                    start,
                    stop
                )
                VALUES (?,?,?,?,?)
            """, (
                p.attrib.get("channel", ""),
                p.findtext("title", ""),
                p.findtext("desc", ""),
                p.attrib.get("start", ""),
                p.attrib.get("stop", "")
            ))

        db.commit()