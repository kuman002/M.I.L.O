from faster_whisper import download_model
import os

# Define where to save the model (Inside your project)
# This makes it truly "Offline" and portable
save_path = os.path.join("assets", "milo_brain")

print(f"⏳ Downloading 'small' model to: {save_path}")
print("   (This helps fix the 'model.bin' error)")

try:
    # 1. Download the model files explicitly
    path = download_model("small", output_dir=save_path)
    print(f"✅ Success! Model saved at: {path}")
    print("   You can now run 'src.main' again.")
    
except Exception as e:
    print(f"❌ Download Failed: {e}")