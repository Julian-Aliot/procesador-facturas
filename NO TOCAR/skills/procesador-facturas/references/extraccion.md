# Contrato de extracción 1.0

`extraccion.json` contiene `{"version_esquema":"1.0", "facturas":[...]}`. Un registro por archivo del manifiesto. No dividir ni fusionar archivos automáticamente en esta versión. El inventario genera las claves de cada registro; completa sus valores.

Campos:

- `archivo_original`, `sha256`: identidad asignada por inventario; inalterable.
- `tipo_documento`: `factura`, `rectificativa`, `otro` o null. Rectificativas van a revisión en esta versión.
- `proveedor`, `nif_proveedor`, `receptor`, `nif_receptor`, `numero_factura`: texto literal, sin buscar identificadores externos. Conserva ceros y puntuación del número de factura.
- `fecha`: fecha ISO `AAAA-MM-DD`; si el orden día/mes es ambiguo, null y motivo.
- `concepto`: descripción completa del concepto, en su idioma original; `pais_proveedor`: sólo si consta.
- `subconceptos`: lista de textos con todas las líneas de servicios o productos, en orden y sin omitir repeticiones. Conserva las descripciones completas, periodos, cantidades, unidades, precios unitarios y referencias que pertenezcan al concepto, cuando consten. Revisa todas las páginas. No incluyas datos bancarios ni pies legales ajenos al concepto. Si hay varias líneas, se exportan con guion y salto de línea dentro de CONCEPTO. Un solo concepto no necesita guion. No dividas automáticamente por guiones de fechas o referencias. No sustituyas el detalle por el resumen.
- `resumen_concepto`: resumen breve en español del concepto, traduciendo si procede. No añadir servicios, finalidades ni categorías que no aparezcan en el documento.
- `ext_o_nac`: `EXT`, `NAC` o null; `ue`: `SI`, `NO` o null. Son clasificaciones apoyadas en el país del proveedor y las reglas corporativas confirmadas, no en el país del receptor ni en un prefijo de identificador aislado. Si falta la regla o el país, conservar null y explicar fuera de la tabla.
- `fecha_contable`: fecha ISO o null, sólo si se facilita o existe una regla corporativa explícita. No usar fecha actual ni fecha de factura por defecto.
- `mencion_tributaria`: texto literal breve del documento sobre el impuesto, cuando exista, sin reinterpretarlo fiscalmente. Un código de tipo no porcentual puede conservarse como `literal_tipo` dentro de su elemento de `impuestos` (por ejemplo, `EAM`).
- `base_imponible`, `importe_iva`, `total`: números JSON, sin moneda ni separadores de miles. Un valor que no aparece es null. Un cero explícito es 0.
- `moneda`: código ISO de tres letras sólo si puede determinarse en el documento. Un símbolo `$` ambiguo exige revisión; no se presupone EUR por idioma o país.
- `impuestos`: lista de objetos `{"base":100,"tipo":21,"cuota":21}`. Tipo se expresa en puntos porcentuales (21, no 0.21). Un tipo desconocido queda null; no deducirlo de una división. Exención explícita: base y cuota 0 de impuesto, tipo 0 únicamente si consta; explicar exención en observaciones.
- `ajustes`: lista `{"concepto":"Retención", "importe":-15}`. Incluye sólo ajustes explícitos que intervienen en total y no están ya incluidos en base/IVA. No duplicar descuentos ya incluidos. Lista vacía cuando no hay ajustes. Si se desconoce cómo conciliar, motivo de revisión.
- `evidencias`: objeto por campo: `{"numero_factura":{"pagina":1,"texto":"Factura F-123"}}`. En imágenes página 1. Evidencia requerida de proveedor, NIF proveedor, fecha, número, total y moneda para superar controles. No pegues páginas enteras ni datos bancarios.
- `motivos_revision`: lista de problemas importantes: ambigüedad, varias facturas por archivo, páginas faltantes, receptor incierto, dato ilegible. El validador conserva estos motivos.
- `observaciones`: texto opcional con contexto útil. No sustituye un motivo importante por una nota.

No hay un porcentaje de confianza inventado ni un campo `estado` decidido por el modelo: el validador calcula el resultado. Los campos auxiliares anteriores son internos; la salida visible contiene las 15 columnas de datos más ARCHIVO FACTURA, según `plantilla.md`. No asignes decisiones fiscales o contables por conjetura.

Reglas numéricas: suma de bases y cuotas por impuesto debe conciliar con los agregados; base + IVA + ajustes debe conciliar con total. Se usa tolerancia absoluta por factura configurable (0.02 por defecto), no proporcional al importe. Importes negativos y rectificativas se revisan inicialmente. Una fecha fuera del ejercicio configurado o demasiado futura se revisa. La comprobación básica de NIF/VAT no prueba existencia, validez fiscal ni registro VIES.
