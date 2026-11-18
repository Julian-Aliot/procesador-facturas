# Resultado de 16 columnas · versión 0.7

El entregable contiene exclusivamente las siguientes columnas, en este orden. Una única hoja Facturas, encabezados en fila 5 y una fila vacía con formato en fila 6. Sin hojas auxiliares, columnas ocultas, datos reales o macros.

| Columna | Encabezado exacto | Regla |
|---|---|---|
| A | NOMBRE RECEPTOR | Empresa receptora que figura en la factura; contrastar con el cliente declarado. |
| B | NOMBRE PROVEEDOR | Nombre del emisor; separar identificadores adicionales en datos internos. |
| C | CIF | NIF/CIF/VAT del proveedor tal como aparece; almacenar como texto. |
| D | EXT O NAC | EXT o NAC según país del proveedor y regla corporativa confirmada; desconocido: vacío. |
| E | PAIS | País del proveedor respaldado por el documento, no del receptor. |
| F | UE | SI o NO según país del proveedor y regla territorial corporativa confirmada; desconocido: vacío. |
| G | Nº FACTURA | Número íntegro, conservando ceros, barras y guiones en la celda. |
| H | FECHA | Fecha de emisión, no de servicio ni vencimiento; fecha real de Excel, presentación dd/mm/aaaa. |
| I | AÑO | Año derivado de la fecha de emisión válida. |
| J | FECHA CONTABLE | Sólo si el usuario la proporciona o existe una regla corporativa. Vacía por defecto. |
| K | CONCEPTO | Detalle completo del documento conservando su idioma. Varios subconceptos: cada uno con guion y salto de línea dentro de la misma celda; no resumir ni omitir líneas. |
| L | TRADUCCIÓN RESUMEN CONCEPTO | Resumen breve en español, traduciendo si procede. No añadir interpretaciones. |
| M | IMPORTE TOTAL CONCEPTO | Total final a pagar, después de retenciones. No el saldo pendiente tras pagos ni el precio antes de impuestos. |
| N | BASE IMPONIBLE | Base indicada en el documento. No inventarla desde el total ni equiparar automáticamente cualquier subtotal a una base fiscal. |
| O | IVA FACTURA | Sólo porcentaje: 21 %. Varios tipos: 21 % / 10 %. Sin cuotas ni menciones fiscales. |

| P | ARCHIVO FACTURA | Enlace relativo a la copia renombrada en facturas/, con texto Abrir factura. |

Las definiciones de L, M y O fueron confirmadas por el usuario. La configuración contiene idioma_resumen=es, importe_total_concepto=total_a_pagar e iva_factura=porcentaje.

## IVA sin porcentaje numérico

No convertir datos ausentes en cero. Si no consta un porcentaje numérico, dejar la celda vacía. Los códigos como EAM, menciones tributarias y cuotas permanecen en JSON interno para validar. Los porcentajes múltiples se muestran una sola vez por tipo y en orden. La columna es texto para permitir varios porcentajes. M y N se guardan como valores numéricos con moneda en el formato de cada celda. Las fechas son valores reales de Excel, los números de factura y NIF son texto para preservar ceros. No sumar monedas distintas. CSV es sólo una opción explícita y no admite formatos monetarios por celda.

## Resultado e informes internos

Una fila por factura/documento de la prueba, incluso si tiene campos desconocidos: se dejan vacíos. Estados, motivos, hashes, nombres de archivo, evidencias, retenciones y otros auxiliares quedan en JSON interno y se comunican fuera de la tabla. No agregarlos al Excel o CSV ni ocultar una fila por falta de un auxiliar.

El modo clientes actualiza un único Excel acumulado de 16 columnas por cliente. Los duplicados mantienen su fila y número literal: se marcan con color amarillo y nota en Nº FACTURA, sin columna adicional. Todas las demás filas son blancas, incluida la primera copia y las posibles duplicadas. Las incidencias se explican aparte y en las notas existentes. Cada fila tiene una nota que la vincula a su archivo de entrada y copia de salida, incluso si las celdas están vacías. Los recuentos usan el rango de la tabla, no CONTARA. Los detalles completos se conservan aparte en JSON técnico. El modo análisis crea un libro nuevo sin archivo acumulado. No se modifican los originales ni los informes históricos.

La última columna ARCHIVO FACTURA permite abrir la copia renombrada con un clic. Usa un enlace relativo desde el Excel a facturas/<nombre>; al compartir, conserva el Excel y la subcarpeta facturas juntos. La duplicidad se decide exclusivamente por número íntegro y total final a pagar coincidentes dentro del cliente; no por hash ni por NIF.
