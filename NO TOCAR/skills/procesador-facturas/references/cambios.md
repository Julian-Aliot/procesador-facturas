# Conversión a euros

Conservar IMPORTE TOTAL CONCEPTO y BASE IMPONIBLE en la moneda original. Añadir IMPORTE TOTAL CONCEPTO EUROS y BASE IMPONIBLE EUROS como importes numéricos en EUR. Para facturas EUR repetir los valores originales en las dos columnas nuevas. Para USD dividir por el tipo USD por EUR del BCE y redondear a dos decimales, mitad hacia arriba. Mantener el desglose de conceptos en la moneda original.

Leer el histórico diario `eur-usd.csv`, que cubre desde el 02/01/2020 hasta el 24/11/2026 con 1768 observaciones. Se ha contrastado con el XML histórico y la API oficial del BCE el 24/11/2026. Usar la fecha de emisión de factura y, para días sin publicación, el último tipo anterior disponible con una antigüedad máxima de siete días.

Cuando la fecha quede fuera del histórico, scripts/cambios.py consulta automáticamente la serie D.USD.EUR.SP00.A de la API del BCE para esa fecha y su semana anterior. El resultado se mantiene durante la ejecución. No extrapolar tipos para fechas futuras. Si la consulta falla o falta una fecha válida, conservar los importes originales, dejar los equivalentes pendientes y comunicar el motivo. Las monedas distintas de EUR/USD requieren un tipo oficial específico y quedan pendientes de conversión en esta versión.

Registrar fecha aplicada, tipo, fórmula y fuente en la nota de Nº FACTURA. Para ampliar el histórico, incorporar únicamente observaciones oficiales verificadas con el formato fecha,usd_por_eur.

Fuente oficial de la serie y sus parámetros de consulta en https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A . Histórico XML en https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml .
