#!/usr/bin/env python3
"""
A simple LaTeX compiler wrapper for compiling LaTeX documents.
"""

import subprocess
import os
import sys
from pathlib import Path


class LatexCompiler:
    """A simple LaTeX compiler class."""
    
    def __init__(self, latex_engine="xelatex", max_compiles=2):
        """
        Initialize the LaTeX compiler.
        
        Args:
            latex_engine (str): The LaTeX engine to use (pdflatex, xelatex, lualatex)
            max_compiles (int): Maximum number of compilation passes for references
        """
        self.latex_engine = latex_engine
        self.max_compiles = max_compiles
        
    def compile_latex(self, tex_file, output_dir=".", clean=True, silent=False):
        """
        Compile a LaTeX file.
        
        Args:
            tex_file (str): Path to the .tex file
            output_dir (str): Directory to output the PDF
            clean (bool): Whether to clean auxiliary files
            silent (bool): Whether to suppress compilation output
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Check if the LaTeX engine is available
            if not self._check_engine():
                return False, f"LaTeX engine '{self.latex_engine}' not found. Please install TeX Live, MiKTeX, or MacTeX."
            
            # Get absolute paths
            tex_path = Path(tex_file)
            if not tex_path.exists():
                return False, f"File '{tex_file}' not found."
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Change to the directory containing the .tex file
            original_dir = os.getcwd()
            os.chdir(tex_path.parent)
            
            try:
                # Compile multiple times for references
                for i in range(self.max_compiles):
                    cmd = [self.latex_engine, "-interaction=nonstopmode", "-output-directory", str(output_path.absolute()), tex_path.name]
                    
                    if silent:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                    else:
                        print(f"Compilation pass {i + 1}/{self.max_compiles}...")
                        result = subprocess.run(cmd)
                    
                    if result.returncode != 0:
                        error_msg = result.stderr if result.stderr else result.stdout
                        return False, f"LaTeX compilation failed: {error_msg}"
                
                # Clean auxiliary files if requested
                if clean:
                    self._clean_aux_files(output_path, tex_path.stem)
                
                pdf_path = output_path / f"{tex_path.stem}.pdf"
                if pdf_path.exists():
                    return True, f"Successfully compiled {tex_file} to {pdf_path}"
                else:
                    return False, "PDF file was not generated"
                    
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            return False, f"Error during compilation: {str(e)}"
    
    def _check_engine(self):
        """Check if the LaTeX engine is available."""
        try:
            result = subprocess.run([self.latex_engine, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _clean_aux_files(self, output_dir, base_name):
        """Clean auxiliary LaTeX files."""
        aux_extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.bbl', '.blg', '.fls', '.fdb_latexmk']
        
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
