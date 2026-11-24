"""Pruebas de acumulación, copias, recuentos y recuperación con datos sintéticos."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('clientes',ROOT / 'NO TOCAR/skills/procesador-facturas/scripts/clientes.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
CFG = json.loads((ROOT / 'NO TOCAR/config/config.json').read_text(encoding='utf-8'))


class Clientes(unittest.TestCase):
    def setUp(self):
        (ROOT / 'NO TOCAR/pruebas-temporales').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'NO TOCAR/pruebas-temporales')
        self.root = Path(self.temp.name).resolve()
        (self.root / 'entrada/Cliente A/mes').mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def archivo(self, name, data=b'factura sintetica', cliente='Cliente A'):
        p = self.root / 'entrada' / cliente / name
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)
        return p

    def preparar(self, cliente='Cliente A'):
        r = c.preparar(self.root,CFG,cliente)
        if r.get('lote'):
            p = Path(r['lote']) / 'extraccion.json'
            obj = c.base.leer(p)
            for f in obj['facturas']:
                if 'ilegible' in f['archivo_original']:
                    f['motivos_revision'] = ['Documento ilegible de prueba']
                    continue
                f.update(tipo_documento='factura',proveedor='Proveedor',nif_proveedor='B12345678',
                         receptor=cliente,numero_factura='F-001',fecha='2026-10-15',
                         concepto='Servicio',resumen_concepto='Servicio de prueba',
                         base_imponible=100,importe_iva=21,total=121,moneda='EUR',
                         impuestos=[{'base':100,'tipo':21,'cuota':21}],ajustes=[])
                f['evidencias'] = {k:{'pagina':1,'texto':'Dato sintético'} for k in c.base.EVIDENCIAS}
            p.write_text(json.dumps(obj),encoding='utf-8')
        return r

    def completar(self, prepared, cliente='Cliente A'):
        return c.completar(self.root,CFG,cliente,prepared['lote'])

    def test_dos_tandas_repeticion_duplicados_e_ilegibles(self):
        original = self.archivo('mes/a.pdf')
        self.archivo('copia.pdf')
        self.archivo('ilegible.pdf',b'documento ilegible')
        before = c.base.sha256(original)
        first = self.completar(self.preparar())
        self.assertEqual((first['entrada'],first['salida'],first['filas_excel']),(3,3,3))
        self.assertEqual(first['duplicadas'],1)
        wb = load_workbook(first['excel'])
        sheet = wb['Facturas']
        notes = [sheet[f'F{n}'].comment.text for n in range(6,9)]
        self.assertEqual(sum('DUPLICADA' in note for note in notes),1)
        self.assertTrue(any('ilegible' in note for note in notes))
        self.assertTrue(all(sheet[f'A{n}'].fill.fgColor.rgb.endswith('FFFFFF') for n in range(6,9)))
        wb.close()
        self.assertEqual(c.base.sha256(original),before)
        xhash = c.base.sha256(Path(first['excel']))
        repeat = self.preparar()
        self.assertEqual(repeat['nuevos'],0)
        self.assertEqual(c.base.sha256(Path(first['excel'])),xhash)
        self.archivo('abril/otra_copia.pdf')
        second = self.completar(self.preparar())
        self.assertEqual(second['excel'],first['excel'])
        self.assertEqual((second['entrada'],second['salida'],second['filas_excel']),(4,4,4))
        self.assertEqual(second['duplicadas'],2)
        self.assertEqual(len(list(Path(second['carpeta_facturas']).glob('*.pdf'))),4)
        self.assertEqual(self.preparar()['nuevos'],0)

    def test_actualizar_conserva_archivos_y_filas(self):
        original = self.archivo('a.pdf')
        self.archivo('b.pdf')
        first = self.completar(self.preparar())
        before = {p.name:c.base.sha256(p) for p in Path(first['carpeta_facturas']).iterdir()}
        correction = self.root/'correcciones.json'
        correction.write_text(json.dumps({'facturas':[{'archivo_original':'a.pdf','sha256':c.base.sha256(original),'subconceptos':['Línea uno','Línea dos']}]}),encoding='utf-8')
        updated = c.actualizar(self.root,CFG,'Cliente A',str(correction))
        self.assertEqual((updated['entrada'],updated['salida'],updated['filas_excel']),(2,2,2))
        self.assertEqual(before,{p.name:c.base.sha256(p) for p in Path(first['carpeta_facturas']).iterdir()})
        wb=load_workbook(updated['excel']); sh=wb['Facturas']
        self.assertEqual(sh['J6'].value,'- Línea uno\n- Línea dos')
        self.assertEqual(sh['Q6'].value,'21 %')
        self.assertEqual(sh['R6'].value,'Abrir factura')
        self.assertTrue(sh['R6'].hyperlink.target.startswith('facturas/'))
        self.assertTrue(sh['A6'].fill.fgColor.rgb.endswith('FFFFFF'))
        self.assertTrue(sh['A7'].fill.fgColor.rgb.endswith('FFFFFF'))
        wb.close()
        correction.write_text(json.dumps({'facturas':[{'archivo_original':'a.pdf','sha256':'incorrecto','subconceptos':['Incorrecto']}]}),encoding='utf-8')
        with self.assertRaises(ValueError):
            c.actualizar(self.root,CFG,'Cliente A',str(correction))

    def test_reconcilia_salida_vacia_parcial_y_nuevos(self):
        self.archivo('a.pdf')
        self.archivo('b.pdf', b'otra factura')
        first = self.completar(self.preparar())
        folder = Path(first['carpeta_facturas'])
        expected = {p.name:c.base.sha256(p) for p in folder.iterdir()}
        for p in folder.iterdir():
            p.unlink()
        folder.rmdir()
        Path(first['excel']).unlink()
        restored = self.preparar()
        self.assertEqual((restored['nuevos'],restored['copias_restauradas'],restored['filas_excel']),(0,2,2))
        self.assertEqual(expected,{p.name:c.base.sha256(p) for p in folder.iterdir()})
        next(folder.iterdir()).unlink()
        self.archivo('c.pdf',b'nueva factura')
        pending = self.preparar()
        self.assertEqual((pending['nuevos'],pending['copias_restauradas']),(1,1))
        final = self.completar(pending)
        self.assertEqual((final['entrada'],final['salida'],final['filas_excel']),(3,3,3))
        digest = c.base.sha256(Path(final['excel']))
        self.assertEqual(self.preparar()['copias_restauradas'],0)
        self.assertEqual(c.base.sha256(Path(final['excel'])),digest)
        next(folder.iterdir()).write_bytes(b'copia editada')
        with self.assertRaises(ValueError):
            self.preparar()

    def test_duplicados_solo_numero_y_total(self):
        from copy import deepcopy
        def record(name,number,total,sha='mismo-hash'):
            return {'id':name,'archivo_original':name+'.pdf','sha256':sha,
                    'datos':{'numero_factura':number,'total':total,'proveedor':'Proveedor','nif_proveedor':'B1'}}
        items=[record('a','F-1',100),record('b','F-1',101),record('c','F-2',100),
               record('d','F-1',100.0,'otro-hash'),record('e',None,100),record('f',None,100),
               record('g','F-1',None),record('h','F-1',None)]
        items[3]['datos']['nif_proveedor']='OTRO'
        ledger={'archivos':[]}
        c.clasificar(ledger,items,CFG)
        self.assertEqual([i['marca']=='DUPLICADA' for i in items],[False,False,False,True,False,False,False,False])
        ledger['archivos']=items
        items[1]['marca']='DUPLICADA'
        c.clasificar(ledger,[],CFG)
        self.assertNotEqual(items[1]['marca'],'DUPLICADA')

    def test_impide_asignar_carpeta_de_otro_cliente(self):
        self.archivo('a.pdf',cliente='Cliente B')
        for entrada in ['entrada','entrada/Cliente B','entrada/Cliente A/mes']:
            with self.assertRaisesRegex(ValueError,'exclusivamente'):
                c.preparar(self.root,CFG,'Cliente A',entrada)
        self.assertFalse((self.root/'resultados').exists())

    def test_rechaza_extraccion_con_cliente_o_lote_cambiados(self):
        self.archivo('a.pdf')
        prepared=self.preparar()
        p=Path(prepared['lote'])/'extraccion.json'
        original=c.base.leer(p)
        for key,value in [('cliente','Cliente B'),('lote_id','otro'),('entrada',str(self.root/'entrada/Cliente B'))]:
            changed=dict(original);changed[key]=value
            p.write_text(json.dumps(changed),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'vinculada'):
                self.completar(prepared)
        p.write_text(json.dumps(original),encoding='utf-8')
        original['facturas'][0]['cliente_origen']='Cliente B'
        p.write_text(json.dumps(original),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'otro cliente'):
            self.completar(prepared)
        self.assertFalse((self.root/'resultados').exists())

    def test_clientes_independientes(self):
        self.archivo('a.pdf')
        self.archivo('a.pdf',cliente='Cliente B')
        a = self.completar(self.preparar())
        excel_a_hash = c.base.sha256(Path(a['excel']))
        control_a = c.rutas(self.root,CFG,'Cliente A')[2]
        registro_a_hash = c.base.sha256(control_a/'registro.json')
        b = self.completar(self.preparar('Cliente B'),'Cliente B')
        self.assertEqual(c.base.sha256(Path(a['excel'])),excel_a_hash)
        self.assertEqual(c.base.sha256(control_a/'registro.json'),registro_a_hash)
        self.assertNotEqual(a['excel'],b['excel'])
        self.assertEqual(a['duplicadas']+b['duplicadas'],0)
        self.assertEqual(c.listar(self.root,CFG)['clientes'][0]['facturas_entrada'],1)

    def test_recupera_interrupcion_sin_repetir_copias(self):
        self.archivo('a.pdf')
        prepared = self.preparar()
        original_replace = c.os.replace
        def fail_excel(src,dst):
            if Path(dst).name == 'Facturas_Cliente_A.xlsx':
                raise PermissionError('Excel abierto simulado')
            return original_replace(src,dst)
        with patch.object(c.os,'replace',side_effect=fail_excel):
            with self.assertRaises(PermissionError):
                self.completar(prepared)
        recovered = self.preparar()
        self.assertEqual(recovered['nuevos'],0)
        self.assertEqual((recovered['entrada'],recovered['salida'],recovered['filas_excel']),(1,1,1))
        self.assertEqual(len(list((self.root/'resultados/Cliente A/facturas').glob('*'))),1)

    def test_conserva_ediciones_manuales(self):
        self.archivo('a.pdf')
        result = self.completar(self.preparar())
        excel = Path(result['excel'])
        excel.write_bytes(excel.read_bytes()+b'cambio manual simulado')
        before = c.base.sha256(excel)
        self.archivo('b.pdf',b'otra factura')
        with self.assertRaisesRegex(ValueError,'ediciones manuales'):
            self.preparar()
        self.assertEqual(c.base.sha256(excel),before)

    def test_no_pierde_originales_eliminados_o_modificados(self):
        source = self.archivo('a.pdf')
        result = self.completar(self.preparar())
        source.write_bytes(b'modificado')
        with self.assertRaisesRegex(ValueError,'modificado un original'):
            self.preparar()
        source.unlink()
        with self.assertRaisesRegex(ValueError,'Falta un original'):
            self.preparar()
        self.assertEqual(len(list(Path(result['carpeta_facturas']).glob('*'))),1)

    def test_bloquea_entrada_cambiada_antes_de_completar(self):
        self.archivo('a.pdf')
        prepared = self.preparar()
        self.archivo('b.pdf',b'nuevo')
        with self.assertRaisesRegex(ValueError,'entrada ha cambiado'):
            self.completar(prepared)
        self.assertFalse((self.root/'resultados/Cliente A').exists())

    def test_migra_libro_antiguo_conservando_copias(self):
        self.archivo('a.pdf')
        first = self.completar(self.preparar())
        excel = Path(first['excel'])
        wb = load_workbook(excel); sh = wb['Facturas']
        sh.delete_cols(19); sh.delete_cols(15,2); sh.insert_cols(4); sh.cell(5,4,"EXT O NAC"); sh.delete_cols(12)
        table = sh.tables['RegistroFacturas']
        table.ref = 'A5:P6'
        from openpyxl.worksheet.table import TableColumn
        table.tableColumns = [TableColumn(id=i+1,name=sh.cell(5,i+1).value) for i in range(16)]
        if table.autoFilter: table.autoFilter.ref = table.ref
        wb.save(excel); wb.close()
        # Estado sintético: simula el hash guardado antes de migrar el formato.
        ledger_path = next((self.root/'NO TOCAR/control').glob('*/registro.json'))
        ledger = json.loads(ledger_path.read_text())
        ledger['excel_sha256'] = c.base.sha256(excel)
        ledger_path.write_text(json.dumps(ledger))
        self.assertEqual(c.filas_excel(excel),1)
        updated = c.actualizar(self.root,CFG,'Cliente A')
        wb = load_workbook(updated['excel'])
        self.assertEqual(wb['Facturas'].max_column,19)
        self.assertIsNotNone(wb['Facturas']['R6'].hyperlink)
        wb.close()

    def test_bloqueo_y_otros_archivos(self):
        self.archivo('a.pdf')
        self.archivo('leeme.txt',b'no es una factura')
        prepared = self.preparar()
        self.assertEqual(prepared['omitidos'],['leeme.txt'])
        _,_,control = c.rutas(self.root,CFG,'Cliente A')
        lock = control/'escritor.lock'
        lock.write_text('bloqueo simulado',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'bloqueo de escritor'):
            self.preparar()
        self.assertTrue(lock.exists())
        lock.unlink()


if __name__ == '__main__':
    unittest.main()
