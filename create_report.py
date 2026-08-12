"""
Script tạo báo cáo Word (.docx) cho dự án VITS TTS Tiếng Việt.
Chạy: python create_report.py
Output: output/BaoCao_VITS_TTS_TiengViet.docx
"""

import os, sys
from pathlib import Path

# Fix encoding cho Windows console
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

# ──────────────────────── Cấu hình ────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "BaoCao_VITS_TTS_TiengViet.docx"

FONT_NAME = "Times New Roman"
FONT_SIZE_BODY = 13          # 13pt cho nội dung
FONT_SIZE_H1 = 16            # Heading 1
FONT_SIZE_H2 = 14            # Heading 2
FONT_SIZE_H3 = 13            # Heading 3
LINE_SPACING = 1.5           # Giãn dòng 1.5


# ──────────────────────── Hàm tiện ích ────────────────────────

def set_cell_shading(cell, color_hex):
    """Đặt màu nền cho ô bảng."""
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_paragraph_format(paragraph, font_size=FONT_SIZE_BODY, bold=False,
                         italic=False, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                         space_after=Pt(6), space_before=Pt(0),
                         first_line_indent=Cm(1.27), font_color=None):
    """Định dạng đoạn văn."""
    pf = paragraph.paragraph_format
    pf.alignment = alignment
    pf.space_after = space_after
    pf.space_before = space_before
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = LINE_SPACING
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent

    for run in paragraph.runs:
        run.font.name = FONT_NAME
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.italic = italic
        run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
        if font_color:
            run.font.color.rgb = font_color


def add_paragraph(doc, text, font_size=FONT_SIZE_BODY, bold=False,
                  italic=False, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                  space_after=Pt(6), space_before=Pt(0),
                  first_line_indent=Cm(1.27), font_color=None):
    """Thêm đoạn văn với định dạng."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
    if font_color:
        run.font.color.rgb = font_color

    pf = p.paragraph_format
    pf.alignment = alignment
    pf.space_after = space_after
    pf.space_before = space_before
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = LINE_SPACING
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent
    return p


def add_heading_custom(doc, text, level=1):
    """Thêm heading với định dạng tùy chỉnh."""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = FONT_NAME
        run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
        if level == 1:
            run.font.size = Pt(FONT_SIZE_H1)
            run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x6E)
        elif level == 2:
            run.font.size = Pt(FONT_SIZE_H2)
            run.font.color.rgb = RGBColor(0x2C, 0x5A, 0x8A)
        elif level == 3:
            run.font.size = Pt(FONT_SIZE_H3)
            run.font.color.rgb = RGBColor(0x3A, 0x6E, 0x9E)
    h.paragraph_format.space_before = Pt(18)
    h.paragraph_format.space_after = Pt(8)
    return h


def add_bullet(doc, text, level=0, bold_prefix=None):
    """Thêm bullet point."""
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.font.name = FONT_NAME
        r_bold.font.size = Pt(FONT_SIZE_BODY)
        r_bold.font.bold = True
        r_bold._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
        r_normal = p.add_run(text)
        r_normal.font.name = FONT_NAME
        r_normal.font.size = Pt(FONT_SIZE_BODY)
        r_normal._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
    else:
        for run in p.runs:
            run.font.name = FONT_NAME
            run.font.size = Pt(FONT_SIZE_BODY)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
        if not p.runs:
            run = p.add_run(text)
            run.font.name = FONT_NAME
            run.font.size = Pt(FONT_SIZE_BODY)
            run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)

    pf = p.paragraph_format
    pf.space_after = Pt(3)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = LINE_SPACING
    if level > 0:
        pf.left_indent = Cm(1.27 * (level + 1))
    return p


def add_table_formatted(doc, headers, rows, col_widths=None, caption=None):
    """Thêm bảng có định dạng đẹp."""
    if caption:
        add_paragraph(doc, caption, font_size=FONT_SIZE_BODY, bold=True, italic=True,
                      alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                      space_before=Pt(10))

    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'

    # Header
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = header
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = FONT_NAME
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
        set_cell_shading(cell, "1A3C6E")

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = str(val)
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = FONT_NAME
                    run.font.size = Pt(12)
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)
            if r_idx % 2 == 1:
                set_cell_shading(cell, "EBF0F7")

    # Cỡ cột
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)

    return table


def add_page_break(doc):
    """Thêm ngắt trang."""
    doc.add_page_break()


# ──────────────────────── NỘI DUNG BÁO CÁO ────────────────────────

def create_cover_page(doc):
    """Trang bìa."""
    for _ in range(4):
        add_paragraph(doc, "", space_after=Pt(0), first_line_indent=None)

    add_paragraph(doc, "BỘ GIÁO DỤC VÀ ĐÀO TẠO", font_size=14, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None)
    add_paragraph(doc, "TRƯỜNG ĐẠI HỌC ...", font_size=14, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None)
    add_paragraph(doc, "KHOA CÔNG NGHỆ THÔNG TIN", font_size=14, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  space_after=Pt(6))

    add_paragraph(doc, "─" * 30, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  first_line_indent=None, font_color=RGBColor(0x1A, 0x3C, 0x6E))

    for _ in range(4):
        add_paragraph(doc, "", space_after=Pt(0), first_line_indent=None)

    add_paragraph(doc, "BÁO CÁO ĐỒ ÁN", font_size=20, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  font_color=RGBColor(0x1A, 0x3C, 0x6E))
    add_paragraph(doc, "", space_after=Pt(6), first_line_indent=None)
    add_paragraph(doc, "XÂY DỰNG HỆ THỐNG TỔNG HỢP GIỌNG NÓI\nTIẾNG VIỆT SỬ DỤNG MÔ HÌNH VITS", font_size=18, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  font_color=RGBColor(0xC0, 0x39, 0x2B))

    add_paragraph(doc, "(Variational Inference with Adversarial Learning\nfor End-to-End Text-to-Speech)",
                  font_size=14, italic=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  space_after=Pt(20))

    for _ in range(5):
        add_paragraph(doc, "", space_after=Pt(0), first_line_indent=None)

    info_lines = [
        "Giảng viên hướng dẫn:  ................................",
        "Sinh viên thực hiện:     ................................",
        "Mã số sinh viên:          ................................",
        "Lớp:                            ................................",
    ]
    for line in info_lines:
        add_paragraph(doc, line, font_size=14, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                      first_line_indent=Cm(3), space_after=Pt(8))

    for _ in range(4):
        add_paragraph(doc, "", space_after=Pt(0), first_line_indent=None)

    import datetime
    year = datetime.datetime.now().year
    add_paragraph(doc, f"TP. Hồ Chí Minh, {year}", font_size=14, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None)
    add_page_break(doc)


def create_toc_page(doc):
    """Trang mục lục."""
    add_paragraph(doc, "MỤC LỤC", font_size=16, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  font_color=RGBColor(0x1A, 0x3C, 0x6E), space_after=Pt(16))

    toc_items = [
        ("CHƯƠNG 1:", "MỞ ĐẦU"),
        ("   1.1", "Lý do chọn đề tài"),
        ("   1.2", "Mục tiêu của đồ án"),
        ("   1.3", "Đối tượng và phạm vi nghiên cứu"),
        ("   1.4", "Phương pháp nghiên cứu"),
        ("   1.5", "Cấu trúc báo cáo"),
        ("CHƯƠNG 2:", "TỔNG QUAN VỀ BÀI TOÁN TEXT-TO-SPEECH"),
        ("   2.1", "Giới thiệu bài toán Text-to-Speech"),
        ("   2.2", "Các phương pháp TTS truyền thống"),
        ("   2.3", "TTS dựa trên Deep Learning"),
        ("   2.4", "Tổng quan về Vocoder"),
        ("   2.5", "So sánh các phương pháp TTS"),
        ("CHƯƠNG 3:", "KIẾN TRÚC MÔ HÌNH VITS"),
        ("   3.1", "Giới thiệu mô hình VITS"),
        ("   3.2", "Text Encoder"),
        ("   3.3", "Posterior Encoder"),
        ("   3.4", "HiFi-GAN Decoder"),
        ("   3.5", "Stochastic Duration Predictor"),
        ("   3.6", "Normalizing Flow"),
        ("   3.7", "Hàm mất mát (Loss Functions)"),
        ("CHƯƠNG 4:", "DỮ LIỆU VÀ MÔI TRƯỜNG HUẤN LUYỆN"),
        ("   4.1", "Giới thiệu bộ dữ liệu VIVOS"),
        ("   4.2", "Tiền xử lý dữ liệu"),
        ("   4.3", "Grapheme-to-Phoneme cho tiếng Việt"),
        ("   4.4", "Framework Piper TTS"),
        ("   4.5", "Cấu hình môi trường huấn luyện"),
        ("CHƯƠNG 5:", "THỰC NGHIỆM VÀ ĐÁNH GIÁ"),
        ("   5.1", "Cấu hình huấn luyện"),
        ("   5.2", "Quá trình huấn luyện"),
        ("   5.3", "Xuất mô hình ONNX"),
        ("   5.4", "Kết quả Inference"),
        ("   5.5", "Xây dựng ứng dụng Web Demo"),
        ("   5.6", "Đánh giá và nhận xét"),
        ("CHƯƠNG 6:", "KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN"),
        ("   6.1", "Kết quả đạt được"),
        ("   6.2", "Hạn chế"),
        ("   6.3", "Hướng phát triển"),
        ("", "TÀI LIỆU THAM KHẢO"),
    ]

    for num, title in toc_items:
        is_chapter = num.startswith("CHƯƠNG") or num == ""
        p = doc.add_paragraph()
        if num:
            r1 = p.add_run(f"{num} ")
            r1.font.name = FONT_NAME
            r1.font.size = Pt(13 if is_chapter else 12)
            r1.font.bold = is_chapter
            r1._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)

        r2 = p.add_run(title)
        r2.font.name = FONT_NAME
        r2.font.size = Pt(13 if is_chapter else 12)
        r2.font.bold = is_chapter
        r2._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)

        pf = p.paragraph_format
        pf.space_after = Pt(2 if not is_chapter else 6)
        pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        pf.line_spacing = 1.3
        if not is_chapter and num:
            pf.left_indent = Cm(1)

    add_page_break(doc)


def create_abbreviations_page(doc):
    """Trang danh mục viết tắt."""
    add_paragraph(doc, "DANH MỤC CÁC TỪ VIẾT TẮT", font_size=16, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  font_color=RGBColor(0x1A, 0x3C, 0x6E), space_after=Pt(16))

    abbrs = [
        ("TTS", "Text-to-Speech – Chuyển văn bản thành giọng nói"),
        ("VITS", "Variational Inference with adversarial learning for end-to-end Text-to-Speech"),
        ("VAE", "Variational Autoencoder – Bộ mã hóa biến phân"),
        ("GAN", "Generative Adversarial Network – Mạng sinh đối kháng"),
        ("ONNX", "Open Neural Network Exchange – Định dạng trao đổi mô hình mạng neural"),
        ("IPA", "International Phonetic Alphabet – Bảng ký hiệu ngữ âm quốc tế"),
        ("RTF", "Real-Time Factor – Hệ số thời gian thực"),
        ("MOS", "Mean Opinion Score – Điểm đánh giá trung bình chủ quan"),
        ("API", "Application Programming Interface – Giao diện lập trình ứng dụng"),
        ("GPU", "Graphics Processing Unit – Bộ xử lý đồ họa"),
        ("CPU", "Central Processing Unit – Bộ xử lý trung tâm"),
        ("FP16", "Float Point 16-bit – Số thực dấu phẩy động 16 bit"),
        ("KL", "Kullback-Leibler (divergence) – Phân kỳ Kullback-Leibler"),
        ("NF", "Normalizing Flow – Luồng chuẩn hóa"),
        ("SDP", "Stochastic Duration Predictor – Bộ dự đoán thời lượng ngẫu nhiên"),
    ]

    add_table_formatted(doc,
        ["Viết tắt", "Ý nghĩa"],
        abbrs,
        col_widths=[3, 14]
    )
    add_page_break(doc)


def create_figures_tables_page(doc):
    """Trang danh mục bảng biểu và hình vẽ."""
    add_paragraph(doc, "DANH MỤC BẢNG BIỂU", font_size=16, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  font_color=RGBColor(0x1A, 0x3C, 0x6E), space_after=Pt(12))

    tables_list = [
        "Bảng 2.1: So sánh các phương pháp TTS",
        "Bảng 4.1: Thông số bộ dữ liệu VIVOS SPK01",
        "Bảng 4.2: Cấu hình tiền xử lý dữ liệu âm thanh",
        "Bảng 5.1: Cấu hình siêu tham số huấn luyện",
        "Bảng 5.2: Cấu hình kiến trúc mô hình VITS",
        "Bảng 5.3: Kết quả inference trên các câu test ngắn",
        "Bảng 5.4: Kết quả inference trên đoạn văn bản dài",
        "Bảng 5.5: Yêu cầu hệ thống",
    ]
    for item in tables_list:
        add_paragraph(doc, item, font_size=12, first_line_indent=Cm(1), space_after=Pt(3))

    add_paragraph(doc, "", space_after=Pt(16), first_line_indent=None)

    add_paragraph(doc, "DANH MỤC HÌNH VẼ", font_size=16, bold=True,
                  alignment=WD_ALIGN_PARAGRAPH.CENTER, first_line_indent=None,
                  font_color=RGBColor(0x1A, 0x3C, 0x6E), space_after=Pt(12))

    figures_list = [
        "Hình 2.1: Sơ đồ tổng quát hệ thống TTS",
        "Hình 2.2: Kiến trúc Tacotron 2",
        "Hình 3.1: Kiến trúc tổng quan mô hình VITS",
        "Hình 3.2: Cấu trúc Text Encoder (Transformer)",
        "Hình 3.3: Cấu trúc HiFi-GAN Decoder",
        "Hình 3.4: Sơ đồ Normalizing Flow",
        "Hình 4.1: Pipeline xử lý dữ liệu",
        "Hình 5.1: Giao diện Web Demo TTS",
        "Hình 5.2: Pipeline inference VITS",
    ]
    for item in figures_list:
        add_paragraph(doc, item, font_size=12, first_line_indent=Cm(1), space_after=Pt(3))

    add_page_break(doc)


# ═══════════════════ CHƯƠNG 1 ═══════════════════

def create_chapter_1(doc):
    """Chương 1: Mở đầu."""
    add_heading_custom(doc, "CHƯƠNG 1: MỞ ĐẦU", level=1)

    # 1.1
    add_heading_custom(doc, "1.1. Lý do chọn đề tài", level=2)
    add_paragraph(doc, (
        "Trong thời đại công nghệ số hiện nay, trí tuệ nhân tạo (AI) đang ngày càng "
        "đóng vai trò quan trọng trong nhiều lĩnh vực của đời sống xã hội. Một trong những "
        "ứng dụng nổi bật của AI là tổng hợp giọng nói (Text-to-Speech – TTS), cho phép "
        "chuyển đổi văn bản thành giọng nói tự nhiên. Công nghệ TTS đã và đang được ứng "
        "dụng rộng rãi trong các trợ lý ảo (Siri, Google Assistant, Alexa), hệ thống đọc "
        "sách điện tử, hỗ trợ người khiếm thị, dịch thuật tự động, và nhiều ứng dụng khác."
    ))
    add_paragraph(doc, (
        "Đối với tiếng Việt – một ngôn ngữ thanh điệu phức tạp với 6 thanh điệu (sắc, "
        "huyền, hỏi, ngã, nặng, ngang), việc xây dựng hệ thống TTS chất lượng cao là một "
        "thách thức lớn. Các hệ thống TTS truyền thống thường cho chất lượng giọng nói không "
        "tự nhiên, thiếu biểu cảm và khó triển khai trên nhiều nền tảng khác nhau. Sự ra đời "
        "của các mô hình Deep Learning, đặc biệt là VITS (Variational Inference with Adversarial "
        "Learning for End-to-End Text-to-Speech), đã mở ra hướng tiếp cận mới trong lĩnh vực "
        "tổng hợp giọng nói với chất lượng vượt trội."
    ))
    add_paragraph(doc, (
        "VITS là mô hình tổng hợp giọng nói end-to-end, kết hợp nhiều kỹ thuật tiên tiến "
        "bao gồm Variational Autoencoder (VAE), Normalizing Flow và Generative Adversarial "
        "Network (GAN). Điểm nổi bật của VITS so với các mô hình trước đó (như Tacotron 2, "
        "FastSpeech 2) là khả năng tạo ra giọng nói trực tiếp từ văn bản mà không cần qua "
        "bước trung gian (mel-spectrogram → vocoder riêng biệt), từ đó giảm thiểu sai số "
        "tích lũy và nâng cao chất lượng âm thanh đầu ra."
    ))
    add_paragraph(doc, (
        "Xuất phát từ nhu cầu thực tế và mong muốn nghiên cứu, ứng dụng các kỹ thuật "
        "Deep Learning hiện đại vào xử lý ngôn ngữ tự nhiên tiếng Việt, đề tài \"Xây dựng "
        "hệ thống tổng hợp giọng nói tiếng Việt sử dụng mô hình VITS\" đã được lựa chọn."
    ))

    # 1.2
    add_heading_custom(doc, "1.2. Mục tiêu của đồ án", level=2)
    add_paragraph(doc, "Đồ án được thực hiện nhằm đạt được các mục tiêu chính sau đây:")
    add_bullet(doc, "Nghiên cứu và tìm hiểu kiến trúc mô hình VITS cùng các thành phần cốt lõi: Text Encoder, Posterior Encoder, HiFi-GAN Decoder, Normalizing Flow, Stochastic Duration Predictor.")
    add_bullet(doc, "Huấn luyện mô hình VITS trên bộ dữ liệu tiếng Việt VIVOS, sử dụng framework Piper TTS.")
    add_bullet(doc, "Xuất mô hình đã huấn luyện sang định dạng ONNX để tối ưu tốc độ inference và khả năng triển khai đa nền tảng.")
    add_bullet(doc, "Xây dựng ứng dụng Web Demo cho phép người dùng nhập văn bản tiếng Việt và nghe kết quả tổng hợp giọng nói trực tiếp trên trình duyệt.")
    add_bullet(doc, "Đánh giá chất lượng giọng nói tổng hợp thông qua các chỉ số định lượng (Real-Time Factor) và đánh giá chủ quan.")

    # 1.3
    add_heading_custom(doc, "1.3. Đối tượng và phạm vi nghiên cứu", level=2)

    add_paragraph(doc, "Đối tượng nghiên cứu:", bold=True, first_line_indent=None)
    add_bullet(doc, "Mô hình VITS (Kim et al., ICML 2021) và các biến thể.")
    add_bullet(doc, "Bộ dữ liệu VIVOS (AILab – ĐH Khoa học Tự nhiên TP.HCM).")
    add_bullet(doc, "Framework Piper TTS và ONNX Runtime.")

    add_paragraph(doc, "Phạm vi nghiên cứu:", bold=True, first_line_indent=None,
                  space_before=Pt(6))
    add_bullet(doc, "Tập trung vào single-speaker TTS (giọng đơn) cho tiếng Việt.")
    add_bullet(doc, "Sử dụng bộ dữ liệu VIVOS với speaker VIVOSSPK01 (khoảng 250 câu, ~10 phút audio).")
    add_bullet(doc, "Huấn luyện trên framework Piper TTS (dựa trên PyTorch Lightning).")
    add_bullet(doc, "Triển khai inference bằng ONNX Runtime trên CPU.")

    # 1.4
    add_heading_custom(doc, "1.4. Phương pháp nghiên cứu", level=2)
    add_paragraph(doc, (
        "Đồ án sử dụng kết hợp các phương pháp nghiên cứu sau:"
    ))
    add_bullet(doc, "Nghiên cứu lý thuyết: ", bold_prefix="Nghiên cứu lý thuyết: ")
    add_paragraph(doc, (
        "Tìm hiểu các bài báo khoa học liên quan đến VITS, VAE, Normalizing Flow, GAN "
        "và các mô hình TTS hiện đại. Nghiên cứu tài liệu kỹ thuật của framework Piper TTS, "
        "espeak-ng phonemizer và ONNX Runtime."
    ), first_line_indent=Cm(2))
    add_bullet(doc, "Thực nghiệm: ", bold_prefix="Thực nghiệm: ")
    add_paragraph(doc, (
        "Thu thập và tiền xử lý dữ liệu tiếng Việt từ bộ VIVOS. Huấn luyện mô hình VITS "
        "sử dụng Piper TTS. Thử nghiệm các siêu tham số khác nhau. Xuất mô hình sang ONNX "
        "và đánh giá hiệu năng inference."
    ), first_line_indent=Cm(2))
    add_bullet(doc, "Đánh giá: ", bold_prefix="Đánh giá: ")
    add_paragraph(doc, (
        "Đánh giá chất lượng giọng nói tổng hợp thông qua chỉ số Real-Time Factor (RTF), "
        "thời gian inference, và đánh giá chủ quan bằng cách nghe thực tế."
    ), first_line_indent=Cm(2))

    # 1.5
    add_heading_custom(doc, "1.5. Cấu trúc báo cáo", level=2)
    add_paragraph(doc, "Báo cáo được tổ chức thành 6 chương với nội dung như sau:")
    add_bullet(doc, "Giới thiệu tổng quan đề tài, lý do, mục tiêu, phạm vi và phương pháp nghiên cứu.", bold_prefix="Chương 1 – Mở đầu: ")
    add_bullet(doc, "Trình bày nền tảng lý thuyết về bài toán TTS, các phương pháp TTS từ truyền thống đến Deep Learning.", bold_prefix="Chương 2 – Tổng quan TTS: ")
    add_bullet(doc, "Phân tích chi tiết kiến trúc mô hình VITS và các thành phần cốt lõi.", bold_prefix="Chương 3 – Kiến trúc VITS: ")
    add_bullet(doc, "Giới thiệu bộ dữ liệu, quy trình tiền xử lý và cấu hình môi trường huấn luyện.", bold_prefix="Chương 4 – Dữ liệu và Huấn luyện: ")
    add_bullet(doc, "Trình bày kết quả thực nghiệm, ứng dụng Web Demo và đánh giá.", bold_prefix="Chương 5 – Thực nghiệm: ")
    add_bullet(doc, "Tổng kết kết quả đạt được, hạn chế và đề xuất hướng phát triển.", bold_prefix="Chương 6 – Kết luận: ")

    add_page_break(doc)


# ═══════════════════ CHƯƠNG 2 ═══════════════════

def create_chapter_2(doc):
    """Chương 2: Tổng quan về bài toán Text-to-Speech."""
    add_heading_custom(doc, "CHƯƠNG 2: TỔNG QUAN VỀ BÀI TOÁN TEXT-TO-SPEECH", level=1)

    # 2.1
    add_heading_custom(doc, "2.1. Giới thiệu bài toán Text-to-Speech (TTS)", level=2)
    add_paragraph(doc, (
        "Text-to-Speech (TTS) là bài toán chuyển đổi văn bản (text) đầu vào thành tín "
        "hiệu âm thanh giọng nói (speech) tương ứng. Một hệ thống TTS lý tưởng cần đáp "
        "ứng các yêu cầu sau: (1) Giọng nói đầu ra phải tự nhiên, rõ ràng và dễ nghe; "
        "(2) Phát âm chính xác các từ, đặc biệt là thanh điệu đối với ngôn ngữ có thanh "
        "điệu như tiếng Việt; (3) Tốc độ xử lý đủ nhanh để ứng dụng thời gian thực; "
        "(4) Có khả năng biểu cảm và linh hoạt trong ngữ điệu."
    ))
    add_paragraph(doc, (
        "Về mặt tổng quát, một hệ thống TTS thường bao gồm hai giai đoạn chính: "
        "(1) Phân tích ngôn ngữ (Linguistic Analysis / Front-end): chuyển đổi văn bản thô "
        "thành biểu diễn ngôn ngữ trung gian, bao gồm chuẩn hóa text, tách từ, chuyển đổi "
        "grapheme-to-phoneme (G2P), dự đoán prosody (nhịp điệu, thanh điệu); (2) Tổng hợp "
        "âm thanh (Acoustic Synthesis / Back-end): chuyển đổi biểu diễn ngôn ngữ thành tín "
        "hiệu sóng âm thanh (waveform)."
    ))
    add_paragraph(doc, (
        "Đối với tiếng Việt, bài toán TTS có thêm các thách thức đặc trưng: hệ thống 6 "
        "thanh điệu phức tạp (ngang, sắc, huyền, hỏi, ngã, nặng), các quy tắc đồng hóa "
        "âm và biến đổi thanh điệu trong ngữ cảnh, cùng với sự đa dạng phương ngữ giữa "
        "các vùng miền (Bắc, Trung, Nam)."
    ))

    # 2.2
    add_heading_custom(doc, "2.2. Các phương pháp TTS truyền thống", level=2)

    add_heading_custom(doc, "2.2.1. TTS dựa trên nối ghép (Concatenative TTS)", level=3)
    add_paragraph(doc, (
        "Phương pháp nối ghép (Concatenative Synthesis) hoạt động bằng cách ghép nối các đoạn "
        "âm thanh đã được thu sẵn (gọi là speech units) để tạo thành câu nói hoàn chỉnh. Các "
        "đơn vị âm thanh có thể là diphone (cặp nửa âm vị), triphone, hoặc các đoạn dài hơn. "
        "Hệ thống sử dụng một cơ sở dữ liệu lớn chứa các đơn vị này, sau đó lựa chọn và ghép "
        "nối các đơn vị phù hợp nhất cho câu đầu vào."
    ))
    add_paragraph(doc, (
        "Ưu điểm chính của phương pháp này là chất lượng âm thanh tự nhiên (vì sử dụng giọng "
        "thật). Tuy nhiên, nhược điểm bao gồm: cần cơ sở dữ liệu rất lớn (hàng chục giờ audio), "
        "các mối nối giữa các đơn vị thường không mượt mà, khó linh hoạt thay đổi giọng nói "
        "hay phong cách nói, và chi phí lưu trữ cao."
    ))

    add_heading_custom(doc, "2.2.2. TTS dựa trên tham số (Parametric TTS)", level=3)
    add_paragraph(doc, (
        "Phương pháp tham số (Parametric Synthesis) sử dụng mô hình thống kê (thường là Hidden "
        "Markov Model – HMM) để dự đoán các tham số âm thanh (pitch, duration, spectral envelope) "
        "từ biểu diễn ngôn ngữ, sau đó dùng vocoder để tổng hợp waveform từ các tham số này."
    ))
    add_paragraph(doc, (
        "So với concatenative TTS, phương pháp tham số có ưu điểm: kích thước model nhỏ gọn, dễ "
        "điều chỉnh giọng nói và phong cách, có thể hoạt động với ít dữ liệu hơn. Nhược điểm "
        "là chất lượng âm thanh kém tự nhiên hơn, giọng nói nghe \"máy\" do sự đơn giản hóa "
        "trong mô hình hóa tín hiệu âm thanh."
    ))

    # 2.3
    add_heading_custom(doc, "2.3. TTS dựa trên Deep Learning", level=2)

    add_heading_custom(doc, "2.3.1. Tacotron và Tacotron 2", level=3)
    add_paragraph(doc, (
        "Tacotron (Wang et al., 2017) là một trong những mô hình đầu tiên áp dụng thành công "
        "Deep Learning vào bài toán TTS. Tacotron sử dụng kiến trúc sequence-to-sequence (Seq2Seq) "
        "với cơ chế Attention để chuyển đổi trực tiếp chuỗi ký tự đầu vào thành mel-spectrogram. "
        "Phiên bản cải tiến Tacotron 2 (Shen et al., 2018) thay thế CBHG encoder bằng Bi-LSTM "
        "và sử dụng Location-Sensitive Attention, kết hợp với WaveNet vocoder để tạo ra giọng "
        "nói chất lượng gần như giọng thật."
    ))
    add_paragraph(doc, (
        "Tuy nhiên, Tacotron 2 có nhược điểm: tốc độ inference chậm (do autoregressive decoding), "
        "dễ bị lỗi alignment (bỏ từ, lặp từ), và cần một vocoder riêng biệt (hai-stage pipeline)."
    ))

    add_heading_custom(doc, "2.3.2. FastSpeech và FastSpeech 2", level=3)
    add_paragraph(doc, (
        "FastSpeech (Ren et al., 2019) giải quyết vấn đề tốc độ bằng cách sử dụng kiến trúc "
        "non-autoregressive: tất cả các frame mel-spectrogram được sinh ra đồng thời (parallel). "
        "FastSpeech sử dụng một Duration Predictor để dự đoán thời lượng phát âm của từng "
        "phoneme, từ đó loại bỏ cơ chế Attention dễ lỗi của Tacotron."
    ))
    add_paragraph(doc, (
        "FastSpeech 2 (Ren et al., 2020) cải tiến thêm bằng cách bổ sung Pitch Predictor và "
        "Energy Predictor, cho phép kiểm soát tốt hơn ngữ điệu và cường độ. Tuy nhiên, cả hai "
        "phiên bản vẫn cần vocoder riêng (như HiFi-GAN, WaveGlow) để chuyển mel-spectrogram "
        "thành waveform, tạo ra pipeline hai giai đoạn."
    ))

    # 2.4
    add_heading_custom(doc, "2.4. Tổng quan về Vocoder", level=2)
    add_paragraph(doc, (
        "Vocoder là thành phần chịu trách nhiệm chuyển đổi mel-spectrogram (hoặc biểu diễn "
        "trung gian tương tự) thành tín hiệu sóng âm thanh (waveform) cuối cùng. Chất lượng "
        "của vocoder ảnh hưởng trực tiếp đến chất lượng giọng nói đầu ra."
    ))

    add_heading_custom(doc, "2.4.1. Griffin-Lim", level=3)
    add_paragraph(doc, (
        "Griffin-Lim là thuật toán khôi phục phase từ magnitude spectrogram bằng phương pháp "
        "lặp. Ưu điểm là đơn giản và nhanh, nhược điểm là chất lượng âm thanh thấp, giọng "
        "nghe rất máy móc."
    ))

    add_heading_custom(doc, "2.4.2. WaveNet", level=3)
    add_paragraph(doc, (
        "WaveNet (van den Oord et al., 2016) là mô hình autoregressive sinh từng sample âm "
        "thanh một. WaveNet cho chất lượng rất cao nhưng tốc độ inference cực chậm (không "
        "real-time trên CPU)."
    ))

    add_heading_custom(doc, "2.4.3. HiFi-GAN", level=3)
    add_paragraph(doc, (
        "HiFi-GAN (Kong et al., 2020) là vocoder dựa trên GAN, sử dụng multi-scale và "
        "multi-period discriminator. HiFi-GAN đạt chất lượng tương đương WaveNet nhưng "
        "inference nhanh hơn hàng trăm lần, cho phép tổng hợp giọng nói real-time trên GPU "
        "và gần real-time trên CPU. Đây là vocoder được tích hợp trực tiếp trong VITS."
    ))

    # 2.5
    add_heading_custom(doc, "2.5. So sánh các phương pháp TTS", level=2)
    add_paragraph(doc, (
        "Bảng 2.1 dưới đây tổng hợp so sánh các phương pháp TTS đã đề cập, từ truyền "
        "thống đến hiện đại, theo các tiêu chí quan trọng."
    ))

    add_table_formatted(doc,
        ["Phương pháp", "Chất lượng", "Tốc độ", "End-to-end", "Vocoder riêng"],
        [
            ["Concatenative", "Khá", "Nhanh", "Không", "Không"],
            ["Parametric (HMM)", "Thấp", "Nhanh", "Không", "Có"],
            ["Tacotron 2", "Cao", "Chậm", "Không", "Có (WaveNet)"],
            ["FastSpeech 2", "Cao", "Nhanh", "Không", "Có (HiFi-GAN)"],
            ["VITS", "Rất cao", "Nhanh", "Có", "Không (tích hợp)"],
        ],
        caption="Bảng 2.1: So sánh các phương pháp TTS"
    )

    add_paragraph(doc, (
        "Qua bảng so sánh có thể thấy, VITS là phương pháp duy nhất đạt được kiến trúc "
        "end-to-end thực sự (text → waveform) mà không cần vocoder riêng biệt, đồng thời "
        "vẫn đảm bảo chất lượng giọng nói rất cao và tốc độ inference nhanh. Đây là lý do "
        "chính khiến VITS được lựa chọn cho đồ án này."
    ))

    add_page_break(doc)


# ═══════════════════ CHƯƠNG 3 ═══════════════════

def create_chapter_3(doc):
    """Chương 3: Kiến trúc mô hình VITS."""
    add_heading_custom(doc, "CHƯƠNG 3: KIẾN TRÚC MÔ HÌNH VITS", level=1)

    # 3.1
    add_heading_custom(doc, "3.1. Giới thiệu mô hình VITS", level=2)
    add_paragraph(doc, (
        "VITS (Variational Inference with Adversarial Learning for End-to-End Text-to-Speech) "
        "là mô hình tổng hợp giọng nói end-to-end được giới thiệu bởi Kim et al. tại hội "
        "nghị ICML 2021. VITS kết hợp ba kỹ thuật chính: Conditional Variational Autoencoder "
        "(CVAE), Normalizing Flow và Adversarial Training (GAN), tạo nên một hệ thống thống "
        "nhất có khả năng tổng hợp giọng nói trực tiếp từ văn bản đầu vào."
    ))
    add_paragraph(doc, (
        "Điểm đột phá của VITS so với các mô hình hai giai đoạn (two-stage) trước đó là: "
        "(1) Loại bỏ hoàn toàn sự phụ thuộc vào mel-spectrogram như biểu diễn trung gian, "
        "thay vào đó sử dụng latent representation z được học trực tiếp; (2) Tích hợp "
        "HiFi-GAN decoder làm thành phần nội tại của mô hình thay vì là vocoder riêng biệt; "
        "(3) Sử dụng Stochastic Duration Predictor cho phép tạo ra biến thể ngữ điệu tự "
        "nhiên hơn so với deterministic duration predictor."
    ))
    add_paragraph(doc, (
        "Tổng quan, mô hình VITS bao gồm các thành phần chính sau: Text Encoder (mã hóa "
        "văn bản), Posterior Encoder (mã hóa phân phối hậu nghiệm), Normalizing Flow "
        "(chuyển đổi phân phối), HiFi-GAN Decoder (giải mã sóng âm), và Stochastic Duration "
        "Predictor (dự đoán thời lượng phát âm). Trong quá trình huấn luyện, mô hình sử "
        "dụng cả audio thật (ground truth) để tính loss. Trong quá trình inference, chỉ "
        "cần text đầu vào, VITS sẽ sinh ra waveform trực tiếp."
    ))

    # 3.2
    add_heading_custom(doc, "3.2. Text Encoder", level=2)
    add_paragraph(doc, (
        "Text Encoder có nhiệm vụ chuyển đổi chuỗi phoneme IDs đầu vào thành biểu diễn "
        "ngữ nghĩa ẩn (hidden representation). Trong VITS, Text Encoder sử dụng kiến trúc "
        "Transformer Encoder với các thông số cấu hình như sau:"
    ))

    add_table_formatted(doc,
        ["Tham số", "Giá trị", "Mô tả"],
        [
            ["n_layers", "6", "Số lớp Transformer"],
            ["n_heads", "2", "Số attention heads"],
            ["hidden_channels", "192", "Số kênh ẩn"],
            ["filter_channels", "768", "Số kênh trong Feed-Forward Network"],
            ["kernel_size", "3", "Kích thước kernel trong Conv1d"],
            ["p_dropout", "0.1", "Tỷ lệ dropout"],
        ],
        caption="Bảng 3.1: Cấu hình Text Encoder"
    )

    add_paragraph(doc, (
        "Đầu vào của Text Encoder là chuỗi phoneme IDs được tạo ra bởi module G2P (Grapheme-to-"
        "Phoneme). Chuỗi này đầu tiên được chuyển qua lớp Embedding để tạo vector biểu diễn "
        "cho mỗi phoneme, sau đó đi qua 6 lớp Transformer. Mỗi lớp Transformer bao gồm: "
        "Multi-Head Self-Attention (2 heads) cho phép mô hình học mối quan hệ giữa các phoneme "
        "trong câu, và Feed-Forward Network (FFN) với 768 kênh bao gồm hai lớp Conv1d và hàm "
        "kích hoạt ReLU."
    ))
    add_paragraph(doc, (
        "Đầu ra của Text Encoder là phân phối prior p(z|c) – phân phối tiên nghiệm có điều kiện "
        "theo text. Cụ thể, Text Encoder dự đoán mean (μ) và variance (σ²) của phân phối Gaussian "
        "cho mỗi vị trí phoneme, được sử dụng trong quá trình tính KL divergence loss."
    ))

    # 3.3
    add_heading_custom(doc, "3.3. Posterior Encoder", level=2)
    add_paragraph(doc, (
        "Posterior Encoder chỉ được sử dụng trong quá trình huấn luyện (training time). Nhiệm "
        "vụ của nó là mã hóa mel-spectrogram (hoặc linear spectrogram) của audio thật thành "
        "phân phối hậu nghiệm q(z|x) trong không gian latent."
    ))
    add_paragraph(doc, (
        "Posterior Encoder sử dụng kiến trúc WaveNet-style với n_layers_q = 3 lớp dilated "
        "convolution. Kênh ẩn (inter_channels) có kích thước 192, giống với Text Encoder. "
        "Đầu ra cũng là mean và variance của phân phối Gaussian, từ đó sample latent variable z "
        "bằng kỹ thuật reparameterization trick."
    ))
    add_paragraph(doc, (
        "Trong quá trình inference, Posterior Encoder không được sử dụng. Thay vào đó, z được "
        "sample từ phân phối prior p(z|c) của Text Encoder (sau khi đi qua Normalizing Flow). "
        "Mục tiêu huấn luyện là làm cho p(z|c) càng gần q(z|x) càng tốt, thông qua KL "
        "divergence loss."
    ))

    # 3.4
    add_heading_custom(doc, "3.4. HiFi-GAN Decoder", level=2)
    add_paragraph(doc, (
        "HiFi-GAN Decoder là thành phần chuyển đổi latent representation z thành tín hiệu "
        "sóng âm thanh (waveform) cuối cùng. Đây chính là vocoder được tích hợp trực tiếp "
        "trong VITS, loại bỏ nhu cầu vocoder riêng biệt."
    ))
    add_paragraph(doc, "Cấu hình HiFi-GAN Decoder trong dự án:")

    add_table_formatted(doc,
        ["Tham số", "Giá trị", "Mô tả"],
        [
            ["upsample_rates", "[8, 8, 2, 2]", "Tỷ lệ upsampling (tổng: 256 = hop_length)"],
            ["upsample_initial_channel", "512", "Số kênh đầu vào upsampling"],
            ["upsample_kernel_sizes", "[16, 16, 4, 4]", "Kích thước kernel upsampling"],
            ["resblock_kernel_sizes", "[3, 7, 11]", "Kích thước kernel ResBlock"],
            ["resblock_dilation_sizes", "[[1,3,5]×3]", "Hệ số dilation trong ResBlock"],
        ],
        caption="Bảng 3.2: Cấu hình HiFi-GAN Decoder"
    )

    add_paragraph(doc, (
        "HiFi-GAN Decoder bao gồm chuỗi các lớp Transposed Convolution (để upsample) xen kẽ "
        "với Multi-Receptive Field Fusion (MRF) blocks. Mỗi MRF block chứa nhiều ResBlock với "
        "kernel sizes khác nhau (3, 7, 11) và dilation rates khác nhau (1, 3, 5), cho phép mô "
        "hình capture được cả thông tin cục bộ và toàn cục của tín hiệu âm thanh."
    ))
    add_paragraph(doc, (
        "Tỷ lệ upsampling tổng cộng là 8 × 8 × 2 × 2 = 256, tương ứng với hop_length = 256 "
        "trong quá trình trích xuất spectrogram. Điều này đảm bảo rằng mỗi frame trong latent "
        "representation được mở rộng thành đúng 256 audio samples."
    ))

    # 3.5
    add_heading_custom(doc, "3.5. Stochastic Duration Predictor", level=2)
    add_paragraph(doc, (
        "Stochastic Duration Predictor (SDP) dự đoán thời lượng phát âm (duration) cho mỗi "
        "phoneme đầu vào. Khác với deterministic duration predictor (như trong FastSpeech), "
        "SDP sử dụng mô hình flow-based để sinh duration từ một phân phối, cho phép tạo ra "
        "biến thể ngữ điệu tự nhiên hơn ở mỗi lần inference."
    ))
    add_paragraph(doc, "Các tham số inference của SDP:")
    add_bullet(doc, "noise_scale = 0.667: Kiểm soát mức độ biến thiên của giọng nói. Giá trị cao hơn tạo giọng biểu cảm hơn nhưng có thể kém ổn định.")
    add_bullet(doc, "noise_w = 0.8: Kiểm soát biến thiên của duration. Giá trị cao hơn tạo nhịp nói đa dạng hơn.")
    add_bullet(doc, "length_scale = 1.0: Kiểm soát tốc độ nói. Giá trị > 1 nói chậm hơn, < 1 nói nhanh hơn.")

    # 3.6
    add_heading_custom(doc, "3.6. Normalizing Flow", level=2)
    add_paragraph(doc, (
        "Normalizing Flow là kỹ thuật cho phép chuyển đổi một phân phối đơn giản (ví dụ: "
        "Gaussian) thành phân phối phức tạp hơn thông qua chuỗi các biến đổi khả nghịch "
        "(invertible transformations). Trong VITS, Normalizing Flow đóng vai trò cầu nối "
        "giữa phân phối prior p(z|c) và phân phối posterior q(z|x)."
    ))
    add_paragraph(doc, (
        "Cụ thể, trong quá trình huấn luyện, latent variable z được sample từ posterior "
        "q(z|x), sau đó đi qua Normalizing Flow theo chiều thuận (forward) để chuyển sang "
        "không gian latent của prior. Trong quá trình inference, z được sample từ prior "
        "p(z|c) và đi qua Normalizing Flow theo chiều nghịch (inverse) để chuyển về không "
        "gian latent mà HiFi-GAN Decoder có thể giải mã."
    ))
    add_paragraph(doc, (
        "Normalizing Flow trong VITS sử dụng affine coupling layers kết hợp với WaveNet-style "
        "residual blocks. Nhờ tính chất khả nghịch, Flow cho phép tính chính xác log-likelihood, "
        "từ đó cải thiện chất lượng huấn luyện thông qua maximum likelihood estimation."
    ))

    # 3.7
    add_heading_custom(doc, "3.7. Hàm mất mát (Loss Functions)", level=2)
    add_paragraph(doc, (
        "Quá trình huấn luyện VITS sử dụng tổng hợp nhiều hàm mất mát, bao gồm:"
    ))

    add_paragraph(doc, "a) Reconstruction Loss (Mel-spectrogram Loss):", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Đo lường sự khác biệt giữa mel-spectrogram của audio tổng hợp và audio thật. "
        "Hệ số c_mel = 45, cho thấy reconstruction loss được đánh trọng số rất cao trong "
        "tổng loss, nhấn mạnh tầm quan trọng của việc tái tạo chính xác đặc trưng âm thanh."
    ))

    add_paragraph(doc, "b) KL Divergence Loss:", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Đo lường khoảng cách giữa phân phối posterior q(z|x) và prior p(z|c). Hệ số "
        "c_kl = 1.0. KL loss đảm bảo rằng phân phối prior (từ text encoder) học được cách "
        "xấp xỉ tốt phân phối posterior (từ audio thật), cho phép inference chỉ từ text."
    ))

    add_paragraph(doc, "c) Adversarial Loss (GAN Loss):", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "VITS sử dụng multi-period discriminator (MPD) tương tự HiFi-GAN để phân biệt "
        "audio thật và audio tổng hợp. Generator (decoder) được huấn luyện để \"lừa\" "
        "discriminator, trong khi discriminator được huấn luyện để phân biệt tốt hơn. "
        "Quá trình adversarial training này giúp cải thiện đáng kể chất lượng audio đầu ra."
    ))

    add_paragraph(doc, "d) Feature Matching Loss:", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Tính khoảng cách L1 giữa feature maps trung gian của discriminator khi nhận "
        "audio thật và audio tổng hợp. Loss này giúp ổn định quá trình huấn luyện GAN "
        "và cải thiện chất lượng chi tiết của giọng nói."
    ))

    add_paragraph(doc, "e) Duration Loss:", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Huấn luyện Stochastic Duration Predictor để dự đoán chính xác thời lượng phát "
        "âm của mỗi phoneme, sử dụng duration ground truth được trích xuất từ Monotonic "
        "Alignment Search (MAS) trong quá trình huấn luyện."
    ))

    add_page_break(doc)


# ═══════════════════ CHƯƠNG 4 ═══════════════════

def create_chapter_4(doc):
    """Chương 4: Dữ liệu và Môi trường huấn luyện."""
    add_heading_custom(doc, "CHƯƠNG 4: DỮ LIỆU VÀ MÔI TRƯỜNG HUẤN LUYỆN", level=1)

    # 4.1
    add_heading_custom(doc, "4.1. Giới thiệu bộ dữ liệu VIVOS", level=2)
    add_paragraph(doc, (
        "VIVOS là bộ dữ liệu tiếng nói tiếng Việt được phát triển bởi AILab, Trường Đại học "
        "Khoa học Tự nhiên, Đại học Quốc gia TP. Hồ Chí Minh (HCMUS). Bộ dữ liệu này được "
        "thiết kế ban đầu cho bài toán nhận dạng giọng nói (Automatic Speech Recognition – ASR) "
        "và bao gồm nhiều giọng đọc (multi-speaker) với nội dung đa dạng."
    ))
    add_paragraph(doc, (
        "Trong dự án này, chúng tôi sử dụng một subset của VIVOS, cụ thể là speaker "
        "VIVOSSPK01, để huấn luyện mô hình VITS single-speaker. Chi tiết bộ dữ liệu "
        "được trình bày trong Bảng 4.1."
    ))

    add_table_formatted(doc,
        ["Thông số", "Giá trị"],
        [
            ["Nguồn dữ liệu", "VIVOS (AILab – HCMUS)"],
            ["Speaker", "VIVOSSPK01 (single speaker)"],
            ["Số lượng câu", "250 câu"],
            ["Tổng thời lượng", "~10 phút"],
            ["Sample rate", "22050 Hz"],
            ["Định dạng audio", "WAV 16-bit mono"],
            ["Text cleaners", "vietnamese_cleaners"],
            ["Add blank", "True"],
            ["Train / Validation split", "240 / 10 câu"],
        ],
        col_widths=[5, 10],
        caption="Bảng 4.1: Thông số bộ dữ liệu VIVOS SPK01"
    )

    add_paragraph(doc, (
        "Cần lưu ý rằng 250 câu (~10 phút audio) là lượng dữ liệu tương đối nhỏ cho bài "
        "toán TTS. Thông thường, để đạt chất lượng cao, các hệ thống TTS cần từ 3-20 giờ "
        "audio. Tuy nhiên, với kiến trúc hiệu quả của VITS và framework Piper TTS đã được "
        "tối ưu, mô hình vẫn có thể học được các đặc trưng cơ bản của giọng nói tiếng Việt."
    ))

    # 4.2
    add_heading_custom(doc, "4.2. Tiền xử lý dữ liệu", level=2)
    add_paragraph(doc, (
        "Quá trình tiền xử lý dữ liệu bao gồm các bước chính sau:"
    ))

    add_paragraph(doc, "Bước 1: Thu thập và chuẩn hóa audio", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Các file audio WAV được trích xuất từ bộ VIVOS, đảm bảo đồng nhất định dạng: "
        "mono channel, 16-bit depth, sample rate 22050 Hz. Các file audio bị nhiễu hoặc "
        "có chất lượng thấp được loại bỏ."
    ))

    add_paragraph(doc, "Bước 2: Chuẩn hóa văn bản (Text normalization)", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Sử dụng vietnamese_cleaners để chuẩn hóa văn bản đầu vào, bao gồm: chuyển về "
        "chữ thường, loại bỏ ký tự đặc biệt không cần thiết, chuẩn hóa dấu câu, và "
        "xử lý các trường hợp đặc biệt của tiếng Việt (ví dụ: số đọc thành chữ)."
    ))

    add_paragraph(doc, "Bước 3: Trích xuất mel-spectrogram", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Mel-spectrogram được trích xuất từ audio với các tham số cấu hình trong Bảng 4.2."
    ))

    add_table_formatted(doc,
        ["Tham số", "Giá trị", "Mô tả"],
        [
            ["n_mel_channels", "80", "Số kênh mel-spectrogram"],
            ["sampling_rate", "22050", "Tần số lấy mẫu (Hz)"],
            ["filter_length (n_fft)", "1024", "Kích thước cửa sổ FFT"],
            ["hop_length", "256", "Bước nhảy giữa các frame"],
            ["win_length", "1024", "Chiều dài cửa sổ"],
            ["mel_fmin", "0.0", "Tần số mel tối thiểu"],
            ["mel_fmax", "null (Nyquist)", "Tần số mel tối đa"],
        ],
        col_widths=[4.5, 4.5, 7],
        caption="Bảng 4.2: Cấu hình tiền xử lý dữ liệu âm thanh"
    )

    add_paragraph(doc, "Bước 4: Chia tập Train / Validation", bold=True, first_line_indent=None)
    add_paragraph(doc, (
        "Bộ dữ liệu được chia thành tập huấn luyện (train) gồm 240 câu và tập kiểm tra "
        "(validation) gồm 10 câu. Thông tin metadata được lưu trong các file train.csv và "
        "val.csv, mỗi dòng chứa đường dẫn audio và nội dung text tương ứng."
    ))

    # 4.3
    add_heading_custom(doc, "4.3. Grapheme-to-Phoneme (G2P) cho tiếng Việt", level=2)
    add_paragraph(doc, (
        "Grapheme-to-Phoneme (G2P) là quá trình chuyển đổi từ ký tự chữ viết (grapheme) "
        "sang ký hiệu phiên âm quốc tế (phoneme – IPA). Đây là bước quan trọng trong "
        "pipeline TTS vì mô hình cần hiểu cách phát âm chứ không chỉ nhìn ký tự."
    ))
    add_paragraph(doc, (
        "Trong dự án này, chúng tôi sử dụng espeak-ng làm công cụ G2P cho tiếng Việt "
        "(voice: vi), thông qua thư viện piper-phonemize. Espeak-ng hỗ trợ phiên âm IPA "
        "cho tiếng Việt, bao gồm đầy đủ 6 thanh điệu và các âm vị đặc trưng."
    ))
    add_paragraph(doc, (
        "Mô hình sử dụng phoneme_id_map gồm 156 ký hiệu IPA (trong tổng số 256 symbols "
        "được cấp phát), bao gồm các ký hiệu: nguyên âm (a, e, i, o, u và các biến thể IPA), "
        "phụ âm (b, d, f, g, h, k, l, m, n, p, r, s, t, v, w, z...), thanh điệu (↑, ↓, ˥, ˩...), "
        "ký tự đặc biệt (BOS ^, EOS $, blank _, space, dấu câu), và các diacritical marks."
    ))
    add_paragraph(doc, (
        "Ngoài ra, hệ thống cũng cung cấp phương thức fallback khi không cài được "
        "piper-phonemize: ánh xạ trực tiếp từng ký tự sang phoneme ID. Phương thức này "
        "cho chất lượng thấp hơn nhưng vẫn đảm bảo mô hình có thể chạy được demo."
    ))

    # 4.4
    add_heading_custom(doc, "4.4. Framework Piper TTS", level=2)
    add_paragraph(doc, (
        "Piper TTS là framework mã nguồn mở dành cho tổng hợp giọng nói, được phát triển "
        "bởi Michael Hansen (rhasspy). Piper được thiết kế đặc biệt để hỗ trợ nhiều ngôn ngữ "
        "và có khả năng chạy inference nhanh trên cả CPU, phù hợp cho các ứng dụng edge/embedded."
    ))
    add_paragraph(doc, "Các đặc điểm chính của Piper TTS:")
    add_bullet(doc, "Dựa trên kiến trúc VITS (PyTorch Lightning).")
    add_bullet(doc, "Hỗ trợ hơn 30 ngôn ngữ, bao gồm tiếng Việt.")
    add_bullet(doc, "Hỗ trợ xuất mô hình sang ONNX để deploy linh hoạt.")
    add_bullet(doc, "Sử dụng espeak-ng làm phonemizer mặc định.")
    add_bullet(doc, "Cung cấp pre-trained models và hướng dẫn fine-tuning.")
    add_bullet(doc, "Tối ưu cho inference trên CPU (không bắt buộc GPU).")

    # 4.5
    add_heading_custom(doc, "4.5. Cấu hình môi trường huấn luyện", level=2)
    add_paragraph(doc, (
        "Quá trình huấn luyện được thực hiện trên môi trường sau:"
    ))
    add_bullet(doc, "Hệ điều hành: Windows / Linux")
    add_bullet(doc, "Python: 3.11+")
    add_bullet(doc, "Framework: Piper TTS (PyTorch Lightning)")
    add_bullet(doc, "GPU: NVIDIA (CUDA) – khuyến nghị")
    add_bullet(doc, "RAM: 16GB+")
    add_bullet(doc, "Thư viện chính: PyTorch, ONNX Runtime, piper-phonemize, espeak-ng")

    add_paragraph(doc, (
        "Sau khi huấn luyện xong, mô hình được xuất sang định dạng ONNX "
        "(model_epoch_4988.onnx, ~60MB) kèm file cấu hình JSON chứa metadata, phoneme_id_map "
        "và inference parameters. Việc sử dụng ONNX cho phép inference mà không cần cài đặt "
        "PyTorch, giảm đáng kể kích thước dependencies và tăng tốc độ trên CPU."
    ))

    add_page_break(doc)


# ═══════════════════ CHƯƠNG 5 ═══════════════════

def create_chapter_5(doc):
    """Chương 5: Thực nghiệm và Đánh giá."""
    add_heading_custom(doc, "CHƯƠNG 5: THỰC NGHIỆM VÀ ĐÁNH GIÁ", level=1)

    # 5.1
    add_heading_custom(doc, "5.1. Cấu hình huấn luyện", level=2)
    add_paragraph(doc, (
        "Bảng 5.1 trình bày chi tiết các siêu tham số (hyperparameters) được sử dụng trong "
        "quá trình huấn luyện mô hình VITS. Các tham số này được cấu hình trong file "
        "vits_vi.json và tuân theo khuyến nghị mặc định của Piper TTS với một số điều chỉnh "
        "phù hợp cho bộ dữ liệu tiếng Việt."
    ))

    add_table_formatted(doc,
        ["Hyperparameter", "Giá trị", "Mô tả"],
        [
            ["epochs", "10,000", "Tổng số epoch huấn luyện"],
            ["batch_size", "16", "Kích thước batch"],
            ["learning_rate", "2×10⁻⁴", "Tốc độ học ban đầu"],
            ["lr_decay", "0.99988", "Hệ số suy giảm learning rate"],
            ["betas", "[0.8, 0.99]", "Hệ số β của Adam optimizer"],
            ["epsilon", "1×10⁻⁹", "Epsilon của Adam optimizer"],
            ["segment_size", "8,192", "Kích thước segment audio cho training"],
            ["fp16_run", "True", "Sử dụng mixed precision (FP16)"],
            ["c_mel", "45", "Trọng số mel-spectrogram loss"],
            ["c_kl", "1.0", "Trọng số KL divergence loss"],
            ["seed", "1234", "Random seed cho reproducibility"],
        ],
        col_widths=[4, 3.5, 8],
        caption="Bảng 5.1: Cấu hình siêu tham số huấn luyện"
    )

    add_paragraph(doc, (
        "Bảng 5.2 trình bày cấu hình kiến trúc mô hình VITS được sử dụng."
    ))

    add_table_formatted(doc,
        ["Tham số", "Giá trị", "Thành phần"],
        [
            ["inter_channels", "192", "Posterior Encoder / Flow"],
            ["hidden_channels", "192", "Text Encoder"],
            ["filter_channels", "768", "Text Encoder FFN"],
            ["n_heads", "2", "Text Encoder Attention"],
            ["n_layers", "6", "Text Encoder"],
            ["kernel_size", "3", "Text Encoder Conv"],
            ["p_dropout", "0.1", "Text Encoder"],
            ["resblock", "1", "HiFi-GAN Decoder"],
            ["upsample_rates", "[8, 8, 2, 2]", "HiFi-GAN Decoder"],
            ["upsample_initial_channel", "512", "HiFi-GAN Decoder"],
            ["n_layers_q", "3", "Posterior Encoder"],
        ],
        col_widths=[5.5, 3.5, 6.5],
        caption="Bảng 5.2: Cấu hình kiến trúc mô hình VITS"
    )

    # 5.2
    add_heading_custom(doc, "5.2. Quá trình huấn luyện", level=2)
    add_paragraph(doc, (
        "Mô hình được huấn luyện sử dụng framework Piper TTS với optimizer AdamW và "
        "learning rate scheduling (exponential decay). Mixed precision training (FP16) được "
        "bật để tăng tốc huấn luyện và giảm bộ nhớ GPU."
    ))
    add_paragraph(doc, (
        "Quá trình huấn luyện được thực hiện với mục tiêu 10,000 epochs. Tại thời điểm báo "
        "cáo, mô hình đã được huấn luyện đến epoch 4,988 (khoảng 50% mục tiêu). Checkpoint "
        "bao gồm cả Generator (G) và Discriminator (D) được lưu lại."
    ))
    add_paragraph(doc, (
        "Trong quá trình huấn luyện, các loss được theo dõi bao gồm: Mel-spectrogram "
        "reconstruction loss (với trọng số c_mel = 45), KL divergence loss (c_kl = 1.0), "
        "Adversarial loss (GAN), Feature matching loss, và Duration prediction loss. "
        "Log interval được đặt là 200 steps và evaluation interval là 1,000 steps."
    ))
    add_paragraph(doc, (
        "Nhận xét: Với 4,988 epochs trên 240 câu huấn luyện, mô hình đã hội tụ đủ để "
        "tạo ra giọng nói tiếng Việt có thể nhận diện được. Tuy nhiên, do lượng dữ liệu "
        "nhỏ (~10 phút), chất lượng giọng nói chưa đạt mức tự nhiên hoàn toàn, đặc biệt "
        "ở các từ hiếm hoặc câu phức tạp."
    ))

    # 5.3
    add_heading_custom(doc, "5.3. Xuất mô hình ONNX", level=2)
    add_paragraph(doc, (
        "Sau khi huấn luyện, mô hình PyTorch được xuất sang định dạng ONNX (Open Neural "
        "Network Exchange) để tối ưu inference. File ONNX xuất ra bao gồm:"
    ))
    add_bullet(doc, "model_epoch_4988.onnx (~60MB): Chứa trọng số mô hình Generator (Text Encoder + Flow + Decoder). Discriminator không được xuất vì không cần thiết cho inference.")
    add_bullet(doc, "model_epoch_4988.onnx.json (~7.5KB): File cấu hình JSON chứa metadata (language, sample_rate, piper_version), phoneme_id_map (156 ký hiệu IPA → ID), inference parameters (noise_scale, length_scale, noise_w), và thông tin speaker.")

    add_paragraph(doc, "Các input của mô hình ONNX:")

    add_table_formatted(doc,
        ["Input Name", "Shape", "Data Type", "Mô tả"],
        [
            ["input", "(1, T)", "int64", "Chuỗi phoneme IDs"],
            ["input_lengths", "(1,)", "int64", "Độ dài chuỗi phoneme"],
            ["scales", "(3,)", "float32", "Tham số: noise_scale, length_scale, noise_w"],
        ],
        col_widths=[3.5, 3, 3, 6],
        caption="Bảng 5.3: Input của mô hình ONNX"
    )

    add_paragraph(doc, (
        "Output của mô hình là tensor audio waveform có shape (1, 1, N) với N là số "
        "samples, kiểu float32 trong khoảng [-1.0, 1.0]."
    ))

    # 5.4
    add_heading_custom(doc, "5.4. Kết quả Inference", level=2)
    add_paragraph(doc, (
        "Mô hình được đánh giá trên cả câu ngắn và đoạn văn bản dài. Inference được "
        "thực hiện trên CPU sử dụng ONNX Runtime với graph optimization level ORT_ENABLE_ALL."
    ))

    add_heading_custom(doc, "5.4.1. Kết quả trên câu test ngắn", level=3)
    add_table_formatted(doc,
        ["#", "Câu test", "Inference", "Audio", "RTF"],
        [
            ["1", "Xin chào, tôi là trợ lý ảo tiếng Việt.", "0.14s", "2.47s", "0.056"],
            ["2", "Hôm nay thời tiết rất đẹp, chúng ta hãy đi dạo.", "0.12s", "3.07s", "0.040"],
            ["3", "Trí tuệ nhân tạo đang thay đổi thế giới.", "0.10s", "2.44s", "0.041"],
            ["4", "Việt Nam là đất nước tươi đẹp với nhiều danh lam...", "0.14s", "3.18s", "0.043"],
            ["5", "Cảm ơn bạn đã sử dụng mô hình tổng hợp giọng nói.", "0.12s", "3.00s", "0.042"],
        ],
        caption="Bảng 5.4: Kết quả inference trên các câu test ngắn"
    )

    add_paragraph(doc, (
        "Kết quả cho thấy: Thời gian inference trung bình: 0.12 giây. Thời lượng audio "
        "trung bình: 2.83 giây. RTF (Real-Time Factor) trung bình: 0.044, nghĩa là mô hình "
        "tổng hợp giọng nói nhanh hơn khoảng 23 lần so với thời gian thực (real-time). "
        "Đây là kết quả rất tốt cho inference trên CPU."
    ))

    add_heading_custom(doc, "5.4.2. Kết quả trên đoạn văn bản dài", level=3)
    add_paragraph(doc, (
        "Để đánh giá khả năng xử lý văn bản dài, chúng tôi test với một đoạn văn khoảng "
        "100 từ (4 câu) về Việt Nam:"
    ))
    add_paragraph(doc, (
        "\"Việt Nam là một quốc gia nằm ở phía đông bán đảo Đông Dương, thuộc khu vực "
        "Đông Nam Á. Với đường bờ biển dài hơn ba nghìn hai trăm kilômét, Việt Nam sở hữu "
        "nhiều bãi biển đẹp và vịnh nổi tiếng thế giới như vịnh Hạ Long, đã được UNESCO "
        "công nhận là di sản thiên nhiên thế giới. Đất nước hình chữ S này có nền văn hóa "
        "lâu đời với hơn bốn nghìn năm lịch sử...\""
    ), italic=True)

    add_table_formatted(doc,
        ["Chỉ số", "Giá trị"],
        [
            ["Thời gian Inference", "1.24 giây"],
            ["Thời lượng Audio", "26.81 giây"],
            ["Real-Time Factor (RTF)", "0.046"],
            ["Nhanh hơn real-time", "~22 lần"],
        ],
        col_widths=[6, 8],
        caption="Bảng 5.5: Kết quả inference trên đoạn văn bản dài"
    )

    add_paragraph(doc, (
        "Kết quả cho thấy mô hình duy trì hiệu năng ổn định ngay cả với đoạn văn bản dài, "
        "RTF vẫn ở mức ~0.046 (nhanh hơn real-time 22 lần). Điều này xác nhận khả năng "
        "ứng dụng thực tế của mô hình trong các hệ thống đọc sách, trợ lý ảo, v.v."
    ))

    # 5.5
    add_heading_custom(doc, "5.5. Xây dựng ứng dụng Web Demo", level=2)
    add_paragraph(doc, (
        "Để minh họa trực quan khả năng của mô hình VITS, chúng tôi đã xây dựng một ứng "
        "dụng web demo sử dụng Flask (Python) kết hợp với giao diện HTML/CSS/JavaScript hiện "
        "đại."
    ))

    add_paragraph(doc, "Kiến trúc ứng dụng:", bold=True, first_line_indent=None)
    add_bullet(doc, "Backend: Flask (Python), ONNX Runtime cho inference.")
    add_bullet(doc, "Frontend: HTML5, CSS3 (glassmorphism design), JavaScript (vanilla).")
    add_bullet(doc, "API endpoint: POST /api/tts hoặc POST /api/synthesize nhận JSON với trường \"text\".")
    add_bullet(doc, "Response: File audio WAV hoặc JSON chứa audio URL và thống kê inference.")

    add_paragraph(doc, "Tính năng chính:", bold=True, first_line_indent=None)
    add_bullet(doc, "Người dùng nhập văn bản tiếng Việt vào textarea.")
    add_bullet(doc, "Nhấn nút \"Tổng Hợp Giọng Nói\" để gọi API.")
    add_bullet(doc, "Audio được phát trực tiếp trên trình duyệt.")
    add_bullet(doc, "Hỗ trợ điều chỉnh tham số: noise_scale, length_scale, noise_w (phiên bản GUI nâng cao).")
    add_bullet(doc, "Hiển thị thông tin inference: thời gian xử lý, thời lượng audio, RTF.")

    add_paragraph(doc, (
        "Giao diện web được thiết kế theo phong cách glassmorphism với nền gradient tối "
        "(dark mode), hiệu ứng backdrop blur, và các animation mượt mà, tạo trải nghiệm "
        "người dùng hiện đại và thẩm mỹ."
    ))

    add_paragraph(doc, "Yêu cầu hệ thống để chạy ứng dụng:", bold=True, first_line_indent=None)

    add_table_formatted(doc,
        ["Yêu cầu", "Chi tiết"],
        [
            ["Python", "3.11+ (khuyến nghị 3.14)"],
            ["ONNX Runtime", "1.28+"],
            ["piper-phonemize", "piper-phonemize-fix (Windows wheel)"],
            ["Thư viện khác", "NumPy, SoundFile, Flask"],
            ["GPU", "NVIDIA (tùy chọn, cần CUDA)"],
            ["RAM", "~500MB cho inference"],
            ["Disk", "~60MB (ONNX model)"],
        ],
        col_widths=[4, 11],
        caption="Bảng 5.6: Yêu cầu hệ thống"
    )

    # 5.6
    add_heading_custom(doc, "5.6. Đánh giá và nhận xét", level=2)

    add_paragraph(doc, "Ưu điểm:", bold=True, first_line_indent=None)
    add_bullet(doc, "Tốc độ inference rất nhanh trên CPU (RTF ~0.044), đảm bảo real-time capability.")
    add_bullet(doc, "Mô hình ONNX nhỏ gọn (~60MB), dễ triển khai trên nhiều nền tảng.")
    add_bullet(doc, "Pipeline hoàn chỉnh từ text đầu vào đến audio đầu ra, không cần vocoder riêng.")
    add_bullet(doc, "Ứng dụng web demo trực quan, dễ sử dụng.")
    add_bullet(doc, "Hỗ trợ cả 2 mode inference: phonemize bằng espeak-ng (chất lượng cao) và fallback trực tiếp (khi không cài được piper-phonemize).")

    add_paragraph(doc, "Hạn chế:", bold=True, first_line_indent=None, space_before=Pt(6))
    add_bullet(doc, "Dữ liệu huấn luyện ít (~10 phút), ảnh hưởng đến chất lượng giọng nói ở các câu phức tạp.")
    add_bullet(doc, "Mô hình mới train được 4,988/10,000 epochs, chưa hội tụ hoàn toàn.")
    add_bullet(doc, "Chỉ hỗ trợ single-speaker (1 giọng), chưa hỗ trợ multi-speaker.")
    add_bullet(doc, "Chưa có đánh giá MOS (Mean Opinion Score) bài bản với nhiều người nghe.")
    add_bullet(doc, "Một số thanh điệu tiếng Việt chưa được phát âm chính xác 100%, đặc biệt thanh ngã và thanh hỏi trong một số ngữ cảnh.")

    add_page_break(doc)


# ═══════════════════ CHƯƠNG 6 ═══════════════════

def create_chapter_6(doc):
    """Chương 6: Kết luận và Hướng phát triển."""
    add_heading_custom(doc, "CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", level=1)

    # 6.1
    add_heading_custom(doc, "6.1. Kết quả đạt được", level=2)
    add_paragraph(doc, (
        "Qua quá trình nghiên cứu và thực hiện, đồ án đã đạt được các kết quả sau:"
    ))
    add_bullet(doc, "Đã nghiên cứu và hiểu rõ kiến trúc mô hình VITS cùng các thành phần cốt lõi: Text Encoder (Transformer 6 layers), Posterior Encoder (WaveNet-style), HiFi-GAN Decoder (multi-scale upsampling), Normalizing Flow (affine coupling), và Stochastic Duration Predictor (flow-based).")
    add_bullet(doc, "Đã huấn luyện thành công mô hình VITS trên bộ dữ liệu tiếng Việt VIVOS (speaker VIVOSSPK01, 250 câu, ~10 phút audio) đến epoch 4,988 sử dụng framework Piper TTS.")
    add_bullet(doc, "Đã xuất mô hình sang định dạng ONNX (~60MB) với file cấu hình JSON đầy đủ, cho phép inference linh hoạt trên nhiều nền tảng mà không cần cài đặt PyTorch.")
    add_bullet(doc, "Đã đánh giá hiệu năng inference: Real-Time Factor (RTF) trung bình ~0.044 trên CPU, tương đương nhanh hơn 22 lần so với real-time, đảm bảo khả năng ứng dụng thực tế.")
    add_bullet(doc, "Đã xây dựng ứng dụng Web Demo hoàn chỉnh sử dụng Flask, cho phép người dùng trải nghiệm trực tiếp tính năng tổng hợp giọng nói tiếng Việt trên trình duyệt web.")
    add_bullet(doc, "Đã xây dựng script test đa chế độ (single, batch, interactive) và script tạo báo cáo slide PowerPoint tự động.")

    # 6.2
    add_heading_custom(doc, "6.2. Hạn chế", level=2)
    add_paragraph(doc, (
        "Bên cạnh các kết quả đạt được, đồ án vẫn còn một số hạn chế cần được khắc phục:"
    ))
    add_bullet(doc, "Lượng dữ liệu huấn luyện còn hạn chế (~10 phút audio, 250 câu). Các hệ thống TTS chuyên nghiệp thường sử dụng 3-20 giờ audio để đạt chất lượng cao.")
    add_bullet(doc, "Mô hình mới train được khoảng 50% mục tiêu (4,988/10,000 epochs), chất lượng giọng nói chưa đạt mức tối ưu.")
    add_bullet(doc, "Chỉ hỗ trợ single-speaker, chưa thử nghiệm multi-speaker hoặc voice cloning.")
    add_bullet(doc, "Chưa thực hiện đánh giá MOS (Mean Opinion Score) bài bản với nhóm người nghe đa dạng.")
    add_bullet(doc, "Một số thanh điệu và âm vị đặc trưng tiếng Việt chưa được mô hình hóa chính xác hoàn toàn.")

    # 6.3
    add_heading_custom(doc, "6.3. Hướng phát triển", level=2)
    add_paragraph(doc, (
        "Dựa trên kết quả và hạn chế đã phân tích, chúng tôi đề xuất các hướng phát triển sau:"
    ))

    add_paragraph(doc, "Về dữ liệu:", bold=True, first_line_indent=None)
    add_bullet(doc, "Tăng lượng dữ liệu huấn luyện từ 10 phút lên 3-5 giờ audio bằng cách sử dụng thêm speakers từ bộ VIVOS hoặc thu thập dữ liệu mới.")
    add_bullet(doc, "Thử nghiệm data augmentation (thay đổi tốc độ, thêm nhiễu nhẹ) để tăng tính đa dạng.")
    add_bullet(doc, "Thu thập dữ liệu nhiều phương ngữ (Bắc, Trung, Nam) cho multi-dialect TTS.")

    add_paragraph(doc, "Về mô hình:", bold=True, first_line_indent=None, space_before=Pt(6))
    add_bullet(doc, "Tiếp tục huấn luyện từ 4,988 đến 15,000-20,000 epochs để mô hình hội tụ tốt hơn.")
    add_bullet(doc, "Thử nghiệm multi-speaker training để hỗ trợ nhiều giọng nói khác nhau.")
    add_bullet(doc, "Nghiên cứu áp dụng VITS2 hoặc các biến thể cải tiến mới hơn.")
    add_bullet(doc, "Tối ưu mô hình bằng quantization (INT8) và pruning để giảm kích thước và tăng tốc.")

    add_paragraph(doc, "Về triển khai:", bold=True, first_line_indent=None, space_before=Pt(6))
    add_bullet(doc, "Chuyển sang FastAPI thay vì Flask để cải thiện hiệu năng và hỗ trợ async.")
    add_bullet(doc, "Triển khai trên cloud (AWS, GCP, Azure) với auto-scaling.")
    add_bullet(doc, "Tích hợp vào ứng dụng mobile (Android/iOS) sử dụng ONNX Runtime Mobile.")
    add_bullet(doc, "Xây dựng API RESTful hoàn chỉnh với authentication, rate limiting và monitoring.")

    add_paragraph(doc, "Về đánh giá:", bold=True, first_line_indent=None, space_before=Pt(6))
    add_bullet(doc, "Thực hiện đánh giá MOS (Mean Opinion Score) với nhóm từ 20-50 người nghe.")
    add_bullet(doc, "So sánh trực tiếp với các hệ thống TTS tiếng Việt khác (Google TTS, Zalo TTS).")
    add_bullet(doc, "Đánh giá chi tiết từng thanh điệu và loại câu (câu hỏi, câu cảm thán, v.v.).")

    add_page_break(doc)


# ═══════════════════ TÀI LIỆU THAM KHẢO ═══════════════════

def create_references(doc):
    """Tài liệu tham khảo."""
    add_heading_custom(doc, "TÀI LIỆU THAM KHẢO", level=1)

    references = [
        "[1] Kim, J., Kong, J., & Son, J. (2021). \"Conditional Variational Autoencoder with Adversarial Learning for End-to-End Text-to-Speech.\" Proceedings of the 38th International Conference on Machine Learning (ICML 2021).",
        "[2] Kong, J., Kim, J., & Bae, J. (2020). \"HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis.\" Advances in Neural Information Processing Systems (NeurIPS 2020).",
        "[3] Shen, J., Pang, R., Weiss, R. J., et al. (2018). \"Natural TTS Synthesis by Conditioning WaveNet on Mel Spectrogram Predictions.\" IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP 2018).",
        "[4] Ren, Y., Ruan, Y., Tan, X., et al. (2019). \"FastSpeech: Fast, Robust and Controllable Text to Speech.\" Advances in Neural Information Processing Systems (NeurIPS 2019).",
        "[5] Ren, Y., Hu, C., Tan, X., et al. (2020). \"FastSpeech 2: Fast and High-Quality End-to-End Text to Speech.\" arXiv preprint arXiv:2006.04558.",
        "[6] van den Oord, A., Dieleman, S., Zen, H., et al. (2016). \"WaveNet: A Generative Model for Raw Audio.\" arXiv preprint arXiv:1609.03499.",
        "[7] Wang, Y., Skerry-Ryan, R. J., Stanton, D., et al. (2017). \"Tacotron: Towards End-to-End Speech Synthesis.\" Interspeech 2017.",
        "[8] Kingma, D. P., & Welling, M. (2014). \"Auto-Encoding Variational Bayes.\" International Conference on Learning Representations (ICLR 2014).",
        "[9] Rezende, D. J., & Mohamed, S. (2015). \"Variational Inference with Normalizing Flows.\" Proceedings of the 32nd International Conference on Machine Learning (ICML 2015).",
        "[10] Goodfellow, I. J., Pouget-Abadie, J., Mirza, M., et al. (2014). \"Generative Adversarial Nets.\" Advances in Neural Information Processing Systems (NeurIPS 2014).",
        "[11] Hansen, M. (2023). \"Piper: A fast, local neural text to speech system.\" GitHub Repository: https://github.com/rhasspy/piper.",
        "[12] ONNX Runtime. Microsoft. https://onnxruntime.ai/.",
        "[13] Luong, H. T., & Vu, H. Q. (2016). \"A non-expert Kaldi recipe for Vietnamese Speech Recognition System.\" Proceedings of the Third International Workshop on Worldwide Language Service Infrastructure (WLSI 2016). (Bộ dữ liệu VIVOS)",
        "[14] espeak-ng. \"eSpeak NG: An open source speech synthesizer.\" GitHub Repository: https://github.com/espeak-ng/espeak-ng.",
    ]

    for ref in references:
        add_paragraph(doc, ref, font_size=12, first_line_indent=None,
                      space_after=Pt(6))


# ──────────────────────── MAIN ────────────────────────

def create_report():
    """Tạo báo cáo Word hoàn chỉnh."""
    print("📝 Bắt đầu tạo báo cáo Word...")

    doc = Document()

    # ── Cài đặt page layout ──
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)
        section.page_width = Cm(21.0)   # A4
        section.page_height = Cm(29.7)  # A4

    # ── Cài đặt default font ──
    style = doc.styles['Normal']
    font = style.font
    font.name = FONT_NAME
    font.size = Pt(FONT_SIZE_BODY)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)

    # Heading styles
    for i in range(1, 4):
        h_style = doc.styles[f'Heading {i}']
        h_font = h_style.font
        h_font.name = FONT_NAME
        h_style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT_NAME)

    # ── Tạo nội dung ──
    print("  📄 Trang bìa...")
    create_cover_page(doc)

    print("  📑 Mục lục...")
    create_toc_page(doc)

    print("  📋 Danh mục viết tắt...")
    create_abbreviations_page(doc)

    print("  📊 Danh mục bảng biểu & hình vẽ...")
    create_figures_tables_page(doc)

    print("  📖 Chương 1: Mở đầu...")
    create_chapter_1(doc)

    print("  📖 Chương 2: Tổng quan TTS...")
    create_chapter_2(doc)

    print("  📖 Chương 3: Kiến trúc VITS...")
    create_chapter_3(doc)

    print("  📖 Chương 4: Dữ liệu và Huấn luyện...")
    create_chapter_4(doc)

    print("  📖 Chương 5: Thực nghiệm và Đánh giá...")
    create_chapter_5(doc)

    print("  📖 Chương 6: Kết luận...")
    create_chapter_6(doc)

    print("  📚 Tài liệu tham khảo...")
    create_references(doc)

    # ── Lưu file ──
    doc.save(str(OUTPUT_FILE))
    print(f"\n✅ Đã tạo báo cáo: {OUTPUT_FILE}")
    print(f"   Kích thước: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")
    return OUTPUT_FILE


if __name__ == "__main__":
    create_report()
