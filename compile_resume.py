#!/usr/bin/env python3
"""
Compile resume.tex using XeLaTeX.

WSL support
-----------
If XeLaTeX is not found on the native Windows PATH but WSL is available,
compilation is automatically routed through WSL.  You can also force a
specific backend:

    compiler = LatexCompiler(latex_engine="xelatex", use_wsl=True)   # always WSL
    compiler = LatexCompiler(latex_engine="xelatex", use_wsl=False)  # never  WSL
    compiler = LatexCompiler(latex_engine="xelatex")                  # auto   (default)
"""

from latex_compiler import LatexCompiler, _is_wsl_available
import os


def main():
    """Compile the resume.tex file."""

    # Auto mode: uses WSL when available and native xelatex is absent.
    compiler = LatexCompiler(latex_engine="xelatex", max_compiles=2)

    tex_file = "resume.tex"

    # Let the user know which backend will be used before starting.
    use_wsl = compiler._resolve_wsl_mode()
    if use_wsl:
        wsl_has_engine = compiler._check_engine_wsl()
        if not wsl_has_engine:
            print(
                "✗ WSL is available but XeLaTeX was not found inside it.\n"
                "  Install it with:  wsl sudo apt install texlive-xetex"
            )
            return
        print("Backend : WSL (wsl xelatex)")
    else:
        if not compiler._check_engine_native():
            print(
                "✗ XeLaTeX not found on native PATH and WSL is"
                f"{'not ' if not _is_wsl_available() else ''}available.\n"
                "  Options:\n"
                "  • Install TeX Live / MiKTeX on Windows, or\n"
                "  • Install WSL (wsl --install) and then:\n"
                "      wsl sudo apt install texlive-xetex"
            )
            return
        print("Backend : native xelatex")

    print(f"Compiling {tex_file}...")
    success, message = compiler.compile_latex(
        tex_file,
        output_dir=".",  # Current directory
        clean=True,       # Clean temporary files after compile
        silent=False,     # Show compilation output
    )

    if success:
        print(f"✓ {message}")
        print("PDF generated: resume.pdf")
    else:
        print(f"✗ {message}")
        print("\nTroubleshooting tips:")
        print("1. Make sure XeLaTeX is installed:")
        print("   - Windows : TeX Live (tug.org/texlive) or MiKTeX (miktex.org)")
        print("   - WSL/Linux: sudo apt install texlive-xetex")
        print("2. Ensure the Raleway-Medium.otf font file is in the project folder")
        print("3. Run manually to see full errors:")
        print("   - Windows : xelatex resume.tex")
        print("   - WSL     : wsl xelatex resume.tex")


if __name__ == "__main__":
    main()
