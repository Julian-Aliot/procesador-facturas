# Comprobar versión antes de cada envío

Fuente del programa: https://github.com/Julian-Aliot/procesador-facturas, rama main.

Antes de comenzar un envío, consulta la revisión actual mediante las herramientas de GitHub o `git ls-remote https://github.com/Julian-Aliot/procesador-facturas.git refs/heads/main`. No basta con recordar la versión de este chat.

Si tienes una copia Git limpia y del proyecto correcto, puedes actualizarla con fast-forward (`git pull --ff-only`). Comprueba primero su remoto y cambios. Si hay cambios locales, la descarga no tiene Git o la actualización no es fast-forward, conserva esa copia y descarga/clona una copia nueva en un directorio de trabajo nuevo. No uses reset --hard, clean ni sobrescribas archivos del usuario. No necesitas copiar documentos o registros de envíos anteriores.

Lee otra vez el AGENTS.md y la Skill de la revisión descargada. Comprueba sus dependencias y comunica brevemente el identificador de revisión usado. Mantén ese código fijo durante toda la ejecución, aunque main cambie después.

Si no puedes comprobar/descargar la última revisión, informa de que no está verificada y pregunta si el usuario quiere continuar con la versión disponible. Nunca digas que estás actualizado basándote sólo en archivos locales.

Una copia vieja anterior a esta regla necesita actualizarse una primera vez mediante una orden explícita. La regla no puede actualizar un chat que nunca llegue a leerla.
