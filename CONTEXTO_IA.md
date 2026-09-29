# Contexto para asistentes: proyectos con la plantilla DUNNE

> Instantánea de la plantilla **v0.7.0**. La fuente de verdad es el repositorio
> `EmmanuelIsaiasGuizarBayardo/plantilla-proyecto`: su README explica las
> decisiones de diseño y su `CHANGELOG.md`, cada versión. Si algo de aquí
> contradice al repositorio, manda el repositorio.

## Cuándo usar este archivo

- **Dentro de un proyecto generado con la plantilla, no hace falta.** `AGENTS.md`
  carga el estándar que aplica a ese proyecto: Antigravity lo recibe por
  `.agents/rules/` y Claude Code por `CLAUDE.md`.
- **Para crear un proyecto, adoptar uno existente o mantener la plantilla**, este
  archivo es el contexto de partida.

## Entorno

Windows con PowerShell 5.1, uv, Git y GitHub CLI. Entorno de desarrollo: Google
Antigravity (IDE y CLI). Python 3.12 por defecto.

## Crear un proyecto

La forma más simple es interactiva: Copier pregunta todo, con valores por defecto.

```powershell
uvx copier copy --trust gh:EmmanuelIsaiasGuizarBayardo/plantilla-proyecto Mi_Proyecto
```

Para preparar el comando con las respuestas ya decididas:

```powershell
$respuestas = @(
    "-d", "nombre_proyecto=Mi_Proyecto",
    "-d", "descripcion=Una línea que lo describa.",
    "-d", "autor_nombres=Emmanuel Isaías",
    "-d", "autor_apellidos=Guízar Bayardo",
    "-d", "proyecto_dunne=true",
    "-d", "organizacion_github=EmmanuelIsaiasGuizarBayardo",
    "-d", "contenido_didactico=true"
)
uvx copier copy --trust --defaults @respuestas gh:EmmanuelIsaiasGuizarBayardo/plantilla-proyecto Mi_Proyecto
```

| Pregunta | Qué decide |
|---|---|
| `nombre_proyecto` | Nombre; de él salen el módulo de Python y el de distribución |
| `autor_nombres`, `autor_apellidos` | Solo nombres de pila, y aparte los apellidos; vacíos dejan marcas `[COMPLETAR]` que el CI exige llenar |
| `proyecto_dunne` | Afiliación oficial, copyright compartido con la división, logotipo reservado |
| `python_version` | 3.12 por defecto, o 3.13 |
| `entrada_propia` | Proyecto con su propio punto de entrada, como una app Dash: sin `main.py` |
| `investigacion` | `data/`, `notebooks/`, reproducibilidad y reglas de fuga de datos |
| `usa_gpu` e `indice_cuda` | Extra `gpu` con PyTorch; el índice se elige en pytorch.org según el driver |
| `contenido_didactico` | `content/` bajo CC BY 4.0, con esquema JSON y su prueba |
| `datos_de_personas` | Declaración obligatoria en el README |
| `operacion_en_vivo` | Guía del operador y reglas para operar frente a público |
| `senal_externa` | Ausencia explícita, compuerta, fuente simulada y pruebas sin hardware |
| `organizacion_github` | Cuenta donde se crea el repositorio; vacío, no se crea |

**De DUNNE o individual.** Un proyecto de DUNNE responde `proyecto_dunne=true` y
va a la organización de DUNNE cuando exista; mientras, a la cuenta personal, para
transferirlo después. Uno individual responde `proyecto_dunne=false` y va a la
cuenta personal: su copyright queda como "Los autores de <proyecto>", sin
afiliación ni logotipo.

## Dentro de un proyecto

- Las reglas están en `docs/estandar/`: un núcleo y un módulo por rasgo activo.
  Un módulo ausente no aplica. Los comandos frecuentes, en `docs/comandos.md`.
- Son del estándar y se regeneran: `docs/estandar/`, `AGENTS.md`, `CLAUDE.md`,
  `.agents/rules/`, `LICENSE`, `.github/workflows/ci.yml` y las pruebas del
  estándar. Sus cambios se proponen en la plantilla.
- Son del proyecto y la plantilla no los toca: `README.md`, `CITATION.cff`,
  `CREDITS.md`, `content/*.json`, `docs/operacion.md`, `__init__.py`, `main.py`
  y `utils.py`.
- Actualizar: `uvx copier update --trust` con el árbol limpio, revisar con
  `git diff` y commitear de inmediato. Sin `--defaults`, pregunta los rasgos nuevos.

## Figuras de investigación

Las figuras de investigación usan la biblioteca `figuras-cientificas`, que vive
aparte de la plantilla porque no todo proyecto la necesita. En el proyecto, se
agrega con la etiqueta más reciente (hoy `v0.1.2`) y se instalan sus reglas para
Antigravity:

```powershell
uv add git+https://github.com/EmmanuelIsaiasGuizarBayardo/figuras-cientificas --tag v0.1.2
uv run python -m figuras_cientificas regla
```

Sus reglas, con referencias, están en `src/figuras_cientificas/visualizacion.md`
de ese repositorio. En resumen: el mapa de color lo decide `mapa_para(datos)`, las
categorías `categorica(n)`, el tamaño `tamano_figura` y el estilo `usar_estilo`,
según la guía de Nature; antes de enviar una figura, `revisar_figura(fig)` la
muestra con daltonismo simulado.

## Adoptar un proyecto existente

Así se adoptó NeuroDAC:

1. Rama aparte y árbol limpio.
2. `uvx copier copy --trust --overwrite --skip-tasks --defaults --skip pyproject.toml @respuestas gh:EmmanuelIsaiasGuizarBayardo/plantilla-proyecto .`
   Conserva los archivos del proyecto; reemplaza `LICENSE`, `.gitignore` y el CI.
3. Ajustar lo que Copier no puede saber: `pyyaml` y `jsonschema` en el grupo dev,
   el CFF, los créditos, el esquema del contenido y su `review.status`.
4. Revisar `git diff` de `.gitignore` y `.github/workflows/ci.yml`. Los pasos de CI
   propios del proyecto van a un workflow aparte; en NeuroDAC, el reemplazo borró
   "Manual al día" y se restauró en `manual.yml`.
5. `uv sync`, `uv run python tools/export_requirements.py`,
   `uv run pre-commit autoupdate`, `uv run pre-commit install` y `uv run pytest -q`.
   Luego *pull request* y fusión.

## Reglas que un asistente no debe romper

- Dependencias con `uv add`, nunca `pip install` suelto. `requirements.txt` se
  regenera solo con `uv run python tools/export_requirements.py`.
- Ningún dato de personas entra al repositorio, sea público o privado.
- `LICENSE` contiene solo el texto MIT; las aclaraciones van en el README.
- La versión de `pyproject.toml` y la de `CITATION.cff` coinciden. Las versiones
  se publican con etiqueta anotada (`git tag -a`) y `git push --follow-tags`.
- Si una petición viola una REGLA DURA del estándar, se señala antes de escribir
  código.

## PowerShell 5.1

- `>` escribe en UTF-16; para compartir una salida, `| Out-File -Encoding utf8`.
- No existe `&&`. Para que un paso dependa del anterior:
  `if ($LASTEXITCODE -eq 0) { ... }`.
- Los scripts `.ps1` van en UTF-8 **con** BOM; todo lo demás, UTF-8 sin BOM y LF.
- Listas de argumentos con `@(...)` y `@nombre`, no con líneas continuadas con
  acento grave, que se rompen al pegar.
- Siempre rutas reales en los comandos: una ruta de ejemplo que falla deja correr
  las líneas siguientes.

## Mantener la plantilla

Se edita directamente en su repositorio. Cada cambio se registra en
`CHANGELOG.md` y se verifica con `uv run pruebas/verificar_plantilla.py`, que
también corre en el CI de la plantilla. Para mirar un cambio sin publicarlo:
`uvx copier copy --trust --vcs-ref=HEAD . /tmp/prueba`. Se publica con
`git tag -a vX.Y.Z -m "..."` y `git push --follow-tags`. Si el cambio contradice
algo de este archivo, se actualiza en el mismo commit.

## Pendientes de gobernanza

- Crear la organización de GitHub de DUNNE con al menos dos dueños.
- Transferir la plantilla a esa organización y cambiar el valor por defecto de
  `organizacion_github`; después, no crear otro repositorio con el nombre anterior.
- Neurona AR: autorización por escrito de Mauricio Mendiola Rivera para el modelo.
- Un *stack* de sitio estático, si Neurona AR se reactiva o aparece otro proyecto así.
