import os
import json
import argparse
from tqdm import tqdm
from PIL import Image
import pytesseract
import cv2

from pdf2image import convert_from_path
from striprtf.striprtf import rtf_to_text
from docx import Document
import pandas as pd
from ebooklib import epub
from bs4 import BeautifulSoup

# --- OCR portable config (Windows) ---
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/Tesseract5.5.0")
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/poppler-24.08.0/Library/bin")
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/gs10.05.1/bin")
os.environ["GS"] = os.path.abspath("../app-ocr/gs10.05.1/bin/gswin64c.exe")

EXT_MAP = {
    "image": ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'),
    "video": ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.m4v', '.flv'),
    "pdf": ('.pdf',),
    "docx": ('.docx',),
    "doc": ('.doc',),
    "xlsx": ('.xlsx',),
    "xls": ('.xls',),
    "rtf": ('.rtf',),
    "txt": ('.txt',),
    "md": ('.md',),
    "epub": ('.epub',),
    "azw": ('.azw', '.azw3', '.mobi'),
}

def find_files_recursive(folder, exts):
    file_list = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(exts):
                rel_path = os.path.relpath(os.path.join(root, f), folder)
                file_list.append(rel_path)
    return sorted(file_list)

def ocr_image(img_path, lang="eng"):
    img = Image.open(img_path)
    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()

def ocr_video(video_path, input_folder, lang="eng", frame_interval=5, done_set=None):
    results = []
    abs_video_path = os.path.join(input_folder, video_path)
    vidcap = cv2.VideoCapture(abs_video_path)
    if not vidcap.isOpened():
        return results, [f"[ERR] Cannot open video: {video_path}"]
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    sec_points = list(range(0, int(duration) + 1, frame_interval))
    msg_list = []
    for sec in tqdm(sec_points, desc=f"OCR video {video_path}", leave=False):
        frame_idx = int(sec * fps)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        success, frame = vidcap.read()
        if not success:
            msg_list.append(f"[ERR] Frame {sec}s not found in {video_path}")
            continue
        frame_id = f"{video_path}|{sec}"
        if done_set is not None and frame_id in done_set:
            continue
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        try:
            text = pytesseract.image_to_string(img, lang=lang).strip()
            results.append({
                "type": "video",
                "filename": video_path,
                "second": sec,
                "frame_id": frame_id,
                "text": text
            })
            msg_list.append(f"[OK] {video_path} at {sec}s")
        except Exception as e:
            msg_list.append(f"[ERR] {video_path} at {sec}s: {e}")
    vidcap.release()
    return results, msg_list

def extract_text_from_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
        return text.strip()
    except Exception as e:
        return f"[ERR] PDF: {e}"

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs]).strip()

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read().strip()

def extract_text_from_rtf(rtf_path):
    with open(rtf_path, 'r', encoding='utf-8', errors='ignore') as f:
        rtf_content = f.read()
    text = rtf_to_text(rtf_content)
    return text.strip()

def extract_text_from_xlsx(xlsx_path):
    dfs = pd.read_excel(xlsx_path, sheet_name=None)
    text = ""
    for sheet, df in dfs.items():
        text += f"\n--- Sheet: {sheet} ---\n"
        text += df.astype(str).to_csv(sep='\t', index=False)
    return text.strip()

def extract_text_from_xls(xls_path):
    dfs = pd.read_excel(xls_path, sheet_name=None)
    text = ""
    for sheet, df in dfs.items():
        text += f"\n--- Sheet: {sheet} ---\n"
        text += df.astype(str).to_csv(sep='\t', index=False)
    return text.strip()

def extract_text_from_epub(epub_path):
    try:
        book = epub.read_epub(epub_path)
        text = ""
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text += soup.get_text(separator="\n")
        return text.strip()
    except Exception as e:
        return f"[ERR] EPUB: {e}"

def extract_text_from_md(md_path):
    return extract_text_from_txt(md_path)

def extract_text_from_doc(doc_path):
    # Option 1: Use antiword or textract (needs installing).
    # Option 2: Skip .doc, or convert .doc to .docx/.pdf outside script for stable use.
    return "[WARN] .doc not natively supported, please convert to .docx"

def extract_text_from_azw(azw_path):
    # Placeholder: Recommend convert to epub/txt via Calibre or use mobi-python.
    return "[WARN] AZW/MOBI not natively supported, please convert to epub/txt"

# Tự động chọn hàm phù hợp
EXTRACT_FUNCS = {
    "image": ocr_image,
    "video": ocr_video, # special case
    "pdf": extract_text_from_pdf,
    "docx": extract_text_from_docx,
    "doc": extract_text_from_doc,
    "xlsx": extract_text_from_xlsx,
    "xls": extract_text_from_xls,
    "rtf": extract_text_from_rtf,
    "txt": extract_text_from_txt,
    "md": extract_text_from_md,
    "epub": extract_text_from_epub,
    "azw": extract_text_from_azw,
}

def get_filetype(filename):
    ext = os.path.splitext(filename)[1].lower()
    for k, v in EXT_MAP.items():
        if ext in v:
            return k
    return None

def main(input_folder, lang="eng", frame_interval=5):
    index_file = os.path.join(input_folder, "index.json")
    log_file = os.path.join(input_folder, "ocr_log.txt")

    # Resume logic
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        done = { (item["type"], item.get("filename", "")) for item in index_data if item.get("type") != "video" }
        done_videos = set(item.get("frame_id") for item in index_data if item.get("type") == "video")
        results = index_data
        print(f"🟩 Resume mode: {len(done)} files, {len(done_videos)} video frames done.")
    else:
        done = set()
        done_videos = set()
        results = []

    log_mode = "a" if os.path.exists(log_file) else "w"
    log = open(log_file, log_mode, encoding="utf-8")

    # Process each type
    for filetype in EXT_MAP:
        file_exts = EXT_MAP[filetype]
        file_list = find_files_recursive(input_folder, file_exts)
        # Skip videos here, handle separately
        if filetype == "video":
            continue
        new_files = [f for f in file_list if (filetype, f) not in done]
        if not new_files:
            continue
        for rel_path in tqdm(new_files, desc=f"OCR {filetype.upper()}"):
            abs_path = os.path.join(input_folder, rel_path)
            try:
                text = EXTRACT_FUNCS[filetype](abs_path)
                results.append({
                    "type": filetype,
                    "filename": rel_path,
                    "text": text
                })
                msg = f"[OK] {rel_path}"
            except Exception as e:
                msg = f"[ERR] {rel_path}: {e}"
            print(msg)
            log.write(msg + "\n")

    # OCR all videos (frame-by-frame)
    video_files = find_files_recursive(input_folder, EXT_MAP["video"])
    for rel_video in video_files:
        video_results, msg_list = ocr_video(
            rel_video, input_folder, lang=lang,
            frame_interval=frame_interval, done_set=done_videos
        )
        results.extend(video_results)
        for m in msg_list:
            print(m)
            log.write(m + "\n")

    log.close()

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Index saved to: {index_file} ({len(results)} entries)")
    print(f"📄 Log file: {log_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OCR/index images, video, pdf, doc, docx, xls, xlsx, rtf, txt, md, epub, azw/mobi in folder/subfolder (auto resume, log)"
    )
    parser.add_argument('-i', '--input', required=True, help="Input folder containing files")
    parser.add_argument('--lang', default="eng", help="Tesseract language code (default: eng)")
    parser.add_argument('--interval', type=int, default=5, help="Seconds between video frames (default: 5)")
    args = parser.parse_args()
    main(args.input, lang=args.lang, frame_interval=args.interval)
