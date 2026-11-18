"""Envíos independientes: mismo cliente no implica acumulación."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'NO TOCAR/skills/procesador-facturas/scripts'))
import envios

class EnviosIndependientes(unittest.TestCase):
    def test_mismo_cliente_dos_envios_no_acumulan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'proyecto';source=Path(tmp)/'seleccion';source.mkdir()
            (source/'uno.pdf').write_bytes(b'factura sintetica')
            (source/'dos.pdf').write_bytes(b'factura sintetica')
            config=root/'NO TOCAR/config';config.mkdir(parents=True)
            (config/'config.json').write_bytes((ROOT/'NO TOCAR/config/config.json').read_bytes())
            # Datos de una tanda antigua del mismo cliente: no deben leerse ni tocarse.
            old=root/'entrada/Cliente/antigua.pdf';old.parent.mkdir(parents=True);old.write_bytes(b'historial ajeno al envio')
            outputs=[]
            for _ in range(2):
                prepared=envios.preparar(root,'Cliente',[source])
                path=Path(prepared['lote'])/'extraccion.json';obj=json.loads(path.read_text())
                self.assertEqual(len(obj['facturas']),2)
                for f in obj['facturas']:
                    f.update(tipo_documento='factura',proveedor='Proveedor',nif_proveedor='B12345678',numero_factura='A-001',fecha='2026-10-15',receptor='Cliente',pais_proveedor='España',tipo_gasto='otro',concepto='Servicio',lineas_concepto=[{'descripcion':'Servicio','coste':100}],base_imponible=100,importe_iva=21,total=121,moneda='EUR',impuestos=[{'base':100,'tipo':21,'cuota':21}],ajustes=[],evidencias={k:{'pagina':1,'texto':'Sintético'} for k in envios.clientes.base.EVIDENCIAS})
                path.write_text(json.dumps(obj))
                out=envios.completar(root,prepared['envio']);outputs.append(out)
                self.assertEqual((out['entrada'],out['salida'],out['filas_excel'],out['duplicadas']),(2,2,2,1))
                self.assertTrue(Path(out['excel']).is_file())
                with ZipFile(out['zip']) as z:self.assertEqual(len(z.namelist()),3)
                repeated=envios.completar(root,prepared['envio'])
                self.assertEqual(repeated['filas_excel'],2)
            self.assertNotEqual(outputs[0]['envio_id'],outputs[1]['envio_id'])
            self.assertTrue(all(Path(o['excel']).is_file() for o in outputs))
            self.assertEqual(old.read_bytes(),b'historial ajeno al envio')

    def test_cliente_invalido_no_crea_rutas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'NO TOCAR/config';p.mkdir(parents=True)
            (p/'config.json').write_bytes((ROOT/'NO TOCAR/config/config.json').read_bytes())
            with self.assertRaises(ValueError):envios.preparar(root,'../otro',[root])
