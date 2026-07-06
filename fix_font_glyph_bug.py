#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tráo đổi ký tự để sửa lỗi render ngược dấu của game engine Prison Architect.
Tác giả: Vũ Đức Minh & AI
"""
import os
import argparse
import sys

def main():
    if sys.platform.startswith('win'):
        sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Tráo đổi ký tự tiếng Việt trong các file dịch của Prison Architect.")
    parser.add_argument('--swap-text-chars', nargs=2, default=['à', 'á'], metavar=('CHAR1', 'CHAR2'),
                        help="Hai ký tự cần tráo đổi cho nhau, ví dụ: à á (mặc định: à á)")
    parser.add_argument('--text-files', nargs='+', default=['base-language.txt', 'd11.txt', 'fullgame.txt', 'tablets.txt', 'changelog.txt', 'eula.txt'],
                        help="Danh sách các file dịch cần xử lý (mặc định: base-language.txt d11.txt fullgame.txt tablets.txt changelog.txt eula.txt)")

    parser.add_argument('--dry-run', action='store_true',
                        help="Chỉ chạy thử để xem số lượng thay đổi, không ghi đè vào file.")

    
    args = parser.parse_args()
    char1, char2 = args.swap_text_chars[0], args.swap_text_chars[1]
    
    print(f"=== TIẾN TRÌNH TRÁO ĐỔI KÝ TỰ: '{char1}' <-> '{char2}' ===")
    if args.dry_run:
        print("[CHẾ ĐỘ CHẠY THỬ - DRY RUN] Không có file nào bị thay đổi thực tế.")
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    lang_dir = os.path.join(script_dir, "data", "language")
    temp_char = "\uFFFF"

    for file_name in args.text_files:
        file_path = os.path.join(lang_dir, file_name)
        if not os.path.exists(file_path):
            file_path = os.path.abspath(file_name)
            if not os.path.exists(file_path):
                print(f"❌ Không tìm thấy file: {file_name}")
                continue

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()

            count1 = content.count(char1)
            count2 = content.count(char2)

            if count1 == 0 and count2 == 0:
                print(f"ℹ️ File {os.path.basename(file_path)}: Không chứa ký tự '{char1}' hoặc '{char2}'. Bỏ qua.")
                continue

            print(f"📂 File: {os.path.basename(file_path)}")
            print(f"   - Tìm thấy '{char1}': {count1} lần")
            print(f"   - Tìm thấy '{char2}': {count2} lần")

            if not args.dry_run:
                content_mod = content.replace(char1, temp_char)
                content_mod = content_mod.replace(char2, char1)
                content_mod = content_mod.replace(temp_char, char2)

                with open(file_path, 'w', encoding='utf-8-sig') as f:
                    f.write(content_mod)
                print(f"   ✅ Đã tráo đổi và lưu file thành công!")
            else:
                print(f"   [Dry Run] Sẽ tráo đổi tổng cộng {count1 + count2} ký tự.")
            print()

        except Exception as e:
            print(f"❌ Lỗi khi xử lý file {file_name}: {str(e)}\n")

    print("=== HOÀN THÀNH ===")

if __name__ == "__main__":
    main()
