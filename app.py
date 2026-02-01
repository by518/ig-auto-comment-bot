import streamlit as st
from instagrapi import Client
import random
import time
import threading
import queue
from pathlib import Path

# ===================== KONFIGURASI DEFAULT =====================
SESSION_FILE = "ig_session.json"  # File session disimpan di folder yang sama

DEFAULT_COMMENTS = [
    "Keren banget ini! 🔥",
    "Mantap jiwaa 🙌",
    "Suka banget sama vibesnya 😍",
    "Ini lokasinya di mana ya? penasaran nih",
    "Bagus sekali, semangat terus ya! 💪",
    "Wow amazing! 👏",
    "Love this so much 🥰",
    "Super keren bro 🔥🔥",
    "Gimana caranya bisa sebagus ini? spill dong",
    "Next level nih! 🚀",
    "Cocok banget buat daily look 👌",
    "Inspiratif sekali! Terima kasih share-nya 😊"
]

# Queue untuk log real-time
log_queue = queue.Queue()

def log(msg):
    log_queue.put(msg + "\n")
    print(msg)

# Fungsi bot di thread terpisah (biar dashboard ga freeze)
def run_auto_comment_bot(username, password, hashtag, max_comments):
    cl = Client()
    cl.delay_range = [4, 12]  # Delay acak antar action (detik)

    try:
        # Coba load session kalau ada
        if Path(SESSION_FILE).exists():
            cl.load_settings(SESSION_FILE)
            cl.get_timeline_feed()  # Test session masih valid
            log("✅ Login berhasil pakai session existing")
        else:
            log("Login pertama kali...")
            cl.login(username, password)
            cl.dump_settings(SESSION_FILE)
            log("✅ Login sukses & session disimpan permanen")

        log(f"🔍 Mulai cari post terbaru di #{hashtag} (max {max_comments} comment)")

        # Ambil lebih banyak post biar bisa pilih yang fresh
        medias = cl.hashtag_medias_recent(hashtag, amount=max_comments * 4)

        commented_count = 0
        for media in medias:
            if commented_count >= max_comments:
                break

            try:
                comment_text = random.choice(DEFAULT_COMMENTS)
                # Tambah emoji random biar variasi
                if random.random() > 0.5:
                    comment_text += random.choice([" 😍", " 🔥", " 🙌", " 💯", " 👏"])

                log(f"💬 Comment di post {media.id[:10]}...: {comment_text}")

                cl.media_comment(media.id, comment_text)

                commented_count += 1

                # Delay super aman (1-4 menit antar comment)
                sleep_time = random.uniform(60, 240)
                log(f"⏳ Tunggu {sleep_time//60:.0f} menit {sleep_time%60:.0f} detik...")
                time.sleep(sleep_time)

            except Exception as e:
                err = str(e).lower()
                log(f"❌ Error di post {media.id[:10]}...: {err}")
                if "block" in err or "challenge" in err or "rate limit" in err:
                    log("🚨 DETEKSI BLOCK / LIMIT! STOP BOT SEKARANG JUGA 🚨")
                    break
                time.sleep(30)  # Cooldown singkat

        log(f"🏁 Selesai! Total berhasil comment: {commented_count}")

    except Exception as e:
        log(f"🚨 ERROR BESAR (mungkin login gagal): {str(e)}")
        log("Coba hapus file ig_session.json lalu login ulang.")

# ===================== DASHBOARD STREAMLIT =====================
st.set_page_config(page_title="IG Auto-Comment Bot | Bang's Dashboard", layout="wide")

st.title("Instagram Auto-Comment Bot Dashboard ⚡ (2026 Safe Mode)")
st.markdown("**Gunakan akun dummy/test dulu! Risiko ban tinggi kalau over-use.**")

# Tab biar rapi
tab1, tab2 = st.tabs(["🔑 Login & Settings", "📊 Run Bot & Log"])

with tab1:
    st.subheader("Login Instagram (session aman disimpan)")
    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("Username IG", key="username")
    with col2:
        password = st.text_input("Password IG", type="password", key="password")

    st.subheader("Pengaturan Auto-Comment")
    hashtag = st.text_input("Hashtag Target (tanpa #)", value="jakarta", help="Contoh: makananenak, ootd, bisnisukm")
    max_comments = st.slider("Max Comment per Run (satu kali start)", 1, 20, 5, help="Mulai dari kecil: 5-10/hari aja dulu!")
    
    st.info("""
    **Tips Aman Banget (2026 Update):**
    - Max 10-15 comment/hari awal → naik pelan-pelan
    - Pakai residential proxy kalau punya (bukan VPS biasa)
    - Variasikan komentar & hashtag
    - Jangan run 24/7 → manual 1-2x/hari
    - Kalau kena action block: stop 3-7 hari
    """)

with tab2:
    st.subheader("Kontrol Bot & Live Log")

    if "bot_running" not in st.session_state:
        st.session_state.bot_running = False

    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("🚀 START BOT SEKARANG", type="primary", disabled=st.session_state.bot_running or not username or not password):
            if not username or not password:
                st.error("Isi username & password dulu ya Bang!")
            else:
                st.session_state.bot_running = True
                st.session_state.log_text = ""  # Reset log
                thread = threading.Thread(
                    target=run_auto_comment_bot,
                    args=(username, password, hashtag, max_comments)
                )
                thread.daemon = True
                thread.start()
                st.success("Bot jalan di background! Pantau log di bawah 👇")

    with col_stop:
        if st.button("🛑 STOP / REFRESH LOG", disabled=not st.session_state.bot_running):
            st.session_state.bot_running = False
            st.rerun()

    # Tampilkan log real-time
    st.subheader("Log Aktivitas (real-time)")
    log_area = st.empty()

    # Update log setiap rerun (Streamlit limitation)
    if "log_text" not in st.session_state:
        st.session_state.log_text = ""

    while not log_queue.empty():
        new_msg = log_queue.get()
        st.session_state.log_text += new_msg

    log_area.text_area("Log", value=st.session_state.log_text, height=400, disabled=True, key=f"log_{time.time()}")

    if st.button("Clear Log"):
        st.session_state.log_text = ""
        st.rerun()

# Footer
st.markdown("---")
st.caption("Dibuat khusus buat Bang | Pakai instagrapi + Streamlit | Tes dulu di akun dummy! Jangan sampe kena ban permanen ya 🚫")
