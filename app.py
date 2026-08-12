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
ONNX_MODEL_PATH = PROJECT_DIR / "model_epoch_4988.onnx"
ONNX_CONFIG_PATH = PROJECT_DIR / "model_epoch_4988.onnx.json"

# Biến toàn cục cho model
session = None
config = None
sample_rate = 22050
use_piper = False

def init_model():
    global session, config, sample_rate, use_piper
    
    if not ONNX_MODEL_PATH.exists() or not ONNX_CONFIG_PATH.exists():
        print("Không tìm thấy model hoặc config!")
        return False
        
    config = load_config(ONNX_CONFIG_PATH)
    sample_rate = config.get("audio", {}).get("sample_rate", 22050)
    
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    
    providers = []
    available = ort.get_available_providers()
    if "CUDAExecutionProvider" in available:
        providers.append("CUDAExecutionProvider")
    providers.append("CPUExecutionProvider")
    
    session = ort.InferenceSession(
        str(ONNX_MODEL_PATH),
        sess_options=sess_options,
        providers=providers,
    )
    
    try:
        import piper_phonemize
        use_piper = True
    except ImportError:
        use_piper = False
        
    return True

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
    if session is None:
        return jsonify({"error": "Model chưa được tải"}), 500
        
    data = request.json
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "Vui lòng nhập văn bản"}), 400
        
    try:
        audio = synthesize(text, session, config, use_piper)
        wav_bytes = audio_to_wav_bytes(audio, sample_rate)
        
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
