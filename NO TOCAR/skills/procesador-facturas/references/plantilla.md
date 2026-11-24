# Resultado de 19 columnas · versión 1.1

El entregable contiene exclusivamente las siguientes columnas, en este orden. Una única hoja Facturas, encabezados en fila 5 y una fila vacía con formato en fila 6. Sin hojas auxiliares, columnas ocultas, datos reales o macros.

| Columna | Encabezado exacto | Regla |
|---|---|---|
| A | NOMBRE RECEPTOR | Empresa receptora visible. |
| B | NOMBRE PROVEEDOR | Emisor visible. |
| C | CIF | NIF/CIF/VAT literal como texto. |
| D | PAIS | País del proveedor visible. |
| E | UE | SI/NO por pertenencia a UE-27. |
| F | Nº FACTURA | Número íntegro como texto. |
| G | FECHA | Fecha de emisión como fecha real. |
| H | AÑO | Año derivado de emisión. |
| I | FECHA CONTABLE | Solo por regla o dato explícito. |
| J | CONCEPTO | Detalle original completo. |
| K | CONCEPTO TOTAL | Viñetas con descripción y coste original de cada línea. |
| L | TRADUCCIÓN RESUMEN CONCEPTO | Resumen breve en español. |
| M | IMPORTE TOTAL CONCEPTO | Total final en la moneda original. |
| N | BASE IMPONIBLE | Base explícita en la moneda original. |
| O | IMPORTE TOTAL CONCEPTO EUROS | Total equivalente en EUR, según cambios.md. |
| P | BASE IMPONIBLE EUROS | Base equivalente en EUR, según cambios.md. |
| Q | IVA FACTURA | Porcentajes explícitos, sin cuotas. |
| R | ARCHIVO FACTURA | Enlace relativo a facturas/, texto Abrir factura. |
| S | Partida | COLABORADORAS para servicios y OTROS GASTOS para compras según extraccion.md. |

## IVA sin porcentaje numérico

No convertir datos ausentes en cero. Si no consta un porcentaje numérico, dejar la celda vacía. Los códigos como EAM, menciones tributarias y cuotas permanecen en JSON interno para validar. Los porcentajes múltiples se muestran una sola vez por tipo y en orden. La columna es texto para permitir varios porcentajes. M y N se guardan como valores numéricos con moneda en el formato de cada celda. Las fechas son valores reales de Excel, los números de factura y NIF son texto para preservar ceros. No sumar monedas distintas. CSV es sólo una opción explícita y no admite formatos monetarios por celda.

## Resultado e informes internos

Una fila por factura/documento de la prueba, incluso si tiene campos desconocidos: se dejan vacíos. Estados, motivos, hashes, nombres de archivo, evidencias, retenciones y otros auxiliares quedan en JSON interno y se comunican fuera de la tabla. No agregarlos al Excel o CSV ni ocultar una fila por falta de un auxiliar.

El modo clientes actualiza un único Excel acumulado de 19 columnas por cliente. Los duplicados mantienen su fila y número literal: se señalan con nota en Nº FACTURA, sin columna adicional. Todas las demás filas son blancas, incluida la primera copia y las posibles duplicadas. Las incidencias se explican aparte y en las notas existentes. Cada fila tiene una nota que la vincula a su archivo de entrada y copia de salida, incluso si las celdas están vacías. Los recuentos usan el rango de la tabla, no CONTARA. Los detalles completos se conservan aparte en JSON técnico. El modo análisis crea un libro nuevo sin archivo acumulado. No se modifican los originales ni los informes históricos.

La columna ARCHIVO FACTURA permite abrir la copia renombrada con un clic. Usa un enlace relativo desde el Excel a facturas/<nombre>; al compartir, conserva el Excel y la subcarpeta facturas juntos. La duplicidad se decide exclusivamente por número íntegro y total final a pagar coincidentes dentro del cliente; no por hash ni por NIF.

## Formato compacto

Mantener todas las filas de datos blancas, incluidas las duplicadas. Conservar las incidencias y trazabilidad en notas. Usar anchos de 24 caracteres, 42 en conceptos y 9 en UE/AÑO, con filas de datos de 30 puntos y ajuste de texto. El contenido íntegro permanece en la celda y puede consultarse en la barra de fórmulas o ampliando la fila.
