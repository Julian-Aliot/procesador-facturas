# Procesar un envío independiente

1. Comprueba la versión según versiones.md y las dependencias con `source 'NO TOCAR/herramientas/entorno-codex.sh'` en el mismo shell que ejecuta los scripts.
2. Usa sólo los adjuntos de la petición actual o la carpeta seleccionada explícitamente. Descomprime ZIP en una carpeta técnica nueva, validando rutas, enlaces y conflictos. No ejecutes sus contenidos ni extraigas encima del proyecto. Un mismo nombre de cliente no implica recuperar nada de otra petición.
3. Ejecuta `python '<skill>/scripts/envios.py' preparar --root '<proyecto>' --cliente '<cliente>' --archivos '<archivo o carpeta seleccionada>' [...]`. El script copia exclusivamente esa selección a una raíz aislada y devuelve envio, envio_id y lote. No pasa por la entrada acumulada del cliente del proyecto principal.
4. Lee extraccion.md y plantilla.md. Completa el extraccion.json del lote devuelto, con un registro y evidencias por cada archivo. No cambies identidades, hashes ni cliente_origen. Lee todas las páginas. El archivo está dentro de la raíz aislada; las rutas del manifiesto parten de esa raíz, no del proyecto principal.
5. Ejecuta `python '<skill>/scripts/envios.py' completar --root '<proyecto>' --envio '<envio devuelto>'`. Este comando valida, genera el Excel y las copias, los entrega en resultados/<cliente>/<id-envio> y prepara un ZIP. Sólo da por terminado si entrada, copias y filas coinciden.
6. Sube el XLSX y el ZIP devueltos a una carpeta nueva de ejecución en Drive según entrega-drive.md y entrega los enlaces verificados. Las incidencias se explican en lenguaje sencillo. Si falla sólo la transferencia, reintenta esa transferencia sin crear un envío nuevo.

Cada nueva petición crea un id nuevo, incluso para el mismo cliente o los mismos archivos. Repetir los documentos en otro envío no los considera ya procesados. Los duplicados se comprueban sólo entre documentos del envío actual. Dentro del envío, las utilidades conservan el estado técnico necesario para completar/reintentar; no es historial del cliente ni se restaura en otro chat.

No se mezclan tandas ni se pide una copia anterior del proyecto. El usuario combina resultados por su cuenta si quiere. Los comandos históricos de clientes.md se conservan por compatibilidad técnica y pruebas, pero no son el flujo habitual.
