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
current_voice_id = None
current_session = None
current_config = None
current_sample_rate = 22050
use_piper = False

def load_voice(voice_id):
    global current_voice_id, current_session, current_config, current_sample_rate
    
    # Nếu đã load đúng giọng này rồi thì dùng luôn
    if voice_id == current_voice_id and current_session is not None:
        return True
        
    info = MODELS_INFO.get(voice_id)
    if not info:
        return False
        
    if not info["model_path"].exists() or not info["config_path"].exists():
        print(f"Không tìm thấy model hoặc config cho {info['name']}! Bỏ qua.")
        return False
        
    try:
        # Xóa model cũ khỏi RAM trước khi load model mới
        current_session = None
        current_config = None
        import gc
        gc.collect()

        config = load_config(info["config_path"])
        sample_rate = config.get("audio", {}).get("sample_rate", 22050)
        
        sess_options = ort.SessionOptions()
        # Chuyển xuống BASIC để tiết kiệm rất nhiều RAM trên Render Free
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        
        providers = []
        available = ort.get_available_providers()
        if "CUDAExecutionProvider" in available:
            providers.append("CUDAExecutionProvider")
        providers.append("CPUExecutionProvider")
        
        session = ort.InferenceSession(
            str(info["model_path"]),
            sess_options=sess_options,
            providers=providers,
        )
        
        current_session = session
        current_config = config
        current_sample_rate = sample_rate
        current_voice_id = voice_id
        
        print(f"✅ Đã tải thành công: {info['name']}")
        return True
    except Exception as e:
        print(f"❌ Lỗi tải mô hình {info['name']}: {e}")
        return False

def init_model():
    global use_piper
    
    try:
        import piper_phonemize
        use_piper = True
    except ImportError:
        use_piper = False
        
    # Mặc định tải giọng 1 khi khởi động
    return load_voice("voice1")

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
    data = request.json
    text = data.get("text", "").strip()
    voice_id = data.get("voice", "voice1")
    
    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản"}), 400
        
    if voice_id not in MODELS_INFO:
        voice_id = "voice1"
        
    if not load_voice(voice_id):
        return jsonify({"error": "Không thể tải mô hình cho giọng này"}), 500
    
    try:
        audio = synthesize(text, current_session, current_config, use_piper)
        wav_bytes = audio_to_wav_bytes(audio, current_sample_rate)
        
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
