import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document

# --- Sayfa Ayarları ---
st.set_page_config(
    page_title="FixText AI", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Hafıza Başlatma ---
if 'history' not in st.session_state: st.session_state['history'] = []
if 'last_result' not in st.session_state: st.session_state['last_result'] = ""
if 'file_content' not in st.session_state: st.session_state['file_content'] = ""

# --- FONKSİYONLAR ---
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages: text += page.extract_text() or ""
    return text

def read_docx(file):
    doc = Document(file)
    text = ""
    for para in doc.paragraphs: text += para.text + "\n"
    return text

# --- 🎨 TASARIM (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main-header {
        text-align: center; padding: 30px;
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white; border-radius: 15px; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stButton button {
        background: linear-gradient(45deg, #4b6cb7, #182848);
        color: white; border: none; padding: 15px 30px;
        border-radius: 12px; font-weight: 700; font-size: 18px; width: 100%;
        margin-top: 10px; transition: 0.3s; box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.2); }

    .result-card {
        background-color: #ffffff; border-left: 6px solid #4b6cb7;
        padding: 30px; border-radius: 12px; margin-top: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); font-size: 1.1em;
        line-height: 1.6; color: #333; animation: fadeIn 0.5s ease-in-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @media (prefers-color-scheme: dark) { .result-card { background-color: #262730; border-left-color: #7897e6; color: #eee; } }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ve API Key Yönetimi ---
with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    
    # --- YENİ KISIM: OTOMATİK ŞİFRE KONTROLÜ ---
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Otomatik Giriş Yapıldı")
    else:
        api_key = st.text_input("🔑 API Anahtarı", type="password")
        
    if api_key: genai.configure(api_key=api_key)
    st.markdown("---")
    
    st.subheader("📂 Dosya Yükle")
    uploaded_file = st.file_uploader("PDF veya Word seç", type=["pdf", "docx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".pdf"): extracted_text = read_pdf(uploaded_file)
            else: extracted_text = read_docx(uploaded_file)
            if extracted_text != st.session_state['file_content']:
                st.session_state['file_content'] = extracted_text
                st.success(f"✅ {uploaded_file.name} okundu!")
        except Exception as e: st.error(f"Hata: {e}")

    st.markdown("---")
    st.subheader("🎛️ Ton Ayarı")
    tone_value = st.slider("Resmiyet", 0, 100, 50, 10)
    mode_option = st.radio("🛠️ İşlem:", ["Resmi Dile Çevir", "E-posta Yaz", "Düzelt", "Özet Çıkar"])
    
    st.markdown("---")
    if st.button("🗑️ Temizle"):
        st.session_state['history'] = []
        st.session_state['file_content'] = ""
        st.session_state['last_result'] = ""
        st.rerun()

# --- ANA EKRAN ---
st.markdown("""
<div class="main-header">
    <h1 style='color: white;'>🤖 FixText AI Asistan</h1>
    <p style='color: #eee;'>Dosya Oku • Yazışmaları Yönet • Profesyonel Ol</p>
</div>
""", unsafe_allow_html=True)

st.subheader("✍️ Metin / İçerik")
default_text = st.session_state.get('file_content', "")
user_input = st.text_area("İşlenecek metni buraya yazın veya dosya yükleyin:", value=default_text, height=250)

if st.button("✨ SİHİRLİ DÖNÜŞÜMÜ BAŞLAT ✨"):
    if not api_key: st.error("⚠️ API Anahtarı bulunamadı. Lütfen ayarlardan ekleyin veya soldan girin.")
    elif not user_input: st.warning("⚠️ Metin girilmedi.")
    else:
        with st.spinner("Yapay zeka çalışıyor..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                tone_desc = f"Ton: %{tone_value} resmiyet."
                if tone_value > 80: tone_desc += " (Bürokratik, 'siz' dili)."
                elif tone_value < 30: tone_desc += " (Samimi)."
                
                strict_instruction = "SADECE dönüştürülmüş metni ver. Başka hiçbir açıklama, giriş cümlesi veya not yazma."
                
                prompts = {
                    "Resmi Dile Çevir": f"{strict_instruction}\nMetni şu tonda yeniden yaz: {tone_desc}\nMETİN: {user_input}",
                    "E-posta Yaz": f"{strict_instruction}\nŞu konuda e-posta taslağı yaz ({tone_desc}). Giriş ve kapanış ekle.\nKONU: {user_input}",
                    "Düzelt": f"{strict_instruction}\nHataları düzelt ({tone_desc}).\nMETİN: {user_input}",
                    "Özet Çıkar": f"{strict_instruction}\nMaddeler halinde özetle ({tone_desc}).\nMETİN: {user_input}"
                }
                
                resp = model.generate_content(prompts[mode_option])
                st.session_state['last_result'] = resp.text
                st.session_state['history'].insert(0, {"input": user_input[:60]+"...", "output": resp.text, "mode": mode_option, "tone": tone_value})
            except Exception as e: st.error(f"Hata: {e}")

# SONUÇ ALANI
if st.session_state['last_result']:
    st.markdown("---")
    st.subheader("🚀 Sonuç")
    st.markdown(f"""
    <div class="result-card">
        {st.session_state['last_result'].replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

# GEÇMİŞ
if st.session_state['history']:
    st.markdown("---")
    st.subheader("📚 Geçmiş İşlemler")
    for item in st.session_state['history']:
        with st.expander(f"{item['mode']} | {item['input']}"):
            st.markdown(item['output'])