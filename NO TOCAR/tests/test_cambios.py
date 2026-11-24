"""Regresiones de conversión, clasificación y consulta de fechas nuevas."""
import csv
import importlib.util
import io
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/procesador-facturas/scripts'
sys.path.insert(0, str(SCRIPTS))
import cambios
import facturas


class Cambios(unittest.TestCase):
    def tearDown(self):
        cambios.tipo_cambio.cache_clear()
        cambios.convertir.cache_clear()

    def test_historico_y_fin_de_semana(self):
        with cambios.HISTORICO.open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]['fecha'], '2020-01-02')
        self.assertEqual(rows[-1]['fecha'], '2026-11-24')
        self.assertEqual(len({r['fecha'] for r in rows}), len(rows))
        day, rate = cambios.tipo_cambio('2026-11-22')
        self.assertEqual(day, '2026-11-20')
        self.assertEqual(rate, Decimal('1.099'))
        total, base, eur_total, eur_base, note = cambios.convertir('2026-11-22', 109.9, 0)
        self.assertEqual((total,base,eur_total,eur_base), (109.9,0,100,0))
        self.assertIn('2026-11-20', note)

    def test_importes_originales_y_euros(self):
        cfg = {'salida_campos': {'importe_total_concepto':'total_a_pagar'}}
        f = {'moneda':'USD','fecha':'2026-11-22','total':109.9,'base_imponible':None}
        row = dict(zip(facturas.COLUMNAS_SALIDA, facturas.fila_salida(f,cfg)))
        self.assertEqual(row['IMPORTE TOTAL CONCEPTO'], 109.9)
        self.assertEqual(row['IMPORTE TOTAL CONCEPTO EUROS'], 100)
        self.assertIsNone(row['BASE IMPONIBLE EUROS'])
        f['moneda']='EUR'
        self.assertEqual(facturas.importes_salida(f,109.9)[:4],(109.9,None,109.9,None))
        self.assertNotIn('EXT O NAC', row)

    def test_ausencia_fecha_y_fallo_red_conservan_original(self):
        self.assertEqual(cambios.convertir(None, 123, 100)[:4], (123,100,None,None))
        with patch.object(cambios,'tipo_cambio',side_effect=OSError('sin red')):
            result = cambios.convertir('2026-11-24',123,100)
        self.assertEqual(result[:4], (123,100,None,None))
        self.assertIn('pendiente',result[4])

    def test_busca_fecha_fuera_del_historico(self):
        sample = b'CURRENCY,CURRENCY_DENOM,TIME_PERIOD,OBS_VALUE\nUSD,EUR,2019-12-31,1.1234\n'
        with patch.object(cambios,'urlopen',return_value=io.BytesIO(sample)) as request:
            self.assertEqual(cambios.tipo_cambio('2019-12-31'),('2019-12-31',Decimal('1.1234')))
            self.assertIn('endPeriod=2019-12-31',request.call_args.args[0])

    def test_partidas_compatibles(self):
        for kind, expected in [('autonomo','COLABORADORAS'),('servicio','COLABORADORAS'),('otro','OTROS GASTOS'),('consumible','OTROS GASTOS')]:
            self.assertEqual(facturas.partida_visible({'tipo_gasto':kind}), expected)
        self.assertEqual(facturas.partida_visible({'partida':'AUTONOMOS'}),'COLABORADORAS')
        self.assertIsNone(facturas.partida_visible({'tipo_gasto':'mixto'}))
