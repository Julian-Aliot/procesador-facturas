# Uso sencillo: una petición, un envío

Activa la Skill con peticiones naturales: «procesa facturas», «hazme el Excel», «ordena estos PDF» o «procesa este ZIP para Empresa A». No exijas comandos, rutas ni invocar la Skill explícitamente.

Identifica el cliente de la petición o del contexto explícito; si falta o es ambiguo pregunta sólo «¿Para qué cliente preparo estas facturas?». No lo deduzcas del receptor de un documento sin autorización. Si faltan archivos, pide adjuntar ZIP/PDF/imágenes o indicar una carpeta accesible. En la nube no se puede leer directamente una ruta del PC.

Antes de procesar, comprueba main siguiendo versiones.md. Trabaja con la versión descargada durante todo el envío. Aplica envios.md para aislar exclusivamente los archivos seleccionados por el usuario. No busques historial aunque el cliente se haya usado antes. No pidas Excels, originales ni controles de otras tandas.

Si alguien pide «añadir al Excel anterior», explica que el modo actual produce resultados independientes y no los combina. Pregunta sólo si desea procesar los nuevos documentos como un envío separado o si quiere definir expresamente otra tarea de combinación; no acumules silenciosamente.

Prepara carpetas y comprueba dependencias automáticamente. Comprueba la posibilidad de subida a Drive al empezar, para no prometer una entrega no disponible. No instales dependencias silenciosamente.

Usa lenguaje sencillo. Explica problemas concretos y conserva los datos desconocidos vacíos. Al terminar entrega dos enlaces verificados de Drive, los recuentos y las incidencias reales. Si sólo falla subir, conserva los archivos y reintenta la entrega sin reprocesar.

Ejemplo: «Preparadas 12 facturas para Empresa A en este envío: 12 copias y 12 filas. Hay 2 duplicados dentro del envío y 1 documento para revisar. [Excel en Drive] · [ZIP en Drive]».

Los resultados quedan separados por id de envío. El usuario decide si los combina después. No se mantienen ni recuperan historiales de cliente en el flujo habitual.

## Descargas

La entrega preferida es Drive según entrega-drive.md. La interfaz probada de Codex abría enlaces locales y sandbox en el visor sin descarga utilizable. No presentes esa vía como confirmada. Sólo utiliza una alternativa de descarga si el entorno actual la documenta y se verifica; no inventes enlaces ni intentes crear carpetas protegidas o cambiar permisos para forzar una descarga.
