# -*- coding: utf-8 -*-
"""
Build the five Pôle Élec hub templates from one list of links.

    python build_hub.py

Reads hub_links.json (sections, tiles, URLs, news) and templates/*.html, writes
pole_elec_hub_<n>_<name>.html next to this script. To change a link or a label,
edit hub_links.json and run the script again: the five pages stay in step.
"""
import glob, json, os

HERE = os.path.dirname(os.path.abspath(__file__))

# 24 x 24 stroke icons, drawn with currentColor
ICONS = {
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1" fill="currentColor"/>',
    "follow": '<path d="M3.5 3.5v17h17"/><path d="M7 15.5l4-4.5 3 2.5 5.5-6.5"/><circle cx="19.5" cy="7" r="1.2"/>',
    "fod": '<path d="M12 2.8l8 4.6v9.2l-8 4.6-8-4.6V7.4z"/><circle cx="12" cy="12" r="3.3"/>',
    "pen": '<path d="M4 20h4.2L19.4 8.8a2 2 0 0 0 0-2.8l-1.4-1.4a2 2 0 0 0-2.8 0L4 15.8z"/><path d="M13.6 6.2l4.2 4.2"/>',
    "pareto": '<path d="M4 20.5V9h3.6v11.5M10.2 20.5V13h3.6v7.5M16.4 20.5V16.5H20v4"/><path d="M3.5 6.5C9 6 13.5 4.6 20.5 3.5"/>',
    "alert": '<path d="M10.3 4.2L2.6 17.6A2 2 0 0 0 4.3 20.6h15.4a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4.5"/><path d="M12 17.2v.3"/>',
    "euro": '<path d="M17.5 6.6A7.2 7.2 0 1 0 17.5 17.4"/><path d="M4 10.2h9.5M4 13.8h9.5"/>',
    "check": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2.8h6V4"/><path d="M8.8 12.6l2.2 2.2 4.4-4.6"/>',
    "quiz": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M7.5 8.2l1.5 1.5 2.6-2.8M13.8 8.6h3M7.5 14.6l1.5 1.5 2.6-2.8M13.8 15h3"/>',
    "stamp": '<path d="M10 3.2h4a1.2 1.2 0 0 1 1.2 1.2v2.4c0 1.8-1.3 2.6-1.3 4.6h-3.8c0-2-1.3-2.8-1.3-4.6V4.4A1.2 1.2 0 0 1 10 3.2z"/><path d="M4.5 12.8h15v4h-15z"/><path d="M6.5 20.3h11"/>',
    "doc": '<path d="M6 2.8h8l4.5 4.5v13.9H6z"/><path d="M14 2.8v4.5h4.5M9 12h6M9 15.5h6"/>',
    "search": '<circle cx="10.8" cy="10.8" r="6.3"/><path d="M15.4 15.4l5 5"/>',
    "arrow": '<path d="M5 12h13M13 6.5l5.5 5.5-5.5 5.5"/>',
}


def js(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def main():
    hub = json.load(open(os.path.join(HERE, "hub_links.json"), encoding="utf-8"))
    for tpl in sorted(glob.glob(os.path.join(HERE, "templates", "*.html"))):
        html = open(tpl, encoding="utf-8").read()
        assert "/*__HUB__*/null" in html, tpl
        html = html.replace("/*__HUB__*/null", js(hub)).replace("/*__ICONS__*/null", js(ICONS))
        out = os.path.join(HERE, "pole_elec_hub_" + os.path.basename(tpl))
        open(out, "w", encoding="utf-8").write(html)
        print("written", os.path.basename(out), "%.0f kB" % (len(html.encode("utf-8")) / 1024))


if __name__ == "__main__":
    main()
