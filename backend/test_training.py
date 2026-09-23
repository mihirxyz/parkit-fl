import subprocess
import sys
import os

def run_training():
    """Run the centralized training script."""
    backend_dir = r"C:\Users\inamd\Desktop\parkit-fl\backend"
    script_path = os.path.join(backend_dir, "app", "ml", "train_centralized.py")
    
    # Activate venv and run the script
    python_exe = os.path.join(backend_dir, ".venv", "Scripts", "python.exe")
    
    cmd = f'"{python_exe}" "{script_path}"'
    
    print(f"Running command: {cmd}")
    print("-" * 80)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=backend_dir)
        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing centralized training script...")
    print(f"Current working directory: {os.getcwd()}")
    success = run_training()
    
    if success:
        print("\n✅ Training completed successfully!")
    else:
        print("\n❌ Training failed. Check above output for details.")
