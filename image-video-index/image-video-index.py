import os
import json
import argparse
from tqdm import tqdm
from PIL import Image
import pytesseract
import cv2

# --- Cấu hình tool OCR portable ---
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/Tesseract5.5.0")
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/poppler-24.08.0/Library/bin")
os.environ["PATH"] += os.pathsep + os.path.abspath("../app-ocr/gs10.05.1/bin")
os.environ["GS"] = os.path.abspath("../app-ocr/gs10.05.1/bin/gswin64c.exe")

# Định dạng file ảnh & video hỗ trợ
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff')
VIDEO_EXTS = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.m4v', '.flv')

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
                "video": video_path,
                "second": sec,
                "frame_id": frame_id,
                "text": text
            })
            msg_list.append(f"[OK] {video_path} at {sec}s")
        except Exception as e:
            msg_list.append(f"[ERR] {video_path} at {sec}s: {e}")
    vidcap.release()
    return results, msg_list

def main(input_folder, lang="eng", frame_interval=5):
    index_file = os.path.join(input_folder, "index.json")
    log_file = os.path.join(input_folder, "ocr_log.txt")

    # Resume
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            index_data = json.load(f)
        done_images = set(item["filename"] for item in index_data if item.get("type", "image") == "image")
        done_videos = set(item.get("frame_id") for item in index_data if item.get("type") == "video")
        results = index_data
        print(f"🟩 Resume mode: {len(done_images)} images, {len(done_videos)} video frames done.")
    else:
        done_images = set()
        done_videos = set()
        results = []

    log_mode = "a" if os.path.exists(log_file) else "w"
    log = open(log_file, log_mode, encoding="utf-8")

    # 1. OCR all images
    image_files = find_files_recursive(input_folder, IMAGE_EXTS)
    new_images = [f for f in image_files if f not in done_images]
    for rel_path in tqdm(new_images, desc="OCR Images"):
        img_path = os.path.join(input_folder, rel_path)
        try:
            text = ocr_image(img_path, lang=lang)
            results.append({
                "type": "image",
                "filename": rel_path,
                "text": text
            })
            msg = f"[OK] {rel_path}"
        except Exception as e:
            msg = f"[ERR] {rel_path}: {e}"
        print(msg)
        log.write(msg + "\n")

    # 2. OCR all videos
    video_files = find_files_recursive(input_folder, VIDEO_EXTS)
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
        description="OCR all images & videos (frame-by-frame) in folder and export index.json (auto resume)"
    )
    parser.add_argument('-i', '--input', required=True, help="Input folder containing images/videos")
    parser.add_argument('--lang', default="eng", help="Tesseract language code (default: eng)")
    parser.add_argument('--interval', type=int, default=5, help="Seconds between video frames (default: 5)")
    args = parser.parse_args()
    main(args.input, lang=args.lang, frame_interval=args.interval)
