# Cambios de la plantilla DUNNE

Cada versión es una etiqueta anotada. Un proyecto la recibe con
`uvx copier update --trust`; sin `--defaults`, Copier pregunta los rasgos nuevos.

## v0.8.1

- En una actualización, la tarea de puesta en marcha ya no toca el entorno: Copier la
  corre antes de reaplicar los cambios del proyecto, y sincronizar ahí desinstalaba las
  dependencias propias y reescribía `uv.lock` sin ellas. El resumen indica `uv sync` y
  el export para después; la autoverificación prueba el caso.
- `tools/publicar.py` consulta también las etiquetas de GitHub y sube la etiqueta de
  forma explícita: una etiqueta borrada solo en la máquina ya no se republica en silencio.

## v0.8.0

- `tools/publicar.py`: publicar una versión en un solo comando, que se detiene antes de
  etiquetar si algo falla y no reutiliza etiquetas.
- `tools/sincronizar_cff.py`: versión y fecha de lanzamiento de `CITATION.cff` desde
  `pyproject.toml`.
- `.github/workflows/etiqueta.yml`: cada etiqueta debe coincidir con la versión del paquete.
- El núcleo y el chuletario enseñan el comando en lugar de los pasos a mano.

## v0.7.0

- Autoverificación de la plantilla (`pruebas/verificar_plantilla.py`) y su CI.
- Convención: los pasos de CI propios de un proyecto van en un workflow aparte.
- Preferencia: cada documento derivado se verifica en el CI con `--check`.
- Guía de mantenimiento, este registro y los pendientes de gobernanza.

## v0.6.0

- Pregunta `entrada_propia`: sin `main.py` ni comando de consola.
- `README.md`, `CITATION.cff` y `CREDITS.md` pasan a ser del proyecto.
- Los archivos del proyecto que dependen de un rasgo solo nacen: apagar un rasgo ya no los borra.
- Pruebas: humo solo importa; sección de datos de personas; guía del operador; esquema del contenido.

## v0.5.0

- Rasgos `operacion_en_vivo` y `senal_externa`, con sus módulos y la guía del operador.
- Una regla de Antigravity por módulo, por el límite de 24,000 bytes.
- Pregunta de nombres más clara y prueba de apellidos repetidos.

## v0.4.0

- Convención de contenido: módulo, esquema JSON, archivo inicial y prueba de contenido.
- Regla de artefactos generados en el núcleo.

## v0.3.0

- Gobernanza: `LICENSE`, `CITATION.cff`, `CREDITS.md`, `CONTRIBUTING.md` y prueba de gobernanza.
- Rasgos `proyecto_dunne`, `contenido_didactico` y `datos_de_personas`.
- Puente para que Antigravity inserte los módulos.

## v0.2.0

- El estándar viaja con cada proyecto: `docs/estandar/`, `AGENTS.md`, `CLAUDE.md` y `docs/comandos.md`.

## v0.1.1

- LF en todo lo generado; sin caché de Python en el repositorio.

## v0.1.0

- Primera versión en Copier, con paridad respecto al script de PowerShell y los rasgos `investigacion` y `usa_gpu`.
