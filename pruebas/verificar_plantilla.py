# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Autoverificacion de la plantilla DUNNE.

Reune en un solo script las comprobaciones que se hicieron al disenar cada
version, para que quien mantenga la plantilla no dependa de nadie:

1. Genera un proyecto sin ningun rasgo y otro con todos, desde el arbol de
   trabajo, y revisa en cada uno:
   - que los modulos del estandar, las reglas de Antigravity y las
     importaciones de AGENTS.md coincidan exactamente;
   - que ninguna regla de Antigravity pase de 24,000 bytes al expandirse y
     que ningun modulo llegue a 200 lineas (limite de Claude Code);
   - que no queden restos de Jinja, BOM, CRLF ni archivos sin salto final;
   - que Ruff pase y que las pruebas del estandar pasen tras completar las
     marcas, como lo haria un estudiante.
2. Actualiza un proyecto de la version anterior con archivos del proyecto
   editados, primero tal cual y luego apagando rasgos, y confirma que ningun
   archivo del proyecto se pierde ni pierde su contenido.

Uso, desde la raiz de la plantilla:
    uv run pruebas/verificar_plantilla.py
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
LIMITE_ANTIGRAVITY = 24_000
LIMITE_LINEAS = 200
MARCA = "TRABAJO DEL ESTUDIANTE"
GIT = ["git", "-c", "user.name=verificador", "-c", "user.email=verificador@dunne.invalid"]
FALLAS: list[str] = []


def ok(mensaje: str) -> None:
    """Reporta una comprobacion superada."""
    print(f"  [ok]    {mensaje}")


def falla(mensaje: str) -> None:
    """Reporta y registra una comprobacion fallida."""
    FALLAS.append(mensaje)
    print(f"  [FALLA] {mensaje}")


def correr(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Ejecuta un comando sin shell y captura su salida."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def rasgos() -> list[str]:
    """Preguntas booleanas de copier.yml: los rasgos que decide cada proyecto."""
    conf = yaml.safe_load((RAIZ / "copier.yml").read_text(encoding="utf-8"))
    return [
        k
        for k, v in conf.items()
        if not k.startswith("_") and isinstance(v, dict) and v.get("type") == "bool"
    ]


def copier(
    accion: list[str], datos: dict[str, object], cwd: Path
) -> subprocess.CompletedProcess[str]:
    """Invoca Copier con respuestas fijas y sin tareas."""
    cmd = ["uvx", "copier", *accion[:1], "--trust", "--defaults", "--skip-tasks", "--quiet"]
    for clave, valor in datos.items():
        cmd += ["-d", f"{clave}={valor}"]
    return correr([*cmd, *accion[1:]], cwd)


def revisar_configuracion() -> None:
    """Invariantes de la plantilla que ninguna generacion dinamica puede ver."""
    atributos = RAIZ / ".gitattributes"
    if atributos.is_file() and "* text=auto eol=lf" in atributos.read_text(encoding="utf-8"):
        ok("configuracion: el repositorio de la plantilla fuerza LF")
    else:
        # En Linux no se nota; en Windows con core.autocrlf=true, cada proyecto
        # generado traeria CRLF en los archivos que no pasan por Jinja.
        falla("configuracion: falta '* text=auto eol=lf' en el .gitattributes de la plantilla")

    # Un archivo del proyecto con nombre condicional necesita exclusion durante
    # la actualizacion, o Copier lo borra al apagar su rasgo. La prueba dinamica
    # no lo ve de inmediato: Copier tambien aplica las exclusiones de la version
    # anterior, asi que el dano aparece una version despues.
    conf = yaml.safe_load((RAIZ / "copier.yml").read_text(encoding="utf-8"))
    propios = conf.get("_skip_if_exists", [])
    en_actualizacion = [
        m.group(1).strip()
        for patron in conf.get("_exclude", [])
        if "_copier_operation == 'update'" in patron
        for m in [re.search(r"%\}(.+?)\{%", patron)]
        if m
    ]
    sin_proteccion = []
    for ruta in (RAIZ / "plantilla").rglob("*"):
        relativa = ruta.relative_to(RAIZ / "plantilla").as_posix()
        if not ruta.is_file() or "{% if" not in relativa:
            continue
        destino = re.sub(r"\{\{[^}]*\}\}", "x", relativa)
        destino = re.sub(r"\{%[^%]*%\}", "", destino).removesuffix(".jinja")
        es_propio = any(fnmatch.fnmatch(destino, p) for p in propios)
        if es_propio and not any(fnmatch.fnmatch(destino, p) for p in en_actualizacion):
            sin_proteccion.append(destino)
    if sin_proteccion:
        falla(
            f"configuracion: archivos del proyecto condicionales sin exclusion al actualizar: {sin_proteccion}"
        )
    else:
        ok("configuracion: todo archivo del proyecto condicional se excluye al actualizar")


def completar_marcas(destino: Path) -> None:
    """Llena las marcas [COMPLETAR: ...] como lo haria el estudiante."""
    for nombre in ("CITATION.cff", "CREDITS.md", "README.md"):
        ruta = destino / nombre
        if ruta.is_file():
            texto = re.sub(r"\[COMPLETAR:[^\]]*\]", "Completado", ruta.read_text(encoding="utf-8"))
            ruta.write_text(texto, encoding="utf-8", newline="\n")


def revisar_proyecto(nombre: str, destino: Path) -> None:
    """Todas las comprobaciones sobre un proyecto recien generado."""
    modulos = sorted(p.name for p in (destino / "docs" / "estandar").glob("*.md"))
    incluidos, mayor = [], 0
    for regla in sorted((destino / ".agents" / "rules").glob("*.md")):
        texto = regla.read_text(encoding="utf-8")
        rutas = [(regla.parent / i).resolve() for i in re.findall(r"@\[[^\]]+\]\(([^)]+)\)", texto)]
        if not texto.startswith("---\ntrigger: always_on\n") or not all(r.is_file() for r in rutas):
            falla(f"{nombre}: regla mal formada o con inclusion rota: {regla.name}")
        mayor = max(
            mayor, len(texto.encode()) + sum(len(r.read_bytes()) for r in rutas if r.is_file())
        )
        incluidos += [r.name for r in rutas]
    agents = re.sub(
        r"```.*?```", "", (destino / "AGENTS.md").read_text(encoding="utf-8"), flags=re.DOTALL
    )
    importados = sorted(
        Path(linea[1:].strip()).name for linea in agents.splitlines() if linea.startswith("@docs/")
    )
    if modulos == sorted(incluidos) == importados:
        ok(f"{nombre}: {len(modulos)} modulos = reglas de Antigravity = importaciones de AGENTS.md")
    else:
        falla(
            f"{nombre}: modulos {modulos}, reglas {sorted(incluidos)}, importaciones {importados}"
        )
    if mayor <= LIMITE_ANTIGRAVITY:
        ok(f"{nombre}: la regla mas grande expande a {mayor} de {LIMITE_ANTIGRAVITY} bytes")
    else:
        falla(f"{nombre}: una regla expande a {mayor} bytes, mas que {LIMITE_ANTIGRAVITY}")
    largos = [
        p.name
        for p in (destino / "docs" / "estandar").glob("*.md")
        if len(p.read_text(encoding="utf-8").splitlines()) >= LIMITE_LINEAS
    ]
    if largos:
        falla(f"{nombre}: modulos con {LIMITE_LINEAS} lineas o mas: {largos}")
    else:
        ok(f"{nombre}: ningun modulo llega a {LIMITE_LINEAS} lineas")

    problemas = []
    for ruta in (p for p in destino.rglob("*") if p.is_file() and ".git" not in p.parts):
        datos = ruta.read_bytes()
        texto = datos.decode("utf-8", errors="replace")
        if datos.startswith(b"\xef\xbb\xbf"):
            problemas.append(f"BOM en {ruta.name}")
        if b"\r\n" in datos:
            problemas.append(f"CRLF en {ruta.name}")
        if datos and not datos.endswith(b"\n"):
            problemas.append(f"sin salto final: {ruta.name}")
        if re.search(r"\{\{|\{%", texto):
            problemas.append(f"Jinja sin renderizar en {ruta.name}")
    if problemas:
        falla(f"{nombre}: {problemas}")
    else:
        ok(f"{nombre}: sin BOM, sin CRLF, con salto final y sin restos de Jinja")

    lint = correr(["uvx", "ruff", "check", "."], destino)
    formato = correr(["uvx", "ruff", "format", "--check", "."], destino)
    if lint.returncode == formato.returncode == 0:
        ok(f"{nombre}: Ruff limpio")
    else:
        falla(f"{nombre}: Ruff\n{lint.stdout[-800:]}{formato.stdout[-800:]}")

    completar_marcas(destino)
    pruebas = [
        t
        for t in ("tests/test_gobernanza.py", "tests/test_contenido.py")
        if (destino / t).is_file()
    ]
    resultado = correr(
        [
            "uvx",
            "--with",
            "pyyaml",
            "--with",
            "jsonschema",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            *pruebas,
        ],
        destino,
    )
    if resultado.returncode == 0:
        ok(f"{nombre}: pruebas del estandar ({resultado.stdout.strip().splitlines()[-1]})")
    else:
        falla(f"{nombre}: pruebas del estandar\n{resultado.stdout[-1500:]}")


def marcar(destino: Path) -> list[Path]:
    """Deja una huella del estudiante en cada archivo del proyecto que exista."""

    def agregar(ruta: Path, linea: str) -> None:
        # newline="\n": en Windows, el modo texto convertiria todo a CRLF.
        texto = ruta.read_text(encoding="utf-8") + linea
        ruta.write_text(texto, encoding="utf-8", newline="\n")

    marcados = []
    for patron in (
        "src/*/main.py",
        "src/*/utils.py",
        "docs/operacion.md",
        "README.md",
        "CREDITS.md",
    ):
        for ruta in destino.glob(patron):
            agregar(ruta, f"\n{'# ' if ruta.suffix == '.py' else ''}{MARCA}\n")
            marcados.append(ruta)
    cff = destino / "CITATION.cff"
    agregar(cff, f"# {MARCA}\n")
    marcados.append(cff)
    for ruta in (destino / "content").glob("*.es.json"):
        texto = ruta.read_text(encoding="utf-8").replace("Ejemplo de entrada", MARCA)
        ruta.write_text(texto, encoding="utf-8", newline="\n")
        marcados.append(ruta)
    return marcados


def conservados(marcados: list[Path]) -> list[str]:
    """Archivos del proyecto que se perdieron o perdieron la huella."""
    return [
        str(r.name)
        for r in marcados
        if not r.is_file() or MARCA not in r.read_text(encoding="utf-8")
    ]


def prueba_de_actualizacion(base: Path) -> None:
    """Actualizar desde la version anterior nunca pierde trabajo del estudiante.

    Cada escenario usa su propio proyecto y una sola actualizacion. Con cambios
    sin commitear, Copier registra como version una instantanea temporal del
    arbol de trabajo, y una segunda actualizacion no podria partir de ella.
    """
    anterior = correr(["git", "describe", "--tags", "--abbrev=0", "HEAD~1"], RAIZ).stdout.strip()
    if not anterior:
        ok("actualizacion: no hay version anterior; se omite")
        return
    datos = {
        "nombre_proyecto": "actualizable",
        "autor_nombres": "Ana",
        "autor_apellidos": "Ruiz",
        "investigacion": True,
        "contenido_didactico": True,
        "operacion_en_vivo": True,
    }
    escenarios = (
        ("tal cual", {}),
        (
            "apagando rasgos",
            {
                "investigacion": False,
                "contenido_didactico": False,
                "operacion_en_vivo": False,
                "entrada_propia": True,
            },
        ),
    )
    for etiqueta, extra in escenarios:
        destino = base / f"actualizable_{etiqueta.replace(' ', '_')}"
        if copier(
            ["copy", f"--vcs-ref={anterior}", str(RAIZ), str(destino)], datos, base
        ).returncode:
            falla(f"actualizacion {etiqueta}: no se pudo generar desde {anterior}")
            continue
        marcados = marcar(destino)
        for paso in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "base"]):
            correr([*GIT, *paso], destino)
        r = copier(["update", "--vcs-ref=HEAD"], extra, destino)
        perdidos = conservados(marcados)
        if r.returncode:
            falla(f"actualizacion {etiqueta}: copier update fallo\n{r.stderr[-800:]}")
        elif perdidos:
            falla(f"actualizacion {etiqueta}: se perdio trabajo del estudiante en {perdidos}")
        else:
            ok(
                f"actualizacion {etiqueta}, desde {anterior}: {len(marcados)} archivos del proyecto intactos"
            )


def prueba_de_dependencias_propias(base: Path) -> None:
    """Actualizar con las tareas activas conserva las dependencias propias.

    Copier corre las tareas antes de reaplicar los cambios del proyecto, sobre un
    pyproject.toml que todavía es el de la plantilla. Una tarea que sincronizara el
    entorno en ese momento reescribiría uv.lock sin las dependencias propias.
    """
    anterior = correr(["git", "describe", "--tags", "--abbrev=0", "HEAD~1"], RAIZ).stdout.strip()
    if not anterior:
        ok("dependencias propias: no hay version anterior; se omite")
        return
    destino = base / "con_dependencia"
    datos = {
        "nombre_proyecto": "con_dependencia",
        "autor_nombres": "Ana",
        "autor_apellidos": "Ruiz",
    }
    if copier(["copy", f"--vcs-ref={anterior}", str(RAIZ), str(destino)], datos, base).returncode:
        falla(f"dependencias propias: no se pudo generar desde {anterior}")
        return
    agregar = correr(["uv", "add", "--quiet", "six"], destino)
    if agregar.returncode:
        falla(f"dependencias propias: uv add fallo\n{agregar.stderr[-600:]}")
        return
    for paso in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-qm", "base"]):
        correr([*GIT, *paso], destino)
    orden = ["uvx", "copier", "update", "--trust", "--defaults", "--quiet", "--vcs-ref=HEAD"]
    r = correr(orden, destino)
    if r.returncode:
        falla(f"dependencias propias: copier update con tareas fallo\n{r.stderr[-800:]}")
    elif 'name = "six"' not in (destino / "uv.lock").read_text(encoding="utf-8"):
        falla("dependencias propias: la actualizacion con tareas reescribio uv.lock sin ellas")
    else:
        ok(f"dependencias propias: actualizar con tareas desde {anterior} conserva uv.lock")


def main() -> int:
    """Corre todas las comprobaciones y devuelve 1 si alguna falla."""
    todos = rasgos()
    print(f"Plantilla en {RAIZ}\nRasgos: {', '.join(todos)}\n")
    revisar_configuracion()
    # En Windows, Git deja sus objetos como solo lectura y el borrado del temporal
    # puede fallar despues de que todo paso; eso no es una falla de la plantilla.
    with tempfile.TemporaryDirectory(
        prefix="verificar-plantilla-", ignore_cleanup_errors=True
    ) as tmp:
        base = Path(tmp)
        for nombre, valor in (("sin rasgos", False), ("todos los rasgos", True)):
            destino = base / nombre.replace(" ", "_")
            datos = {r: valor for r in todos} | {
                "nombre_proyecto": "verificacion",
                "autor_nombres": "Ana",
                "autor_apellidos": "Ruiz",
            }
            generado = copier(["copy", "--vcs-ref=HEAD", str(RAIZ), str(destino)], datos, base)
            if generado.returncode:
                falla(f"{nombre}: copier copy fallo\n{generado.stderr[-800:]}")
                continue
            revisar_proyecto(nombre, destino)
        prueba_de_actualizacion(base)
        prueba_de_dependencias_propias(base)
    print(f"\n{'Todo en orden.' if not FALLAS else f'{len(FALLAS)} falla(s).'}")
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
