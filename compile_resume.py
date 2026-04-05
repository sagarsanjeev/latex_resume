#!/usr/bin/env python3
"""
Example script to compile the resume using the LaTeX compiler.
"""

from latex_compiler import LatexCompiler
import os

def main():
    """Compile the resume.tex file."""
    # Initialize compiler with XeLaTeX (required for this resume)
    compiler = LatexCompiler(latex_engine="xelatex", max_compiles=2)
    
    # Compile the resume
    tex_file = "resume.tex"
    
    print(f"Compiling {tex_file}...")
    success, message = compiler.compile_latex(
        tex_file,
        output_dir=".",  # Current directory
        clean=True,       # Clean temporary files
        silent=False      # Show compilation output
    )
    
    if success:
        print(f"✓ {message}")
        print(f"PDF generated: resume.pdf")
    else:
        print(f"✗ {message}")
        print("\nTroubleshooting tips:")
        print("1. Make sure XeLaTeX is installed (TeX Live, MiKTeX, or MacTeX)")
        print("2. Check that all required fonts are available")
        print("3. Verify the Raleway-Medium.otf font file is present")
        print("4. Try running: xelatex resume.tex manually to see detailed errors")

if __name__ == '__main__':
    main()
