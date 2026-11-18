// Excel de análisis: una sola hoja, exactamente 18 columnas, sin modificar originales.
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

async function main() {
  const [inputPath, outputPath, previewDir] = process.argv.slice(2);
  if (!inputPath || !outputPath || !outputPath.endsWith('.xlsx')) {
    throw new Error('Uso: node exportar-excel.mjs <salida.json> <resultado.xlsx> [carpeta-previsualizaciones]');
  }
  try { await fs.access(outputPath); throw new Error('El destino ya existe; no se sobrescribe.'); }
  catch (err) { if (err.code !== 'ENOENT') throw err; }
  const modules = process.env.FACTURAS_NODE_MODULES || path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules');
  const require = createRequire(path.join(modules, '__facturas_resolver__.cjs'));
  let api;
  try { api = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href); }
  catch { throw new Error('No se encuentra artifact-tool del entorno de Codex. Consulta las dependencias del entorno; no se ha generado Excel.'); }
  const { FileBlob, SpreadsheetFile } = api;
  const payload = JSON.parse(await fs.readFile(inputPath, 'utf8'));
  if (payload.columnas?.length !== 18 || !Array.isArray(payload.filas) || payload.filas.some(r => !Array.isArray(r) || r.length !== 18)) {
    throw new Error('La salida debe tener exactamente 18 columnas por fila.');
  }
  const template = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../assets/plantilla-facturas.xlsx');
  const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(template));
  const sheet = wb.worksheets.getItem('Facturas');
  if (JSON.stringify(sheet.getRange('A5:R5').values[0]) !== JSON.stringify(payload.columnas)) {
    throw new Error('La plantilla y los encabezados de salida no coinciden.');
  }
  const values = payload.filas.map(row => row.map((value, col) => {
    if (value === null || value === undefined) return null;
    if (col === 7 || col === 9) {
      if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error('Fecha de salida no válida.');
      const date = new Date(value + 'T00:00:00Z');
      if (!Number.isFinite(date.getTime()) || date.toISOString().slice(0,10) !== value) throw new Error('Fecha de salida no válida.');
      return date;
    }
    if ([8,13,14].includes(col)) {
      if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Se esperaba un valor numérico en año o importes.');
      return value;
    }
    const text = String(value);
    return text.startsWith('=') ? "'" + text : text;
  }));
  // Sustituye la tabla vacía de la plantilla por el rango con las filas del lote.
  for (const table of [...sheet.tables.items]) table.delete();
  const last = Math.max(6, values.length + 5);
  if (values.length) sheet.getRange(`A6:R${last}`).values = values;
  const table = sheet.tables.add(`A5:R${last}`, true, 'RegistroFacturas');
  table.showFilterButton = true;
  // El blanco directo anula tanto los colores anteriores como las franjas de la tabla.
  sheet.getRange(`A6:R${last}`).format.fill = '#FFFFFF';
  sheet.getRange(`A6:R${last}`).format.wrapText = true;
  sheet.getRange(`A6:R${last}`).format.verticalAlignment = 'top';
  sheet.getRange(`A6:R${last}`).format.autofitRows();
  for (const col of ['C','G']) sheet.getRange(`${col}6:${col}${last}`).setNumberFormat('@');
  for (const col of ['H','J']) sheet.getRange(`${col}6:${col}${last}`).setNumberFormat('dd/mm/yyyy');
  for (let i=0; i<values.length; i++) {
    const currency = payload.monedas?.[i];
    const code = typeof currency === 'string' && /^[A-Z]{3}$/.test(currency) ? currency : null;
    sheet.getRange(`N${i+6}:O${i+6}`).setNumberFormat('#,##0.00' + (code ? ` "${code}"` : ''));
    const flag = payload.marcas?.[i];
    if (flag?.archivo) {
      if (/[\\/]/.test(flag.archivo) || flag.archivo === '.' || flag.archivo === '..') throw new Error('Nombre de copia no válido');
      // El enlace nativo se incorpora al paquete XLSX tras exportar, sin fórmulas.
      sheet.getRange(`Q${i+6}`).values = [['Abrir factura']];
      sheet.getRange(`Q${i+6}`).format.font = {color:'#0563C1',underline:'single'};
    }
    if (flag?.tipo === 'DUPLICADA') {
      sheet.getRange(`A${i+6}:R${i+6}`).format.fill = '#FFF2CC';
    }
    if (flag?.texto || flag?.archivo) {
      wb.notes.add({id:`Facturas:G${i+6}`,target:{cell:{sheetName:'Facturas',sheetId:sheet.sheetId,address:`G${i+6}`}},authorId:'',createdAt:'',body:{plainText:[flag.tipo,flag.texto,flag.archivo ? 'Copia: '+flag.archivo : null].filter(Boolean).join('\n')}});
    }
  }
  wb.recalculate();
  const errors = await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:10},maxChars:1000});
  if (/"(?:matches|count)"\s*:\s*[1-9]/.test(errors.ndjson)) throw new Error('Se han detectado errores en el libro.');
  await (await SpreadsheetFile.exportXlsx(wb)).save(outputPath);
  if (previewDir) {
    await fs.mkdir(previewDir, {recursive:true});
    for (const [range, name] of [[`A1:H${Math.min(last+1,14)}`,'identificacion'],[`I4:R${Math.min(last+1,14)}`,'conceptos']]) {
      const img = await wb.render({sheetName:'Facturas',range,scale:1.25,format:'png'});
      await fs.writeFile(path.join(previewDir, name+'.png'), new Uint8Array(await img.arrayBuffer()));
    }
  }
  console.log(JSON.stringify({excel:outputPath,filas:values.length,columnas:18}));
}

try { await main(); process.exit(0); }
catch (error) { console.error(error.message); process.exit(1); }
