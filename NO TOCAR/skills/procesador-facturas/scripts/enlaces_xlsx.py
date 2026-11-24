"""Hipervínculos OOXML nativos: complemento de la exportación artifact-tool.

El motor no calcula HYPERLINK; conservar el texto y añadir relaciones evita
fórmulas con valores de error en caché. No modifica celdas ni estilos.
"""
import os
from pathlib import Path
from urllib.parse import quote
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

MAIN='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG='http://schemas.openxmlformats.org/package/2006/relationships'

def incorporar_enlaces(path, archivos):
    path=Path(path)
    with ZipFile(path) as z:
        contents={i.filename:z.read(i.filename) for i in z.infolist()}
    workbook = ET.fromstring(contents['xl/workbook.xml'])
    names = workbook.find('{'+MAIN+'}definedNames')
    if names is None:
        names = ET.Element('{'+MAIN+'}definedNames')
        later = {'calcPr', 'oleSize', 'customWorkbookViews', 'pivotCaches', 'smartTagPr', 'smartTagTypes', 'webPublishing', 'fileRecoveryPr', 'webPublishObjects', 'extLst'}
        position = next((i for i, child in enumerate(workbook) if child.tag.rsplit('}',1)[-1] in later), len(workbook))
        workbook.insert(position, names)
    area = next((n for n in names if n.get('name') == '_xlnm.Print_Area'), None)
    if area is None:
        area = ET.SubElement(names, '{'+MAIN+'}definedName', {'name':'_xlnm.Print_Area', 'localSheetId':'0'})
    area.text = "'Facturas'!$A$1:$S$" + str(max(6, len(archivos) + 5))
    contents['xl/workbook.xml'] = ET.tostring(workbook, encoding='utf-8', xml_declaration=True)
    sheetname='xl/worksheets/sheet1.xml'
    relname='xl/worksheets/_rels/sheet1.xml.rels'
    sheet=ET.fromstring(contents[sheetname])
    rels=ET.fromstring(contents[relname]) if relname in contents else ET.Element('{'+PKG+'}Relationships')
    links=ET.Element('{'+MAIN+'}hyperlinks')
    used={r.attrib['Id'] for r in rels}
    for row,name in enumerate(archivos,6):
        if not name:
            continue
        if '/' in name or '\\' in name or name in {'.','..'}:
            raise ValueError('Nombre de copia no válido para enlace')
        rid='factura'+str(row)
        while rid in used:
            rid+='x'
        used.add(rid)
        ET.SubElement(rels,'{'+PKG+'}Relationship',{'Id':rid,'Type':REL+'/hyperlink','Target':quote('facturas/'+name,safe='/'),'TargetMode':'External'})
        ET.SubElement(links,'{'+MAIN+'}hyperlink',{'ref':'R'+str(row),'{'+REL+'}id':rid,'display':'Abrir factura'})
    old=sheet.find('{'+MAIN+'}hyperlinks')
    if old is not None:
        sheet.remove(old)
    after={'printOptions','pageMargins','pageSetup','headerFooter','rowBreaks','colBreaks','customProperties','cellWatches','ignoredErrors','smartTags','drawing','legacyDrawing','legacyDrawingHF','picture','oleObjects','controls','webPublishItems','tableParts','extLst'}
    index=next((i for i,c in enumerate(sheet) if c.tag.rsplit('}',1)[-1] in after),len(sheet))
    sheet.insert(index,links)
    contents[sheetname]=ET.tostring(sheet,encoding='utf-8',xml_declaration=True)
    contents[relname]=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
    temp=path.with_suffix('.enlaces.tmp')
    try:
        with ZipFile(temp,'x',ZIP_DEFLATED) as z:
            for name,data in contents.items():
                z.writestr(name,data)
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)
