# Procesador de facturas para Codex

Proyecto para interpretar facturas con Codex y generar, por cliente, copias ordenadas y un Excel acumulado de 16 columnas. No llama a APIs de modelos ni a servicios OCR externos. La interpretación la realiza el agente; los scripts solos no interpretan las facturas.

## Para usarlo sin conocimientos técnicos

Con el proyecto abierto en Codex y sus instrucciones disponibles, adjunta un ZIP o las facturas y escribe, por ejemplo:

- «Procesa estas facturas para Empresa A».
- «Hazme el Excel de estos PDF para Empresa A».
- «Añade estas facturas al historial de Empresa A».

El agente prepara las carpetas, comprueba las dependencias y pregunta el cliente sólo si falta. Entrega el Excel y un ZIP con las copias ordenadas cuando los controles terminan. Si faltan documentos o hay un problema, explica el siguiente paso en lenguaje sencillo.

Para acumular en otra sesión no basta con el Excel ni con el ZIP de resultados: hacen falta también los originales y el registro de control compatible. Si falta el historial, el agente pedirá recuperarlo o permitirá elegir un resultado separado, sin dar por acumuladas las facturas anteriores. Los adjuntos y resultados no se suben a GitHub.

## Abrir en Codex online

1. Conecta y selecciona este repositorio en Codex y crea su entorno de trabajo.
2. Pide que lea `AGENTS.md` y `NO TOCAR/skills/procesador-facturas/SKILL.md`.
3. Comprueba el entorno ejecutando desde la raíz:

   ```bash
   source 'NO TOCAR/herramientas/entorno-codex.sh'
   ```

   Requiere Python 3.10+, openpyxl, Node y `@oai/artifact-tool`. El último es una dependencia del entorno Codex: no se presupone que esté disponible en todos los entornos ni se instala automáticamente. El ayudante detecta Node desde PATH; si las dependencias están en otra ubicación, configura `FACTURAS_NODE` y `FACTURAS_NODE_MODULES`. Las variables deben mantenerse en el proceso que ejecuta los scripts. Para leer PDF digital se recomienda pypdf o PyMuPDF; los escaneos necesitan visión disponible en la sesión.

4. Lleva las facturas al entorno en `entrada/Prueba/<archivos>`, mediante las opciones de transferencia disponibles. Conectar GitHub no sube automáticamente los archivos del ordenador. Si la interfaz no admite adjuntos, se necesita otro mecanismo de transferencia autorizado.
5. Escribe:

   > Lee AGENTS.md y la Skill. Comprueba el entorno de Excel. Procesa exclusivamente entrada/Prueba, conserva los originales y genera su Excel y sus copias en resultados/Prueba. Entrega un ZIP con esa carpeta completa e informa de los recuentos e incidencias.

6. Descarga los resultados antes de finalizar el entorno. Conserva juntos el Excel y `facturas/` para mantener los enlaces.

## Estado y siguientes tandas

GitHub contiene el programa, no los documentos. `entrada/`, `resultados/`, `NO TOCAR/control/` y `NO TOCAR/trabajo/` están excluidos de Git. Un commit o una tarea nueva no conserva esos archivos. Para continuar un cliente en otro entorno, restaura conjuntamente originales, resultados y control desde una copia de seguridad privada. Los registros usan rutas del entorno: no reutilices un registro de otra raíz sin revisar su compatibilidad. No ejecutes dos escritores simultáneos sobre el mismo estado.

Esta importación empieza sin clientes: excluye los documentos, resultados, controles, históricos, ensayos y auxiliares del paquete original. No reutiliza las rutas absolutas del ordenador de origen. Los ejemplos de nombres en la documentación original son ilustrativos.

## Verificación técnica

```bash
source 'NO TOCAR/herramientas/entorno-codex.sh'
python -m unittest discover -s 'NO TOCAR/tests' -v
python 'NO TOCAR/skills/procesador-facturas/scripts/clientes.py' listar --root .
```

Las pruebas usan datos sintéticos; no validan la precisión de interpretación de facturas reales. Consulta `NO TOCAR/README.md` para el uso original y la Skill para el procedimiento completo. El repositorio no incluye interfaz propia, servidor ni automatización al subir documentos.

## Entrega preferida por Google Drive

El agente tiene instrucciones para subir el Excel y el ZIP a Google Drive y devolver enlaces verificados cuando la sesión disponga de subida de archivos. La instalación del complemento no garantiza que sus herramientas estén disponibles en cada chat. Las carpetas se mantienen privadas y las salidas anteriores se conservan. Si falla la conexión, el agente informa de entrega pendiente y conserva el trabajo sin volver a interpretar las facturas.
