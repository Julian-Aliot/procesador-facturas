# Procesador de facturas · 1.0

Cada petición procesa exclusivamente sus documentos y genera un Excel de 18 columnas y copias ordenadas. Los envíos del mismo cliente permanecen separados. No se recupera historial ni se acumulan tandas. El usuario decide si combina los resultados después.

Repositorio: https://github.com/Julian-Aliot/procesador-facturas · rama main.

## Uso por chat

Abre el proyecto en Codex, adjunta un ZIP/PDF/imágenes y escribe:

> Procesa este ZIP para Empresa A.

El agente comprueba la última revisión de main, lee AGENTS.md y la Skill, pregunta el cliente sólo si falta, prepara una ejecución independiente y entrega el Excel y el ZIP en tu Drive conectado. No necesita registros ni Excels anteriores.

Para actualizar una copia antigua en otra cuenta:

> Descarga la última versión de main de https://github.com/Julian-Aliot/procesador-facturas en una carpeta nueva, lee AGENTS.md y sigue su Skill. Cada envío es independiente; no recuperes historial. Comprueba Google Drive y las dependencias antes de procesar.

Las instrucciones actualizadas exigen comprobar main antes de cada envío, sin sobrescribir cambios locales ni cambiar el código durante un procesamiento. Una copia antigua debe actualizarse una primera vez para incorporar esta regla.

## Preparación técnica

Python 3.10+, openpyxl, Node y @oai/artifact-tool. El último depende del entorno Codex; no se presupone disponible en todos los entornos. Para PDF digital usa herramientas locales disponibles; los escaneos requieren visión. El agente no llama a APIs externas de IA u OCR ni instala dependencias silenciosamente.

```bash
source 'NO TOCAR/herramientas/entorno-codex.sh'
python 'NO TOCAR/skills/procesador-facturas/scripts/envios.py' preparar --root . --cliente 'Empresa A' --archivos '/ruta/a/los/documentos-de-este-envio'
```

El comando devuelve envio y lote. Codex completa extraccion.json del lote tras leer los documentos. Después:

```bash
python 'NO TOCAR/skills/procesador-facturas/scripts/envios.py' completar --root . --envio '<envio devuelto>'
```

Sólo los documentos seleccionados se copian a una raíz aislada en NO TOCAR/trabajo/envios/<id>. Los resultados quedan en resultados/<cliente>/<id>. Los registros internos sirven para terminar/reintentar ese envío y nunca se cargan en uno nuevo.

## Excel y controles

18 columnas. UE por país UE-27; CONCEPTO TOTAL junto a CONCEPTO, con una viñeta y coste explícito por línea; Partida al final: AUTONOMOS, FUNGIBLES u OTROS GASTOS según las reglas aprobadas. Ambigüedades y costes ausentes requieren revisión. No se inventan datos ni IVA cero.

Una fila y copia por documento compatible. Duplicados por número íntegro y total iguales únicamente dentro del envío. Las primeras copias permanecen blancas y las siguientes duplicadas amarillas. Se verifican originales, copias, filas, tipos de celda y enlaces relativos.

## Drive y privacidad

Se suben el XLSX sin conversión y el ZIP de resultados a una carpeta privada por cliente y ejecución. Debe estar disponible una conexión que permita subir archivos. Se verifican las subidas y se devuelven enlaces reales. Los envíos anteriores se conservan sin sobrescribirlos. El ZIP incluye el Excel y facturas/ para mantener sus enlaces.

GitHub contiene sólo el programa. Documentos, resultados y controles están excluidos. No se suben allí facturas ni se hacen públicos los archivos de Drive. El complemento instalado no garantiza que sus herramientas estén disponibles en todos los chats.

## Pruebas

```bash
source 'NO TOCAR/herramientas/entorno-codex.sh'
python -m unittest discover -s 'NO TOCAR/tests' -v
```

Los módulos acumulativos antiguos se conservan por compatibilidad y no se usan sobre clientes principales en el flujo habitual. Ningún cambio de modo borra historiales anteriores.
