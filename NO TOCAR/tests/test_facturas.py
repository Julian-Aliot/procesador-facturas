"""Pruebas sintéticas: no leen ni modifican facturas del usuario."""
import importlib.util
import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("facturas", ROOT / "NO TOCAR/skills/procesador-facturas/scripts/facturas.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
CFG = json.loads((ROOT / "NO TOCAR/config/config.json").read_text(encoding="utf-8"))


def factura():
    return {"archivo_original": "a.pdf", "tipo_documento": "factura", "proveedor": "Proveedor de prueba",
            "nif_proveedor": "B12345678", "numero_factura": "F/001", "fecha": "2026-10-15",
            "base_imponible": 150, "importe_iva": 26, "total": 176, "moneda": "EUR",
            "impuestos": [{"base": 100, "tipo": 21, "cuota": 21}, {"base": 50, "tipo": 10, "cuota": 5}],
            "ajustes": [], "motivos_revision": [],
            "evidencias": {k: {"pagina": 1, "texto": "Dato sintético " + k} for k in m.EVIDENCIAS}}


class Validaciones(unittest.TestCase):
    def validar(self, f):
        return m.validar_factura(f, CFG, date(2026, 10, 22))

    def test_varios_impuestos_y_retencion(self):
        f = factura()
        self.assertEqual(self.validar(f), [])
        f["ajustes"] = [{"concepto": "Retención", "importe": -15}]
        f["total"] = 161
        self.assertEqual(self.validar(f), [])

    def test_fallo_total_o_desglose(self):
        f = factura()
        f["total"] = 177
        self.assertTrue(any("total" in s for s in self.validar(f)))
        f = factura()
        f["impuestos"][0]["cuota"] = 22
        self.assertTrue(any("desglose" in s for s in self.validar(f)))

    def test_no_confunde_ausente_y_cero(self):
        f = factura()
        f.update(base_imponible=100, importe_iva=0, total=100, impuestos=[{"base": 100, "tipo": 0, "cuota": 0}])
        self.assertEqual(self.validar(f), [])
        f["importe_iva"] = None
        self.assertTrue(self.validar(f))

    def test_evidencia_negativos_fecha(self):
        f = factura()
        f["evidencias"] = {}
        self.assertTrue(any("evidencia" in s for s in self.validar(f)))
        f = factura()
        f["total"] = -176
        self.assertTrue(any("negativos" in s for s in self.validar(f)))
        f = factura()
        f["fecha"] = "2026-02-30"
        self.assertTrue(any("Fecha" in s for s in self.validar(f)))

    def test_nombres_y_csv(self):
        self.assertNotIn("/", m.seguro("F/001"))
        self.assertEqual(m.seguro("CON"), "_CON")
        self.assertTrue(m.celda_csv("=HYPERLINK(1)").startswith("'"))

    def test_salida_exactamente_16_columnas(self):
        f = factura()
        f.update(receptor="Cliente", resumen_concepto="Desarrollo de software", concepto="Software development", fecha_contable=None)
        row = m.fila_salida(f, CFG)
        self.assertEqual(len(m.COLUMNAS_SALIDA), 16)
        self.assertEqual(len(row), 16)
        self.assertEqual(row[0], "Cliente")
        self.assertEqual(row[8], 2026)
        self.assertIsNone(row[9])
        self.assertEqual(row[11], "Desarrollo de software")
        self.assertEqual(row[12], 176)
        self.assertEqual(row[13], 150)
        self.assertEqual(row[14], "21 % / 10 %")
        self.assertNotIn("Estado", m.COLUMNAS_SALIDA)

    def test_porcentajes_y_conceptos_completos(self):
        f = factura()
        f['subconceptos'] = ['Servicio 01-02-2025; 2 horas', 'Otro servicio', 'Otro servicio']
        self.assertEqual(m.fila_salida(f, CFG)[10], '- Servicio 01-02-2025; 2 horas\n- Otro servicio\n- Otro servicio')
        f['impuestos'] = [{'tipo': 0, 'cuota': 0}]
        self.assertEqual(m.fila_salida(f, CFG)[14], '0 %')
        f['impuestos'] = [{'tipo': None, 'literal_tipo': 'EAM', 'cuota': 0}]
        self.assertIsNone(m.fila_salida(f, CFG)[14])

    def test_iva_literal_no_inventa_cero(self):
        f = factura()
        f["impuestos"] = [{"base": 1750, "tipo": None, "literal_tipo": "EAM", "cuota": 0}]
        self.assertEqual(m.iva_visible(f), "EAM: 0,00 EUR")
        f.update(impuestos=[], importe_iva=None, mencion_tributaria="No sujeta a IVA")
        self.assertEqual(m.iva_visible(f), "No sujeta a IVA")
        f["mencion_tributaria"] = None
        self.assertIsNone(m.iva_visible(f))

    def test_inventario_duplicados_originales_e_integridad(self):
        (ROOT / "NO TOCAR/pruebas-temporales").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "NO TOCAR/pruebas-temporales") as folder:
            root = Path(folder).resolve()
            (root / "entrada").mkdir()
            (root / "entrada/a.pdf").write_bytes(b"documento sintetico")
            (root / "entrada/b.pdf").write_bytes(b"documento sintetico")
            original = m.sha256(root / "entrada/a.pdf")
            result = m.inventariar(root, CFG)
            run = Path(result["lote"])
            data = m.leer(run / "extraccion.json")
            for item in data["facturas"]:
                f = factura()
                f.update(archivo_original=item["archivo_original"], sha256=item["sha256"])
                item.update(f)
            (run / "extraccion.json").write_text(json.dumps(data), encoding="utf-8")
            csv_cfg = dict(CFG, formato_salida="csv")
            report = m.validar(root, csv_cfg, str(run))
            with Path(report["resumen"]).open(encoding="utf-8-sig", newline="") as stream:
                exported = list(csv.reader(stream, delimiter=";"))
            self.assertEqual(exported[0], m.COLUMNAS_SALIDA)
            self.assertEqual(len(exported), 3)
            self.assertTrue(all(len(row) == 16 for row in exported))
            self.assertEqual(report["recuentos"]["duplicado"], 1)
            self.assertEqual(m.sha256(root / "entrada/a.pdf"), original)
            (root / "entrada/a.pdf").write_bytes(b"contenido cambiado")
            report2 = m.validar(root, csv_cfg, str(run))
            self.assertEqual(report2["recuentos"]["error"], 1)
            self.assertNotEqual(report["informe"], report2["informe"])
            data["facturas"].pop()
            (run / "extraccion.json").write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                m.validar(root, csv_cfg, str(run))

    def test_regresion_adobe_numeros_distintos_mismo_importe(self):
        a = dict(factura(), numero_factura='IEE2025000177923', total=21.84)
        b = dict(factura(), numero_factura='IEE2025001474101', total=21.84)
        self.assertNotEqual(m.identidad_factura(a),m.identidad_factura(b))
        for number in ['IEE2025000177924','IEE20250001779230','IEE-2025000177923','iee2025000177923','IEE2025000177923/1']:
            self.assertNotEqual(m.identidad_factura(a),m.identidad_factura(dict(a,numero_factura=number)))
        with self.assertRaisesRegex(ValueError,'sin otra factura'):
            m.marcas_excel([{'datos':a},{'datos':b,'marca':'DUPLICADA'}])
        marks=m.marcas_excel([{'datos':a},{'datos':dict(a),'marca':'DUPLICADA'},
                             {'datos':b},{'datos':dict(b),'marca':'DUPLICADA'}])
        self.assertIn('fila 6',marks[1]['texto'])
        self.assertIn('fila 8',marks[3]['texto'])

    def test_excel_real_tipos_orden_y_sin_sobrescritura(self):
        from openpyxl import load_workbook
        from datetime import datetime
        (ROOT / "NO TOCAR/pruebas-temporales").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "NO TOCAR/pruebas-temporales") as folder:
            run = Path(folder).resolve()
            f1 = factura()
            f1.update(numero_factura="001", fecha="2026-10-15", resumen_concepto="Resumen en español")
            f2 = factura()
            f2.update(numero_factura="=1+1", fecha="2026-09-01", moneda="USD")
            results = [{"datos":f1}, {"datos":f2}]
            p = m.generar_excel(run, "prueba", results, CFG)
            w = load_workbook(p)
            self.assertEqual(w.sheetnames, ["Facturas"])
            s = w["Facturas"]
            self.assertEqual(s.max_column, 16)
            self.assertEqual([c.value for c in s[5]], m.COLUMNAS_SALIDA)
            self.assertIsInstance(s["H6"].value, datetime)
            self.assertEqual(s["H6"].value.month, 9)
            self.assertNotEqual(s["G6"].data_type, "f")
            self.assertEqual(s["G7"].value, "001")
            self.assertEqual(s["M6"].value, 176)
            self.assertIn('USD', s["M6"].number_format)
            self.assertIn('EUR', s["N7"].number_format)
            self.assertIsNone(s["J6"].value)
            w.close()
            with self.assertRaises(FileExistsError):
                m.generar_excel(run, "prueba", results, CFG)


if __name__ == "__main__":
    unittest.main()
