# Uso del procesador de facturas · 0.7

Abre siempre PROCESADOR como proyecto de Codex. La carpeta principal muestra únicamente:

```text
PROCESADOR/
├── entrada/
│   └── Dubme/                 Facturas originales; puede haber subcarpetas
├── resultados/
│   └── Dubme/
│       ├── Facturas_Dubme.xlsx
│       └── facturas/          Copias renombradas
└── NO TOCAR/                  Skill, configuración, registro y herramientas
```

## Nueva prueba en un chat nuevo

1. Añade facturas a `entrada/<cliente>/`, conservando las tandas anteriores y sus rutas.
2. Cierra el Excel de resultados antes de procesar.
3. Abre un chat nuevo dentro del proyecto PROCESADOR y escribe:

**$procesador-facturas Procesa las carpetas de clientes de entrada y actualiza sus Excel.**

Para un único cliente: **$procesador-facturas Procesa entrada/Dubme y actualiza su Excel acumulado.**

La Skill ya está configurada en este ordenador. No hay que ejecutar scripts manualmente ni volver a explicar las reglas en el chat nuevo. Si no aparece en el selector, el archivo de instrucciones del proyecto también indica su ubicación; reinicia Codex si el selector no se actualiza.

## Reglas

Una copia y una fila por archivo compatible, aunque sea duplicado o dudoso. Repetir la ejecución no vuelve a añadir las mismas rutas. Los duplicados nuevos se marcan en el nombre, y con color y nota en el Excel. Los documentos dudosos mantienen sus celdas desconocidas vacías y se explican aparte. Se comprueba por cliente que entrada, copias y filas de tabla coincidan. No se suman monedas distintas.

El Excel tiene exactamente las 16 columnas confirmadas. IVA FACTURA contiene sólo el porcentaje; IMPORTE TOTAL CONCEPTO es el total final a pagar; el resumen está en español. CONCEPTO conserva el detalle completo, con guion y salto de línea para cada subconcepto cuando hay varios. Las filas son blancas salvo las copias duplicadas, que se resaltan en amarillo; la primera copia queda blanca. FECHA CONTABLE queda vacía sin regla de empresa. No se añaden columnas ocultas ni hojas auxiliares.

Si falta o cambia un original, cambia una copia o hay una edición manual del Excel, se detiene para conciliar la diferencia, sin borrar información. Los formatos admitidos son PDF, JPG, JPEG y PNG; otros archivos se enumeran como excluidos. Los originales permanecen intactos.

## Contenido técnico

- `NO TOCAR/skills/procesador-facturas/`: única copia de la Skill, con scripts, referencias y plantilla.
- `NO TOCAR/config/config.json`: configuración; rutas relativas a PROCESADOR.
- `NO TOCAR/control/`: memoria persistente por cliente, lotes, transacciones, informes y copias del Excel anterior. No borrarla entre tandas.
- `NO TOCAR/trabajo/analisis/`: resultados del modo de análisis sin archivo.
- `NO TOCAR/historico/`: pruebas y versiones anteriores conservadas.
- `NO TOCAR/herramientas/` y `NO TOCAR/tests/`: utilidades y comprobaciones de desarrollo.

En la raíz hay accesos técnicos ocultos para que Codex descubra automáticamente la Skill y las instrucciones. El enlace `.agents/skills/procesador-facturas` apunta a la única copia en NO TOCAR. No hay que tocarlo. El script de instalación restaura ese acceso local, sin generar otra copia de la Skill.

## Compartir con compañeros

Preparar un proyecto limpio con entrada y resultados vacías. Dentro de NO TOCAR distribuir sólo `skills/`, `config/`, `AGENTS.md`, este README y `Instalar-Skill.ps1`. No copiar control, históricos, herramientas con datos, facturas ni resultados reales. En el nuevo ordenador ejecutar `./NO TOCAR/Instalar-Skill.ps1 -Actualizar` desde PROCESADOR; ajustará el enlace a la ubicación de ese ordenador. Después abrir el proyecto en Codex.

Se utiliza Python, Node y artifact-tool incluidos en Codex; no se añaden servidores ni APIs adicionales. La interpretación por Codex utiliza el servicio de OpenAI: usa documentos autorizados para ese entorno.

La última columna ARCHIVO FACTURA permite abrir la copia renombrada con un clic. Usa un enlace relativo desde el Excel a facturas/<nombre>; al compartir, conserva el Excel y la subcarpeta facturas juntos. La duplicidad se decide exclusivamente por número íntegro y total final a pagar coincidentes dentro del cliente; no por hash ni por NIF.
