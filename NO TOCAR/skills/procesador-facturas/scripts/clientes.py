"""Carpetas por cliente: un archivo, una copia y una fila; acumulación local."""
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone, date
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facturas as base


def nuevo_id():
    return uuid.uuid4().hex


def atomico(path, value):
    tmp = path.with_name(path.name + '.' + nuevo_id() + '.tmp')
    with tmp.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def rutas(root, cfg, cliente, entrada=None):
    if not cliente or cliente.startswith('.') or re.search(r'[<>:"/\\|?*\x00-\x1f]', cliente) or cliente != cliente.rstrip(' .'):
        raise ValueError('Nombre de cliente no válido')
    root = root.resolve()
    input_base = base.resolver(root, cfg['entrada'])
    expected_source = input_base / cliente
    source = base.resolver(root, entrada) if entrada else input_base / cliente
    source = source.resolve()
    if (not base.contenido_en(input_base,root)
            or source != expected_source.absolute()
            or source.parent != input_base or source.name.casefold() != cliente.casefold()):
        raise ValueError('Cada cliente debe usar exclusivamente entrada/<cliente>; no se permite otra carpeta, la raíz de entrada ni enlaces a otro cliente')
    results = base.resolver(root, cfg['resultados'])
    if not base.contenido_en(results, root) or base.contenido_en(results, source) or base.contenido_en(source, results):
        raise ValueError('Entrada y resultados deben estar separados; resultados debe quedar en el proyecto')
    if not source.is_dir():
        raise ValueError(f'No existe la carpeta de cliente: {source}')
    # El hash evita colisiones en el área técnica; la carpeta pública conserva el nombre.
    control_base = base.resolver(root, cfg.get('control', 'NO TOCAR/control'))
    control = control_base / hashlib.sha256(cliente.casefold().encode()).hexdigest()[:20]
    destination = results / cliente
    if destination.resolve().parent != results or not base.contenido_en(control.resolve(), root) or base.contenido_en(control.resolve(), source) or base.contenido_en(control.resolve(), results) or source.is_symlink() or results.is_symlink():
        raise ValueError('No se admiten rutas de salida redirigidas')
    return source, destination, control


@contextmanager
def bloqueo(control):
    control.mkdir(parents=True, exist_ok=True)
    lock = control / 'escritor.lock'
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ValueError(f'Existe un bloqueo de escritor: {lock}. No se ha modificado el cliente; comprueba si hay otra ejecución o un cierre inesperado.')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump({'pid':os.getpid(), 'utc':datetime.now(timezone.utc).isoformat()}, stream)
        yield
    finally:
        lock.unlink(missing_ok=True)


def inventario(source):
    docs, omitted = {}, []
    for path in sorted(source.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        if path.suffix.lower() not in base.EXTENSIONES:
            omitted.append(relative)
            continue
        if path.is_symlink() or not base.contenido_en(path.resolve(), source):
            raise ValueError('No se sigue un enlace en entrada: ' + relative)
        key = relative.casefold()
        if key in docs:
            raise ValueError('Dos rutas se confunden en Windows: ' + relative)
        docs[key] = {'archivo_original':relative,'sha256':base.sha256(path)}
    return docs, omitted


def registro(control, cliente, source):
    p = control / 'registro.json'
    if p.exists():
        obj = base.leer(p)
        validar_registro(obj)
        if obj['cliente'] != cliente or Path(obj['entrada']).resolve() != source:
            raise ValueError('El nombre o la carpeta original del cliente ha cambiado. Se requiere una migración explícita para conservar la correspondencia.')
        return obj
    return {'version':base.VERSION,'revision':None,'cliente':cliente,'entrada':str(source),
            'excel':'Facturas_' + base.seguro(cliente,60) + '.xlsx','excel_sha256':None,'archivos':[]}


def validar_registro(obj):
    def leaf(name):
        return isinstance(name,str) and name not in {'','.','..'} and not re.search(r'[<>:"/\\|?*\x00-\x1f]',name)
    if not leaf(obj.get('excel')) or not obj['excel'].endswith('.xlsx'):
        raise ValueError('Nombre de Excel no válido en registro')
    if obj.get('revision') is not None and not re.fullmatch(r'[0-9a-f]{32}',obj['revision']):
        raise ValueError('Revisión no válida en registro')
    keys, outputs = set(), set()
    for item in obj['archivos']:
        rel = item['archivo_original']
        if not isinstance(rel,str) or Path(rel).is_absolute() or '..' in Path(rel).parts or item['clave'] != rel.casefold():
            raise ValueError('Ruta de original no válida en registro')
        if not leaf(item.get('archivo_final')) or not re.fullmatch(r'[0-9a-f]{64}',item['sha256']):
            raise ValueError('Copia de salida no válida en registro')
        if item['clave'] in keys or item['archivo_final'].casefold() in outputs:
            raise ValueError('El registro contiene identidades repetidas')
        data = item.get('datos')
        if (not isinstance(data,dict) or data.get('archivo_original') != rel
                or data.get('sha256') != item['sha256']
                or data.get('cliente_origen',obj['cliente']) != obj['cliente']):
            raise ValueError('La extracción registrada pertenece a otro archivo o cliente: '+rel)
        keys.add(item['clave'])
        outputs.add(item['archivo_final'].casefold())


def revisar_entrada(current, ledger):
    for item in ledger['archivos']:
        now = current.get(item['clave'])
        if now is None:
            raise ValueError('Falta un original ya registrado: ' + item['archivo_original'] + '. Conserva las tandas anteriores en entrada.')
        if now['sha256'] != item['sha256']:
            raise ValueError('Se ha modificado un original registrado: ' + item['archivo_original'] + '. No se actualiza silenciosamente.')


def filas_excel(path):
    with ZipFile(path) as archive:
        ns = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        if len(workbook.find('m:sheets',ns)) != 1:
            raise ValueError('El Excel debe contener una sola hoja')
        tables = [n for n in archive.namelist() if re.fullmatch(r'xl/tables/table\d+\.xml', n)]
        if len(tables) != 1:
            raise ValueError('El Excel debe contener una sola tabla')
        table = ET.fromstring(archive.read(tables[0]))
        cols = table.find('m:tableColumns',ns)
        previous = [c for c in base.COLUMNAS_SALIDA if c not in {'IMPORTE TOTAL CONCEPTO EUROS', 'BASE IMPONIBLE EUROS'}]
        previous.insert(3, 'EXT O NAC')
        legacy = [c for c in previous if c not in {'CONCEPTO TOTAL','Partida'}]
        if [c.attrib['name'] for c in cols] not in (base.COLUMNAS_SALIDA,previous,legacy,legacy[:-1]):
            raise ValueError('El Excel no tiene las columnas acordadas')
        ref = re.fullmatch(r'A5:[OPRS](\d+)',table.attrib['ref'])
        if not ref:
            raise ValueError('Rango de tabla inesperado')
        return int(ref[1]) - 5


def verificar_salida(destination, ledger, permitir_faltantes=False):
    if destination.exists() and any(p.name not in {'facturas',ledger['excel']} for p in destination.iterdir()):
        raise ValueError('La carpeta de cliente contiene archivos ajenos al registro; no se mezclan ni se borran')
    folder = destination / 'facturas'
    expected = {i['archivo_final'] for i in ledger['archivos']}
    actual = {p.name for p in folder.iterdir() if p.is_file()} if folder.exists() else set()
    if folder.exists() and (folder.resolve().parent != destination.resolve() or any(p.is_dir() or p.is_symlink() for p in folder.iterdir())):
        raise ValueError('La salida debe ser una carpeta plana sin enlaces')
    if folder.is_symlink() or actual - expected or (not permitir_faltantes and actual != expected):
        raise ValueError('La carpeta de salida no coincide con el registro; no se borran ni sobrescriben archivos desconocidos')
    for item in ledger['archivos']:
        if permitir_faltantes and item['archivo_final'] not in actual:
            continue
        if base.sha256(folder / item['archivo_final']) != item['sha256']:
            raise ValueError('Se ha modificado una copia de salida: ' + item['archivo_final'])
    excel = destination / ledger['excel']
    if ledger['archivos']:
        if permitir_faltantes and not excel.exists():
            return
        if not excel.is_file() or base.sha256(excel) != ledger['excel_sha256']:
            raise ValueError('El Excel ha cambiado o no está disponible. No se sobrescriben ediciones manuales; hay que conciliarlas primero.')
        if filas_excel(excel) != len(ledger['archivos']):
            raise ValueError('El número de filas no coincide con los documentos registrados')
    elif excel.exists():
        raise ValueError('Ya existe un Excel sin registro asociado; no se sobrescribe')


def copiar_exclusivo(source, destination, digest):
    if destination.exists():
        if destination.is_symlink() or base.sha256(destination) != digest:
            raise ValueError('Conflicto de archivo: ' + str(destination))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with source.open('rb') as src, destination.open('xb') as dst:
            created = True
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        if base.sha256(destination) != digest:
            raise ValueError('Fallo de comprobación de copia: ' + str(destination))
    except Exception:
        # Sólo se retira una copia incompleta creada por esta operación; nunca un original.
        if created:
            destination.unlink(missing_ok=True)
        raise


def recuperar(control, destination):
    pointer = control / 'transaccion.json'
    if not pointer.exists():
        return
    plan = base.leer(pointer)
    stage = Path(plan['stage']).resolve()
    if not base.contenido_en(stage, control.resolve()) or stage == control.resolve():
        raise ValueError('Área de transacción no válida')
    ledger_path = control / 'registro.json'
    old = base.leer(ledger_path) if ledger_path.exists() else {'revision':None}
    target = base.leer(stage / 'registro_nuevo.json')
    validar_registro(target)
    if target['cliente'] != destination.name or plan['revision_anterior'] is not None and not re.fullmatch(r'[0-9a-f]{32}',plan['revision_anterior']):
        raise ValueError('Identidad de transacción no válida')
    expected_copies = {(i['archivo_final'],i['sha256']) for i in target['archivos']}
    if any((i['archivo_final'],i['sha256']) not in expected_copies for i in plan['nuevos']):
        raise ValueError('Copias no reconocidas en la transacción')
    if old['revision'] not in {plan['revision_anterior'],target['revision']}:
        raise ValueError('El registro ha cambiado durante una transacción')
    excel = destination / target['excel']
    actual_excel = base.sha256(excel) if excel.exists() else None
    if actual_excel not in {plan['excel_anterior'], target['excel_sha256']}:
        raise ValueError('El Excel ha cambiado durante una transacción; no se sobrescribe')
    for item in plan['nuevos']:
        copiar_exclusivo(stage / 'copias' / item['archivo_final'], destination / 'facturas' / item['archivo_final'], item['sha256'])
    if actual_excel != target['excel_sha256']:
        staged_excel = stage / 'nuevo.xlsx'
        if not staged_excel.is_file() or base.sha256(staged_excel) != target['excel_sha256']:
            raise ValueError('No se puede recuperar el Excel preparado')
        if excel.exists():
            backup = control / 'copias_excel' / (str(plan['revision_anterior']) + '.xlsx')
            copiar_exclusivo(excel, backup, plan['excel_anterior'])
        destination.mkdir(parents=True, exist_ok=True)
        os.replace(staged_excel, excel)
    atomico(ledger_path, target)
    verificar_salida(destination, target)
    pointer.unlink()
    for item in plan['nuevos']:
        try:
            (stage / 'copias' / item['archivo_final']).unlink(missing_ok=True)
        except OSError:
            pass  # La salida ya está verificada; se conserva el auxiliar bloqueado.


def listar(root, cfg):
    entry = base.resolver(root, cfg['entrada'])
    clients = []
    for p in sorted(entry.iterdir()):
        if p.is_dir() and not p.is_symlink() and not p.name.startswith('.'):
            current, omitted = inventario(p.resolve())
            clients.append({'cliente':p.name,'facturas_entrada':len(current),'otros_archivos':len(omitted)})
    return {'clientes':clients,'archivos_sueltos_sin_cliente':[p.name for p in entry.iterdir() if p.is_file() and p.name != '.gitkeep']}


def reconciliar(source, destination, control, ledger, cfg):
    """Restaura sólo salidas ausentes; conserva identidades y extracciones."""
    verificar_salida(destination, ledger, permitir_faltantes=True)
    missing = [i for i in ledger['archivos'] if not (destination/'facturas'/i['archivo_final']).exists()]
    excel = destination/ledger['excel']
    if not ledger['archivos']:
        return ledger, 0
    target = copy.deepcopy(ledger)
    clasificar(target, [], cfg)
    changed = any((a.get('marca'),a.get('duplicada_de')) != (b.get('marca'),b.get('duplicada_de'))
                  for a,b in zip(ledger['archivos'],target['archivos']))
    if not missing and excel.exists() and not changed:
        return ledger, 0
    target['revision'] = nuevo_id()
    target['version'] = base.VERSION
    stage = control/'lotes'/('reconciliacion_'+nuevo_id())
    stage.mkdir(parents=True)
    for item in missing:
        copiar_exclusivo(source/item['archivo_original'], stage/'copias'/item['archivo_final'], item['sha256'])
    generated = base.generar_excel(stage, 'reconciliado', filas_registro(target), cfg)
    if filas_excel(generated) != len(target['archivos']):
        raise ValueError('La reconstrucción no conserva todas las filas')
    os.replace(generated, stage/'nuevo.xlsx')
    target['excel_sha256'] = base.sha256(stage/'nuevo.xlsx')
    base.guardar_nuevo(stage/'registro_nuevo.json', target)
    atomico(control/'transaccion.json', {'stage':str(stage),'revision_anterior':ledger['revision'],
        'excel_anterior':base.sha256(excel) if excel.exists() else None,
        'nuevos':[{'archivo_final':i['archivo_final'],'sha256':i['sha256']} for i in missing]})
    recuperar(control, destination)
    return target, len(missing)


def preparar(root, cfg, cliente, entrada=None):
    source, destination, control = rutas(root, cfg, cliente, entrada)
    with bloqueo(control):
        recuperar(control, destination)
        ledger = registro(control, cliente, source)
        current, omitted = inventario(source)
        revisar_entrada(current, ledger)
        ledger, restored = reconciliar(source, destination, control, ledger, cfg)
        if inventario(source)[0] != current:
            raise ValueError('La entrada cambió durante la reconciliación; vuelve a preparar')
        verificar_salida(destination, ledger)
        known = {i['clave']:i for i in ledger['archivos']}
        pending = [(k,v) for k,v in current.items() if k not in known]
        if not pending:
            return {'cliente':cliente,'nuevos':0,'copias_restauradas':restored,'entrada':len(current),'salida':len(known),
                    'filas_excel':len(known),'excel':str(destination / ledger['excel']) if known else None,'omitidos':omitted,
                    'duplicadas':sum(i['marca']=='DUPLICADA' for i in ledger['archivos']),
                    'con_incidencias':sum(bool(i['motivos']) for i in ledger['archivos']),
                    'informe':str(control / 'ultimo_resultado.json') if (control/'ultimo_resultado.json').exists() else None}
        run = control / 'lotes' / nuevo_id()
        run.mkdir(parents=True)
        manifest = {'cliente':cliente,'entrada':str(source),'revision_base':ledger['revision'],
                    'documentos':[dict(v,clave=k) for k,v in pending], 'todos':current,'omitidos':omitted}
        by_hash = {i['sha256']:i['datos'] for i in ledger['archivos']}
        extractions = []
        for _, item in pending:
            data = copy.deepcopy(by_hash[item['sha256']]) if item['sha256'] in by_hash else base.vacia(item)
            data.update(archivo_original=item['archivo_original'],sha256=item['sha256'],cliente_origen=cliente)
            extractions.append(data)
        base.guardar_nuevo(run / 'manifiesto.json',manifest)
        base.guardar_nuevo(run / 'extraccion.json',{'version_esquema':'1.0','cliente':cliente,
            'entrada':str(source),'lote_id':run.name,'manifiesto_sha256':base.sha256(run/'manifiesto.json'),
            'facturas':extractions})
        return {'cliente':cliente,'nuevos':len(pending),'copias_restauradas':restored,'ya_registrados':len(known),'lote':str(run),'omitidos':omitted}


def datos_para_excel(data):
    """Un dato mal formado se deja vacío en su celda, sin perder el registro."""
    f = copy.deepcopy(data)
    for k in ('fecha','fecha_contable'):
        try:
            if not isinstance(f.get(k), str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}',f[k]):
                raise ValueError()
            date.fromisoformat(f[k])
        except (ValueError,TypeError):
            f[k] = None
    for k in ('base_imponible','importe_iva','total'):
        try:
            base.numero(f.get(k))
        except (ValueError,TypeError):
            f[k] = None
    if not isinstance(f.get('impuestos'),list):
        f['impuestos'] = []
    for tax in f['impuestos']:
        if isinstance(tax,dict):
            for k in ('base','tipo','cuota'):
                try:
                    base.numero(tax.get(k))
                except (ValueError,TypeError):
                    tax[k] = None
    return f


def clasificar(ledger, additions, cfg):
    identities = {}
    used = {i['archivo_final'].casefold() for i in ledger['archivos']}
    for item in ledger['archivos'] + additions:
        f = item['datos']
        identity = base.identidad_factura(f)
        reference = identities.get(identity) if identity is not None else None
        reasons = base.validar_factura(f,cfg)
        item['marca'] = 'DUPLICADA' if reference else 'REVISAR' if reasons else None
        item.pop('duplicada_de',None)
        if reference:
            reasons.insert(0,'Coincidencia de número de factura y total con: '+reference)
            item['duplicada_de'] = {'cliente':ledger.get('cliente'), 'archivo_original':reference,
                                   'numero_factura':identity[0], 'total':f['total']}
        item['motivos'] = reasons
        if 'archivo_final' not in item:
            number = base.seguro(f.get('numero_factura') or 'SIN_NUMERO',40)
            supplier = base.seguro(f.get('proveedor') or 'SIN_PROVEEDOR',45)
            prefix = 'DUPLICADA_' if reference else 'PENDIENTE_' if not f.get('numero_factura') or not f.get('proveedor') else ''
            stem = prefix + number + '_' + supplier
            ext = Path(item['archivo_original']).suffix
            candidate = stem + ext
            if candidate.casefold() in used:
                candidate = stem + '_' + item['id'][:10] + ext
            if candidate.casefold() in used:
                raise ValueError('Conflicto de nombres de salida')
            item['archivo_final'] = candidate
            used.add(candidate.casefold())
        if identity is not None:
            identities.setdefault(identity,item['archivo_original'])


def filas_registro(ledger):
    return [{'datos':datos_para_excel(i['datos']),'marca':i['marca'],
             'archivo_final':i['archivo_final'],
             'nota_excel':'Original: '+i['archivo_original']+'\n'+'\n'.join(i['motivos'])} for i in ledger['archivos']]


def actualizar(root,cfg,cliente,datos=None,entrada=None):
    """Reexporta las filas existentes sin añadir archivos ni alterar las copias."""
    source,destination,control = rutas(root,cfg,cliente,entrada)
    with bloqueo(control):
        recuperar(control,destination)
        ledger=registro(control,cliente,source)
        current,omitted=inventario(source)
        revisar_entrada(current,ledger)
        verificar_salida(destination,ledger)
        if not ledger['archivos']:
            raise ValueError('No hay registros acumulados que actualizar')
        target=copy.deepcopy(ledger)
        items={i['archivo_original']:i for i in target['archivos']}
        if datos:
            updates=base.leer(base.resolver(root,datos)).get('facturas')
            if not isinstance(updates,list):
                raise ValueError('Las correcciones deben contener una lista facturas')
            seen=set()
            for update in updates:
                if not isinstance(update,dict) or set(update)-{'archivo_original','sha256','subconceptos','concepto','lineas_concepto','partida','tipo_gasto','pais_codigo'}:
                    raise ValueError('Sólo se admiten correcciones de concepto, desglose, país y partida')
                name=update.get('archivo_original')
                if name in seen or name not in items or update.get('sha256')!=items[name]['sha256']:
                    raise ValueError('Identidad de corrección no válida')
                seen.add(name)
                for field in ('lineas_concepto', 'partida', 'tipo_gasto', 'pais_codigo'):
                    if field in update:
                        items[name]['datos'][field] = update[field]
                if 'subconceptos' in update:
                    parts=update['subconceptos']
                    if not isinstance(parts,list) or not parts or not all(base.texto(p) for p in parts):
                        raise ValueError('subconceptos debe contener descripciones no vacías')
                    items[name]['datos']['subconceptos']=parts
                if 'concepto' in update:
                    if not base.texto(update['concepto']):
                        raise ValueError('concepto debe ser texto')
                    items[name]['datos']['concepto']=update['concepto']
        clasificar(target,[],cfg)
        target['revision']=nuevo_id()
        target['version']=base.VERSION
        stage=control/'lotes'/('actualizacion_'+nuevo_id())
        stage.mkdir(parents=True)
        generated=base.generar_excel(stage,'actualizado',filas_registro(target),cfg)
        if filas_excel(generated)!=len(target['archivos']):
            raise ValueError('El Excel actualizado no conserva todas las filas')
        os.replace(generated,stage/'nuevo.xlsx')
        target['excel_sha256']=base.sha256(stage/'nuevo.xlsx')
        base.guardar_nuevo(stage/'registro_nuevo.json',target)
        atomico(control/'transaccion.json',{'stage':str(stage),'revision_anterior':ledger['revision'],
                'excel_anterior':ledger['excel_sha256'],'nuevos':[]})
        recuperar(control,destination)
        if inventario(source)[0]!=current:
            raise ValueError('La entrada cambió durante la actualización; vuelve a comprobar los recuentos')
        report={'cliente':cliente,'actualizacion':'formato y conceptos','nuevos':0,'entrada':len(current),
                'salida':len(target['archivos']),'filas_excel':filas_excel(destination/target['excel']),
                'pendientes_nuevos':len(current)-len(target['archivos']),
                'duplicadas':sum(i['marca']=='DUPLICADA' for i in target['archivos']),
                'excel':str(destination/target['excel']),'omitidos':omitted,
                'informe':str(control/'ultimo_resultado.json'),
                'incidencias':[{'archivo':i['archivo_original'],'marca':i['marca'],'motivos':i['motivos']} for i in target['archivos'] if i['motivos']]}
        atomico(control/'ultimo_resultado.json',report)
        return report


def completar(root, cfg, cliente, lote, entrada=None):
    source, destination, control = rutas(root,cfg,cliente,entrada)
    run = base.resolver(root,lote)
    if not base.contenido_en(run,control / 'lotes'):
        raise ValueError('Lote fuera del área de trabajo del cliente')
    with bloqueo(control):
        recuperar(control,destination)
        ledger = registro(control,cliente,source)
        manifest = base.leer(run / 'manifiesto.json')
        if manifest['cliente'] != cliente or Path(manifest['entrada']).resolve() != source or manifest['revision_base'] != ledger['revision']:
            raise ValueError('El lote ya se ha completado o el cliente ha cambiado; prepara de nuevo para no repetir filas')
        current, omitted = inventario(source)
        revisar_entrada(current,ledger)
        if current != manifest['todos']:
            raise ValueError('La entrada ha cambiado desde la preparación; vuelve a preparar el lote')
        verificar_salida(destination,ledger)
        extraction = base.leer(run / 'extraccion.json')
        if (extraction.get('cliente') != cliente or extraction.get('entrada') != str(source)
                or extraction.get('lote_id') != run.name
                or extraction.get('manifiesto_sha256') != base.sha256(run/'manifiesto.json')):
            raise ValueError('La extracción no está vinculada a este cliente y lote; vuelve a preparar la carpeta correcta')
        records = extraction.get('facturas')
        if extraction.get('version_esquema') != '1.0' or not isinstance(records,list) or not all(isinstance(f,dict) for f in records):
            raise ValueError('Extracción no válida')
        names = [f.get('archivo_original') for f in records]
        if len(set(names)) != len(names) or sorted(names) != sorted(i['archivo_original'] for i in manifest['documentos']):
            raise ValueError('Debe haber un registro por cada nuevo archivo del lote')
        by_name = {f['archivo_original']:f for f in records}
        additions = []
        for item in manifest['documentos']:
            data = by_name[item['archivo_original']]
            if data.get('sha256') != item['sha256']:
                raise ValueError('La extracción no conserva el hash original')
            if data.get('cliente_origen') != cliente:
                raise ValueError('La factura extraída pertenece a otro cliente: '+item['archivo_original'])
            additions.append(dict(item,id=nuevo_id(),datos=data))
        target = copy.deepcopy(ledger)
        clasificar(target,additions,cfg)
        target['archivos'].extend(additions)
        target['revision'] = nuevo_id()
        target['version'] = base.VERSION
        stage = run / ('transaccion_' + nuevo_id())
        stage.mkdir()
        for item in additions:
            copiar_exclusivo(source / item['archivo_original'],stage / 'copias' / item['archivo_final'],item['sha256'])
        results = filas_registro(target)
        exported = base.generar_excel(stage,'acumulado',results,cfg)
        if filas_excel(exported) != len(current):
            raise ValueError('No coincide el número de filas del Excel preparado')
        os.replace(exported,stage / 'nuevo.xlsx')
        target['excel_sha256'] = base.sha256(stage / 'nuevo.xlsx')
        base.guardar_nuevo(stage / 'registro_nuevo.json',target)
        plan = {'stage':str(stage),'revision_anterior':ledger['revision'],
                'excel_anterior':ledger['excel_sha256'],
                'nuevos':[{'archivo_final':i['archivo_final'],'sha256':i['sha256']} for i in additions]}
        atomico(control / 'transaccion.json',plan)
        recuperar(control,destination)
        final_current, _ = inventario(source)
        if final_current != current:
            raise ValueError('Se ha actualizado la salida, pero la entrada cambió durante el trabajo. Vuelve a ejecutar para reconciliar los recuentos.')
        report = {'cliente':cliente,'nuevos':len(additions),'entrada':len(current),'salida':len(target['archivos']),
                  'filas_excel':filas_excel(destination / target['excel']),
                  'duplicadas':sum(i['marca']=='DUPLICADA' for i in target['archivos']),
                  'posibles_duplicadas':sum(i['marca']=='POSIBLE DUPLICADA' for i in target['archivos']),
                  'con_incidencias':sum(bool(i['motivos']) for i in target['archivos']),
                  'excel':str(destination / target['excel']),'carpeta_facturas':str(destination / 'facturas'),
                  'informe':str(control / 'ultimo_resultado.json'),
                  'omitidos':omitted,'incidencias':[{'archivo':i['archivo_original'],'copia':i['archivo_final'],'marca':i['marca'],'motivos':i['motivos']} for i in target['archivos'] if i['motivos']]}
        atomico(control / 'ultimo_resultado.json',report)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion',choices=['listar','preparar','completar','actualizar'])
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--cliente')
    parser.add_argument('--entrada')
    parser.add_argument('--lote')
    parser.add_argument('--datos')
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        cfg = base.configuracion(root)
        if args.accion == 'listar':
            result = listar(root,cfg)
        else:
            if not args.cliente:
                parser.error('Se requiere --cliente')
            if args.accion == 'actualizar':
                result = actualizar(root,cfg,args.cliente,args.datos,args.entrada)
            elif args.accion == 'completar':
                if not args.lote:
                    parser.error('Se requiere --lote')
                result = completar(root,cfg,args.cliente,args.lote,args.entrada)
            else:
                result = preparar(root,cfg,args.cliente,args.entrada)
        print(json.dumps(result,ensure_ascii=True,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as ex:
        parser.exit(1,f'Error: {ex}\n')


if __name__ == '__main__':
    main()
