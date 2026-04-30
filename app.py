import streamlit as st

st.set_page_config(page_title="US Small Cap Research App", layout="wide")

st.title("US Small Cap & Government Contract Research App")

st.write("Bu uygulama küçük ve orta ölçekli ABD şirketlerini araştırmak için hazırlanıyor.")

ticker = st.text_input("Ticker girin:", placeholder="Örn: RKLB")
company_name = st.text_input("Şirket adı girin:", placeholder="Örn: Rocket Lab")

theme = st.selectbox(
    "Tema seçin:",
    [
        "AI",
        "Cybersecurity",
        "Defense Technology",
        "Space Data",
        "Quantum",
        "Energy Infrastructure",
        "Robotics",
        "Semiconductor Supply Chain",
    ],
)

if st.button("Analiz Et"):
    st.subheader("Analiz Sonucu")

    st.write(f"**Şirket:** {company_name}")
    st.write(f"**Ticker:** {ticker}")
    st.write(f"**Tema:** {theme}")

    st.markdown("### Şirket Özeti")
    st.write("Bu bölümde şirketin genel özeti görünecek.")

    st.markdown("### Hükümet Bağlantısı")
    st.write("Bu bölümde ABD hükümet kontratları, NASA, DoD, DOE veya Space Force bağlantıları görünecek.")

    st.markdown("### Big Tech Bağlantısı")
    st.write("Bu bölümde Nvidia, Microsoft, AWS, Google, Palantir gibi şirketlerle bağlantılar görünecek.")

    st.markdown("### SWOT Analizi")
    st.write("""
    **Güçlü Yanlar:** Henüz analiz edilmedi.  
    **Zayıf Yanlar:** Henüz analiz edilmedi.  
    **Fırsatlar:** Henüz analiz edilmedi.  
    **Tehditler:** Henüz analiz edilmedi.
    """)

    st.markdown("### Skorlar")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Erken Sinyal Skoru", "0/100")
    with col2:
        st.metric("Risk Skoru", "0/100")
