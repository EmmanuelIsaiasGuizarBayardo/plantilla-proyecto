# Plantilla de proyectos DUNNE

Genera proyectos con la estructura, el entorno y las herramientas del estándar
DUNNE. Funciona igual en Windows, Mac y Linux.

## Crear un proyecto

Requisito: [uv](https://docs.astral.sh/uv/). Recomendados: Git y
[GitHub CLI](https://cli.github.com) con sesión iniciada (`gh auth login`).

```
uvx copier copy --trust gh:EmmanuelIsaiasGuizarBayardo/plantilla-proyecto Nombre_Del_Proyecto
```

Copier hace unas cuantas preguntas; todas tienen respuesta por defecto, así que
basta con Enter para obtener un proyecto mínimo que funciona. Al terminar
muestra un resumen: lo que no pudo hacer (por falta de red, de `gh` o de la
configuración de Git) aparece con el comando exacto para completarlo. Nada de
eso impide que el proyecto quede generado.

`--trust` es necesario porque la plantilla ejecuta una tarea al final: sincroniza
el entorno, inicializa Git, instala los hooks y, si se indicó organización, crea
el repositorio en GitHub.

### Qué cambia cada respuesta

| Pregunta | Si es sí |
|---|---|
| Investigación | `data/`, `notebooks/`, `results/`, módulo de reproducibilidad, pila científica (MNE, NumPy, SciPy, scikit-learn) |
| GPU | Extra `gpu` con torch y torchvision desde el índice CUDA elegido, `device.py` con diagnóstico |
| DUNNE | Afiliación oficial, copyright compartido con la división, cláusula del logotipo |
| Contenido didáctico | `content/` bajo CC BY 4.0 con su `LICENSE.md`, un esquema JSON, un archivo de texto inicial y su prueba; doble licencia en el CFF |
| Datos de personas | Declaración obligatoria en el README, verificada por la prueba de gobernanza |
| Operación en vivo | Guía del operador en `docs/operacion.md`, que después es del proyecto |
| Señal externa | Módulo de ausencia explícita, compuerta, fuente simulada y pruebas sin hardware |

Todos los proyectos llevan además `LICENSE` (MIT), `CITATION.cff`, `CREDITS.md` y
`CONTRIBUTING.md`. Las preguntas de autoría pueden dejarse vacías: el proyecto se
genera con marcas `[COMPLETAR: ...]`, el resumen final las señala y el CI falla
hasta llenarlas. Un proyecto con punto de entrada propio, como una app Dash con
`interfaz.py`, lo declara en su pregunta y no recibe `main.py` ni comando de consola.

Un proyecto sin rasgos activos no trae carpetas vacías ni módulos que no
aplican.

Cada rasgo trae además su módulo del estándar en `docs/estandar/`, y `AGENTS.md`
los importa para los asistentes de IA. Un proyecto recibe exactamente las reglas
que le aplican, sin tener que deducirlas.

## Actualizar un proyecto al estándar más reciente

Desde la raíz del proyecto, con el árbol de trabajo limpio:

```
uvx copier update --trust
```

Copier aplica los cambios del estándar sobre el trabajo del estudiante. Si ambos
tocaron las mismas líneas, deja marcadores de conflicto para resolverlos a mano.
Los archivos que después de nacer pertenecen al estudiante (`main.py`,
`__init__.py`, `utils.py`) nunca se tocan. Los cambios quedan sin commitear para
revisarlos con `git diff`.

## Mantener la plantilla

**Publicar una versión** es crear una etiqueta anotada; `copier update` compara
etiquetas, no commits sueltos, y `--follow-tags` solo sube las anotadas:

```
git tag -a v0.2.0 -m "Qué cambia en esta versión"
git push --follow-tags
```

**Probar cambios sin publicarlos.** Copier usa por defecto la etiqueta más
reciente, no el árbol de trabajo. Para probar un cambio local:

```
uvx copier copy --trust --vcs-ref=HEAD ruta/a/la/plantilla /tmp/prueba
```

**Proyectos de DUNNE.** En la pregunta de GitHub, responde con el nombre de la
organización, no con tu usuario. Un proyecto de la división creado en una cuenta
personal queda huérfano cuando su autor deja la división.

### Decisiones de diseño que no conviene deshacer

**Una sola tarea en `copier.yml`.** Copier aborta todas las tareas restantes en
cuanto una falla. La tarea única invoca `extensiones/post_generacion.py`, que
ejecuta cada paso por separado y siempre termina bien. Agregar pasos se hace en
ese script, no como tareas nuevas.

**El script sale de inmediato en los temporales de `copier update`.** Copier
renderiza la plantilla dos veces más en directorios temporales para calcular la
diferencia, y ejecuta las tareas también ahí. Sin esa salida, cada actualización
instalaría entornos completos que se tiran.

**Sin entorno no hay commit.** Si `uv sync` falla, el script no hace el commit
inicial ni publica: un repositorio sin `uv.lock` rompería el CI en el primer push.

**`.gitignore` y `.gitattributes` llevan sufijo `.jinja`** aunque no tengan
variables. Sin él, el propio repositorio de la plantilla los interpretaría como
suyos.

**El repositorio de la plantilla fuerza LF con su propio `.gitattributes`.** En
Windows, Git con `core.autocrlf=true` convierte a CRLF al clonar, y Copier copia
tal cual los archivos sin sufijo `.jinja`; los que sí lo llevan salen en LF
porque Jinja normaliza los saltos de línea. Sin ese archivo, cada proyecto
generado en Windows traería una mezcla de ambos.

**Un rasgo, un módulo.** Cada pregunta booleana de `copier.yml` corresponde a un
archivo en `plantilla/docs/estandar/`, condicionado por esa respuesta. Las
reglas de un módulo no se condicionan por dentro: si una regla depende de un
rasgo, va en el módulo de ese rasgo.

**`AGENTS.md` es el archivo canónico; `CLAUDE.md`, un puente.** La mayoría de
los asistentes de código lee `AGENTS.md`. Claude Code lo lee directamente desde
la versión 2.1.277, pero solo si no hay `CLAUDE.md`; el puente con `@AGENTS.md`
cubre las versiones anteriores y nunca lo carga dos veces. Ambos llevan sufijo
`.jinja` para que el repositorio de la plantilla no los tome como propios.

**Cada archivo del estándar, por debajo de 200 líneas.** Es la recomendación de
Claude Code para no perder adherencia; las importaciones no la alivian, porque
se cargan completas al iniciar.

**Antigravity recibe los módulos por `.agents/rules/`, una regla por módulo.**
Antigravity inserta archivos con `@[etiqueta](ruta)`; la sintaxis `@ruta` de
`AGENTS.md` solo la convierte en referencia. Cada módulo tiene su propia regla
porque Antigravity trunca sin aviso cualquier regla que pase de 24,000 bytes tras
expandir sus inclusiones, y una sola regla con todos los módulos ya ocupaba el 75%.
Claude Code no lee `.agents/`, así que cada herramienta ve una sola sintaxis.

**Dos nombres de la organización.** `org_nombre_completo`, para las afiliaciones
del CFF, y `org_nombre_corto`, para avisos y atribuciones. Si cambian, se editan
una sola vez en `copier.yml`; llegan solos a los archivos del estándar, y la prueba
de gobernanza señala las afiliaciones del CFF que hay que corregir a mano.

**La licencia del contenido vive en `content/LICENSE.md`.** El directorio es la
frontera de la licencia, y la raíz conserva un único archivo de licencia para que
GitHub la detecte sin ambigüedad.

**El contenido es del proyecto; sus reglas, de la plantilla.** `content/*.json` está
en `_skip_if_exists`: la plantilla crea el esquema y un archivo inicial y nunca
vuelve a tocarlos. Lo que no se negocia (estado de revisión declarado, nombres,
claves ASCII, sin HTML) lo verifica `tests/test_contenido.py`, que sí es de la
plantilla, así que se cumple aunque un proyecto reescriba su esquema.

**`README.md`, `CITATION.cff` y `CREDITS.md` son del proyecto.** Están en
`_skip_if_exists`: la plantilla los crea una vez y no los vuelve a tocar. Lo mostró
la adopción de NeuroDAC: un README, un CFF y unos créditos reales no se parecen a
los generados, y fusionarles cada cambio de la plantilla produciría conflictos en
cada actualización. Lo que no se negocia de ellos lo verifica la prueba de
gobernanza.

**Los archivos del proyecto que dependen de un rasgo solo nacen.** `main.py`,
`utils.py`, `content/*.json` y `docs/operacion.md` se excluyen durante las
actualizaciones con un patrón condicionado a `_copier_operation`. Sin eso, apagar
un rasgo borraba esos archivos aunque el estudiante los hubiera editado; lo reveló
la prueba de aceptación con NeuroDAC. El costo: activar un rasgo en un proyecto
existente no crea su esquema ni su guía, y las pruebas dicen qué falta.

**Nombres de archivo condicionales sin comillas dobles.** Son ilegales en rutas
de Windows; si una condición necesita comparar texto, usa comillas simples.
