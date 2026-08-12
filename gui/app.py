import json
import os
import sys
import time
import wave
from pathlib import Path
import uuid

# Fix encoding cho Windows console (tránh UnicodeEncodeError)
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import numpy as np
import onnxruntime as ort
from flask import Flask, request, jsonify, render_template, send_from_directory

# ──────────────────────── Đường dẫn thư mục ────────────────────────
GUI_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GUI_DIR.parent
ONNX_MODEL_PATH = PROJECT_DIR / "model_epoch_4988.onnx"
ONNX_CONFIG_PATH = PROJECT_DIR / "model_epoch_4988.onnx.json"
AUDIO_OUTPUT_DIR = GUI_DIR / "static" / "audio"

# Đảm bảo thư mục audio output tồn tại
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Khởi tạo Flask
app = Flask(__name__, template_folder=str(GUI_DIR / "templates"), static_folder=str(GUI_DIR / "static"))

# ──────────────────────── Tải cấu hình & Model ──────────────────────
def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Tải cấu hình
if not ONNX_MODEL_PATH.exists() or not ONNX_CONFIG_PATH.exists():
    print(f"❌ Không tìm thấy model hoặc config tại: {PROJECT_DIR}")
    sys.exit(1)

config = load_config(ONNX_CONFIG_PATH)
sample_rate = config.get("audio", {}).get("sample_rate", 22050)

# Khởi tạo ONNX Runtime Session
print("⏳ Đang tải mô hình ONNX...")
sess_options = ort.SessionOptions()
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

providers = []
available = ort.get_available_providers()
if "CUDAExecutionProvider" in available:
    providers.append("CUDAExecutionProvider")
    print("  ✅ Sử dụng GPU (CUDA)")
providers.append("CPUExecutionProvider")
if len(providers) == 1:
    print("  ℹ️  Sử dụng CPU")

session = ort.InferenceSession(
    str(ONNX_MODEL_PATH),
    sess_options=sess_options,
    providers=providers,
)
print("  ✅ Tải model thành công!\n")

# Kiểm tra piper_phonemize
use_piper = True
try:
    import piper_phonemize
    print("  ✅ piper_phonemize đã được cài đặt (espeak-ng)")
except ImportError:
    use_piper = False
    print("  ⚠️  piper_phonemize chưa cài -> dùng fallback (ký tự trực tiếp)")

# Dọn dẹp các file âm thanh cũ trong thư mục static khi khởi động
def cleanup_old_audio():
    for f in AUDIO_OUTPUT_DIR.glob("*.wav"):
        try:
            f.unlink()
        except Exception:
            pass

cleanup_old_audio()

# ──────────────────────── Phân tích Text → Phoneme IDs ────────────────
def text_to_phoneme_ids(text: str, config: dict) -> list[int]:
    from piper_phonemize import phonemize_espeak

    phoneme_id_map = config["phoneme_id_map"]
    language = config.get("espeak", {}).get("voice", "vi")

    sentences = phonemize_espeak(text, language)
    ids: list[int] = []

    if "^" in phoneme_id_map:
        ids.extend(phoneme_id_map["^"])
    
    for sentence_phonemes in sentences:
        for phoneme_str in sentence_phonemes:
            for char in phoneme_str:
                if char in phoneme_id_map:
                    ids.extend(phoneme_id_map[char])
                    if "_" in phoneme_id_map:
                        ids.extend(phoneme_id_map["_"])

    if "$" in phoneme_id_map:
        ids.extend(phoneme_id_map["$"])

    return ids

def text_to_phoneme_ids_fallback(text: str, config: dict) -> list[int]:
    phoneme_id_map = config["phoneme_id_map"]
    ids: list[int] = []

    if "^" in phoneme_id_map:
        ids.extend(phoneme_id_map["^"])

    for char in text.lower():
        if char in phoneme_id_map:
            ids.extend(phoneme_id_map[char])
            if "_" in phoneme_id_map:
                ids.extend(phoneme_id_map["_"])
        elif char == " ":
            if " " in phoneme_id_map:
                ids.extend(phoneme_id_map[" "])

    if "$" in phoneme_id_map:
        ids.extend(phoneme_id_map["$"])

    return ids

# ──────────────────────── Inference VITS ────────────────────────────
def synthesize(
    text: str,
    session: ort.InferenceSession,
    config: dict,
    noise_scale: float = 0.667,
    length_scale: float = 1.0,
    noise_w: float = 0.8,
) -> np.ndarray:
    if use_piper:
        phoneme_ids = text_to_phoneme_ids(text, config)
    else:
        phoneme_ids = text_to_phoneme_ids_fallback(text, config)

    if not phoneme_ids:
        raise ValueError(f"Không tạo được phoneme IDs từ text: '{text}'")

    phoneme_ids_array = np.array([phoneme_ids], dtype=np.int64)
    phoneme_ids_lengths = np.array([len(phoneme_ids)], dtype=np.int64)
    scales = np.array([noise_scale, length_scale, noise_w], dtype=np.float32)

    feed = {}
    for inp in session.get_inputs():
        name = inp.name
        expected_shape = inp.shape

        if name == "input":
            feed[name] = phoneme_ids_array
        elif name == "input_lengths":
            feed[name] = phoneme_ids_lengths
        elif name == "scales":
            feed[name] = scales
        elif name == "sid" or "speaker" in name.lower():
            feed[name] = np.array([0], dtype=np.int64)
        else:
            if expected_shape and len(expected_shape) == 2:
                feed[name] = phoneme_ids_array
            elif expected_shape and len(expected_shape) == 1:
                if expected_shape[0] == 3:
                    feed[name] = scales
                else:
                    feed[name] = phoneme_ids_lengths

    output = session.run(None, feed)
    audio = output[0].squeeze()
    return audio

def save_wav(audio: np.ndarray, output_path: Path, sample_rate: int = 22050):
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

# ──────────────────────── Routes ────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/synthesize", methods=["POST"])
def api_synthesize():
    try:
        data = request.json or {}
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Vui lòng nhập văn bản cần chuyển đổi!"}), 400

        # Lấy các tham số tùy chọn từ request
        noise_scale = float(data.get("noise_scale", 0.667))
        length_scale = float(data.get("length_scale", 1.0))
        noise_w = float(data.get("noise_w", 0.8))

        # Giới hạn tham số hợp lý
        noise_scale = max(0.1, min(2.0, noise_scale))
        length_scale = max(0.1, min(3.0, length_scale))
        noise_w = max(0.1, min(2.0, noise_w))

        # Tạo tên file ngẫu nhiên độc nhất bằng uuid
        filename = f"tts_{uuid.uuid4().hex[:10]}_{int(time.time())}.wav"
        output_file = AUDIO_OUTPUT_DIR / filename

        # Thực hiện tổng hợp giọng nói
        start_time = time.perf_counter()
        audio = synthesize(text, session, config, noise_scale, length_scale, noise_w)
        elapsed = time.perf_counter() - start_time
        
        save_wav(audio, output_file, sample_rate)
        duration = len(audio) / sample_rate

        # Trả về thông tin file âm thanh và thống kê
        return jsonify({
            "success": True,
            "audio_url": f"/static/audio/{filename}",
            "filename": filename,
            "duration": f"{duration:.2f}",
            "elapsed": f"{elapsed:.2f}",
            "rtf": f"{elapsed/duration:.3f}" if duration > 0 else "0.00"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Lỗi trong quá trình tổng hợp: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
