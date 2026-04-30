import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="US Small Cap Research App", layout="wide")

st.title("US Small Cap & Government Contract Research App")
st.caption("Ücretsiz veri kaynaklarıyla çalışan araştırma paneli: yfinance + USAspending + SEC EDGAR")

# -----------------------------
# Helper functions
# -----------------------------

def safe_get(dictionary, key, default="N/A"):
    try:
        value = dictionary.get(key, default)
        if value is None or value == "":
            return default
        return value
    except Exception:
        return default


def format_number(value):
    try:
        if value is None:
            return "N/A"
        value = float(value)
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        if value >= 1_000:
            return f"${value / 1_000:.2f}K"
        return f"${value:.2f}"
    except Exception:
        return "N/A"


def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist
    except Exception as e:
        st.error(f"Finansal veri çekilirken hata oluştu: {e}")
        return {}, pd.DataFrame()


def get_usaspending_contracts(company_name):
    """
    USAspending API ile şirket adına göre son 24 ayda award/contract araması.
    Not: Şirket adı eşleşmesi mükemmel olmayabilir.
    """
    if not company_name:
        return []

    end_date = datetime.today()
    start_date = end_date - timedelta(days=730)

    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

    payload = {
        "filters": {
            "time_period": [
                {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                }
            ],
            "recipient_search_text": [company_name],
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Start Date",
            "End Date",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Description",
        ],
        "page": 1,
        "limit": 10,
        "sort": "Award Amount",
        "order": "desc",
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        st.warning(f"USAspending verisi çekilemedi veya eşleşme bulunamadı: {e}")
        return []


def get_sec_company_tickers():
    """
    SEC company_tickers.json dosyasından ticker-CIK eşleşmesi.
    SEC erişimi için User-Agent gerekiyor.
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "stock-research-app contact@example.com"}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"SEC ticker listesi çekilemedi: {e}")
        return {}


def find_cik_for_ticker(ticker):
    data = get_sec_company_tickers()
    ticker = ticker.upper().strip()

    for _, item in data.items():
        if item.get("ticker", "").upper() == ticker:
            cik = str(item.get("cik_str")).zfill(10)
            return cik, item.get("title", "N/A")

    return None, None


def get_sec_recent_filings(ticker):
    cik, sec_name = find_cik_for_ticker(ticker)
    if not cik:
        return None, sec_name, []

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": "stock-research-app contact@example.com"}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])

        filings = []
        for form, date, acc in zip(forms, dates, accession_numbers):
            if form in ["10-K", "10-Q", "8-K"]:
                filings.append(
                    {
                        "form": form,
                        "date": date,
                        "accession": acc,
                    }
                )
            if len(filings) >= 10:
                break

        return cik, sec_name, filings
    except Exception as e:
        st.warning(f"SEC filing verisi çekilemedi: {e}")
        return cik, sec_name, []


def calculate_scores(info, contracts, theme):
    early_score = 0
    risk_score = 0

    market_cap = info.get("marketCap")
    revenue_growth = info.get("revenueGrowth")
    debt_to_equity = info.get("debtToEquity")
    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")
    current_price = info.get("currentPrice")
    target_mean_price = info.get("targetMeanPrice")

    if market_cap:
        if 50_000_000 <= market_cap <= 2_000_000_000:
            early_score += 20
        elif 2_000_000_000 < market_cap <= 10_000_000_000:
            early_score += 10
        elif market_cap < 50_000_000:
            early_score += 5
            risk_score += 15

    if contracts:
        early_score += 25
        total_contract_value = sum([float(c.get("Award Amount") or 0) for c in contracts])
        if total_contract_value > 10_000_000:
            early_score += 15
        if total_contract_value > 50_000_000:
            early_score += 10

    strategic_themes = [
        "AI",
        "Cybersecurity",
        "Defense Technology",
        "Space Data",
        "Quantum",
        "Energy Infrastructure",
        "Robotics",
        "Semiconductor Supply Chain",
    ]

    if theme in strategic_themes:
        early_score += 15

    try:
        if revenue_growth is not None and revenue_growth > 0.15:
            early_score += 10
        elif revenue_growth is not None and revenue_growth < 0:
            risk_score += 10
    except Exception:
        pass

    try:
        if debt_to_equity is not None and debt_to_equity > 100:
            risk_score += 15
    except Exception:
        pass

    try:
        if total_debt and total_cash and total_debt > total_cash:
            risk_score += 10
    except Exception:
        pass

    missing_fields = 0
    for field in [market_cap, revenue_growth, total_cash, total_debt]:
        if field is None:
            missing_fields += 1
    risk_score += missing_fields * 5

    try:
        if current_price and target_mean_price and target_mean_price > current_price:
            early_score += 5
    except Exception:
        pass

    early_score = max(0, min(100, early_score))
    risk_score = max(0, min(100, risk_score))

    return early_score, risk_score


def generate_rule_based_swot(info, contracts, theme):
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    market_cap = info.get("marketCap")
    sector = safe_get(info, "sector")
    industry = safe_get(info, "industry")

    if contracts:
        strengths.append("Son 24 ay içinde USAspending verisinde hükümet kontratı/eşleşmesi bulundu.")
        opportunities.append("Federal kurumlarla iş ilişkisi büyüme katalizörü olabilir.")
    else:
        weaknesses.append("USAspending tarafında şirket adıyla net kontrat eşleşmesi bulunamadı.")
        threats.append("Hükümet kontratı iddiası varsa ayrıca manuel doğrulama gerekir.")

    if theme in ["AI", "Cybersecurity", "Defense Technology", "Space Data", "Quantum", "Energy Infrastructure"]:
        opportunities.append(f"{theme} teması uzun vadeli stratejik büyüme alanlarından biri olabilir.")

    if market_cap and market_cap < 2_000_000_000:
        strengths.append("Şirket küçük/orta ölçekli olduğu için büyüme potansiyeli yüksek olabilir.")
        threats.append("Küçük ölçekli şirketlerde likidite, sermaye artırımı ve volatilite riski daha yüksektir.")

    if sector != "N/A":
        strengths.append(f"Şirketin sektörü: {sector}.")
    if industry != "N/A":
        strengths.append(f"Şirketin endüstrisi: {industry}.")

    weaknesses.append("Bu SWOT, ücretsiz veri ve kural tabanlı sistemle üretilmiştir; AI analizi değildir.")
    threats.append("Veriler eksik, gecikmeli veya hatalı olabilir; yatırım kararı öncesi SEC dosyaları ve bilanço manuel kontrol edilmelidir.")

    return strengths, weaknesses, opportunities, threats


def tradingview_symbol_link(ticker, exchange):
    if not ticker:
        return None

    exchange_map = {
        "NasdaqGS": "NASDAQ",
        "NasdaqGM": "NASDAQ",
        "NasdaqCM": "NASDAQ",
        "NYSE": "NYSE",
        "AMEX": "AMEX",
    }

    tv_exchange = exchange_map.get(exchange, "NASDAQ")
    return f"https://www.tradingview.com/symbols/{tv_exchange}-{ticker.upper()}/"


# -----------------------------
# UI
# -----------------------------

with st.sidebar:
    st.header("Araştırma Ayarları")
    ticker = st.text_input("Ticker girin", value="RKLB")
    company_name = st.text_input("Şirket adı girin", value="Rocket Lab")
    theme = st.selectbox(
        "Tema seçin",
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
        index=3,
    )

    run_analysis = st.button("Ücretsiz Verilerle Analiz Et", type="primary")

st.info("Bu uygulama yatırım tavsiyesi değildir. Ücretsiz ve açık kaynak/veri kaynaklarıyla ön araştırma yapar.")

if run_analysis:
    ticker = ticker.upper().strip()
    company_name = company_name.strip()

    with st.spinner("Veriler çekiliyor..."):
        info, hist = get_stock_data(ticker)
        contracts = get_usaspending_contracts(company_name)
        cik, sec_name, filings = get_sec_recent_filings(ticker)
        early_score, risk_score = calculate_scores(info, contracts, theme)
        strengths, weaknesses, opportunities, threats = generate_rule_based_swot(info, contracts, theme)

    st.header(f"{company_name} ({ticker})")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fiyat", format_number(info.get("currentPrice")))
    col2.metric("Market Cap", format_number(info.get("marketCap")))
    col3.metric("Erken Sinyal Skoru", f"{early_score}/100")
    col4.metric("Risk Skoru", f"{risk_score}/100")

    st.subheader("Şirket Profili")
    st.write(safe_get(info, "longBusinessSummary", "Şirket özeti bulunamadı."))

    profile_cols = st.columns(3)
    profile_cols[0].write(f"**Sektör:** {safe_get(info, 'sector')}")
    profile_cols[1].write(f"**Endüstri:** {safe_get(info, 'industry')}")
    profile_cols[2].write(f"**Borsa:** {safe_get(info, 'exchange')}")

    tv_link = tradingview_symbol_link(ticker, info.get("exchange"))
    if tv_link:
        st.markdown(f"**TradingView grafiği:** [TradingView'de aç]({tv_link})")

    st.subheader("1 Yıllık Fiyat Grafiği")
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close"))
        fig.update_layout(height=400, xaxis_title="Tarih", yaxis_title="Fiyat")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Fiyat geçmişi bulunamadı.")

    st.subheader("USAspending Hükümet Kontratları")
    if contracts:
        contract_df = pd.DataFrame(contracts)
        st.dataframe(contract_df, use_container_width=True)

        total_contract_value = sum([float(c.get("Award Amount") or 0) for c in contracts])
        st.write(f"**Listelenen kontratların toplamı:** {format_number(total_contract_value)}")
    else:
        st.warning("Şirket adıyla USAspending üzerinde kontrat bulunamadı veya eşleşme sağlanamadı.")

    st.subheader("SEC EDGAR Son Dosyalar")
    if cik:
        st.write(f"**SEC şirket adı:** {sec_name}")
        st.write(f"**CIK:** {cik}")
    if filings:
        filings_df = pd.DataFrame(filings)
        st.dataframe(filings_df, use_container_width=True)
    else:
        st.warning("SEC dosyası bulunamadı veya ticker eşleşmedi.")

    st.subheader("Kural Tabanlı SWOT Analizi")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Güçlü Yanlar")
        for item in strengths:
            st.write(f"- {item}")

        st.markdown("### Fırsatlar")
        for item in opportunities:
            st.write(f"- {item}")

    with c2:
        st.markdown("### Zayıf Yanlar")
        for item in weaknesses:
            st.write(f"- {item}")

        st.markdown("### Tehditler")
        for item in threats:
            st.write(f"- {item}")

    st.subheader("Yorum")
    if early_score >= 70 and risk_score <= 50:
        st.success("Ön sinyal güçlü görünüyor. Derin araştırmaya alınabilir.")
    elif early_score >= 50:
        st.warning("Orta seviye sinyal var. Kontratlar, SEC dosyaları ve finansallar manuel doğrulanmalı.")
    else:
        st.info("Erken sinyal zayıf veya veri yetersiz. İzleme listesine alınabilir ama acele edilmemeli.")
