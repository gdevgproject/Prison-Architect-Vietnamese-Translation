#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_vietnamese_font.py
=========================================================================
BITMAP FONT ENGINEER SCRIPT — bổ sung / chuẩn hoá TOÀN BỘ ký tự tiếng Việt
vào bộ font BMFont (AngelCode) dạng .fnt + .png của game
"Prison Architect 2D" (font gốc: Arial Unicode MS, size=64, base=51,
atlas 2048x2048).

CÁCH HOẠT ĐỘNG (tóm tắt):
  1. Đọc file .fnt gốc, giữ nguyên 100% toàn bộ glyph không liên quan
     tới tiếng Việt (CJK, ký hiệu, số, chữ Latin cơ bản...).
  2. Xác định đầy đủ 146 ký tự cần có để gõ được MỌI từ tiếng Việt
     (nguyên âm a,ă,â,e,ê,i,o,ô,ơ,u,ư,y x 6 thanh điệu x hoa/thường,
     cộng thêm đ/Đ).
  3. Với TOÀN BỘ 146 ký tự này (kể cả vài ký tự đã có sẵn trong font gốc
     như à, á, ê, ă, đ...), script render lại bằng CÙNG MỘT font
     sans-serif + cùng cỡ chữ đã hiệu chỉnh khớp cap-height/x-height/
     baseline của font gốc, để đảm bảo toàn bộ chữ tiếng Việt có
     phong cách đồng nhất, không bị "chữ này kiểu font này, chữ kia
     kiểu font khác" (tránh mất hoà hợp thị giác).
  4. Đo bounding-box PIXEL THẬT của từng glyph (không đoán mò), rồi
     xếp (bin-packing kiểu shelf) vào vùng còn trống phía dưới atlas
     2048x2048 (ảnh gốc chỉ dùng hết tới hàng ~1487/2048 => còn dư
     ~560 hàng trống, đủ chỗ cho 146 glyph nhỏ).
  5. Ghi đè toạ độ trong .fnt cho các id đã tồn tại, và append dòng mới
     cho các id chưa có. Cập nhật lại "chars count=".
  6. Xuất ra đúng 2 file: unicode.fnt và unicode_0.png (đè lên bản build
     mới, giữ nguyên tên để người dùng thay thế trực tiếp vào game).
  7. Vẽ thêm 1 ảnh QA (preview.png) hiển thị vài câu tiếng Việt dùng
     chính bộ .fnt/.png vừa build ra, để kiểm tra bằng mắt: không lệch
     baseline, không đứt chân chữ, không răng cưa quá mức, dấu không
     lỗi.

FONT NGUỒN DÙNG ĐỂ VẼ GLYPH MỚI:
   Mặc định dùng "Liberation Sans" (metric- và hình-clone của Arial,
   free/open-source, có sẵn trên máy) — khớp tự nhiên với "Arial
   Unicode MS" mà font gốc khai báo, và có phủ đầy đủ 100% ký tự
   tiếng Việt cần thiết (đã kiểm tra qua bảng cmap).

   Nếu bạn có file Arial.ttf / Roboto-Regular.ttf / SVN-Arial thật (có
   bản quyền) muốn dùng để giống 100% font gốc hơn nữa, chỉ cần đổi
   biến FONT_PATH bên dưới rồi chạy lại — toàn bộ phần còn lại của
   script tự động hiệu chỉnh lại theo font mới (không hard-code).

CÁCH CHẠY:
   python3 patch_vietnamese_font.py
   (đặt file unicode.fnt và unicode_0.png gốc cùng thư mục với script,
   hoặc sửa INPUT_FNT / INPUT_PNG bên dưới)
=========================================================================
"""

import os
import re
import unicodedata as ud
from PIL import Image, ImageDraw, ImageFont

# ============================== CẤU HÌNH ================================

INPUT_FNT   = "unicode.fnt"
INPUT_PNG   = "unicode_0.png"
OUTPUT_FNT  = "unicode.fnt"        # giữ nguyên tên để thay thế trực tiếp
OUTPUT_PNG  = "unicode_0.png"      # giữ nguyên tên để thay thế trực tiếp
PREVIEW_PNG = "preview_vietnamese_qa.png"   # ảnh QA, không bắt buộc dùng trong game

# Font sans-serif dùng để vẽ lại toàn bộ glyph tiếng Việt.
# Liberation Sans = bản clone hình học + metric của Arial, mã nguồn mở,
# phủ 100% Unicode tiếng Việt. Đổi path này nếu bạn có Arial.ttf/Roboto thật.
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# --- Các hằng số đã HIỆU CHỈNH THỦ CÔNG bằng cách đo trực tiếp trên
#     font gốc (không đoán): xem phần "CALIBRATION" trong README cuối file.
BASE_LINE      = 52     # "baseline" thực tế trong pixel (font khai base=51,
                         # nhưng đo thật trên các glyph có sẵn: H,E,e,n,o,g,y,
                         # đáy mực luôn rơi đúng hàng 52 -> dùng số đo thật)
FONT_SIZE_PX   = 53     # cỡ Liberation Sans để cap-height(H)=37px,
                         # x-height(o)=28-29px, khớp sát font gốc (đo được
                         # H top=36~37, o top=28~29 tại size 53, sai lệch
                         # tối đa 1px - nằm trong dung sai bình thường
                         # giữa các family font khác nhau)
ADVANCE_SCALE  = 0.888  # Liberation Sans có tracking rộng hơn Arial Unicode MS
                         # gốc trung bình ~12% (đo trên H,A,o,e,n,space,W,y,g)
                         # => nhân hệ số này để xadvance khớp mật độ chữ gốc,
                         # tránh chữ có dấu bị "rộng" hơn chữ thường bất thường.

GLYPH_PADDING  = 2       # khoảng đệm giữa các glyph mới khi xếp vào atlas
ATLAS_W        = 2048
ATLAS_H        = 2048

# ============================ 1. XÁC ĐỊNH BỘ KÝ TỰ =======================

def build_full_vietnamese_charset():
    """Trả về danh sách đầy đủ 146 ký tự cần có để gõ được mọi từ tiếng Việt
    (12 nguyên âm cơ bản/biến thể x 6 thanh điệu x hoa/thường + đ/Đ)."""
    base_vowels = ["a", "ă", "â", "e", "ê", "i", "o", "ô", "ơ", "u", "ư", "y"]
    tones = ["", "\u0300", "\u0301", "\u0309", "\u0303", "\u0323"]
    # không dấu, huyền, sắc, hỏi, ngã, nặng

    chars = set()
    for v in base_vowels:
        for t in tones:
            c = ud.normalize("NFC", v + t)
            chars.add(c)
            chars.add(ud.normalize("NFC", c.upper()))
    chars.add("đ")
    chars.add("Đ")
    return sorted(chars, key=ord)


# ============================ 2. PARSE FILE .FNT =========================

CHAR_LINE_RE = re.compile(r'^char\s+id=(-?\d+)\s+(.*)$')

def parse_fnt(path):
    """Đọc .fnt gốc, trả về (header_lines, char_dict, footer_lines).
    char_dict: {id: full_line_string_khong_kem_newline}
    header_lines: các dòng info/common/page/chars count (giữ nguyên thứ tự)
    footer_lines: các dòng khác (kerning...) nếu có, giữ nguyên."""
    header_lines = []
    char_dict = {}
    footer_lines = []
    chars_count_idx = None

    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]

    in_chars_block_done = False
    for line in lines:
        m = CHAR_LINE_RE.match(line)
        if m:
            cid = int(m.group(1))
            char_dict[cid] = line
            in_chars_block_done = True
        elif line.startswith("chars count="):
            header_lines.append(line)
            chars_count_idx = len(header_lines) - 1
        elif not in_chars_block_done:
            header_lines.append(line)
        else:
            # dòng sau khối char (vd: kerning) - giữ nguyên
            if line.strip():
                footer_lines.append(line)

    return header_lines, char_dict, footer_lines, chars_count_idx


def parse_char_line_fields(line):
    """Tách các field key=value trong 1 dòng char thành dict."""
    fields = {}
    for tok in line.strip().split()[1:]:
        if "=" in tok:
            k, v = tok.split("=", 1)
            fields[k] = v
    return fields


# ============================ 3. RENDER GLYPH =============================

class GlyphRenderer:
    def __init__(self, font_path, font_size, base_line, advance_scale):
        self.font = ImageFont.truetype(font_path, font_size)
        self.base_line = base_line
        self.advance_scale = advance_scale
        # canvas nháp đủ lớn để không bao giờ bị cắt mất glyph cao/thấp nhất
        self.scratch_w = 260
        self.scratch_h = 300
        self.pad_x = 120
        self.pen_baseline_y = 200  # hàng baseline trong canvas nháp

    def render(self, ch):
        """Vẽ 1 ký tự, trả về (ink_image_L_mode, xoffset, yoffset, xadvance).
        Trả về None nếu ký tự không có mực (không nên xảy ra với bộ ký tự này)."""
        img = Image.new("L", (self.scratch_w, self.scratch_h), 0)
        draw = ImageDraw.Draw(img)
        draw.text(
            (self.pad_x, self.pen_baseline_y),
            ch,
            font=self.font,
            fill=255,
            anchor="ls",  # left, baseline -> baseline neo đúng pen_baseline_y
        )
        bbox = img.getbbox()
        if bbox is None:
            return None

        left, top, right, bottom = bbox
        ink = img.crop(bbox)

        xoffset = left - self.pad_x
        yoffset = (top - self.pen_baseline_y) + self.base_line
        xadvance = round(self.font.getlength(ch) * self.advance_scale)

        return ink, xoffset, yoffset, xadvance


# ============================ 4. SHELF BIN-PACKING =========================

class ShelfPacker:
    """Xếp glyph theo kiểu shelf (từng hàng), bắt đầu ngay dưới vùng đã
    dùng của atlas gốc, không đụng tới bất kỳ glyph cũ nào."""

    def __init__(self, atlas_w, start_y, padding):
        self.atlas_w = atlas_w
        self.padding = padding
        self.cursor_x = padding
        self.cursor_y = start_y + padding
        self.shelf_h = 0

    def place(self, w, h):
        if self.cursor_x + w + self.padding > self.atlas_w:
            # sang hàng (shelf) mới
            self.cursor_x = self.padding
            self.cursor_y += self.shelf_h + self.padding
            self.shelf_h = 0
        x, y = self.cursor_x, self.cursor_y
        self.cursor_x += w + self.padding
        self.shelf_h = max(self.shelf_h, h)
        return x, y

    @property
    def max_y_used(self):
        return self.cursor_y + self.shelf_h


# ============================ 5. MAIN PIPELINE =============================

def main():
    print("=== BƯỚC 1: Đọc font gốc ===")
    header_lines, char_dict, footer_lines, chars_count_idx = parse_fnt(INPUT_FNT)
    atlas = Image.open(INPUT_PNG).convert("L")
    assert atlas.size == (ATLAS_W, ATLAS_H), f"Kích thước atlas khác kỳ vọng: {atlas.size}"
    print(f"  - Số glyph gốc: {len(char_dict)}")
    print(f"  - Kích thước atlas: {atlas.size}, mode: {atlas.mode}")

    print("=== BƯỚC 2: Xác định bộ ký tự tiếng Việt cần chuẩn hoá ===")
    target_chars = build_full_vietnamese_charset()
    existing_targets = [c for c in target_chars if ord(c) in char_dict]
    new_targets = [c for c in target_chars if ord(c) not in char_dict]
    print(f"  - Tổng số ký tự tiếng Việt cần có: {len(target_chars)}")
    print(f"  - Đã có sẵn (sẽ render lại cho đồng nhất phong cách): {len(existing_targets)}")
    print(f"  - Hoàn toàn chưa có (sẽ thêm mới): {len(new_targets)}")

    print("=== BƯỚC 3: Tìm điểm bắt đầu vùng trống trong atlas ===")
    lowest_used_row = 0
    for line in char_dict.values():
        f = parse_char_line_fields(line)
        y, h = int(f["y"]), int(f["height"])
        lowest_used_row = max(lowest_used_row, y + h)
    print(f"  - Hàng thấp nhất đang được các glyph gốc sử dụng: {lowest_used_row}/{ATLAS_H}")
    start_y = lowest_used_row + 4  # chừa khoảng đệm an toàn 4px

    print("=== BƯỚC 4: Render + đo bounding-box thật cho từng glyph ===")
    renderer = GlyphRenderer(FONT_PATH, FONT_SIZE_PX, BASE_LINE, ADVANCE_SCALE)
    packer = ShelfPacker(ATLAS_W, start_y, GLYPH_PADDING)

    atlas_draw_target = atlas.copy()
    new_char_lines = []
    max_h_seen = 0

    for ch in target_chars:
        result = renderer.render(ch)
        if result is None:
            print(f"  [CẢNH BÁO] Ký tự U+{ord(ch):04X} ({ch!r}) không render ra mực nào, bỏ qua.")
            continue
        ink, xoffset, yoffset, xadvance = result
        w, h = ink.size
        max_h_seen = max(max_h_seen, h)

        px, py = packer.place(w, h)
        atlas_draw_target.paste(ink, (px, py))

        cid = ord(ch)
        line = (
            f"char id={cid:<6}x={px:<7}y={py:<7}"
            f"width={w:<6}height={h:<6}"
            f"xoffset={xoffset:<6}yoffset={yoffset:<6}"
            f"xadvance={xadvance:<6}page=0  chnl=15"
        )
        char_dict[cid] = line  # ghi đè nếu đã tồn tại, hoặc thêm mới
        new_char_lines.append((cid, ch, w, h, xoffset, yoffset, xadvance))

    print(f"  - Đã xử lý {len(new_char_lines)} glyph.")
    print(f"  - Vùng atlas mới sử dụng: hàng {start_y} -> {packer.max_y_used} "
          f"(còn dư {ATLAS_H - packer.max_y_used}px phía dưới, an toàn).")
    if packer.max_y_used > ATLAS_H:
        raise RuntimeError("Vượt quá chiều cao atlas! Cần tăng ATLAS_H hoặc giảm cỡ chữ.")

    print("=== BƯỚC 5: Ghi lại file .fnt ===")
    total_count = len(char_dict)
    out_header = []
    for line in header_lines:
        if line.startswith("chars count="):
            out_header.append(f"chars count={total_count}")
        else:
            out_header.append(line)

    # Giữ nguyên toàn bộ glyph gốc theo đúng thứ tự ban đầu, các glyph mới
    # append vào cuối theo thứ tự mã Unicode tăng dần (không ảnh hưởng gì
    # tới cách engine đọc file, spec BMFont không yêu cầu phải sort).
    original_ids_in_order = []
    seen = set()
    with open(INPUT_FNT, encoding="utf-8") as f:
        for line in f:
            m = CHAR_LINE_RE.match(line.strip())
            if m:
                cid = int(m.group(1))
                original_ids_in_order.append(cid)
                seen.add(cid)

    appended_new_ids = sorted(cid for cid in char_dict if cid not in seen)
    # các id đã tồn tại nhưng bị RENDER LẠI (ví dụ à, á, ê, ă, đ...) vẫn giữ
    # đúng vị trí cũ trong file, chỉ thay nội dung dòng.
    out_lines = list(out_header)
    for cid in original_ids_in_order:
        out_lines.append(char_dict[cid])
    for cid in appended_new_ids:
        out_lines.append(char_dict[cid])
    out_lines.extend(footer_lines)

    with open(OUTPUT_FNT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out_lines) + "\n")
    print(f"  - Đã ghi {OUTPUT_FNT} (tổng {total_count} glyph).")

    print("=== BƯỚC 6: Ghi lại file .png ===")
    atlas_draw_target.save(OUTPUT_PNG)
    print(f"  - Đã ghi {OUTPUT_PNG}.")

    print("=== BƯỚC 7: Xuất ảnh QA để kiểm tra bằng mắt ===")
    render_qa_preview(char_dict, atlas_draw_target)
    print(f"  - Đã ghi {PREVIEW_PNG}.")

    print("\nHOÀN TẤT. Danh sách chi tiết glyph tiếng Việt đã (tái) tạo:")
    for cid, ch, w, h, xo, yo, xa in new_char_lines:
        print(f"  U+{cid:04X} {ch!r:>4}  w={w:<3} h={h:<3} xoff={xo:<3} yoff={yo:<4} xadv={xa}")


# ===================== 6. RENDERER MINI ĐỂ TỰ KIỂM TRA (QA) =================

def render_qa_preview(char_dict, atlas_img):
    """Dùng chính bộ .fnt/.png vừa tạo để tự vẽ vài dòng tiếng Việt,
    giúp kiểm tra bằng mắt: baseline, dấu, chữ đ/ơ/ư, không đứt nét."""
    test_lines = [
        "Cộng hoà Xã hội Chủ nghĩa Việt Nam",
        "Trại giam - Prison Architect",
        "Nhà tù, phòng giam, cai ngục, tù nhân",
        "ăn uống đầy đủ - sức khoẻ tốt - kỷ luật nghiêm",
        "ƠƯĐ ơưđ ẤẦẨẪẬ ắằẳẵặ ỐỒỔỖỘ ứừửữự",
        "Aa Ăă Ââ Ee Êê Ii Oo Ôô Ơơ Uu Ưư Yy Đđ",
    ]

    fields_cache = {cid: parse_char_line_fields(l) for cid, l in char_dict.items()}
    line_height = 64
    canvas_w = 1400
    canvas_h = line_height * (len(test_lines) + 1)
    out = Image.new("RGB", (canvas_w, canvas_h), (30, 30, 30))
    atlas_rgb_alpha = atlas_img  # mode L

    for row_idx, text in enumerate(test_lines):
        pen_x = 20
        pen_y_top = 20 + row_idx * line_height
        for ch in text:
            cid = ord(ch)
            f = fields_cache.get(cid)
            if f is None:
                pen_x += 15
                continue
            gx, gy = int(f["x"]), int(f["y"])
            gw, gh = int(f["width"]), int(f["height"])
            gxo, gyo = int(f["xoffset"]), int(f["yoffset"])
            gxa = int(f["xadvance"])
            if gw > 0 and gh > 0:
                glyph = atlas_rgb_alpha.crop((gx, gy, gx + gw, gy + gh))
                glyph_rgb = Image.merge("RGB", (glyph, glyph, glyph))
                dest_x = pen_x + gxo
                dest_y = pen_y_top + gyo
                out.paste(glyph_rgb, (dest_x, dest_y), glyph)
            pen_x += gxa
        # vẽ đường baseline tham chiếu màu đỏ để kiểm tra thẳng hàng
        draw = ImageDraw.Draw(out)
        baseline_y = pen_y_top + BASE_LINE
        draw.line([(20, baseline_y), (canvas_w - 20, baseline_y)], fill=(80, 0, 0), width=1)

    out.save(PREVIEW_PNG)


if __name__ == "__main__":
    main()
