"""Cada envío usa una raíz aislada: nunca recupera registros de otro envío."""
import argparse
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import clientes


def preparar(root, cliente, archivos):
    root = Path(root).resolve()
    cfg = clientes.base.configuracion(root)
    # Valida el nombre antes de crear rutas.
    if not cliente or cliente.startswith('.') or clientes.re.search(r'[<>:"/\\|?*\x00-\x1f]',cliente) or cliente != cliente.rstrip(' .'):
        raise ValueError('Nombre de cliente no válido')
    selected = [Path(p).resolve() for p in archivos]
    if not selected or any(not p.exists() for p in selected):
        raise ValueError('Indica los archivos o carpetas de este envío')
    envio_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:12]
    area = root/'NO TOCAR/trabajo/envios'
    if not clientes.base.contenido_en(area.resolve(),root):
        raise ValueError('Área de envío fuera del proyecto')
    work = area/envio_id
    source = work/'entrada'/cliente
    source.mkdir(parents=True)
    for p in selected:
        destination = source/p.name
        if destination.exists():
            raise ValueError('Dos entradas tienen el mismo nombre; conserva carpetas distintas')
        if p.is_dir():
            if any(f.is_symlink() for f in p.rglob('*')):
                raise ValueError('El envío no admite enlaces simbólicos')
            if clientes.base.contenido_en(work,p):
                raise ValueError('La entrada no puede contener el área de ejecución')
            shutil.copytree(p,destination)
        else:
            shutil.copy2(p,destination)
    cfg.update(modo='clientes',entrada='entrada',resultados='resultados',control='NO TOCAR/control')
    config = work/'NO TOCAR/config/config.json';config.parent.mkdir(parents=True)
    config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2))
    metadata = {'cliente':cliente,'envio_id':envio_id,'proyecto':str(root),'version':clientes.base.VERSION}
    result = clientes.preparar(work,cfg,cliente)
    if not result.get('lote'):
        raise ValueError('El envío no contiene documentos compatibles')
    metadata['lote'] = result['lote']
    (work/'envio.json').write_text(json.dumps(metadata,indent=2))
    return dict(result,envio=str(work),envio_id=envio_id,alcance='solo este envío')


def completar(root, envio):
    root=Path(root).resolve();work=Path(envio).resolve()
    area=(root/'NO TOCAR/trabajo/envios').resolve()
    if work.parent != area or not clientes.base.contenido_en(area,root):
        raise ValueError('Envío fuera del proyecto')
    meta=json.loads((work/'envio.json').read_text())
    if meta['proyecto'] != str(root) or meta['envio_id'] != work.name:
        raise ValueError('Identidad de envío incorrecta')
    cfg=clientes.base.configuracion(work);cliente=meta['cliente']
    if meta.get('completado'):
        result=clientes.preparar(work,cfg,cliente)
    else:
        result=clientes.completar(work,cfg,cliente,meta['lote'])
        meta['completado']=True
        (work/'envio.json').write_text(json.dumps(meta,indent=2))
    source,destination,control=clientes.rutas(work,cfg,cliente)
    public=root/'resultados'/cliente/work.name
    if not clientes.base.contenido_en(public.resolve(),root/'resultados'):
        raise ValueError('Salida redirigida')
    if public.exists():
        # Una repetición sólo entrega la misma salida si todas sus copias coinciden.
        expected={str(p.relative_to(destination)):clientes.base.sha256(p) for p in destination.rglob('*') if p.is_file()}
        actual={str(p.relative_to(public)):clientes.base.sha256(p) for p in public.rglob('*') if p.is_file()}
        if actual != expected:raise ValueError('La entrega existente ha cambiado')
    else:
        shutil.copytree(destination,public)
    zip_path=work/('Resultados_'+cliente+'_'+work.name+'.zip')
    if not zip_path.exists():
        with ZipFile(zip_path,'x',ZIP_DEFLATED) as z:
            for p in sorted(public.rglob('*')):
                if p.is_file():z.write(p,Path(cliente)/p.relative_to(public))
    return dict(result,envio_id=work.name,excel=str(public/('Facturas_'+clientes.base.seguro(cliente,60)+'.xlsx')),carpeta_facturas=str(public/'facturas'),zip=str(zip_path),alcance='solo este envío')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion',choices=['preparar','completar'])
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--cliente');parser.add_argument('--archivos',nargs='+');parser.add_argument('--envio')
    args=parser.parse_args()
    try:
        if args.accion=='preparar':
            if not args.cliente or not args.archivos:parser.error('Faltan cliente o archivos')
            result=preparar(args.root,args.cliente,args.archivos)
        else:
            if not args.envio:parser.error('Falta --envio')
            result=completar(args.root,args.envio)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError) as ex:parser.exit(1,str(ex)+'\n')

if __name__=='__main__':main()
