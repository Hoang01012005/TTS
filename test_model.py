"""
Test script cho mô hình VITS TTS tiếng Việt (Piper ONNX).

Cách dùng:
    python test_model.py                          # Chạy với câu mặc định
    python test_model.py "Xin chào Việt Nam"      # Chạy với câu tùy chọn
    python test_model.py --interactive             # Chế độ nhập liên tục

Yêu cầu cài đặt:
    pip install numpy onnxruntime soundfile
    pip install piper-phonemize-fix              # Windows (có sẵn wheel)
"""

import json
import os
import sys
import time
import wave
from pathlib import Path

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


# ──────────────────────── Đường dẫn mặc định ────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent
ONNX_MODEL_PATH = PROJECT_DIR / "model_epoch_4988.onnx"
ONNX_CONFIG_PATH = PROJECT_DIR / "model_epoch_4988.onnx.json"
OUTPUT_DIR = PROJECT_DIR / "output"


# ──────────────────────── Tải cấu hình ──────────────────────────────
def load_config(config_path: Path) -> dict:
    """Đọc file JSON cấu hình của mô hình ONNX."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────── Chuyển text → phoneme IDs ─────────────────
def text_to_phoneme_ids(text: str, config: dict) -> list[int]:
    """
    Dùng piper_phonemize (espeak-ng) để chuyển text → phoneme,
    sau đó ánh xạ phoneme → ID theo phoneme_id_map trong config.
    """
    from piper_phonemize import phonemize_espeak

    phoneme_id_map = config["phoneme_id_map"]
    language = config.get("espeak", {}).get("voice", "vi")

    # phonemize_espeak trả về danh sách câu, mỗi câu là danh sách phoneme
    sentences = phonemize_espeak(text, language)

    # Xây dựng danh sách phoneme IDs
    ids: list[int] = []

    # Thêm ký tự bắt đầu (BOS) – thường là "^" hoặc "_"
    if "^" in phoneme_id_map:
        ids.extend(phoneme_id_map["^"])
    
    for sentence_phonemes in sentences:
        for phoneme_str in sentence_phonemes:
            for char in phoneme_str:
                if char in phoneme_id_map:
                    ids.extend(phoneme_id_map[char])
                    # Thêm blank (pad) giữa các ký tự nếu cần
                    if "_" in phoneme_id_map:
                        ids.extend(phoneme_id_map["_"])

    # Thêm ký tự kết thúc (EOS) – thường là "$"
    if "$" in phoneme_id_map:
        ids.extend(phoneme_id_map["$"])

    return ids


def text_to_phoneme_ids_fallback(text: str, config: dict) -> list[int]:
    """
    Fallback khi không cài được piper_phonemize:
    Ánh xạ trực tiếp từng ký tự trong text sang phoneme ID.
    Kết quả không chính xác bằng espeak nhưng vẫn chạy được demo.
    """
    phoneme_id_map = config["phoneme_id_map"]
    ids: list[int] = []

    # BOS
    if "^" in phoneme_id_map:
        ids.extend(phoneme_id_map["^"])

    for char in text.lower():
        if char in phoneme_id_map:
            ids.extend(phoneme_id_map[char])
            # Thêm blank giữa các ký tự
            if "_" in phoneme_id_map:
                ids.extend(phoneme_id_map["_"])
        elif char == " ":
            if " " in phoneme_id_map:
                ids.extend(phoneme_id_map[" "])

    # EOS
    if "$" in phoneme_id_map:
        ids.extend(phoneme_id_map["$"])

    return ids


# ──────────────────────── Inference ONNX ────────────────────────────
def synthesize(
    text: str,
    session: ort.InferenceSession,
    config: dict,
    use_piper_phonemize: bool = True,
) -> np.ndarray:
    """
    Chạy inference VITS ONNX:
      text → phoneme IDs → ONNX model → audio waveform (numpy array)
    """
    # 1. Text → phoneme IDs
    if use_piper_phonemize:
        phoneme_ids = text_to_phoneme_ids(text, config)
    else:
        phoneme_ids = text_to_phoneme_ids_fallback(text, config)

    if not phoneme_ids:
        raise ValueError(f"Không tạo được phoneme IDs từ text: '{text}'")

    # 2. Chuẩn bị input tensors cho ONNX
    phoneme_ids_array = np.array([phoneme_ids], dtype=np.int64)        # (1, T)
    phoneme_ids_lengths = np.array([len(phoneme_ids)], dtype=np.int64) # (1,)

    # Inference parameters từ config
    inference_cfg = config.get("inference", {})
    noise_scale = inference_cfg.get("noise_scale", 0.667)
    length_scale = inference_cfg.get("length_scale", 1.0)
    noise_w = inference_cfg.get("noise_w", 0.8)

    # Piper VITS gộp 3 tham số vào 1 tensor "scales" shape [3]
    scales = np.array([noise_scale, length_scale, noise_w], dtype=np.float32)

    # 3. Build feed dict dựa trên input names của model
    input_names = [inp.name for inp in session.get_inputs()]
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
            # Fallback: đoán dựa trên shape
            if expected_shape and len(expected_shape) == 2:
                feed[name] = phoneme_ids_array
            elif expected_shape and len(expected_shape) == 1:
                if expected_shape[0] == 3:
                    feed[name] = scales
                else:
                    feed[name] = phoneme_ids_lengths

    # 4. Chạy inference
    output = session.run(None, feed)
    audio = output[0].squeeze()  # (samples,)

    return audio


# ──────────────────────── Lưu file WAV ──────────────────────────────
def save_wav(audio: np.ndarray, output_path: Path, sample_rate: int = 22050):
    """Lưu numpy audio array thành file WAV 16-bit."""
    # Chuẩn hóa audio về [-1, 1] rồi chuyển sang int16
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())


# ──────────────────────── Hiển thị thông tin model ──────────────────
def print_model_info(session: ort.InferenceSession, config: dict):
    """In thông tin chi tiết về model."""
    print("=" * 60)
    print("  🎤 VITS TTS Model - Tiếng Việt")
    print("=" * 60)
    print(f"  Piper version : {config.get('piper_version', 'N/A')}")
    print(f"  Language       : {config.get('language', {}).get('code', 'vi')}")
    print(f"  Sample rate    : {config.get('audio', {}).get('sample_rate', 22050)} Hz")
    print(f"  Num speakers   : {config.get('num_speakers', 1)}")
    print(f"  Num symbols    : {config.get('num_symbols', 'N/A')}")
    print(f"  Phoneme type   : {config.get('phoneme_type', 'N/A')}")
    print("-" * 60)
    print("  ONNX Inputs:")
    for inp in session.get_inputs():
        print(f"    - {inp.name:30s}  shape={inp.shape}  dtype={inp.type}")
    print("  ONNX Outputs:")
    for out in session.get_outputs():
        print(f"    - {out.name:30s}  shape={out.shape}  dtype={out.type}")
    print("=" * 60)


# ──────────────────────── Chương trình chính ────────────────────────
def main():
    # Kiểm tra file model tồn tại
    if not ONNX_MODEL_PATH.exists():
        print(f"❌ Không tìm thấy model ONNX: {ONNX_MODEL_PATH}")
        sys.exit(1)
    if not ONNX_CONFIG_PATH.exists():
        print(f"❌ Không tìm thấy config: {ONNX_CONFIG_PATH}")
        sys.exit(1)

    # Tải config
    config = load_config(ONNX_CONFIG_PATH)
    sample_rate = config.get("audio", {}).get("sample_rate", 22050)

    # Tạo thư mục output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Khởi tạo ONNX Runtime session
    print("\n⏳ Đang tải mô hình ONNX...")
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    # Chọn provider: CUDA nếu có, không thì CPU
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

    # Hiển thị thông tin model
    print_model_info(session, config)

    # Kiểm tra piper_phonemize
    use_piper = True
    try:
        import piper_phonemize  # noqa: F401
        print("\n  ✅ piper_phonemize da duoc cai dat (espeak-ng)")
    except ImportError:
        use_piper = False
        print("\n  ⚠️  piper_phonemize chua cai -> dung fallback (ky tu truc tiep)")
        print("     De co ket qua tot hon, cai: pip install piper-phonemize-fix")

    # Xác định chế độ chạy
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # ── Chế độ interactive ──
        print("\n🎙️  Chế độ interactive - nhập text để tổng hợp giọng nói")
        print("   (Gõ 'quit' hoặc 'exit' để thoát)\n")

        count = 0
        while True:
            try:
                text = input("📝 Nhập text: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Tạm biệt!")
                break

            if not text or text.lower() in ("quit", "exit", "q"):
                print("\n👋 Tạm biệt!")
                break

            count += 1
            output_file = OUTPUT_DIR / f"output_{count:03d}.wav"

            try:
                start = time.perf_counter()
                audio = synthesize(text, session, config, use_piper)
                elapsed = time.perf_counter() - start

                save_wav(audio, output_file, sample_rate)
                duration = len(audio) / sample_rate

                print(f"  ✅ Đã lưu: {output_file}")
                print(f"  ⏱️  Inference: {elapsed:.2f}s | Audio: {duration:.2f}s | "
                      f"RTF: {elapsed/duration:.3f}")
                print()
            except Exception as e:
                print(f"  ❌ Lỗi: {e}\n")

    else:
        # ── Chế độ single / argument ──
        test_texts = []

        if len(sys.argv) > 1:
            # Lấy text từ argument
            test_texts = [" ".join(sys.argv[1:])]
        else:
            # Các câu mẫu mặc định
            test_texts = [
                "bố hoàng quá đẹp trai .",
                "Hôm nay thời tiết rất đẹp, chúng ta hãy đi dạo nhé.",
                "Trí tuệ nhân tạo đang thay đổi thế giới.",
                "Việt Nam là đất nước tươi đẹp với nhiều danh lam thắng cảnh.",
                "Cảm ơn bạn đã sử dụng mô hình tổng hợp giọng nói.",
            ]

        print(f"\n🚀 Bắt đầu tổng hợp {len(test_texts)} câu...\n")

        for i, text in enumerate(test_texts, 1):
            output_file = OUTPUT_DIR / f"test_{i:03d}.wav"
            print(f"[{i}/{len(test_texts)}] \"{text}\"")

            try:
                start = time.perf_counter()
                audio = synthesize(text, session, config, use_piper)
                elapsed = time.perf_counter() - start

                save_wav(audio, output_file, sample_rate)
                duration = len(audio) / sample_rate

                print(f"  ✅ Đã lưu: {output_file}")
                print(f"  ⏱️  Inference: {elapsed:.2f}s | Audio: {duration:.2f}s | "
                      f"RTF: {elapsed/duration:.3f}")
            except Exception as e:
                print(f"  ❌ Lỗi: {e}")
            print()

        print("=" * 60)
        print(f"✅ Hoàn tất! Các file audio nằm trong: {OUTPUT_DIR}")
        print("=" * 60)


if __name__ == "__main__":
    main()
