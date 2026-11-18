# Flujo por cliente · 0.7

## Contrato confirmado por el usuario

- Cada carpeta inmediata de `entrada/` representa un cliente. Recorrer todas sus subcarpetas.
- Una copia y una fila por **archivo de factura**. Dos rutas distintas son dos archivos recibidos, incluso si sus bytes coinciden.
- Una ejecución repetida sobre las mismas rutas y contenidos no añade copias ni filas.
- Conservar todas las tandas en entrada. No mover, borrar o renombrar originales.
- Incluir archivos ilegibles, corruptos o con campos desconocidos: copiar los bytes disponibles, dejar vacías las celdas desconocidas y comunicar la incidencia aparte.
- Un solo Excel de 16 columnas por cliente, acumulado entre tandas y ejercicios. No separar por año salvo que el usuario cambie esa regla.
- Cada PDF se trata como un documento/una fila. Si contiene varias facturas, señalarlo para revisión; no dividir silenciosamente ni inventar una factura resumen.

Salida: `resultados/<cliente>/Facturas_<cliente>.xlsx` y `resultados/<cliente>/facturas/`. Las subcarpetas de entrada se aplanan en la salida. Los nombres son `NUMERO_PROVEEDOR.ext`; datos ausentes generan un nombre provisional explícito. Se conserva la extensión original de PDF o imagen, sin conversiones. Se añaden sufijos cuando hace falta evitar conflictos.

## Procedimiento de Codex

1. Lee `extraccion.md` y `plantilla.md`. Ejecuta `python "<skill>/scripts/clientes.py" listar --root <proyecto>` para descubrir los clientes sin modificarlos. Los archivos sueltos en la raíz de entrada se comunican como sin asignar, no se mueven. Selecciona exclusivamente los clientes pedidos; una orden sobre una carpeta nueva no autoriza actualizar las anteriores. La carpeta de entrada debe ser exactamente entrada/<cliente>. --entrada sólo se acepta si apunta a esa misma carpeta; la raíz general, una subcarpeta de proveedor y carpetas de otro cliente se rechazan.
2. Por cada cliente seleccionado, ejecuta `python "<skill>/scripts/clientes.py" preparar --root <proyecto> --cliente <nombre>`. Compara siempre entrada, copias de resultados y filas del Excel. Restaura automáticamente las copias y el Excel ausentes usando los originales y la extracción registrada; después devuelve el lote de archivos nuevos o un resumen sin nuevos, con `copias_restauradas`. Una ejecución a medias no exige reiniciar ni borrar el registro. No uses el inventario antiguo para este flujo.
3. Completa `extraccion.json` del lote con un registro por archivo de su manifiesto. Interpreta con Codex y herramientas locales. Agrupa hashes iguales para leer el contenido una sola vez y rellenar los registros de cada ruta por separado. Los archivos idénticos a otros ya registrados reutilizan sus datos, con la identidad del nuevo archivo. No cambies rutas ni hashes.
4. Extrae los datos y el resumen en español. Si no es legible, conserva null y añade motivo. No omitas el registro para lograr una tasa de validación mejor. La carpeta del cliente es la asignación declarada; el receptor de cada documento se conserva literalmente y cualquier conflicto se comunica. No rellenar NIF ausentes desde otros documentos como si se hubieran leído.
5. Ejecuta `python "<skill>/scripts/clientes.py" completar --root <proyecto> --cliente <nombre> --lote <lote>`. El script conserva el historial, marca duplicados, prepara el nuevo Excel, copia y verifica archivos y comprueba los recuentos. El Excel debe estar cerrado para sustituirlo en Windows.
6. Entrega por cliente enlaces a Excel y carpeta, nuevos archivos, total de entrada, copias, filas y número de duplicados/incidencias. Sólo declarar completado si los tres recuentos coinciden. Mostrar avisos de formatos excluidos y archivos sin cliente.

No sumar monedas distintas. Las columnas son exactamente las de `plantilla.md`; no añadir Estado o Duplicada como columna.

## Duplicados y revisión

Una factura es DUPLICADA únicamente si coincide el número de factura completo (sin espacios exteriores) y el total final a pagar, numéricamente exacto, con una anterior del mismo cliente. No usar hash, NIF, proveedor o fecha como clave alternativa. Si falta número o total, no asignar duplicado. El primer registro permanece blanco; sólo los siguientes se resaltan en amarillo. Todas las rutas conservan copia y fila. Los hashes se usan para integridad y reutilizar lecturas, no para clasificar duplicados.

Todas las demás filas permanecen blancas. Otras incidencias se explican en la nota y en el informe interno. También los registros completamente desconocidos tienen una fila de tabla y una nota con su archivo, aunque las 16 celdas queden vacías. Los recuentos se hacen sobre filas de la tabla, no mediante CONTARA de una columna que puede tener valores ausentes.

## Integridad y fallos

Los auxiliares persistentes están en `NO TOCAR/control/<id-cliente>/`: registro, lotes, transacción pendiente, copia del Excel anterior e informe de incidencias. No moverlos ni borrarlos al añadir tandas; son la memoria local del procesamiento. No se necesita una base de datos.

Si faltan copias o el Excel, `preparar` los reconstruye con una transacción recuperable, sin duplicar filas ni releer mediante IA los documentos ya extraídos. Si también hay archivos nuevos, se procesan después de esa reparación. Si un original desaparece/cambia, una copia existente cambia, hay archivos ajenos en salida o el Excel existente ha sido editado manualmente, detener la actualización y explicar qué debe conciliarse. No destruir datos para forzar los recuentos. La igualdad se refiere a los archivos compatibles presentes en entrada; otros formatos se enumeran como excluidos. La coincidencia de recuentos es necesaria, pero también se comprueban las identidades y los hashes para no dar por buenas copias equivocadas.

Una interrupción entre copias, Excel y registro se recupera en la siguiente preparación bajo el mismo bloqueo. Si hubo cierre forzoso y quedó `escritor.lock`, comprobar que no haya un proceso escritor activo antes de retirar ese archivo de bloqueo; nunca eliminarlo automáticamente basándose sólo en su antigüedad. No tocar los originales ni borrar la transacción pendiente para resolver el bloqueo.

Si hay un archivo accesible pero corrupto, puede copiarse y registrarse como dudoso. Si no se puede leer físicamente para copiarlo, no declarar igualdad ni éxito: explicar el error de acceso.

## Actualizar un Excel existente

Para aplicar cambios de formato sin añadir archivos, usa `python "<skill>/scripts/clientes.py" actualizar --root <proyecto> --cliente <nombre>`. Para completar conceptos ya registrados, añade `--datos <json>` con `{"facturas":[{"archivo_original":"ruta.pdf","sha256":"hash original","subconceptos":["Servicio completo", "Otro servicio"]}]}`. Relee los originales antes de preparar las correcciones. Sólo se admiten ajustes de concepto; rutas y hashes deben coincidir con el registro. Se conservan copias y filas, se verifica integridad y se guarda copia de seguridad del Excel anterior. El libro debe estar cerrado. No edites el registro directamente.

La última columna ARCHIVO FACTURA permite abrir la copia renombrada con un clic. Usa un enlace relativo desde el Excel a facturas/<nombre>; al compartir, conserva el Excel y la subcarpeta facturas juntos. La duplicidad se decide exclusivamente por número íntegro y total final a pagar coincidentes dentro del cliente; no por hash ni por NIF.
