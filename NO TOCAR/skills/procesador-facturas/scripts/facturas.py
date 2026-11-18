"""Fase 1: inventario y validación local. No mueve ni escribe sobre facturas."""
import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import unicodedata
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

VERSION = "0.8.0"
EXTENSIONES = {".pdf", ".jpg", ".jpeg", ".png"}
EVIDENCIAS = ("proveedor", "nif_proveedor", "numero_factura", "fecha", "total", "moneda")
COLUMNAS_SALIDA = [
    "NOMBRE RECEPTOR", "NOMBRE PROVEEDOR", "CIF", "EXT O NAC", "PAIS", "UE",
    "Nº FACTURA", "FECHA", "AÑO", "FECHA CONTABLE", "CONCEPTO",
    "TRADUCCIÓN RESUMEN CONCEPTO", "IMPORTE TOTAL CONCEPTO", "BASE IMPONIBLE", "IVA FACTURA", "ARCHIVO FACTURA",
]


def leer(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def guardar_nuevo(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolver(root, value):
    p = Path(value)
    return (p if p.is_absolute() else root / p).resolve()


def contenido_en(path, parent):
    return path == parent or parent in path.parents


def configuracion(root):
    config_path = root / "NO TOCAR" / "config" / "config.json"
    if not config_path.is_file():
        config_path = root / "config" / "config.json"  # Proyectos antiguos aún no organizados.
    cfg = leer(config_path)
    if cfg.get("modo") not in {"analisis", "clientes"}:
        raise ValueError("modo debe ser analisis o clientes.")
    tolerancia = Decimal(str(cfg.get("tolerancia_importes", 0.02)))
    if not tolerancia.is_finite() or not 0 <= tolerancia <= Decimal("1"):
        raise ValueError("Tolerancia no válida (0 a 1).")
    return cfg


def vacia(item):
    record = {k: None for k in (
        "tipo_documento", "proveedor", "nif_proveedor", "receptor", "nif_receptor",
        "numero_factura", "fecha", "concepto", "pais_proveedor", "base_imponible",
        "importe_iva", "total", "moneda", "observaciones", "ext_o_nac", "ue",
        "fecha_contable", "resumen_concepto", "mencion_tributaria")}
    record.update(archivo_original=item["archivo_original"], sha256=item["sha256"],
                  impuestos=[], ajustes=[], evidencias={}, motivos_revision=[], subconceptos=[])
    return record


def inventariar(root, cfg, entrada=None):
    root = root.resolve()
    source = resolver(root, entrada or cfg["entrada"])
    output = resolver(root, cfg.get("trabajo_analisis", "NO TOCAR/trabajo/analisis"))
    if not source.is_dir():
        raise ValueError(f"No existe la entrada: {source}")
    if not contenido_en(output, root):
        raise ValueError("Los resultados deben quedar dentro del proyecto.")
    if contenido_en(output, source) or contenido_en(source, output):
        raise ValueError("Entrada y resultados no pueden solaparse.")
    run = output / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True, exist_ok=False)
    files = source.rglob("*") if cfg.get("recursivo") else source.iterdir()
    items = []
    for p in sorted(files):
        if not p.is_file():
            continue
        item = {"archivo_original": p.relative_to(source).as_posix(), "sha256": None,
                "compatible": p.suffix.lower() in EXTENSIONES, "error": None}
        try:
            if p.is_symlink() or not contenido_en(p.resolve(), source):
                raise ValueError("No se siguen enlaces fuera de la entrada.")
            item["sha256"] = sha256(p)
            if p.stat().st_size == 0:
                item["error"] = "Archivo vacío"
        except (OSError, ValueError) as ex:
            item["error"] = str(ex)
        items.append(item)
    manifest = {"version": VERSION, "entrada": str(source), "creado_utc": datetime.now(timezone.utc).isoformat(),
                "documentos": items}
    guardar_nuevo(run / "manifiesto.json", manifest)
    guardar_nuevo(run / "extraccion.json", {"version_esquema": "1.0", "facturas": [vacia(i) for i in items]})
    return {"lote": str(run), "archivos": len(items), "modo": "analisis"}


def numero(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Debe ser número JSON")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("Número no finito")
    return result


def texto(value):
    return isinstance(value, str) and bool(value.strip())


def clave(value):
    return re.sub(r"\s+", "", str(value or "")).upper()


def seguro(value, limit=70):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value)
    value = re.sub(r"\s+", "_", value).strip(" ._")[:limit].rstrip(" .") or "SIN_DATO"
    if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", value):
        value = "_" + value
    return value


def validar_factura(f, cfg, hoy=None):
    reasons = []
    declared = f.get("motivos_revision", [])
    if isinstance(declared, list) and all(texto(x) for x in declared):
        reasons.extend(declared)
    else:
        reasons.append("motivos_revision debe ser una lista de textos")
    for field in cfg.get("campos_obligatorios", []):
        if f.get(field) is None or (isinstance(f.get(field), str) and not f[field].strip()):
            reasons.append(f"Campo obligatorio ausente: {field}")
    for field in ("proveedor", "nif_proveedor", "numero_factura", "fecha", "moneda"):
        if f.get(field) is not None and not texto(f[field]):
            reasons.append(f"Campo debe ser texto: {field}")
    if f.get("tipo_documento") != "factura":
        reasons.append("Tipo de documento distinto de factura ordinaria o sin identificar")
    try:
        raw = f.get("fecha")
        if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            raise ValueError()
        d = date.fromisoformat(raw)
        if d < date.fromisoformat(cfg["fecha_minima"]) or d > (hoy or date.today()) + timedelta(days=cfg["dias_futuros_permitidos"]):
            reasons.append("Fecha fuera del intervalo permitido")
        if cfg.get("ejercicio") is not None and d.year != cfg["ejercicio"]:
            reasons.append("Fecha fuera del ejercicio configurado")
    except (ValueError, TypeError):
        reasons.append("Fecha ausente o no válida")
    if not isinstance(f.get("moneda"), str) or not re.fullmatch(r"[A-Z]{3}", f["moneda"]):
        reasons.append("Moneda ausente o no normalizada")
    nif = clave(f.get("nif_proveedor"))
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{3,23}", nif):
        reasons.append("Formato de NIF/VAT no reconocible; no se verifica validez fiscal")
    target = cfg.get("cliente", {}).get("nif")
    if target and clave(f.get("nif_receptor")) != clave(target):
        reasons.append("NIF del receptor ausente o distinto del cliente configurado")
    tol = Decimal(str(cfg["tolerancia_importes"]))
    try:
        base, iva, total = [numero(f.get(k)) for k in ("base_imponible", "importe_iva", "total")]
        if min(base, iva, total) < 0:
            reasons.append("Importes negativos: revisar abono o rectificativa")
        taxes, adjustments = f.get("impuestos"), f.get("ajustes")
        if not isinstance(taxes, list) or not taxes:
            raise ValueError("Falta desglose de impuestos/exención")
        sb = si = Decimal(0)
        for tax in taxes:
            b, rate, amount = [numero(tax.get(k)) for k in ("base", "tipo", "cuota")]
            if rate < 0 or rate > 100:
                reasons.append("Tipo impositivo fuera de intervalo")
            if abs(b * rate / 100 - amount) > tol:
                reasons.append("Cuota de impuesto no concilia con base y tipo")
            sb += b
            si += amount
        if abs(sb - base) > tol or abs(si - iva) > tol:
            reasons.append("El desglose de impuestos no concilia con los agregados")
        if not isinstance(adjustments, list):
            raise ValueError("ajustes debe ser una lista")
        adj = Decimal(0)
        for a in adjustments:
            if not texto(a.get("concepto")):
                raise ValueError("Ajuste sin concepto")
            adj += numero(a.get("importe"))
        if abs(base + iva + adj - total) > tol:
            reasons.append("Base + IVA + ajustes no concilia con total")
    except (ValueError, TypeError, AttributeError, InvalidOperation) as ex:
        reasons.append(f"Importes o desglose incompletos/no válidos: {ex}")
    evidence = f.get("evidencias")
    if not isinstance(evidence, dict):
        evidence = {}
    for field in EVIDENCIAS:
        ev = evidence.get(field)
        if not isinstance(ev, dict) or type(ev.get("pagina")) is not int or ev["pagina"] < 1 or not texto(ev.get("texto")):
            reasons.append(f"Falta evidencia de {field}")
    return list(dict.fromkeys(reasons))


def celda_csv(value):
    s = "" if value is None else str(value)
    # CSV puede abrirse en Excel: neutraliza fórmulas provenientes de documentos.
    return "'" + s if s.lstrip().startswith(("=", "+", "-", "@")) else s


def iva_visible(f):
    """Porcentajes y cuotas explícitos en una celda, sin inferir tipos ausentes."""
    currency = f.get("moneda") or "moneda no indicada"
    parts = []
    for tax in f.get("impuestos") or []:
        if not isinstance(tax, dict):
            continue
        rate = tax.get("tipo")
        label = f"{rate:g} %" if type(rate) in (int, float) else tax.get("literal_tipo") or "Tipo no indicado"
        amount = tax.get("cuota")
        amount_text = f"{numero(amount):.2f}".replace(".", ",") + " " + currency if type(amount) in (int, float) else "importe no indicado"
        parts.append(f"{label}: {amount_text}")
    if not parts:
        amount = f.get("importe_iva")
        if type(amount) in (int, float):
            parts.append("Tipo no indicado: " + f"{numero(amount):.2f}".replace(".", ",") + " " + currency)
    if texto(f.get("mencion_tributaria")):
        parts.append(f["mencion_tributaria"])
    return "; ".join(parts) or None


def iva_porcentajes(f):
    taxes = f.get('impuestos')
    if not isinstance(taxes,list) or not taxes:
        return None
    rates = []
    for item in taxes:
        if not isinstance(item,dict):
            return None
        try:
            rate = numero(item.get('tipo'))
        except (ValueError,TypeError):
            return None
        if not 0 <= rate <= 100:
            return None
        if rate not in rates:
            rates.append(rate)
    return ' / '.join(f'{rate.normalize():f} %' for rate in rates)


def concepto_completo(f):
    parts = f.get('subconceptos')
    if isinstance(parts,list) and parts and all(texto(p) for p in parts):
        parts = [re.sub(r'^[-•]\s+', '', p.strip()) for p in parts]
        return parts[0] if len(parts)==1 else '\n'.join('- '+p for p in parts)
    return f.get('concepto')


def identidad_factura(f):
    """Número literal (sin espacios exteriores) y total exacto; nunca hash/NIF."""
    number = f.get('numero_factura')
    if not isinstance(number,str) or not number.strip():
        return None
    try:
        total = numero(f.get('total'))
    except (ValueError,TypeError):
        return None
    return (number.strip(),total)


def fila_salida(f, cfg):
    """Proyección de sólo 15 columnas; no inventa definiciones pendientes."""
    rules = cfg.get("salida_campos", {})
    try:
        year = date.fromisoformat(f.get("fecha")).year
    except (TypeError, ValueError):
        year = None
    amount = f.get("importe_total_concepto") if rules.get("importe_total_concepto") else None
    if rules.get("importe_total_concepto") == "total_a_pagar":
        amount = f.get("total")
    iva = f.get("iva_factura") if rules.get("iva_factura") else None
    if iva is None and rules.get("iva_factura") == "importe":
        iva = f.get("importe_iva")
    if rules.get("iva_factura") == "porcentaje_e_importe":
        iva = iva_visible(f)
    if rules.get("iva_factura") == "porcentaje":
        iva = iva_porcentajes(f)
    summary = f.get("resumen_concepto") if rules.get("idioma_resumen") else None
    accounting_date = f.get("fecha_contable")
    if accounting_date is None and rules.get("fecha_contable") == "fecha_factura":
        accounting_date = f.get("fecha")
    return [f.get("receptor"), f.get("proveedor"), f.get("nif_proveedor"),
            f.get("ext_o_nac"), f.get("pais_proveedor"), f.get("ue"),
            f.get("numero_factura"), f.get("fecha"), year, accounting_date,
            concepto_completo(f), summary, amount, f.get("base_imponible"), iva, None]


def marcas_excel(ordered):
    """Comprueba cada duplicado contra una referencia real antes de exportar."""
    marks = []
    for index, result in enumerate(ordered):
        note = result.get('nota_excel') or ''
        if result.get('marca') == 'DUPLICADA':
            identity = identidad_factura(result['datos'])
            reference = next((i for i, other in enumerate(ordered)
                              if i != index and other.get('marca') != 'DUPLICADA'
                              and identity is not None and identidad_factura(other['datos']) == identity), None)
            if reference is None:
                raise ValueError('Marca DUPLICADA sin otra factura con el mismo número completo y total: '
                                 + str(result['datos'].get('numero_factura')))
            proof = (f'Duplicada de la fila {reference+6} del Excel. '
                     f'Número completo idéntico: {identity[0]}. Total idéntico: {identity[1]:f}.')
            note = proof + '\n' + note
        marks.append({'tipo':result.get('marca'),'texto':note,'archivo':result.get('archivo_final')})
    return marks


def generar_excel(run, tag, results, cfg):
    """Exporta un nuevo libro de análisis con el runtime incluido en Codex."""
    runtime = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node"
    node = Path(os.environ.get("FACTURAS_NODE", str(runtime / "bin" / ("node.exe" if os.name == "nt" else "node"))))
    if not node.is_file():
        raise ValueError("No se encuentra Node de Codex. Consulta dependencias del entorno o configura FACTURAS_NODE; no se ha generado Excel.")
    ordered = sorted(results, key=lambda r: (str(r["datos"].get("fecha") or "9999-99-99"), clave(r["datos"].get("proveedor")), clave(r["datos"].get("numero_factura"))))
    payload = {"columnas": COLUMNAS_SALIDA,
               "filas": [fila_salida(r["datos"], cfg) for r in ordered],
               "monedas": [r["datos"].get("moneda") for r in ordered],
               "marcas": marcas_excel(ordered)}
    internal = run / ("salida_excel_" + tag + ".json")
    guardar_nuevo(internal, payload)
    destination = run / ("facturas_" + tag + ".xlsx")
    script = Path(__file__).with_name("exportar-excel.mjs")
    try:
        result = subprocess.run([str(node), str(script), str(internal), str(destination)],
                                capture_output=True, text=True, encoding="utf-8", timeout=120)
    except (OSError, subprocess.TimeoutExpired) as ex:
        raise ValueError(f"No se ha podido completar el Excel: {ex}") from ex
    if result.returncode != 0:
        raise ValueError("No se ha completado la exportación Excel: " + result.stderr.strip())
    if not destination.is_file() or destination.stat().st_size == 0:
        raise ValueError("La exportación no ha producido un archivo Excel verificable")
    import importlib.util
    spec = importlib.util.spec_from_file_location('enlaces_xlsx', Path(__file__).with_name('enlaces_xlsx.py'))
    enlaces = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(enlaces)
    enlaces.incorporar_enlaces(destination, [r.get('archivo_final') for r in ordered])
    return destination


def validar(root, cfg, lote):
    root = root.resolve()
    run = resolver(root, lote)
    if not contenido_en(run, resolver(root, cfg.get("trabajo_analisis", "NO TOCAR/trabajo/analisis"))):
        raise ValueError("El lote debe estar en la carpeta de resultados configurada")
    manifest, extraction = leer(run / "manifiesto.json"), leer(run / "extraccion.json")
    if extraction.get("version_esquema") != "1.0" or not isinstance(extraction.get("facturas"), list):
        raise ValueError("Esquema de extracción no compatible")
    records = extraction["facturas"]
    if not all(isinstance(f, dict) for f in records):
        raise ValueError("Cada factura debe ser un objeto")
    names = [f.get("archivo_original") for f in records]
    expected = [i["archivo_original"] for i in manifest["documentos"]]
    if sorted(str(n) for n in names) != sorted(expected):
        raise ValueError("La extracción debe contener exactamente un registro por archivo del manifiesto")
    source = Path(manifest["entrada"]).resolve()
    hashes, identities, fuzzy, proposals = {}, {}, {}, set()
    results = []
    for item in manifest["documentos"]:
        f = records[names.index(item["archivo_original"])]
        reasons = validar_factura(f, cfg)
        errors = []
        original = (source / item["archivo_original"]).resolve()
        try:
            if not contenido_en(original, source):
                raise ValueError("Ruta fuera de entrada")
            if item["sha256"] is None or sha256(original) != item["sha256"] or f.get("sha256") != item["sha256"]:
                errors.append("Original modificado/inaccesible o hash de extracción incorrecto")
        except (OSError, ValueError) as ex:
            errors.append(str(ex))
        if item["error"]:
            errors.append(item["error"])
        if not item["compatible"]:
            reasons.append("Formato no compatible")
        duplicate = None
        h = item["sha256"]
        identity = identidad_factura(f)
        if identity is not None:
            duplicate = identities.get(identity)
            if duplicate:
                reasons.append("Coincidencia de número de factura y total con: " + duplicate)
            identities.setdefault(identity,item['archivo_original'])
        state = "error" if errors else "duplicado" if duplicate else "revisar" if reasons else "validada"
        proposal = None
        if state == "validada":
            stem = seguro(f["numero_factura"], 60) + "_" + seguro(f["proveedor"], 70)
            proposal = stem + original.suffix.lower()
            if proposal.casefold() in proposals:
                proposal = stem + "_" + h[:8] + original.suffix.lower()
            proposals.add(proposal.casefold())
        results.append({"id_documento": h, "archivo_original": item["archivo_original"],
                        "estado": state, "nombre_propuesto": proposal,
                        "motivos": list(dict.fromkeys(errors + reasons)), "datos": f})
    counts = {s: sum(r["estado"] == s for r in results) for s in ("validada", "revisar", "duplicado", "error")}
    report = {"version": VERSION, "modo": "analisis", "creado_utc": datetime.now(timezone.utc).isoformat(),
              "alcance_duplicados": "sólo este lote", "total": len(results), "recuentos": counts,
              "porcentaje_validado": round(100 * counts["validada"] / len(results), 2) if results else 0,
              "documentos": results}
    # Cada validación conserva los informes anteriores para mantener trazabilidad.
    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid.uuid4().hex[:8]
    report_path = run / ("informe_" + tag + ".json")
    guardar_nuevo(report_path, report)
    output_format = cfg.get("formato_salida", "xlsx")
    if output_format == "xlsx":
        output_path = generar_excel(run, tag, results, cfg)
    elif output_format == "csv":
        output_path = run / ("resumen_" + tag + ".csv")
        with output_path.open("x", encoding="utf-8-sig", newline="") as out:
            writer = csv.writer(out, delimiter=";")
            writer.writerow(COLUMNAS_SALIDA)
            for r in results:
                writer.writerow([celda_csv(v) for v in fila_salida(r["datos"], cfg)])
    else:
        raise ValueError("formato_salida debe ser xlsx o csv")
    return {"informe": str(report_path), "resumen": str(output_path), "formato": output_format, "total": len(results), "recuentos": counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("accion", choices=["inventariar", "validar"])
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--entrada")
    parser.add_argument("--lote")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        cfg = configuracion(root)
        if args.accion == "validar" and not args.lote:
            parser.error("validar requiere --lote")
        result = inventariar(root, cfg, args.entrada) if args.accion == "inventariar" else validar(root, cfg, args.lote)
        print(json.dumps(result, ensure_ascii=True, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as ex:
        parser.exit(1, f"Error: {ex}\n")


if __name__ == "__main__":
    main()
