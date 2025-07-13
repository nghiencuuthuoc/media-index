import streamlit as st
import os
import json
import re
from PIL import Image

# Path to the index.json file
INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../media-data/index.json'))
st.set_page_config(page_title="📚 Media Index Search", layout="wide")

st.title("📚 Media OCR Index Search")
st.caption("Search for any keyword in your entire OCR-indexed archive: images, videos, PDF, DOCX, XLSX, TXT, RTF, EPUB, and more.")

# Load index.json (with Streamlit caching for speed)
@st.cache_data
def load_index():
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
index_data = load_index()

# Highlight keyword in text using <mark>
def highlight(text, keyword):
    if not keyword.strip(): return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f'<mark style="background:yellow">{m.group(0)}</mark>', text)

# --- Search UI ---
keyword = st.text_input("🔍 Enter keyword to search:", "")

if keyword.strip():
    # Find all items that contain the keyword (case-insensitive)
    results = [
        item for item in index_data
        if isinstance(item.get("text"), str) and re.search(re.escape(keyword), item.get("text", ""), re.IGNORECASE)
    ]
    st.info(f"🔎 Found {len(results)} matching files/frames for: '{keyword}'")

    if 0 < len(results) <= 3:
        # Show all matches directly
        for item in results:
            with st.expander(f"{item.get('type', '?').capitalize()}: {item.get('filename', '')}"):
                # Show preview for image
                if item.get("type") == "image":
                    img_path = os.path.abspath(os.path.join("../media-data", item["filename"]))
                    if os.path.exists(img_path):
                        st.image(img_path, caption=item["filename"], use_column_width=True)
                # Video frame info
                elif item.get("type") == "video":
                    st.write(f"**Video:** {item['filename']} | Frame: {item.get('second', '?')}s")
                else:
                    st.write(f"**File:** {item.get('filename','?')}")
                # Show highlighted text snippet
                snippet = item["text"]
                if len(snippet) > 2000:
                    snippet = snippet[:2000] + "\n..."
                st.markdown(highlight(snippet, keyword), unsafe_allow_html=True)
    elif len(results) > 3:
        # Show dropdown list if there are many matches
        file_list = [f"{item.get('type','?').capitalize()}: {item.get('filename','')}" for item in results]
        idx = st.selectbox("Select a file/frame to view details:", range(len(results)), format_func=lambda i: file_list[i])
        item = results[idx]
        with st.expander(f"{item.get('type', '?').capitalize()}: {item.get('filename', '')}", expanded=True):
            if item.get("type") == "image":
                img_path = os.path.abspath(os.path.join("../media-data", item["filename"]))
                if os.path.exists(img_path):
                    st.image(img_path, caption=item["filename"], use_column_width=True)
            elif item.get("type") == "video":
                st.write(f"**Video:** {item['filename']} | Frame: {item.get('second', '?')}s")
            else:
                st.write(f"**File:** {item.get('filename','?')}")
            snippet = item["text"]
            if len(snippet) > 2000:
                snippet = snippet[:2000] + "\n..."
            st.markdown(highlight(snippet, keyword), unsafe_allow_html=True)
    else:
        st.warning("No matching files found!")
else:
    st.info("Enter a keyword to begin searching...")

# --- FOOTER ---
st.markdown("""
<br><hr>
<div style='text-align:center; font-size: 12px'>
    | Copyright 2025 | 🥣 <b>Nghien Cuu Thuoc</b> | 🧠 <b>PharmApp</b> |<br>
    | <i>Discover</i> | <i>Design</i> | <i>Optimize</i> | <i>Create</i> | <i>Deliver</i> | <br>
    | <a href="https://www.nghiencuuthuoc.com" target="_blank">www.nghiencuuthuoc.com</a> |
    <a href="https://www.pharmapp.vn" target="_blank">www.pharmapp.vn</a> |
    Zalo: <a href="https://zalo.me/84888999311" target="_blank">+84888999311</a> |
</div>
""", unsafe_allow_html=True)
