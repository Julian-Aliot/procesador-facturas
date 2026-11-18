#!/usr/bin/env bash
# Cargar con: source 'NO TOCAR/herramientas/entorno-codex.sh'
# No instala nada ni realiza llamadas a servicios externos.
_facturas_node="${FACTURAS_NODE:-$(command -v node || true)}"
if [[ -z "$_facturas_node" || ! -x "$_facturas_node" ]]; then
  echo 'Falta Node. Configura FACTURAS_NODE con un ejecutable compatible.' >&2
  return 1
fi
export FACTURAS_NODE="$_facturas_node"
_facturas_modules="${FACTURAS_NODE_MODULES:-$(dirname "$(dirname "$(readlink -f "$_facturas_node")")")/node_modules}"
if [[ ! -d "$_facturas_modules/@oai/artifact-tool" ]]; then
  echo 'Falta @oai/artifact-tool. Configura FACTURAS_NODE_MODULES; no se ha instalado nada.' >&2
  return 1
fi
export FACTURAS_NODE_MODULES="$_facturas_modules"
python -c 'import openpyxl' || return 1
unset _facturas_node _facturas_modules
echo 'Entorno listo para procesar y generar XLSX.'
