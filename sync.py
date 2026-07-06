#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script khôi phục bản dịch gốc và tráo đổi ký tự để sửa lỗi render ngược dấu của game engine Prison Architect.
Tác giả: Vũ Đức Minh & AI
"""
import os
import argparse
import sys
import shutil
import glob

def main():
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Khôi phục bản dịch gốc và tráo đổi ký tự tiếng Việt trong Prison Architect.")
    parser.add_argument('--swap-text-chars', nargs=2, default=['à', 'á'], metavar=('CHAR1', 'CHAR2'),
                        help="Hai ký tự cần tráo đổi cho nhau, ví dụ: à á (mặc định: à á)")
    parser.add_argument('--dry-run', action='store_true',
                        help="Chỉ chạy thử để xem số lượng thay đổi, không ghi đè vào file.")

    args = parser.parse_args()
    char1, char2 = args.swap_text_chars[0], args.swap_text_chars[1]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lang_dir = os.path.join(script_dir, "data", "language")
    ref_dir = os.path.join(script_dir, "original_vietnamese_reference")
    temp_char = "\uFFFF"

    print("=== TIẾN TRÌNH TỰ ĐỘNG KHÔI PHỤC VÀ TRÁO ĐỔI KÝ TỰ ===")
    print(f"Ký tự tráo đổi: '{char1}' <-> '{char2}'")
    if args.dry_run:
        print("[CHẾ ĐỘ CHẠY THỬ - DRY RUN] Không có file nào bị thay đổi thực tế.")
    print()

    # 1. Kiểm tra thư mục tham chiếu gốc
    if not os.path.exists(ref_dir):
        print(f"❌ Không tìm thấy thư mục tham chiếu gốc tại: {ref_dir}")
        print("Vui lòng tạo thư mục 'original_vietnamese_reference' chứa các file tiếng Việt chuẩn ở cùng thư mục với script này.")
        return

    # 2. Xóa các file .txt trong data/language
    if not args.dry_run:
        print("🧹 Đang dọn dẹp các file cũ trong data/language...")
        if os.path.exists(lang_dir):
            for txt_file in glob.glob(os.path.join(lang_dir, "*.txt")):
                try:
                    os.remove(txt_file)
                    print(f"   - Đã xóa: {os.path.basename(txt_file)}")
                except Exception as e:
                    print(f"   ❌ Không thể xóa {os.path.basename(txt_file)}: {e}")
        else:
            os.makedirs(lang_dir, exist_ok=True)
            print("   - Đã tạo mới thư mục data/language.")
    else:
        print("🔍 [Dry Run] Sẽ dọn dẹp các file cũ trong data/language.")

    # 3. Sao chép các file từ original_vietnamese_reference sang data/language
    if not args.dry_run:
        print("\n👯 Đang sao chép các file bản dịch gốc vào data/language...")
        ref_files = glob.glob(os.path.join(ref_dir, "*.txt"))
        if not ref_files:
            print("   ❌ Không tìm thấy file .txt nào trong thư mục original_vietnamese_reference!")
            return
        for src_file in ref_files:
            dest_file = os.path.join(lang_dir, os.path.basename(src_file))
            shutil.copy2(src_file, dest_file)
            print(f"   - Đã clone: {os.path.basename(src_file)}")
    else:
        print("🔍 [Dry Run] Sẽ sao chép các file từ original_vietnamese_reference.")

    # 4. Quét và thực hiện tráo đổi ký tự trên các file mới được clone
    print("\n🔄 Đang tiến hành đảo ký tự...")
    target_files = glob.glob(os.path.join(lang_dir, "*.txt"))
    for file_path in target_files:
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            count1 = content.count(char1)
            count2 = content.count(char2)

            if count1 == 0 and count2 == 0:
                print(f"   ℹ️ File {os.path.basename(file_path)}: Không chứa ký tự '{char1}' hoặc '{char2}'.")
                continue

            print(f"   📂 File: {os.path.basename(file_path)}")
            print(f"      - '{char1}': {count1} lần")
            print(f"      - '{char2}': {count2} lần")

            if not args.dry_run:
                content_mod = content.replace(char1, temp_char)
                content_mod = content_mod.replace(char2, char1)
                content_mod = content_mod.replace(temp_char, char2)

                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(content_mod)
                print(f"      ✅ Đã sửa lỗi đảo dấu thành công!")
            else:
                print(f"      [Dry Run] Sẽ tráo đổi tổng cộng {count1 + count2} ký tự.")

        except Exception as e:
            print(f"   ❌ Lỗi khi xử lý file {os.path.basename(file_path)}: {str(e)}")

    print("\n=== HOÀN THÀNH ===")

if __name__ == "__main__":
    main()
