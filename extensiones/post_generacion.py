"""Puesta en marcha posterior a `copier copy` y `copier update`. Nunca bloquea.

Copier aborta todas las tareas restantes en cuanto una falla. Por eso la
plantilla declara una sola tarea: este script, que ejecuta cada paso por
separado, anota lo que no pudo hacer junto con el comando exacto para repetirlo
y siempre termina con codigo 0. El proyecto queda generado aunque falte red,
`gh` o la configuracion de Git.

Solo usa la biblioteca estandar, porque corre con el Python de Copier y no con
el del proyecto. No se copia al proyecto generado.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Una consola con codificacion limitada no debe tumbar la puesta en marcha.
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(errors="replace")
    except AttributeError:
        pass


@dataclass(frozen=True)
class Resultado:
    """Desenlace de un paso de la puesta en marcha."""

    ok: bool
    paso: str
    remedio: str = ""


RESULTADOS: list[Resultado] = []


def disponible(binario: str) -> bool:
    """Indica si un ejecutable esta en PATH."""
    return shutil.which(binario) is not None


def ejecutar(nombre: str, cmd: list[str], remedio: str | None = None) -> bool:
    """Corre un paso y registra su desenlace sin propagar excepciones.

    Parameters
    ----------
    nombre : str
        Descripcion legible del paso.
    cmd : list of str
        Comando, sin shell: identico en Windows, Mac y Linux.
    remedio : str, optional
        Instruccion para el estudiante si el paso falla. Por defecto, el
        propio comando.

    Returns
    -------
    bool
        True si el comando termino con codigo 0.
    """
    print(f"\n-> {nombre}", flush=True)
    try:
        ok = subprocess.run(cmd, check=False).returncode == 0
    except (OSError, ValueError):
        ok = False
    RESULTADOS.append(Resultado(ok, nombre, "" if ok else (remedio or " ".join(cmd))))
    return ok


def omitir(nombre: str, remedio: str) -> None:
    """Registra un paso que no se intento por falta de un requisito."""
    RESULTADOS.append(Resultado(False, nombre, remedio))


def gh_autenticado() -> bool:
    """Indica si GitHub CLI tiene una sesion activa."""
    try:
        return (
            subprocess.run(
                ["gh", "auth", "status"], capture_output=True, check=False
            ).returncode
            == 0
        )
    except OSError:
        return False


def a_bool(valor: str) -> bool:
    """Convierte el texto que renderiza Jinja ("True"/"False") a booleano."""
    return valor.strip().lower() in {"true", "1", "yes", "si"}


def resumen(es_nuevo: bool) -> None:
    """Imprime el estado final y los comandos para completar lo pendiente."""
    pendientes = [r for r in RESULTADOS if not r.ok]
    print("\n" + "=" * 72)
    print("Resumen de la puesta en marcha")
    print("=" * 72)
    for r in RESULTADOS:
        print(f"  {'[ok]' if r.ok else '[!] '} {r.paso}")
    if pendientes:
        print("\nEl proyecto esta generado. Para completar lo pendiente:")
        for r in pendientes:
            print(f"  - {r.paso}:\n      {r.remedio}")
    else:
        print("\nTodo listo." if es_nuevo else "\nActualizacion aplicada.")
    if not es_nuevo:
        print("\nRevisa los cambios con 'git diff' antes de commitear.")
    print()


def main() -> int:
    """Orquesta la puesta en marcha. Siempre devuelve 0."""
    parser = argparse.ArgumentParser()
    for campo in ("nombre-proyecto", "nombre-modulo", "nombre-dist", "organizacion"):
        parser.add_argument(f"--{campo}", default="")
    parser.add_argument("--investigacion", default="False")
    parser.add_argument("--usa-gpu", default="False")
    args = parser.parse_args()

    investigacion = a_bool(args.investigacion)
    usa_gpu = a_bool(args.usa_gpu)
    operacion = os.environ.get("COPIER_OPERATION", "copy")

    # Durante una actualizacion, Copier renderiza la plantilla dos veces mas en
    # directorios temporales para calcular la diferencia, y ejecuta las tareas
    # tambien ahi. Sin esta salida, cada actualizacion sincronizaria entornos
    # completos que se tiran, y registraria un kernel de Jupyter apuntando a una
    # ruta que desaparece. Los temporales no tienen .git; el proyecto real
    # siempre lo tiene, porque copier update lo exige.
    if operacion != "copy" and not Path(".git").exists():
        return 0

    # Idempotencia: en una actualizacion el repositorio ya existe y no se
    # vuelve a inicializar, commitear ni publicar.
    es_nuevo = operacion == "copy" and not Path(".git").exists()

    if not disponible("uv"):
        omitir(
            "Entorno de Python",
            "Instala uv (https://docs.astral.sh/uv/) y corre: uv sync",
        )
        resumen(es_nuevo)
        return 0

    sync = ["uv", "sync", *(["--extra", "gpu"] if usa_gpu else [])]
    sincronizado = ejecutar("Sincronizar entorno", sync)

    if sincronizado:
        ejecutar(
            "Exportar requirements.txt",
            ["uv", "run", "python", "tools/export_requirements.py"],
        )
        if investigacion:
            ejecutar(
                "Registrar kernel de Jupyter",
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "ipykernel",
                    "install",
                    "--user",
                    "--name",
                    args.nombre_modulo,
                    "--display-name",
                    f"Python ({args.nombre_proyecto})",
                ],
            )

    if es_nuevo:
        if not disponible("git"):
            omitir("Repositorio Git", "Instala Git y corre: git init -b main")
        else:
            ejecutar("Inicializar Git", ["git", "init", "-b", "main", "--quiet"])

    hay_repo = Path(".git").exists()

    if sincronizado and hay_repo:
        if es_nuevo:
            ejecutar(
                "Actualizar revisiones de hooks",
                ["uv", "run", "pre-commit", "autoupdate"],
            )
        ejecutar("Instalar hooks de pre-commit", ["uv", "run", "pre-commit", "install"])

    if es_nuevo and sincronizado:
        # Normaliza lo generado para que el primer commit ya este limpio.
        ejecutar("Formatear codigo", ["uv", "run", "ruff", "format", "--quiet", "."])
        ejecutar(
            "Corregir lint", ["uv", "run", "ruff", "check", ".", "--fix", "--quiet"]
        )

    commit_ok = False
    if es_nuevo and hay_repo and not sincronizado:
        # Un commit sin uv.lock haria fallar el CI en el primer push
        # ('uv sync --locked' exige el lock). Mejor esperar al entorno.
        omitir(
            "Commit inicial",
            f"{' '.join(sync)}; luego: uv run python tools/export_requirements.py; "
            'git add . ; git commit -m "Estructura inicial"',
        )
    elif es_nuevo and hay_repo:
        ejecutar("Preparar commit", ["git", "add", "."])
        commit_ok = ejecutar(
            "Commit inicial",
            [
                "git",
                "commit",
                "--no-verify",
                "--quiet",
                "-m",
                "Estructura inicial desde la plantilla DUNNE",
            ],
            remedio=(
                'git config --global user.name "Tu Nombre"; '
                'git config --global user.email "tu@correo"; '
                'git commit -m "Estructura inicial"'
            ),
        )

    if es_nuevo and args.organizacion:
        destino = f"{args.organizacion}/{args.nombre_dist}"
        crear = f"gh repo create {destino} --public --source=. --remote=origin --push"
        if not disponible("gh"):
            omitir(
                "Repositorio en GitHub",
                f"Instala GitHub CLI (https://cli.github.com) y corre: {crear}",
            )
        elif not gh_autenticado():
            omitir("Repositorio en GitHub", f"gh auth login; luego: {crear}")
        elif not commit_ok:
            omitir(
                "Repositorio en GitHub", f"Completa el commit inicial y corre: {crear}"
            )
        else:
            ejecutar("Repositorio en GitHub", crear.split(), remedio=crear)

    resumen(es_nuevo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
