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

Un proyecto sin ninguno de los dos no trae carpetas vacías ni módulos que no
aplican.

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

**Publicar una versión** es crear una etiqueta; `copier update` compara
etiquetas, no commits sueltos:

```
git tag v0.2.0
git push --tags
```

**Probar cambios sin publicarlos.** Copier usa por defecto la etiqueta más
reciente, no el árbol de trabajo. Para probar un cambio local:

```
uvx copier copy --trust --vcs-ref=HEAD ruta/a/la/plantilla /tmp/prueba
```

**Antes de cambiar el valor por defecto de `organizacion_github`** en
`copier.yml`, verifica que es el nombre exacto de la organización en GitHub.
Con él puesto, todo proyecto nuevo se publica ahí y ninguno queda huérfano en
una cuenta personal.

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

**Nombres de archivo condicionales sin comillas dobles.** Son ilegales en rutas
de Windows; si una condición necesita comparar texto, usa comillas simples.
