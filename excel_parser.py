"""
Excel / OpenXML parser module.

Provides content-based hashing of .xlsx files that is stable across
re-exports. Only actual cell data and drawing positions are included in the
hash; volatile metadata such as timestamps and style identifiers are ignored.
"""
import hashlib
import posixpath
import zipfile
import xml.etree.ElementTree as ET


class ExcelParser:
    """
    Parser for .xlsx files (OpenXML format) that computes deterministic hashes.

    Google Sheets re-exports change internal ZIP metadata even when the
    spreadsheet content is identical. This class extracts only the stable
    semantic content (cell coordinates, values, formulas, and drawing anchor
    positions) to produce a hash that changes only when the data changes.
    """

    NS: dict[str, str] = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rels": "http://schemas.openxmlformats.org/package/2006/relationships",
    }

    @staticmethod
    def _extract_stable_cells(xml_bytes: bytes) -> str:
        """
        Extract a sorted, deterministic string of cell coordinates and values.

        Reads only the cell reference (``r``), numeric/string value (``v``),
        formula (``f``), and inline string text (``is``). Style indices and
        other volatile attributes are intentionally skipped.

        :param xml_bytes: Raw XML bytes of a worksheet (``xl/worksheets/sheetN.xml``).
        :type xml_bytes: bytes
        :return: A newline-joined, lexicographically sorted string of cell records.
        :rtype: str
        """
        if not xml_bytes:
            return ""

        root = ET.fromstring(xml_bytes)
        cells: list[str] = []

        for c in root.iter():
            if c.tag.split("}")[-1] != "c":
                continue

            ref = c.attrib.get("r", "")
            value, formula = "", ""

            for child in c:
                ctag = child.tag.split("}")[-1]
                if ctag == "v":
                    value = child.text or ""
                elif ctag == "f":
                    formula = child.text or ""
                elif ctag == "is":
                    # Inline rich-text string — concatenate all <t> runs.
                    value += "".join(
                        t.text or ""
                        for t in child.iter()
                        if t.tag.split("}")[-1] == "t"
                    )

            if value or formula:
                cells.append(f"{ref}|v={value}|f={formula}")

        return "\n".join(sorted(cells))

    @staticmethod
    def _extract_stable_drawings(xml_bytes: bytes) -> str:
        """
        Extract a sorted, deterministic string of drawing anchor coordinates.

        Only the positional attributes (``col``, ``row``, ``colOff``,
        ``rowOff``) of each anchor element are captured so that image
        repositioning is detected, while unrelated drawing metadata is ignored.

        :param xml_bytes: Raw XML bytes of a drawing file
            (``xl/drawings/drawingN.xml``).
        :type xml_bytes: bytes
        :return: A newline-joined, lexicographically sorted string of anchor
            coordinate records.
        :rtype: str
        """
        if not xml_bytes:
            return ""

        root = ET.fromstring(xml_bytes)
        anchors: list[str] = []

        for anchor in root.iter():
            tag = anchor.tag.split("}")[-1]
            if tag not in ("twoCellAnchor", "oneCellAnchor"):
                continue

            coords: list[str] = []
            for child in anchor.iter():
                ctag = child.tag.split("}")[-1]
                if ctag in ("col", "row", "colOff", "rowOff"):
                    coords.append(f"{ctag}:{child.text}")

            if coords:
                anchors.append(",".join(coords))

        return "\n".join(sorted(anchors))

    @classmethod
    def get_sheet_hashes(
        cls, file_path: str, target_sheets: list[str]
    ) -> tuple[str, dict[str, str]]:
        """
        Compute per-sheet and combined MD5 hashes for an .xlsx file.

        For each sheet (filtered by ``target_sheets`` when provided), builds a
        canonical string from stable cell data and drawing positions, then
        hashes it. The overall hash is an MD5 of all per-sheet hashes
        concatenated in alphabetical sheet-name order.

        :param file_path: Path to the local .xlsx file.
        :type file_path: str
        :param target_sheets: Whitelist of sheet names to include. Pass an
            empty list to include all sheets.
        :type target_sheets: list[str]
        :return: A tuple of ``(overall_hash, per_sheet_hashes)`` where
            ``overall_hash`` is a single MD5 hex string and ``per_sheet_hashes``
            maps sheet names to their individual MD5 hex strings.
        :rtype: tuple[str, dict[str, str]]
        """
        sheet_hashes: dict[str, str] = {}

        with zipfile.ZipFile(file_path) as z:
            # Build a mapping from workbook relationship IDs to sheet XML paths.
            rels_xml = z.read("xl/_rels/workbook.xml.rels")
            rels_root = ET.fromstring(rels_xml)
            workbook_rid_to_target: dict[str, str] = {
                rel.attrib["Id"]: f"xl/{rel.attrib['Target']}"
                for rel in rels_root.findall("rels:Relationship", cls.NS)
            }

            workbook_xml = z.read("xl/workbook.xml")
            workbook_root = ET.fromstring(workbook_xml)

            for sheet in workbook_root.findall(".//main:sheet", cls.NS):
                sheet_name = sheet.attrib["name"]
                rid = sheet.attrib.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                )

                if target_sheets and sheet_name not in target_sheets:
                    continue

                target_path = workbook_rid_to_target.get(rid)
                if not target_path or target_path not in z.namelist():
                    continue

                # Step 1: Extract stable cell content from the sheet XML.
                xml_content = z.read(target_path)
                stable_cells = cls._extract_stable_cells(xml_content)

                # Step 2: Locate the associated drawing relationship, if any.
                drawing_xml_content = b""
                sheet_root = ET.fromstring(xml_content)

                drawing_rid: str | None = None
                for child in sheet_root:
                    if child.tag.endswith("}drawing"):
                        for k, v in child.attrib.items():
                            if k.endswith("}id"):
                                drawing_rid = v
                                break
                        break

                if drawing_rid:
                    sheet_dir = posixpath.dirname(target_path)
                    sheet_basename = posixpath.basename(target_path)
                    rels_path = posixpath.join(
                        sheet_dir, "_rels", f"{sheet_basename}.rels"
                    )

                    if rels_path in z.namelist():
                        s_rels_root = ET.fromstring(z.read(rels_path))
                        for rel in s_rels_root.findall("rels:Relationship", cls.NS):
                            if rel.attrib["Id"] == drawing_rid:
                                drawing_target = rel.attrib["Target"]
                                drawing_full_path = posixpath.normpath(
                                    posixpath.join(sheet_dir, drawing_target)
                                )
                                if drawing_full_path in z.namelist():
                                    drawing_xml_content = z.read(drawing_full_path)
                                break

                # Step 3: Extract stable drawing anchor positions.
                stable_drawings = cls._extract_stable_drawings(drawing_xml_content)

                # Step 4: Combine and hash the canonical content string.
                final_string = f"CELLS:\n{stable_cells}\nDRAWINGS:\n{stable_drawings}"
                sheet_hashes[sheet_name] = hashlib.md5(
                    final_string.encode("utf-8")
                ).hexdigest()

        combined = "".join(hash_val for _, hash_val in sorted(sheet_hashes.items()))
        overall_hash = (
            hashlib.md5(combined.encode("utf-8")).hexdigest() if combined else "empty"
        )

        return overall_hash, sheet_hashes
