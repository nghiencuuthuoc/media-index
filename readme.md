
---

# `media_ocr_index.py`

**Universal Multi-format OCR & Text Indexer**

## Overview

`media_ocr_index.py` is a powerful Python tool that automatically extracts and indexes text from images, videos, and a wide range of document types (PDF, DOCX, XLSX, RTF, TXT, MD, EPUB, and more) within a folder and its subfolders. It supports automatic OCR, full resume (pick up where it left off), detailed logging, and creates a single searchable `index.json` for all your media and documents.

---

## **Key Features**

* **OCR Images** (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tif`, `.tiff`)
* **OCR Video Frames** (`.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.m4v`, `.flv`)
* **Extract Text from:**

  * **PDF** (image-based or scanned)
  * **DOCX** (Word)
  * **XLSX/XLS** (Excel)
  * **RTF**
  * **TXT, MD** (plain text, Markdown)
  * **EPUB** (ebooks)
  * **AZW/MOBI** (Kindle/ebook, requires conversion or extra tools)
* **Resume**: Skips already-processed files for fast incremental runs.
* **Progress Logging**: Writes all progress and errors to `ocr_log.txt`.
* **Searchable Output**: Saves a unified `index.json` with extracted text and file metadata.

---

## **Installation**

### **Python Dependencies**

```bash
pip install tqdm pillow pytesseract opencv-python pdf2image striprtf python-docx openpyxl pandas ebooklib beautifulsoup4
```

* For **AZW/MOBI**: [See notes below](#azwmobi-support)

### **Required Binaries**

* **Tesseract-OCR** and **Poppler**
  (For Windows, place the portable folders as in the code or install system-wide)
* **GhostScript** (for some PDF support)

---

## **Usage**

```bash
python media_ocr_index.py -i <input_folder> [--lang eng] [--interval 5]
```

* `-i, --input` — Path to your root folder (containing images/videos/docs/subfolders)
* `--lang` — Tesseract OCR language (default: `eng`)
* `--interval` — (For video) Seconds between extracted frames (default: 5)

#### **Example**

```bash
python media_ocr_index.py -i "E:/MyDocuments"
```

---

## **How it Works**

1. **Scans all folders/subfolders** for supported file types.
2. **Performs OCR or text extraction** on each file.
3. **Saves each result** to `index.json` (type, filename, text).
4. **Writes logs** (progress, errors) to `ocr_log.txt`.
5. **Resumable**: If interrupted or re-run, only new/unprocessed files are indexed.

---

## **Supported File Types & Extraction Methods**

| File Type     | Extensions                               | Extraction Method   |
| ------------- | ---------------------------------------- | ------------------- |
| Image         | .png, .jpg, .jpeg, .bmp, .tif, .tiff     | OCR (Tesseract)     |
| Video         | .mp4, .avi, .mov, .mkv, .wmv, .flv, .m4v | OCR frames          |
| PDF           | .pdf                                     | pdf2image + OCR     |
| Word          | .docx                                    | python-docx         |
| Word (old)    | .doc                                     | *Conversion needed* |
| Excel         | .xlsx, .xls                              | openpyxl/pandas     |
| RTF           | .rtf                                     | striprtf            |
| Text/Markdown | .txt, .md                                | Read text           |
| EPUB          | .epub                                    | ebooklib + bs4      |
| AZW/MOBI      | .azw, .azw3, .mobi                       | *See below*         |

---

### **AZW/MOBI Support**

* AZW/MOBI files are not natively supported in Python.
* **Recommendation:**

  * Convert them to `.epub` or `.txt` using [Calibre](https://calibre-ebook.com/) or another tool, then run this script.
  * Or use a Python library like [`mobi-python`](https://github.com/ssut/py-mobi) (advanced).

---

## **Output**

* **index.json** — List of indexed items, e.g.

  ```json
  [
    {"type": "image", "filename": "photo1.jpg", "text": "Recognized text..."},
    {"type": "video", "filename": "video1.mp4", "second": 15, "frame_id": "video1.mp4|15", "text": "Frame OCR text..."},
    {"type": "pdf", "filename": "file.pdf", "text": "Extracted text..."},
    ...
  ]
  ```
* **ocr\_log.txt** — Progress and error log for troubleshooting.

---

## **Tips**

* For best OCR accuracy, ensure Tesseract, Poppler, and GhostScript are correctly set up on your system or in the folders referenced in the script.
* For `.doc` files: Convert to `.docx` using MS Word or LibreOffice for best results.
* For `.azw`, `.mobi`: Convert to `.epub` or `.txt` before indexing.

---

## **License**

MIT License.
Feel free to use and modify for personal or research projects.

---

## **Contributors**

Bui Huynh Quoc Dat | www.nghiencuuthuoc.com | www.pharmapp.vn

---


