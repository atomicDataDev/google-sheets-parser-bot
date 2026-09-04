import io
import hashlib
import zipfile
import xml.etree.ElementTree as ET

class ExcelParser:
    NS = {
        'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'rels': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }

    @classmethod
    def get_sheet_hashes(cls, file_path: str, target_sheets: list) -> tuple[str, dict]:

        sheet_hashes ={}

        with zipfile.ZipFile(file_path) as z:
            rels_xml = z.read('xl/_rels/workbook.xml.rels')
            rels_root = ET.fromstring(rels_xml)
            rId_to_target = {
                rel.attrib['Id']: f"xl/{rel.attrib['Target']}" 
                for rel in rels_root.findall('rels:Relationship', cls.NS)
            }

            workbook_xml = z.read('xl/workbook.xml')
            workbook_root = ET.fromstring(workbook_xml)

            for sheet in workbook_root.findall('.//main:sheet', cls.NS):
                sheet_name = sheet.attrib['name']
                rid = sheet.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                
                if target_sheets and sheet_name not in target_sheets:
                    continue
                    
                target_path = rId_to_target.get(rid)
                if target_path and target_path in z.namelist():
                    xml_content = z.read(target_path)
                    sheet_md5 = hashlib.md5(xml_content).hexdigest()
                    sheet_hashes[sheet_name] = sheet_md5

        combined = "".join(hash_val for _, hash_val in sorted(sheet_hashes.items()))
        overall_hash = hashlib.md5(combined.encode('utf-8')).hexdigest() if combined else "empty"
        
        return overall_hash, sheet_hashes