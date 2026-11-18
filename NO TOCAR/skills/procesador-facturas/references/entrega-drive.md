# Entrega habitual por Google Drive

El usuario ha autorizado guardar el Excel y el ZIP de resultados en su Google Drive conectado como parte de «procesa las facturas para <cliente>». No necesita repetir esta preferencia en cada tanda. Esta autorización no incluye hacer públicos los archivos ni compartirlos con terceros.

## Antes de procesar

Comprueba que la sesión tiene una conexión de Drive con operaciones para subir archivos binarios existentes, no sólo buscar o leer. Que un complemento figure instalado no demuestra acceso de escritura. Si faltan herramientas, informa temprano de que la entrega por Drive está pendiente; no prometas enlaces. No cambies permisos ni conexiones silenciosamente. No uses la sesión web como sustituto automático de una conexión que no está disponible; sigue las reglas del entorno para cualquier alternativa.

## Destino y subida

Usa la cuenta de Drive conectada autorizada. Si hay varias cuentas y ninguna está seleccionada, pregunta cuál usar. Reutiliza la carpeta de destino que el usuario haya indicado y cuyo identificador se haya verificado. Si no hay destino indicado, crea con las herramientas disponibles una carpeta privada «Procesador de facturas», y dentro una carpeta por cliente y otra por ejecución. Si aparecen varias carpetas homónimas sin un identificador previamente confirmado, pregunta cuál usar; no elijas por nombre a ciegas. Conserva sus identificadores en configuración local excluida de Git para siguientes tandas.

Verifica el XLSX y el ZIP antes de subirlos siguiendo los controles de uso-sencillo.md. Sube sólo el Excel terminado y el ZIP con el Excel y facturas/. No subas originales adicionales, registros, extracciones, copias de seguridad ni archivos de otros clientes. Mantén el XLSX como archivo Excel, sin convertirlo automáticamente a Google Sheets.

Conserva las salidas de ejecuciones anteriores; no sobrescribas ni borres archivos por coincidencia de nombre. Si una subida se interrumpe, consulta el destino y compara los metadatos disponibles antes de repetirla. Si sólo se sube un archivo, informa de la entrega parcial y reintenta únicamente el que falta; no reproceses las facturas.

## Enlaces y respuesta

Verifica para cada subida su identificador, nombre, tipo y tamaño y, cuando la herramienta lo permita, su checksum o contenido. Usa el enlace real devuelto por Drive. Entrega dos enlaces claramente etiquetados: «Excel en Drive» y «ZIP en Drive». Si la conexión proporciona enlaces de descarga verificados, úsalos; si sólo proporciona enlaces de apertura, indícalo y explica que se descargan desde Drive. No inventes URLs de descarga ni afirmes que abrir un enlace equivale a descargarlo. Conserva los permisos privados: el usuario debe iniciar sesión en la cuenta autorizada.

Ejemplo: «Preparadas 16 facturas para Empresa A. Excel en Drive: <enlace verificado>. ZIP en Drive: <enlace verificado>. Incidencias: <resumen real>».

Si no se puede subir, di «Procesamiento terminado; entrega por Drive pendiente: <causa concreta>». Conserva los archivos generados y facilita el siguiente paso comprobable. No sustituyas esta entrega por enlaces al visor de Codex presentados como descargas. Una carpeta local llamada downloads no garantiza descarga en el PC del usuario. No subas resultados a GitHub ni a servicios públicos.

Drive almacena los entregables, pero no es automáticamente una copia del estado acumulado. Para continuar un cliente en otro entorno siguen siendo necesarios originales, resultados y control compatibles; un Excel o ZIP de resultados no reconstruye todo el historial.
