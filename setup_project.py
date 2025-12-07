# setup_project.py
import os

def create_project_structure():
    """
    Creates the complete directory structure and empty files for Project M.I.L.O.
    """
    project_name = "M.I.L.O"
    
    # Define the folder structure
    directories = [
        f"{project_name}/milo",
        f"{project_name}/milo/core",
        f"{project_name}/milo/managers",
        f"{project_name}/milo/analysis",
        f"{project_name}/milo/features",
        f"{project_name}/milo/security",
        f"{project_name}/milo/iot",
        f"{project_name}/rasa/data",
        f"{project_name}/rasa/models",
        f"{project_name}/data",
        f"{project_name}/android_app",
        f"{project_name}/tests"
    ]

    # Define the files to create (path relative to project root)
    files = [
        f"{project_name}/main.py",
        f"{project_name}/requirements.txt",
        f"{project_name}/README.md",
        f"{project_name}/pyproject.toml",
        f"{project_name}/.gitignore",
        
        # Package initializers
        f"{project_name}/milo/__init__.py",
        f"{project_name}/milo/core/__init__.py",
        f"{project_name}/milo/managers/__init__.py",
        
        # Core modules
        f"{project_name}/milo/core/voice_engine.py",
        f"{project_name}/milo/core/phone_controller.py",
        
        # Managers
        f"{project_name}/milo/managers/memory_manager.py",
        f"{project_name}/milo/managers/reminder_manager.py",
        f"{project_name}/milo/managers/expenses_manager.py",
        
        # Analysis
        f"{project_name}/milo/analysis/pattern_finder.py",
        f"{project_name}/milo/analysis/finance_analyzer.py",
        
        # Security & IoT
        f"{project_name}/milo/security/crypto_manager.py",
        f"{project_name}/milo/iot/smart_plug_controller.py",
        
        # Features
        f"{project_name}/milo/features/focus_mode_manager.py",

        # Rasa Configs
        f"{project_name}/rasa/config.yml",
        f"{project_name}/rasa/domain.yml",
        f"{project_name}/rasa/data/nlu.yml"
    ]

    print(f"🚀 Initializing Project {project_name}...\n")

    # 1. Create Directories
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created Directory: {directory}")
        except OSError as e:
            print(f"❌ Error creating {directory}: {e}")

    # 2. Create Files
    for file_path in files:
        try:
            # Create empty file
            with open(file_path, 'w') as f:
                # Add a docstring to python files
                if file_path.endswith(".py"):
                    filename = os.path.basename(file_path)
                    f.write(f'"""\nModule: {filename}\nDescription: [Add description here]\n"""\n\n')
            print(f"📄 Created File: {file_path}")
        except OSError as e:
            print(f"❌ Error creating {file_path}: {e}")

    print(f"\n✨ {project_name} setup complete! You can now open the folder in your code editor.")

if __name__ == "__main__":
    create_project_structure()