# Entrega habitual por Google Drive

El usuario ha autorizado guardar el ZIP con el Excel de resultados dentro en su Google Drive conectado como parte de «procesa las facturas para <cliente>». No necesita repetir esta preferencia en cada tanda. Esta autorización no incluye hacer públicos los archivos ni compartirlos con terceros.

## Antes de procesar

Comprueba que la sesión tiene una conexión de Drive con operaciones para subir archivos binarios existentes, no sólo buscar o leer. Que un complemento figure instalado no demuestra acceso de escritura. Si faltan herramientas, informa temprano de que la entrega por Drive está pendiente; no prometas enlaces. No cambies permisos ni conexiones silenciosamente. No uses la sesión web como sustituto automático de una conexión que no está disponible; sigue las reglas del entorno para cualquier alternativa.

## Destino y subida

Usa la cuenta de Drive conectada autorizada. Si hay varias cuentas y ninguna está seleccionada, pregunta cuál usar. Reutiliza la carpeta de destino que el usuario haya indicado y cuyo identificador se haya verificado. Si no hay destino indicado, crea con las herramientas disponibles una carpeta privada «Procesador de facturas», y dentro una carpeta por cliente y otra por ejecución. Si aparecen varias carpetas homónimas sin un identificador previamente confirmado, pregunta cuál usar; no elijas por nombre a ciegas. Conserva sus identificadores en configuración local excluida de Git para siguientes tandas.

Verifica el XLSX y el ZIP antes de subir según uso-sencillo.md. Subir únicamente el ZIP terminado con el Excel y facturas/ dentro. El Excel independiente se usa para comprobaciones locales. Conservar las salidas anteriores. Si la subida se interrumpe, comprobar metadatos del destino antes de repetir y reintentar la transferencia del mismo ZIP.

## Enlaces y respuesta

Verifica identificador, nombre, tipo y tamaño del ZIP y, cuando esté disponible, checksum o contenido. Devuelve un único enlace real etiquetado «ZIP en Drive». Mantén los permisos privados. Informa de recuentos e incidencias junto al enlace.

Si no se puede subir, di «Procesamiento terminado; entrega por Drive pendiente: <causa concreta>». Conserva los archivos generados y facilita el siguiente paso comprobable. No sustituyas esta entrega por enlaces al visor de Codex presentados como descargas. Una carpeta local llamada downloads no garantiza descarga en el PC del usuario. No subas resultados a GitHub ni a servicios públicos.

Cada ejecución entrega sólo sus propios documentos. No busques ni recuperes historial en Drive y no combines entregas de un mismo cliente. La carpeta del cliente es organizativa, no una fuente de facturas previas. El usuario decide si combina archivos después.
