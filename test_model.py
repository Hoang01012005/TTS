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
import re
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
    noise_scale: float | None = None,
    length_scale: float | None = None,
    noise_w: float | None = None,
) -> np.ndarray:
    """
    Chạy inference VITS ONNX cho 1 câu:
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

    # Inference parameters từ config (hoặc override nếu có truyền vào)
    inference_cfg = config.get("inference", {})
    ns = noise_scale if noise_scale is not None else inference_cfg.get("noise_scale", 0.667)
    ls = length_scale if length_scale is not None else inference_cfg.get("length_scale", 1.0)
    nw = noise_w if noise_w is not None else inference_cfg.get("noise_w", 0.8)

    # Piper VITS gộp 3 tham số vào 1 tensor "scales" shape [3]
    scales = np.array([ns, ls, nw], dtype=np.float32)

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


# ──────────────────── Tách câu & ngắt nghỉ tự nhiên ────────────────────
def split_text_into_segments(text: str, default_pause: float = 0.28) -> list[tuple[str, float]]:
    """
    Tách văn bản thành các câu và khoảng lặng tương ứng (tính bằng giây).
    Hỗ trợ:
    - Dấu kết thúc câu (. ! ? ; \n)
    - Dấu ba chấm (...) -> chuyển thành khoảng nghỉ 0.35s
    - Custom pause tags: [pause:0.5s], [pause:500ms], [pause], [nghi:0.5s], [nghi]
    Trả về danh sách các tuple: (câu_văn, thời_gian_nghỉ_sau_câu)
    """
    text = text.strip()
    if not text:
        return []

    # Chuẩn hóa dấu ba chấm thành tag ngắt nghỉ
    text = re.sub(r'\.{3,}', ' [pause:0.35s] ', text)

    # Regex tách theo pause tags hoặc dấu câu
    pattern = r'(\[pause(?::\d+(?:\.\d+)?(?:s|ms)?)?\]|\[ngh[iỉ](?::\d+(?:\.\d+)?(?:s|ms)?)?\]|[.!?;\n]+)'
    tokens = re.split(pattern, text, flags=re.IGNORECASE)

    segments: list[tuple[str, float]] = []
    current_text = ""

    i = 0
    while i < len(tokens):
        part = tokens[i]
        if part is None:
            i += 1
            continue
        part_clean = part.strip()
        if not part_clean:
            i += 1
            continue

        match_tag = re.match(r'\[(pause|ngh[iỉ])(?::(\d+(?:\.\d+)?)(?:s|ms)?)?\]', part_clean, re.IGNORECASE)
        match_punct = re.match(r'^[.!?;\n]+$', part_clean)

        if match_tag:
            time_val = match_tag.group(2)
            pause_sec = default_pause
            if time_val:
                pause_sec = float(time_val)
                if 'ms' in part_clean.lower():
                    pause_sec /= 1000.0
            if current_text.strip():
                segments.append((current_text.strip(), pause_sec))
                current_text = ""
        elif match_punct:
            pause_sec = default_pause if any(c in part_clean for c in '.!?\n') else 0.18
            if current_text.strip():
                sentence_with_punct = current_text.strip() + part_clean[0]
                segments.append((sentence_with_punct.strip(), pause_sec))
                current_text = ""
        else:
            current_text += (' ' if current_text else '') + part_clean
        i += 1

    if current_text.strip():
        segments.append((current_text.strip(), 0.0))

    return segments


def synthesize_natural(
    text: str,
    session: ort.InferenceSession,
    config: dict,
    pause_duration: float = 0.28,
    length_scale: float = 1.08,
    noise_scale: float = 0.70,
    noise_w: float = 0.85,
    use_piper_phonemize: bool = True,
) -> np.ndarray:
    """
    Tổng hợp giọng nói với ngắt nghỉ tự nhiên (Natural Prosody):
    - Tách văn bản theo câu và pause tag
    - Inference từng câu riêng rẽ (giữ đúng ngữ điệu đầu/cuối câu)
    - Chèn khoảng lặng tự nhiên giữa các câu (mặc định 0.28s)
    - Mặc định length_scale=1.08 giúp đọc thong thả, rõ chữ
    - Mặc định noise_w=0.85 và noise_scale=0.70 tạo nhịp điệu sinh động, không đều cơ học
    """
    sr = config.get("audio", {}).get("sample_rate", 22050)
    segments = split_text_into_segments(text, default_pause=pause_duration)
    if not segments:
        return np.array([], dtype=np.float32)

    audio_parts: list[np.ndarray] = []
    for idx, (sentence, pause_sec) in enumerate(segments):
        if not sentence.strip():
            continue
        part_audio = synthesize(
            sentence,
            session,
            config,
            use_piper_phonemize=use_piper_phonemize,
            noise_scale=noise_scale,
            length_scale=length_scale,
            noise_w=noise_w,
        )
        audio_parts.append(part_audio)

        # Chèn khoảng lặng sau câu nếu không phải câu cuối
        if pause_sec > 0 and idx < len(segments) - 1:
            silence_samples = int(sr * pause_sec)
            if silence_samples > 0:
                audio_parts.append(np.zeros(silence_samples, dtype=np.float32))

    if not audio_parts:
        return np.array([], dtype=np.float32)

    return np.concatenate(audio_parts)


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
