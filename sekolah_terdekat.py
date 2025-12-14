import streamlit as st
import pandas as pd
from math import radians, cos, sin, sqrt, atan2
from geopy.geocoders import Nominatim
import pydeck as pdk
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import base64
import os

st.set_page_config(page_title="Rekomendasi Sekolah Surabaya", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #fdf6f9, #ffffff);
        font-family: 'Segoe UI', sans-serif;
    }

    .hero-section {
        display: flex;
        align-items: center;
        justify-content: space-around;
        padding: 2rem 1rem;
    }

    .hero-text {
        max-width: 600px;
    }

    .hero-text h1 {
        color: #c2185b;
        font-weight: 900;
        font-size: 2.3rem;
    }

    .hero-text p {
        color: #333;
        font-size: 1.05rem;
    }

    .hero-image {
        text-align: center;
    }

    .hero-image img {
        width: 220px;
        border-radius: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    #mulai-btn {
        background-color: #c2185b;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 25px;
        text-decoration: none;
        transition: 0.3s;
        display: inline-block;
        margin-top: 1.5rem;
    }
    #mulai-btn:hover {
        background-color: #a9144e;
        transform: scale(1.05);
    }

    .school-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    #cari-sekolah-btn {
        background-color: #c2185b;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 25px;
        text-decoration: none;
        transition: 0.3s;
        display: inline-block;
        margin-top: 1.5rem;
        width: auto;
    }
    #cari-sekolah-btn:hover {
        background-color: #a9144e;
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# Read dataset and harversine function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

geolocator = Nominatim(user_agent="rekomendasi_sekolah_app")

def geocode_address(alamat):
    try:
        location = geolocator.geocode(alamat + ", Surabaya, Indonesia", timeout=10)
        if location:
            return location.latitude, location.longitude
    except:
        pass
    return None, None

@st.cache_data
def load_data():
    return pd.read_excel("rekomendasi_SMASMK_surabaya.xlsx")

df = load_data()


def load_image_base64(file_path):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")
 
if "page" not in st.session_state:
    st.session_state["page"] = "landing"
 
# Landing Page
if st.session_state["page"] == "landing":
    image_path = "sma.png"  
    image_base64 = load_image_base64(image_path)
    
    hero_html = f"""
    <div class="hero-section">
        <div class="hero-text">
            <h1>Skoolify: Sistem Rekomendasi Sekolah SMA dan SMK Terbaik di Surabaya</h1>
            <p>Skoolify membantu Anda menemukan sekolah SMA dan SMK Negeri terbaik di Surabaya berdasarkan lokasi dan fasilitas.  
            Temukan sekolah terdekat dengan fasilitas yang sesuai keinginan Anda!</p>
            <a href="?page=main" id="mulai-btn" target="_self">MULAI SEKARANG</a>
        </div>
        <div class="hero-image">
            <img src="data:image/png;base64,{image_base64}" alt="School Icon">
            <h3 style="color:#c2185b;">Skoolify</h3>
            <p style="font-size:0.9rem;">Membantu Pilihan Sekolah Anda</p>
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)

    query_params = st.query_params
    if "page" in query_params and query_params["page"] == "main":
        st.session_state["page"] = "main"
        st.rerun()
 
# Main Page
elif st.session_state["page"] == "main":
    st.title("Sistem Rekomendasi SMA dan SMK Negeri di Surabaya")
    st.markdown("Masukkan alamat dan preferensi fasilitas, lalu tekan tombol **Cari Sekolah** untuk melihat hasil terbaik di peta interaktif.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        nama_jalan = st.text_input("Nama Jalan", placeholder="Contoh: Jalan Raya Darmo")
    with col2:
        kecamatan = st.text_input("Kecamatan", placeholder="Contoh: Wonokromo")

    opsi_fasilitas = st.selectbox(
        "Tingkat Fasilitas Sekolah",
        ["Standar", "Lengkap", "Sangat Lengkap"]
    )

    st.markdown("""
    **Keterangan Tingkat Fasilitas:**
    - Standar → ≥ 10 ruang kelas, ≥ 1 lab, ≥ 1 perpustakaan  
    - Lengkap → ≥ 20 ruang kelas, ≥ 3 lab, ≥ 1 perpustakaan  
    - Sangat Lengkap → ≥ 30 ruang kelas, ≥ 5 lab, ≥ 2 perpustakaan  
    """)

    # Map facility values
    if opsi_fasilitas == "Standar":
        min_kelas, min_lab, min_perpus = 10, 1, 1
    elif opsi_fasilitas == "Lengkap":
        min_kelas, min_lab, min_perpus = 20, 3, 1
    else:
        min_kelas, min_lab, min_perpus = 30, 5, 2

    alamat = f"{nama_jalan}, {kecamatan}, Surabaya"

    cari_button = """
        <a href="#" id="cari-sekolah-btn" class="stButton">Cari Sekolah</a>
    """
    st.markdown(cari_button, unsafe_allow_html=True)

    if cari_button:
        if not nama_jalan.strip() and not kecamatan.strip():
            st.warning("Silakan isi minimal nama jalan atau kecamatan.")
        else:
            user_lat, user_lon = geocode_address(alamat)
            if user_lat is None:
                st.error("Lokasi tidak ditemukan. Coba gunakan nama jalan/kecamatan lain.")
            else:
                st.success(f"Lokasi ditemukan: {alamat} ({user_lat:.4f}, {user_lon:.4f})")

                # Calculate distance and similarity
                df['Jarak (km)'] = df.apply(
                    lambda row: haversine(user_lat, user_lon, row['Latitude'], row['Longitude']),
                    axis=1
                )

                fitur = df[['R. Kelas', 'R. Lab', 'R. Perpus']].copy()
                profil_user = np.array([[min_kelas, min_lab, min_perpus]])
                similarity = cosine_similarity(profil_user, fitur)[0]

                df['Similarity'] = similarity
                df['Skor Akhir'] = 0.7 * df['Similarity'] + 0.3 * (1 / (df['Jarak (km)'] + 1))
                result = df.sort_values(by='Skor Akhir', ascending=False).head(10)

                # Result map
                sekolah_map = result.rename(columns={'Latitude': 'lat', 'Longitude': 'lon'})
                user_df = pd.DataFrame([{'lat': user_lat, 'lon': user_lon, 'Nama Sekolah': 'Lokasi Anda'}])

                layers = [
                    pdk.Layer("ScatterplotLayer", data=sekolah_map, get_position='[lon, lat]', get_radius=120, get_fill_color=[194, 24, 91]),
                    pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon, lat]', get_radius=150, get_fill_color=[0, 0, 255]),
                    pdk.Layer("TextLayer", data=sekolah_map, get_position='[lon, lat]', get_text='Nama Sekolah', get_size=14, get_color=[0, 0, 0]),
                ]

                view = pdk.ViewState(latitude=user_lat, longitude=user_lon, zoom=12)
                r = pdk.Deck(map_style="mapbox://styles/mapbox/streets-v12", initial_view_state=view, layers=layers)
                st.pydeck_chart(r)

                # Recommendation list
                st.write("### 🏫 10 Rekomendasi Sekolah Terbaik")
                for _, row in result.iterrows():
                    st.markdown(f"""
                    <div class='school-card'>
                        <b>{row['Nama Sekolah']}</b><br>
                        Kecamatan: {row['Kecamatan']}<br>
                        Jarak: {row['Jarak (km)']:.2f} km<br>
                        Kelas: {row['R. Kelas']} | Lab: {row['R. Lab']} | Perpus: {row['R. Perpus']}<br>
                        Similarity: {row['Similarity']:.2f} | Skor Akhir: {row['Skor Akhir']:.4f}
                    </div>
                    """, unsafe_allow_html=True)
