# Procesador de facturas
Lee y sigue `NO TOCAR/AGENTS.md` para las instrucciones del proyecto.
La Skill está en `NO TOCAR/skills/procesador-facturas/SKILL.md`.

## Entorno Codex online
Antes de procesar, carga `source 'NO TOCAR/herramientas/entorno-codex.sh'` en el mismo shell que ejecutará los scripts. Explica las dependencias que falten; no instales nada silenciosamente. No presupongas que cada entorno incluye artifact-tool.
Las facturas y el control están excluidos de Git. No los añadas a commits ni publiques su contenido. Al terminar, ofrece un ZIP descargable con el Excel y sus copias. Advierte que el historial acumulado requiere conservar y restaurar originales, resultados y control; GitHub no los persiste.

## Uso por personas sin conocimientos técnicos
Ante peticiones de procesar facturas, aplica siempre `NO TOCAR/skills/procesador-facturas/references/uso-sencillo.md`. Acepta lenguaje natural y adjuntos; prepara las carpetas y comprueba dependencias sin pedir comandos al usuario. Pregunta el cliente sólo si falta o es ambiguo. Distingue primera tanda y continuación; no reinicies historiales ni prometas acumular sólo con un Excel. Entrega enlaces reales al Excel y al ZIP del cliente.
