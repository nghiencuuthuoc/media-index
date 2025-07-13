import os
import json
import argparse
from tqdm import tqdm
from PIL import Image
import pytesseract

# --- Cấu hình tool OCR portable (chỉnh đường dẫn nếu khác cấu trúc) ---
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/Tesseract5.5.0")
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/poppler-24.08.0/Library/bin")
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/gs10.05.1/bin")
os.environ["GS"] = os.path.abspath("../app-ocr/gs10.05.1/bin/gswin64c.exe")

def ocr_folder(input_folder, lang="eng"):
    index_file = os.path.join(input_folder, "index.json")
    log_file = os.path.join(input_folder, "ocr_log.txt")

    # Đọc index.json nếu có, để resume
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        done_files = set(item["filename"] for item in index_data)
        results = index_data
        print(f"🟩 Resume mode: Đã có {len(done_files)} file OCR, chỉ làm file mới.")
    else:
        done_files = set()
        results = []

    # Đọc log file hiện có, ghi nối tiếp
    log_mode = "a" if os.path.exists(log_file) else "w"
    log = open(log_file, log_mode, encoding="utf-8")

    files = sorted([f for f in os.listdir(input_folder)
                    if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    new_files = [f for f in files if f not in done_files]

    for fname in tqdm(new_files, desc="OCR processing"):
        img_path = os.path.join(input_folder, fname)
        try:
            img = Image.open(img_path)
            text = pytesseract.image_to_string(img, lang=lang)
            results.append({
                "filename": fname,
                "text": text.strip()
            })
            msg = f"[OK] {fname}"
        except Exception as e:
            msg = f"[ERR] {fname}: {e}"
        print(msg)
        log.write(msg + "\n")

    log.close()

    # Gộp kết quả cũ + mới, ghi lại index
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Index saved to: {index_file} ({len(results)} files)")
    print(f"📄 Log file: {log_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR all images in folder and export index.json (auto save & resume)")
    parser.add_argument('-i', '--input', required=True, help="Input folder containing images")
    parser.add_argument('--lang', default="eng", help="Tesseract language code (default: eng)")
    args = parser.parse_args()
    ocr_folder(args.input, lang=args.lang)
