import os
import json
from typing import Dict, Any

class ProjectAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.ignored_dirs = {'__pycache__', '.git', '.venv', 'venv', 'env', '.ipynb_checkpoints', '.jupyter'}
        self.ignored_files = {'.pyc', '.pyo', '.pyd', '.so', '.dll', '.html', '.md', '.pdf', 'analyze_project.py', '.gitignore' , '.log', 'hotel_data.json', 'project_structure.json'}

    def should_ignore(self, path: str) -> bool:
        """Check if the path should be ignored."""
        parts = path.split(os.sep)
        return any(part in self.ignored_dirs for part in parts) or \
               any(path.endswith(ext) for ext in self.ignored_files)

    def read_file_content(self, file_path: str) -> str:
        """Read and return file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def analyze_directory(self, dir_path: str) -> Dict[str, Any]:
        """Recursively analyze directory and return structured data."""
        structure = {
            'type': 'directory',
            'name': os.path.basename(dir_path),
            'contents': {}
        }

        try:
            items = os.listdir(dir_path)
            for item in items:
                full_path = os.path.join(dir_path, item)
                
                if self.should_ignore(full_path):
                    continue

                if os.path.isfile(full_path):
                    structure['contents'][item] = {
                        'type': 'file',
                        'name': item,
                        'extension': os.path.splitext(item)[1],
                        'content': self.read_file_content(full_path)
                    }
                elif os.path.isdir(full_path):
                    structure['contents'][item] = self.analyze_directory(full_path)

        except Exception as e:
            structure['error'] = str(e)

        return structure

    def analyze(self) -> Dict[str, Any]:
        """Analyze the entire project and return structured data."""
        return self.analyze_directory(self.root_dir)

    def save_analysis(self, output_file: str):
        """Analyze project and save results to a JSON file."""
        analysis = self.analyze()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

def main():
    # Get the current directory as the root directory
    root_dir = os.getcwd()
    
    # Create analyzer instance
    analyzer = ProjectAnalyzer(root_dir)
    
    # Save analysis to project_structure.json
    analyzer.save_analysis('project_structure.json')
    print("Project analysis completed and saved to project_structure.json")

if __name__ == "__main__":
    main()