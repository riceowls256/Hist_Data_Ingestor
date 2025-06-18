import os
import pathlib
import pathspec

# --- Configuration ---
# The root directory of your project (the script's current location)
ROOT_DIR = pathlib.Path(__file__).parent.resolve()
# The name of the output file
OUTPUT_FILE = "project_context_trimmed.txt"
# Maximum size for any single file to be included (in bytes)
# 1MB = 1024 * 1024 = 1,048,576 bytes. Let's set it to 1MB.
MAX_FILE_SIZE_BYTES = 1048576 

# Directories to completely ignore. Use forward slashes.
# These are often full of non-essential code or heavy data.
DIR_EXCLUDES = [
    ".git/",
    ".idea/",
    ".vscode/",
    "__pycache__/",
    "demos/",
    "tests/hist_api/",
    "tests/fixtures/",
    ".ai/",
    ".bmad-core/",
    ".cursor/",
    ".cursorrules/",
    ".cursorignore/",
    ".cursorignorerules/",
    ".cursorignorerulesrules/",
    "dlq/",
    "logs/",
    "trees/",
    "venv/",
    "wheels/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".pytest_cache/",
    ".vscode/",
    ".vscode/",
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    ".env.development.local",
    ".env.production.local",
    # Ignori theai folder
]

# File extensions to ignore.
EXT_EXCLUDES = [
    ".pyc",
    ".log",
    ".csv",
    ".parquet",
    ".zip",
    ".gz",
    ".DS_Store",
]

# Specific files to ignore
FILE_EXCLUDES = [
    OUTPUT_FILE,
    pathlib.Path(__file__).name # Ignore this script itself
]
# --- End Configuration ---

def get_gitignore_patterns(root_dir):
    """Reads .gitignore from the root and returns pathspec patterns."""
    ignore_file = root_dir / ".gitignore"
    patterns = []
    if ignore_file.is_file():
        with ignore_file.open("r", encoding="utf-8") as f:
            patterns = f.read().splitlines()
    
    # Add all our custom exclusion rules
    patterns.extend(DIR_EXCLUDES)
    patterns.extend(f"*{ext}" for ext in EXT_EXCLUDES)
    patterns.extend(FILE_EXCLUDES)
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

def pack_project_files(root_dir, spec):
    """Walks the project, reads non-ignored files, and returns a single string."""
    all_content = []
    
    # Use rglob to find all files, which is generally efficient
    all_files = list(root_dir.rglob("*"))
    
    print(f"Found {len(all_files)} total paths. Filtering...")

    for filepath in all_files:
        if not filepath.is_file():
            continue

        relative_path_str = str(filepath.relative_to(root_dir).as_posix())

        if spec.match_file(relative_path_str):
            continue

        # Check file size
        try:
            file_size = filepath.stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                header = f"--- File: {relative_path_str} (SKIPPED: Exceeds {MAX_FILE_SIZE_BYTES / 1024:.0f} KB) ---\n"
                all_content.append(header)
                continue
        except FileNotFoundError:
            continue # File might have been deleted during the run

        try:
            with filepath.open("r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            header = f"--- File: {relative_path_str} ---\n"
            all_content.append(header + content + "\n")

        except Exception as e:
            header = f"--- File: {relative_path_str} (Binary or Unreadable) ---\n"
            all_content.append(header + f"Error reading file: {e}\n")

    return "".join(all_content)

if __name__ == "__main__":
    print("Starting surgical project packager...")
    gitignore_spec = get_gitignore_patterns(ROOT_DIR)
    
    packed_content = pack_project_files(ROOT_DIR, gitignore_spec)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(packed_content)
        
    final_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\nDone. Project context trimmed and packed into:\n{OUTPUT_FILE}")
    print(f"Final size: {final_size_mb:.2f} MB")
    print("\nYou can now copy the contents of that file and paste it here.")