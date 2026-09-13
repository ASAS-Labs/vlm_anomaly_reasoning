"""One-off importer: taxonomy .docx -> taxonomy.json (stdlib only; docx may be open in Word).

Usage: uv run python data/taxonomy_validation/import_docx.py
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCX = HERE.parent.parent / "anomaly definition framework" / "semantic_anomaly_taxonomy_framework.docx"
OUT = HERE / "taxonomy.json"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
RELS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

FIELDS = ["object", "nominal_context", "ood_context", "normal_action", "anomalous_action", "example"]
HEADER = [
    "#",
    "Object in Driving Scene",
    "Nominal Context",
    "OOD Context",
    "Normal Action in OOD",
    "Anomalous Action in OOD",
    "Example",
]


def cell_text(cell: ET.Element) -> str:
    return "".join(t.text or "" for t in cell.iter(W + "t")).strip()


def cell_url(cell: ET.Element, rels: dict[str, str]) -> str | None:
    link = cell.find(".//" + W + "hyperlink")
    return rels.get(link.get(R + "id"), None) if link is not None else None


def heading_text(par: ET.Element) -> str | None:
    style = par.find(W + "pPr/" + W + "pStyle")
    if style is None or not style.get(W + "val", "").startswith("Heading2"):
        return None
    return cell_text(par)


def main() -> None:
    with zipfile.ZipFile(DOCX) as z:
        rels_root = ET.fromstring(z.read("word/_rels/document.xml.rels"))
        body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    rels = {
        r.get("Id"): r.get("Target")
        for r in rels_root.iter(RELS + "Relationship")
        if r.get("TargetMode") == "External"
    }

    rows: list[dict] = []
    heading: str | None = None
    table_idx = 0
    for el in body:
        if el.tag == W + "p":
            heading = heading_text(el) or heading
            continue
        if el.tag != W + "tbl":
            continue
        table_idx += 1
        if table_idx == 1:  # worked example, not part of the taxonomy
            continue
        section = "seed" if table_idx == 2 else "extension"
        trs = el.findall(W + "tr")
        header = [cell_text(c) for c in trs[0].findall(W + "tc")]
        expected = HEADER + (["Tag · Source"] if section == "extension" else [])
        assert header == expected, (table_idx, header)
        for tr in trs[1:]:
            cells = tr.findall(W + "tc")
            texts = [cell_text(c) for c in cells]
            row = {"id": int(texts[0]), "section": section, "category": heading if section == "extension" else None}
            row.update(dict(zip(FIELDS, texts[1:7])))
            if section == "extension":
                tag, _, note = texts[7].partition("·")
                row["tag"] = tag.strip()
                row["source_note"] = note.strip() or None
                row["source_url"] = cell_url(cells[7], rels)
            else:
                row.update({"tag": None, "source_note": None, "source_url": None})
            rows.append(row)

    seed = [r for r in rows if r["section"] == "seed"]
    ext = [r for r in rows if r["section"] == "extension"]
    assert [r["id"] for r in rows] == list(range(1, 113)), "ids not contiguous 1..112"
    assert len(seed) == 12 and len(ext) == 100, (len(seed), len(ext))
    tags = [r["tag"] for r in ext]
    assert tags.count("REAL") == 42 and tags.count("SYNTHETIC") == 58, (tags.count("REAL"), tags.count("SYNTHETIC"))
    assert sum(1 for r in ext if r["source_url"]) == 35, "expected 35 hyperlinked sources"
    assert all(r["category"] for r in ext) and all(all(r[f] for f in FIELDS) for r in rows)

    OUT.write_text(json.dumps({"source": str(DOCX.relative_to(HERE.parent.parent)), "rows": rows}, ensure_ascii=False, indent=1))
    print(f"wrote {OUT.name}: {len(seed)} seed + {len(ext)} extension rows, 42 REAL / 58 SYNTHETIC, 35 URLs", file=sys.stderr)


if __name__ == "__main__":
    main()
