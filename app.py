import io
import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify
import numpy as np
import onnxruntime as ort

# Fix encoding cho Windows console (tránh UnicodeEncodeError)
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import các hàm từ test_model
from test_model import load_config, synthesize

app = Flask(__name__)

# Cấu hình đường dẫn
PROJECT_DIR = Path(__file__).resolve().parent
# Cấu hình đường dẫn các mô hình
MODELS_INFO = {
    "voice1": {
        "name": "Giọng 1 (Epoch 4988)",
        "model_path": PROJECT_DIR / "model_epoch_4988.onnx",
        "config_path": PROJECT_DIR / "model_epoch_4988.onnx.json",
    },
    "voice2": {
        "name": "Giọng 2 (Giong Nam)",
        "model_path": PROJECT_DIR / "giongnam.onnx",
        "config_path": PROJECT_DIR / "giongnam.json",
    }
}

# Biến toàn cục cho model
loaded_models = {}
use_piper = False

def init_model():
    global loaded_models, use_piper
    
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    
    providers = []
    available = ort.get_available_providers()
    if "CUDAExecutionProvider" in available:
        providers.append("CUDAExecutionProvider")
    providers.append("CPUExecutionProvider")
    
    for voice_id, info in MODELS_INFO.items():
        if not info["model_path"].exists() or not info["config_path"].exists():
            print(f"Không tìm thấy model hoặc config cho {info['name']}! Bỏ qua.")
            continue
            
        try:
            config = load_config(info["config_path"])
            sample_rate = config.get("audio", {}).get("sample_rate", 22050)
            
            session = ort.InferenceSession(
                str(info["model_path"]),
                sess_options=sess_options,
                providers=providers,
            )
            
            loaded_models[voice_id] = {
                "session": session,
                "config": config,
                "sample_rate": sample_rate
            }
            print(f"✅ Đã tải thành công: {info['name']}")
        except Exception as e:
            print(f"❌ Lỗi tải mô hình {info['name']}: {e}")
            
    try:
        import piper_phonemize
        use_piper = True
    except ImportError:
        use_piper = False
        
    return len(loaded_models) > 0

def audio_to_wav_bytes(audio: np.ndarray, sr: int) -> bytes:
    import wave
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)
    
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    return buffer.getvalue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tts', methods=['POST'])
def tts():
    if not loaded_models:
        return jsonify({"error": "Chưa có mô hình nào được tải"}), 500
        
    data = request.json
    text = data.get("text", "").strip()
    voice_id = data.get("voice", "voice1")
    
    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản"}), 400
        
    if voice_id not in loaded_models:
        # Mặc định lấy model đầu tiên nếu id không hợp lệ
        voice_id = list(loaded_models.keys())[0]
        
    model_data = loaded_models[voice_id]
    
    try:
        audio = synthesize(text, model_data["session"], model_data["config"], use_piper)
        wav_bytes = audio_to_wav_bytes(audio, model_data["sample_rate"])
        
        return send_file(
            io.BytesIO(wav_bytes),
            mimetype="audio/wav",
            as_attachment=False,
            download_name="output.wav"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Khởi tạo model khi load app (cần thiết khi chạy trên server qua gunicorn hoặc docker)
if not init_model():
    print("❌ Lỗi khởi tạo model!")

if __name__ == '__main__':
    print("🚀 Khởi động server Flask tại http://0.0.0.0:7860")
    app.run(host='0.0.0.0', port=7860, debug=True)
