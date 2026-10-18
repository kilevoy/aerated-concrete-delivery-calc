"""Пересчёт матрицы дорожных расстояний заводы → населённые пункты через OSRM.

Координаты берутся из index.html (массивы SUP и PLACES).
Результат: data/roads.json — {id_завода: {пункт: [км, часы]}}.
Скрипт также обновляет константу ROADS в index.html.
"""
import json, re, urllib.request, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
s = (root / "index.html").read_text(encoding="utf-8")
sup = re.findall(r"\{ id:'(\w+)', name:'[^']*', sub:'[^']*', lat:([\d.]+), lon:([\d.]+)", s)
block = s.split("const PLACES = [")[1].split("];")[0]
places = re.findall(r"\['([^']+)',\s*([\d.]+),\s*([\d.]+)\]", block)

coords = ";".join(f"{lo},{la}" for _, la, lo in sup) + ";" + ";".join(f"{lo},{la}" for _, la, lo in places)
n = len(sup)
url = (f"https://router.project-osrm.org/table/v1/driving/{coords}"
       f"?sources={';'.join(map(str, range(n)))}"
       f"&destinations={';'.join(map(str, range(n, n + len(places))))}"
       "&annotations=distance,duration")
d = json.load(urllib.request.urlopen(url, timeout=60))
assert d["code"] == "Ok", d
out = {}
for i, (sid, _, _) in enumerate(sup):
    out[sid] = {}
    for j, (name, _, _) in enumerate(places):
        km, sec = d["distances"][i][j], d["durations"][i][j]
        out[sid][name] = [round(km / 1000) if km is not None else None, round(sec / 3600, 1) if sec is not None else None]
(root / "data" / "roads.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
s = re.sub(r"const ROADS = \{.*?\};\n", lambda m: "const ROADS = " + json.dumps(out, ensure_ascii=False) + ";\n", s, count=1, flags=re.S)
(root / "index.html").write_text(s, encoding="utf-8")
print(f"{n} площадок × {len(places)} пунктов → data/roads.json")
