import gzip
import json
import urllib.request
from pathlib import Path

from google.protobuf import json_format

import index_pb2

UPSTREAM = "https://raw.githubusercontent.com/keiyoushi/extensions/repo/index.json"
KEEP = {
    "eu.kanade.tachiyomi.extension.all.mangadex",
    "eu.kanade.tachiyomi.extension.en.templescan",
    "eu.kanade.tachiyomi.extension.es.mangamx",
    "eu.kanade.tachiyomi.extension.es.zonatmoto",
    "eu.kanade.tachiyomi.extension.es.yupmanga",
    "eu.kanade.tachiyomi.extension.es.emperorscan",
    "eu.kanade.tachiyomi.extension.es.dragontranslationorg",
    "eu.kanade.tachiyomi.extension.es.manhwaweb",
}

root = Path(__file__).resolve().parents[1]
with urllib.request.urlopen(UPSTREAM, timeout=60) as r:
    data = json.load(r)

selected = [e for e in data["extensionList"]["extensions"] if e["packageName"] in KEEP]
missing = KEEP - {e["packageName"] for e in selected}
if missing:
    raise SystemExit("Missing upstream packages: " + ", ".join(sorted(missing)))
selected.sort(key=lambda e: e["packageName"])

index = {
    "name": "MangaSync",
    "badgeLabel": "MS",
    "signingKey": data["signingKey"],
    "extensionList": {"extensions": selected},
}
(root / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(root / "index.min.json").write_text(json.dumps(index, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")

msg = json_format.Parse(json.dumps(index), index_pb2.Index())
(root / "index.pb").write_bytes(gzip.compress(msg.SerializeToString(deterministic=True), mtime=0))

assets = {}
for ext in selected:
    assets[ext["packageName"]] = {"apk": {"url": ext["resources"]["apkUrl"]}, "jar": {"url": ext["resources"].get("jarUrl", "")}}
(root / "release-assets.json").write_text(json.dumps(assets, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

lines = ["<!doctype html>", "<html><body><pre>"]
for ext in selected:
    lines.append(f'<a href="{ext["resources"]["apkUrl"]}">Tachiyomi: {ext["name"]}</a>')
lines += ["</pre></body></html>"]
(root / "index.html").write_text("\n".join(lines) + "\n", encoding="utf-8")

print("Synced", len(selected), "extensions")
for ext in selected:
    print("-", ext["name"], ext["versionName"], ext["packageName"])
