#!/usr/bin/env python3
"""
A simple LaTeX compiler wrapper for compiling LaTeX documents.
Supports running via WSL (Windows Subsystem for Linux) when available.
"""

import subprocess
import os
import sys
import shutil
from pathlib import Path, PurePosixPath


def _is_wsl_available() -> bool:
    """Return True if WSL is installed and reachable on this machine."""
    return shutil.which("wsl") is not None


def _windows_path_to_wsl(path: Path) -> str:
    """
    Convert an absolute Windows path to its WSL mount equivalent.

    Example:
        C:\\Users\\sagar\\resume.tex  ->  /mnt/c/Users/sagar/resume.tex
    """
    abs_path = path.resolve()
    drive = abs_path.drive          # e.g. "C:"
    # Strip the drive letter and colon, replace backslashes with forward slashes
    rest = abs_path.as_posix()[len(drive):]   # e.g. "/Users/sagar/resume.tex"
    drive_letter = drive.rstrip(":").lower()  # e.g. "c"
    return f"/mnt/{drive_letter}{rest}"


class LatexCompiler:
    """A simple LaTeX compiler class with optional WSL support."""

    def __init__(self, latex_engine="xelatex", max_compiles=2, use_wsl=None):
        """
        Initialize the LaTeX compiler.

        Args:
            latex_engine (str): The LaTeX engine to use (pdflatex, xelatex, lualatex).
            max_compiles (int): Maximum number of compilation passes for references.
            use_wsl (bool | None): Force WSL on/off.  None (default) = auto-detect:
                                   use WSL when available *and* the native engine is absent.
        """
        self.latex_engine = latex_engine
        self.max_compiles = max_compiles
        self._use_wsl = use_wsl  # None means "decide later"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile_latex(self, tex_file, output_dir=".", clean=True, silent=False):
        """
        Compile a LaTeX file.

        Args:
            tex_file (str): Path to the .tex file.
            output_dir (str): Directory to output the PDF.
            clean (bool): Whether to clean auxiliary files.
            silent (bool): Whether to suppress compilation output.

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            use_wsl = self._resolve_wsl_mode()

            if use_wsl:
                print("WSL detected – running LaTeX inside WSL.")
            elif not self._check_engine_native():
                return (
                    False,
                    f"LaTeX engine '{self.latex_engine}' not found. "
                    "Install TeX Live / MiKTeX, or enable WSL with a TeX distribution installed.",
                )

            tex_path = Path(tex_file)
            if not tex_path.exists():
                return False, f"File '{tex_file}' not found."

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            original_dir = os.getcwd()
            os.chdir(tex_path.parent)

            try:
                for i in range(self.max_compiles):
                    cmd = self._build_command(
                        tex_path, output_path.absolute(), use_wsl
                    )

                    if not silent:
                        print(f"Compilation pass {i + 1}/{self.max_compiles}...")

                    if silent:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                    else:
                        result = subprocess.run(cmd)

                    if result.returncode != 0:
                        error_msg = (
                            getattr(result, "stderr", "") or
                            getattr(result, "stdout", "")
                        )
                        return False, f"LaTeX compilation failed: {error_msg}"

                if clean:
                    self._clean_aux_files(output_path.absolute(), tex_path.stem)

                pdf_path = output_path.absolute() / f"{tex_path.stem}.pdf"
                if pdf_path.exists():
                    return True, f"Successfully compiled {tex_file} to {pdf_path}"
                return False, "PDF file was not generated"

            finally:
                os.chdir(original_dir)

        except Exception as e:
            return False, f"Error during compilation: {str(e)}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_wsl_mode(self) -> bool:
        """
        Determine whether to use WSL for this run.

        Logic:
        - If use_wsl was explicitly set (True/False), honour it.
        - Otherwise: use WSL only when WSL is available AND the native
          LaTeX engine cannot be found on the Windows PATH.
        """
        if self._use_wsl is True:
            if not _is_wsl_available():
                raise EnvironmentError(
                    "WSL was requested (use_wsl=True) but 'wsl' is not available."
                )
            return True

        if self._use_wsl is False:
            return False

        # Auto-detect
        if _is_wsl_available() and not self._check_engine_native():
            return True

        return False

    def _check_engine_native(self) -> bool:
        """Check if the LaTeX engine is available natively (outside WSL)."""
        try:
            result = subprocess.run(
                [self.latex_engine, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_engine_wsl(self) -> bool:
        """Check if the LaTeX engine is available inside WSL."""
        try:
            result = subprocess.run(
                ["wsl", self.latex_engine, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_engine(self) -> bool:
        """Compatibility shim – checks whichever backend will actually be used."""
        if self._resolve_wsl_mode():
            return self._check_engine_wsl()
        return self._check_engine_native()

    def _build_command(self, tex_path: Path, abs_output: Path, use_wsl: bool) -> list:
        """Build the subprocess command list for the chosen backend."""
        if use_wsl:
            wsl_tex = _windows_path_to_wsl(tex_path.resolve())
            wsl_out = _windows_path_to_wsl(abs_output)
            return [
                "wsl",
                self.latex_engine,
                "-interaction=nonstopmode",
                "-output-directory", wsl_out,
                wsl_tex,
            ]
        else:
            return [
                self.latex_engine,
                "-interaction=nonstopmode",
                "-output-directory", str(abs_output),
                tex_path.name,
            ]

    def _clean_aux_files(self, output_dir: Path, base_name: str):
        """Clean auxiliary LaTeX files."""
        aux_extensions = [
            ".aux", ".log", ".out", ".toc", ".lof", ".lot",
            ".bbl", ".blg", ".fls", ".fdb_latexmk",
        ]
        for ext in aux_extensions:
            aux_file = output_dir / f"{base_name}{ext}"
            if aux_file.exists():
                try:
                    aux_file.unlink()
                except OSError:
                    pass  # Ignore cleanup errors


if __name__ == "__main__":
    # Example usage
    compiler = LatexCompiler(latex_engine="xelatex")
    success, message = compiler.compile_latex("resume.tex")
    print(f"Success: {success}")
    print(f"Message: {message}")
