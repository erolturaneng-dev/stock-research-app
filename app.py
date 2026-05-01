import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="US Small Cap Research App", layout="wide")

st.title("US Small Cap & Government Contract Research App")
st.caption("Ücretsiz veri kaynaklarıyla çalışan araştırma paneli: yfinance + USAspending + SEC EDGAR")

# --------------------------------------------------
# Tema bazlı başlangıç izleme listeleri
# --------------------------------------------------

THEME_WATCHLISTS = {
    "AI": [
        ("PLTR", "Palantir"),
        ("BBAI", "BigBear.ai"),
        ("SOUN", "SoundHound AI"),
        ("AI", "C3.ai"),
        ("AISP", "Airship AI"),
    ],
    "Cybersecurity": [
        ("CRWD", "CrowdStrike"),
        ("S", "SentinelOne"),
        ("QLYS", "Qualys"),
        ("CYBR", "CyberArk"),
        ("TENB", "Tenable"),
    ],
    "Defense Technology": [
        ("RKLB", "Rocket Lab"),
        ("KTOS", "Kratos Defense"),
        ("AVAV", "AeroVironment"),
        ("ACHR", "Archer Aviation"),
        ("JOBY", "Joby Aviation"),
    ],
    "Space Data": [
        ("RKLB", "Rocket Lab"),
        ("ASTS", "AST SpaceMobile"),
        ("SPIR", "Spire Global"),
        ("BKSY", "BlackSky Technology"),
        ("LUNR", "Intuitive Machines"),
        ("RDW", "Redwire"),
    ],
    "Quantum": [
        ("IONQ", "IonQ"),
        ("RGTI", "Rigetti Computing"),
        ("QUBT", "Quantum Computing Inc"),
        ("QBTS", "D-Wave Quantum"),
        ("ARQQ", "Arqit Quantum"),
    ],
    "Energy Infrastructure": [
        ("SMR", "NuScale Power"),
        ("OKLO", "Oklo"),
        ("STEM", "Stem Inc"),
        ("FLNC", "Fluence Energy"),
        ("NNE", "Nano Nuclear Energy"),
    ],
    "Robotics": [
        ("SYM", "Symbotic"),
        ("IRBT", "iRobot"),
        ("TER", "Teradyne"),
        ("SERV", "Serve Robotics"),
        ("RR", "Richtech Robotics"),
    ],
    "Semiconductor Supply Chain": [
        ("FORM", "FormFactor"),
        ("ONTO", "Onto Innovation"),
        ("ACLS", "Axcelis Technologies"),
        ("ICHR", "Ichor Holdings"),
        ("AEHR", "Aehr Test Systems"),
    ],
}

# --------------------------------------------------
# Yardımcı fonksiyonlar
# --------------------------------------------------

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


def format_percent(value):
    try:
        if value is None:
            return "N/A"
        return f"{value * 100:.2f}%"
    except Exception:
        return "N/A"


def get_market_cap_category(market_cap):
    if market_cap is None:
        return "Bilinmiyor"

    try:
        market_cap = float(market_cap)
    except Exception:
        return "Bilinmiyor"

    if market_cap < 50_000_000:
        return "Nano-cap / çok küçük"
    elif market_cap < 300_000_000:
        return "Micro-cap"
    elif market_cap < 2_000_000_000:
        return "Small-cap"
    elif market_cap < 10_000_000_000:
        return "Mid-cap"
    elif market_cap < 200_000_000_000:
        return "Large-cap"
    else:
        return "Mega-cap"


def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist
    except Exception as e:
        st.error(f"Finansal veri çekilirken hata oluştu: {e}")
        return {}, pd.DataFrame()


def get_official_company_names(info, manual_name):
    names = []

    if manual_name:
        names.append(manual_name.strip())

    long_name = info.get("longName")
    short_name = info.get("shortName")

    if long_name:
        names.append(long_name.strip())
    if short_name:
        names.append(short_name.strip())

    clean_names = []
    for name in names:
        if name and name not in clean_names:
            clean_names.append(name)

    return clean_names


# --------------------------------------------------
# Teknik göstergeler
# --------------------------------------------------

def calculate_technical_indicators(hist):
    if hist.empty or len(hist) < 14:
        return None, None, None

    close = hist["Close"]

    ma50 = close.rolling(window=50).mean() if len(close) >= 50 else None
    ma200 = close.rolling(window=200).mean() if len(close) >= 200 else None

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    try:
        rsi_current = round(float(rsi.iloc[-1]), 1)
    except Exception:
        rsi_current = None

    return ma50, ma200, rsi_current


# --------------------------------------------------
# USAspending
# --------------------------------------------------

def get_usaspending_contracts_single_name(company_name):
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
        "limit": 20,
        "sort": "Award Amount",
        "order": "desc",
    }

    try:
        response = requests.post(url, json=payload, timeout=25)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception:
        return []


def get_usaspending_contracts_smart(search_names):
    all_results = []
    seen_awards = set()

    for name in search_names:
        results = get_usaspending_contracts_single_name(name)

        for item in results:
            award_id = item.get("Award ID")
            recipient = item.get("Recipient Name")
            key = f"{award_id}-{recipient}"

            if key not in seen_awards:
                item["Search Name Used"] = name
                all_results.append(item)
                seen_awards.add(key)

    return all_results


def summarize_contracts(contracts):
    if not contracts:
        return {
            "total_contract_value": 0,
            "contract_count": 0,
            "nasa_total": 0,
            "dod_total": 0,
            "doe_total": 0,
            "other_total": 0,
            "agency_list": [],
        }

    total = 0
    nasa_total = 0
    dod_total = 0
    doe_total = 0
    other_total = 0
    agencies = set()

    for contract in contracts:
        amount = float(contract.get("Award Amount") or 0)
        agency_raw = str(contract.get("Awarding Agency") or "")
        agency = agency_raw.lower()

        total += amount

        if agency_raw:
            agencies.add(agency_raw)

        if "national aeronautics" in agency or "nasa" in agency:
            nasa_total += amount
        elif "defense" in agency or "air force" in agency or "army" in agency or "navy" in agency:
            dod_total += amount
        elif "energy" in agency:
            doe_total += amount
        else:
            other_total += amount

    return {
        "total_contract_value": total,
        "contract_count": len(contracts),
        "nasa_total": nasa_total,
        "dod_total": dod_total,
        "doe_total": doe_total,
        "other_total": other_total,
        "agency_list": sorted(list(agencies)),
    }


def format_contracts_readable(contracts):
    if not contracts:
        return pd.DataFrame()

    rows = []

    for c in contracts:
        description = c.get("Description") or "N/A"
        if isinstance(description, str) and len(description) > 90:
            description_short = description[:90] + "..."
        else:
            description_short = description

        rows.append(
            {
                "Award ID": c.get("Award ID", "N/A"),
                "Recipient": c.get("Recipient Name", "N/A"),
                "Amount": format_number(c.get("Award Amount")),
                "Start": c.get("Start Date", "N/A"),
                "End": c.get("End Date", "N/A"),
                "Agency": c.get("Awarding Agency", "N/A"),
                "Sub Agency": c.get("Awarding Sub Agency", "N/A"),
                "Search Name": c.get("Search Name Used", "N/A"),
                "Description": description_short,
            }
        )

    return pd.DataFrame(rows)


# --------------------------------------------------
# SEC EDGAR
# --------------------------------------------------

def get_sec_company_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {
        "User-Agent": "stock-research-app contact@example.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=25)
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


def make_sec_filing_link(cik, accession):
    if not cik or not accession:
        return None

    cik_no_zero = str(int(cik))
    accession_clean = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession_clean}/"


def get_sec_recent_filings(ticker):
    cik, sec_name = find_cik_for_ticker(ticker)

    if not cik:
        return None, sec_name, []

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {
        "User-Agent": "stock-research-app contact@example.com"
    }

    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        data = response.json()

        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])

        filings = []

        for form, date, acc in zip(forms, dates, accession_numbers):
            if form in ["10-K", "10-Q", "8-K", "4"]:
                link = make_sec_filing_link(cik, acc)
                filings.append(
                    {
                        "form": form,
                        "date": date,
                        "link": link,
                    }
                )

            if len(filings) >= 12:
                break

        return cik, sec_name, filings

    except Exception as e:
        st.warning(f"SEC filing verisi çekilemedi: {e}")
        return cik, sec_name, []


def get_insider_form4_filings(filings):
    return [f for f in filings if f.get("form") == "4"][:5]


# --------------------------------------------------
# TradingView link
# --------------------------------------------------

def tradingview_symbol_link(ticker, exchange):
    if not ticker:
        return None

    exchange_map = {
        "NasdaqGS": "NASDAQ",
        "NasdaqGM": "NASDAQ",
        "NasdaqCM": "NASDAQ",
        "NCM": "NASDAQ",
        "NGM": "NASDAQ",
        "NMS": "NASDAQ",
        "NYSE": "NYSE",
        "AMEX": "AMEX",
    }

    tv_exchange = exchange_map.get(exchange, "NASDAQ")
    return f"https://www.tradingview.com/symbols/{tv_exchange}-{ticker.upper()}/"


# --------------------------------------------------
# Skor sistemi
# --------------------------------------------------

def calculate_scores(info, contracts, theme, filings):
    early_score = 0
    risk_score = 0
    notes = []

    market_cap = info.get("marketCap")
    revenue_growth = info.get("revenueGrowth")
    debt_to_equity = info.get("debtToEquity")
    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")
    current_price = info.get("currentPrice")
    target_mean_price = info.get("targetMeanPrice")
    profit_margins = info.get("profitMargins")
    operating_margins = info.get("operatingMargins")
    free_cashflow = info.get("freeCashflow")
    beta = info.get("beta")

    contract_summary = summarize_contracts(contracts)
    total_contract_value = contract_summary["total_contract_value"]

    try:
        if market_cap:
            if 50_000_000 <= market_cap <= 300_000_000:
                early_score += 22
                risk_score += 8
                notes.append("Micro-cap aralığında; erken aşama fırsat olabilir ama risk yüksektir.")
            elif 300_000_000 < market_cap <= 2_000_000_000:
                early_score += 25
                risk_score += 5
                notes.append("Small-cap aralığında; erken büyüme fırsatlarına uygun olabilir.")
            elif 2_000_000_000 < market_cap <= 10_000_000_000:
                early_score += 12
                notes.append("Mid-cap aralığında; artık çok erken aşama olmayabilir.")
            elif market_cap > 10_000_000_000:
                early_score -= 10
                risk_score += 8
                notes.append("Market cap büyük; 'çok erken keşif' potansiyeli daha sınırlı olabilir.")

            if market_cap < 50_000_000:
                risk_score += 25
                notes.append("Çok küçük piyasa değeri yüksek likidite ve volatilite riski taşır.")
    except Exception:
        risk_score += 5

    if contracts:
        early_score += 20
        notes.append("USAspending üzerinde hükümet kontratı/eşleşmesi bulundu.")

        if contract_summary["nasa_total"] > 0:
            early_score += 8
            notes.append("NASA bağlantılı kontrat/eşleşme bulundu.")

        if contract_summary["dod_total"] > 0:
            early_score += 8
            notes.append("DoD / savunma bağlantılı kontrat/eşleşme bulundu.")

        if contract_summary["doe_total"] > 0:
            early_score += 5
            notes.append("DOE / enerji bağlantılı kontrat/eşleşme bulundu.")

        try:
            if market_cap and total_contract_value:
                contract_to_market_cap = total_contract_value / market_cap

                if contract_to_market_cap >= 0.10:
                    early_score += 25
                    notes.append("Kontrat toplamı market cap'e göre çok anlamlı görünüyor.")
                elif contract_to_market_cap >= 0.03:
                    early_score += 15
                    notes.append("Kontrat toplamı market cap'e göre orta düzeyde anlamlı.")
                elif contract_to_market_cap >= 0.005:
                    early_score += 7
                    notes.append("Kontrat toplamı market cap'e göre sınırlı ama izlenebilir.")
                else:
                    early_score += 2
                    risk_score += 5
                    notes.append("Kontrat toplamı market cap'e göre oldukça küçük.")
        except Exception:
            pass
    else:
        risk_score += 5
        notes.append("USAspending üzerinde net kontrat eşleşmesi bulunamadı.")

    strategic_themes = list(THEME_WATCHLISTS.keys())
    if theme in strategic_themes:
        early_score += 12
        notes.append(f"{theme} stratejik büyüme temalarından biri olarak işaretlendi.")

    try:
        if revenue_growth is not None:
            if revenue_growth > 0.30:
                early_score += 15
                notes.append("Gelir büyümesi güçlü görünüyor.")
            elif revenue_growth > 0.10:
                early_score += 8
                notes.append("Gelir büyümesi pozitif görünüyor.")
            elif revenue_growth < 0:
                risk_score += 12
                notes.append("Gelir büyümesi negatif görünüyor.")
    except Exception:
        pass

    try:
        if profit_margins is not None and profit_margins < 0:
            risk_score += 15
            notes.append("Net kâr marjı negatif; kârlılık riski var.")
    except Exception:
        pass

    try:
        if operating_margins is not None and operating_margins < 0:
            risk_score += 10
            notes.append("Operasyonel marj negatif; operasyonel kârlılık riski var.")
    except Exception:
        pass

    try:
        if free_cashflow is not None and free_cashflow < 0:
            risk_score += 15
            notes.append("Free cash flow negatif; nakit yakma riski olabilir.")
    except Exception:
        pass

    try:
        if total_debt and total_cash and total_debt > total_cash:
            risk_score += 15
            notes.append("Toplam borç nakitten yüksek görünüyor.")
        elif total_cash and total_debt and total_cash > total_debt:
            early_score += 5
            notes.append("Nakit, borçtan yüksek görünüyor.")
    except Exception:
        pass

    try:
        if debt_to_equity is not None and debt_to_equity > 100:
            risk_score += 10
            notes.append("Debt/equity yüksek görünüyor.")
    except Exception:
        pass

    try:
        if beta is not None:
            if beta > 2:
                risk_score += 10
                notes.append("Beta yüksek; hisse piyasa ortalamasından daha volatil olabilir.")
            elif beta > 1.5:
                risk_score += 5
                notes.append("Beta orta-yüksek; volatilite izlenmeli.")
    except Exception:
        pass

    if filings:
        early_score += 3
        notes.append("SEC EDGAR dosyaları bulundu; halka açık veriler izlenebilir.")
    else:
        risk_score += 8
        notes.append("SEC dosyası bulunamadı veya ticker eşleşmedi.")

    try:
        if current_price and target_mean_price:
            if target_mean_price > current_price:
                early_score += 3
                notes.append("Analist ortalama hedef fiyatı mevcut fiyatın üzerinde görünüyor.")
            elif target_mean_price < current_price:
                risk_score += 3
                notes.append("Analist ortalama hedef fiyatı mevcut fiyatın altında görünüyor.")
    except Exception:
        pass

    missing_fields = 0
    for field in [
        market_cap,
        revenue_growth,
        total_cash,
        total_debt,
        profit_margins,
        operating_margins,
        free_cashflow,
    ]:
        if field is None:
            missing_fields += 1

    if missing_fields >= 4:
        risk_score += 12
        notes.append("Finansal veri alanlarında ciddi eksiklik var.")
    elif missing_fields >= 2:
        risk_score += 6
        notes.append("Bazı finansal veri alanları eksik.")

    early_score = max(0, min(100, early_score))
    risk_score = max(0, min(100, risk_score))

    return early_score, risk_score, notes


# --------------------------------------------------
# SWOT
# --------------------------------------------------

def generate_rule_based_swot(info, contracts, theme, early_score, risk_score):
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    market_cap = info.get("marketCap")
    sector = safe_get(info, "sector")
    industry = safe_get(info, "industry")
    profit_margins = info.get("profitMargins")
    free_cashflow = info.get("freeCashflow")
    revenue_growth = info.get("revenueGrowth")

    contract_summary = summarize_contracts(contracts)

    if contracts:
        strengths.append("USAspending verisinde hükümet kontratı/eşleşmesi bulundu.")
        opportunities.append("Federal kurumlarla iş ilişkisi büyüme katalizörü olabilir.")

        if contract_summary["nasa_total"] > 0:
            strengths.append("NASA bağlantılı kontrat/eşleşme bulunuyor.")

        if contract_summary["dod_total"] > 0:
            strengths.append("DoD / savunma bağlantılı kontrat/eşleşme bulunuyor.")
    else:
        weaknesses.append("USAspending tarafında şirket adıyla net kontrat eşleşmesi bulunamadı.")
        threats.append("Hükümet kontratı iddiası varsa ayrıca manuel doğrulama gerekir.")

    if theme in ["AI", "Cybersecurity", "Defense Technology", "Space Data", "Quantum", "Energy Infrastructure"]:
        opportunities.append(f"{theme} teması uzun vadeli stratejik büyüme alanlarından biri olabilir.")

    if market_cap:
        category = get_market_cap_category(market_cap)

        if "Small-cap" in category or "Micro-cap" in category:
            strengths.append("Şirket küçük/orta ölçekli olduğu için büyüme potansiyeli yüksek olabilir.")
            threats.append("Küçük ölçekli şirketlerde likidite, sermaye artırımı ve volatilite riski daha yüksektir.")
        elif "Large-cap" in category or "Mega-cap" in category:
            weaknesses.append("Şirket artık büyük ölçekli olabilir; erken aşama getiri potansiyeli sınırlanmış olabilir.")

    if sector != "N/A":
        strengths.append(f"Şirketin sektörü: {sector}.")
    if industry != "N/A":
        strengths.append(f"Şirketin endüstrisi: {industry}.")

    try:
        if revenue_growth is not None and revenue_growth > 0.10:
            strengths.append("Gelir büyümesi pozitif görünüyor.")
        elif revenue_growth is not None and revenue_growth < 0:
            weaknesses.append("Gelir büyümesi negatif görünüyor.")
    except Exception:
        pass

    try:
        if profit_margins is not None and profit_margins < 0:
            weaknesses.append("Net kâr marjı negatif; şirket henüz kârlı olmayabilir.")
            threats.append("Kârlılığa geçiş gecikirse sermaye artırımı veya borçlanma riski artabilir.")
    except Exception:
        pass

    try:
        if free_cashflow is not None and free_cashflow < 0:
            weaknesses.append("Free cash flow negatif; nakit yakma riski olabilir.")
    except Exception:
        pass

    if early_score >= 70:
        opportunities.append("Erken sinyal skoru güçlü; derin araştırma listesine alınabilir.")

    if risk_score >= 60:
        threats.append("Risk skoru yüksek; bilanço, nakit ve borç durumu ayrıca incelenmelidir.")

    weaknesses.append("Bu SWOT, ücretsiz veri ve kural tabanlı sistemle üretilmiştir; AI analizi değildir.")
    threats.append("Veriler eksik, gecikmeli veya hatalı olabilir; yatırım kararı öncesi SEC dosyaları ve bilanço manuel kontrol edilmelidir.")

    return strengths, weaknesses, opportunities, threats


# --------------------------------------------------
# UI Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("Araştırma Ayarları")

    mode = st.radio(
        "Mod seçin",
        ["Tek şirket analizi", "Sektör tarayıcısı"],
        index=0,
    )

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    if mode == "Tek şirket analizi":
        ticker = st.text_input("Ticker girin", value="RKLB")
        company_name = st.text_input("Şirket adı girin", value="Rocket Lab")
        theme = st.selectbox("Tema seçin", list(THEME_WATCHLISTS.keys()), index=3)
        run_analysis = st.button("Ücretsiz Verilerle Analiz Et", type="primary")
    else:
        theme = st.selectbox("Tema seçin", list(THEME_WATCHLISTS.keys()), index=3)
        run_scan = st.button("Sektörü Tara", type="primary")

    st.markdown("---")
    st.subheader("İzleme Listesi")

    if st.session_state.watchlist:
        for item in st.session_state.watchlist:
            st.write(f"- {item}")

        wl_df = pd.DataFrame({"Ticker": st.session_state.watchlist})
        csv_data = wl_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Watchlist CSV indir",
            data=csv_data,
            file_name="watchlist.csv",
            mime="text/csv",
        )

        if st.button("Watchlist temizle"):
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.caption("Henüz şirket eklenmedi.")


st.info(
    "Bu uygulama yatırım tavsiyesi değildir. "
    "Ücretsiz ve açık kaynak/veri kaynaklarıyla ön araştırma yapar."
)

# --------------------------------------------------
# Mod 1: Tek şirket analizi
# --------------------------------------------------

if mode == "Tek şirket analizi" and run_analysis:
    ticker = ticker.upper().strip()
    manual_company_name = company_name.strip()

    with st.spinner("Veriler çekiliyor..."):
        info, hist = get_stock_data(ticker)

        search_names = get_official_company_names(info, manual_company_name)
        contracts = get_usaspending_contracts_smart(search_names)

        cik, sec_name, filings = get_sec_recent_filings(ticker)
        form4_filings = get_insider_form4_filings(filings)

        early_score, risk_score, score_notes = calculate_scores(
            info=info,
            contracts=contracts,
            theme=theme,
            filings=filings,
        )

        strengths, weaknesses, opportunities, threats = generate_rule_based_swot(
            info=info,
            contracts=contracts,
            theme=theme,
            early_score=early_score,
            risk_score=risk_score,
        )

        contract_summary = summarize_contracts(contracts)
        ma50, ma200, rsi_current = calculate_technical_indicators(hist)

    display_name = safe_get(info, "longName", manual_company_name or ticker)

    st.header(f"{display_name} ({ticker})")

    if ticker not in st.session_state.watchlist:
        if st.button(f"+ Watchlist'e ekle ({ticker})"):
            st.session_state.watchlist.append(ticker)
            st.success(f"{ticker} watchlist'e eklendi.")
    else:
        st.success(f"{ticker} zaten watchlist içinde.")

    market_cap = info.get("marketCap")
    market_cap_category = get_market_cap_category(market_cap)

    total_contract_value = contract_summary["total_contract_value"]

    try:
        contract_to_market_cap = total_contract_value / market_cap if market_cap else None
    except Exception:
        contract_to_market_cap = None

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Fiyat", format_number(info.get("currentPrice")))
    col2.metric("Market Cap", format_number(market_cap))
    col3.metric("Erken Sinyal Skoru", f"{early_score}/100")
    col4.metric("Risk Skoru", f"{risk_score}/100")

    st.markdown("### Piyasa Değeri Kategorisi")
    st.write(f"**Kategori:** {market_cap_category}")

    if market_cap and market_cap > 10_000_000_000:
        st.warning(
            "Bu şirket artık large-cap kategorisine yakın veya içinde olabilir. "
            "Bu nedenle 'çok erken keşif' potansiyeli sınırlı olabilir."
        )

    if rsi_current is not None:
        if rsi_current < 30:
            rsi_comment = "Aşırı satım bölgesine yakın olabilir."
        elif rsi_current > 70:
            rsi_comment = "Aşırı alım bölgesine yakın olabilir."
        else:
            rsi_comment = "Nötr bölgede görünüyor."

        st.caption(f"RSI 14 gün: **{rsi_current}** — {rsi_comment}")

    st.subheader("Şirket Profili")
    st.write(safe_get(info, "longBusinessSummary", "Şirket özeti bulunamadı."))

    profile_cols = st.columns(4)
    profile_cols[0].write(f"**Sektör:** {safe_get(info, 'sector')}")
    profile_cols[1].write(f"**Endüstri:** {safe_get(info, 'industry')}")
    profile_cols[2].write(f"**Borsa:** {safe_get(info, 'exchange')}")
    profile_cols[3].write(f"**Market Cap Kategorisi:** {market_cap_category}")

    if search_names:
        with st.expander("USAspending aramasında kullanılan şirket adları"):
            for name in search_names:
                st.write(f"- {name}")

    tv_link = tradingview_symbol_link(ticker, info.get("exchange"))
    if tv_link:
        st.markdown(f"**TradingView grafiği:** [TradingView'de aç]({tv_link})")

    st.subheader("Temel Finansal Göstergeler")

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Revenue Growth", format_percent(info.get("revenueGrowth")))
    f2.metric("Profit Margin", format_percent(info.get("profitMargins")))
    f3.metric("Operating Margin", format_percent(info.get("operatingMargins")))
    f4.metric("Free Cash Flow", format_number(info.get("freeCashflow")))

    f5, f6, f7, f8 = st.columns(4)
    f5.metric("Total Cash", format_number(info.get("totalCash")))
    f6.metric("Total Debt", format_number(info.get("totalDebt")))
    f7.metric("Debt / Equity", safe_get(info, "debtToEquity"))
    f8.metric("Beta", safe_get(info, "beta"))

    st.subheader("1 Yıllık Fiyat Grafiği + Teknik Göstergeler")

    if not hist.empty:
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name="Close",
            )
        )

        if ma50 is not None:
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=ma50,
                    mode="lines",
                    name="MA50",
                )
            )

        if ma200 is not None:
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=ma200,
                    mode="lines",
                    name="MA200",
                )
            )

        fig.update_layout(
            height=420,
            xaxis_title="Tarih",
            yaxis_title="Fiyat",
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Fiyat geçmişi bulunamadı.")

    st.subheader("USAspending Hükümet Kontratları")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kontrat Sayısı", contract_summary["contract_count"])
    c2.metric("Toplam Kontrat", format_number(total_contract_value))
    c3.metric("NASA Toplamı", format_number(contract_summary["nasa_total"]))
    c4.metric("DoD Toplamı", format_number(contract_summary["dod_total"]))

    c5, c6 = st.columns(2)
    c5.metric("DOE Toplamı", format_number(contract_summary["doe_total"]))

    if contract_to_market_cap is not None:
        c6.metric("Kontrat / Market Cap", f"{contract_to_market_cap * 100:.4f}%")
    else:
        c6.metric("Kontrat / Market Cap", "N/A")

    if contracts:
        contract_df = format_contracts_readable(contracts)
        st.dataframe(contract_df, use_container_width=True, height=420)

        with st.expander("Kontrat açıklamalarını detaylı göster"):
            for idx, contract in enumerate(contracts, start=1):
                st.markdown(f"#### {idx}. {contract.get('Recipient Name', 'N/A')}")
                st.write(f"**Award ID:** {contract.get('Award ID', 'N/A')}")
                st.write(f"**Tutar:** {format_number(contract.get('Award Amount'))}")
                st.write(f"**Kurum:** {contract.get('Awarding Agency', 'N/A')}")
                st.write(f"**Alt kurum:** {contract.get('Awarding Sub Agency', 'N/A')}")
                st.write(f"**Başlangıç:** {contract.get('Start Date', 'N/A')}")
                st.write(f"**Bitiş:** {contract.get('End Date', 'N/A')}")
                st.write(f"**Aramada kullanılan ad:** {contract.get('Search Name Used', 'N/A')}")
                st.write(f"**Açıklama:** {contract.get('Description', 'N/A')}")
                st.divider()
    else:
        st.warning("Şirket adıyla USAspending üzerinde kontrat bulunamadı veya eşleşme sağlanamadı.")

    st.subheader("SEC EDGAR Son Dosyalar")

    if cik:
        st.write(f"**SEC şirket adı:** {sec_name}")
        st.write(f"**CIK:** {cik}")

    if filings:
        simple_filings = pd.DataFrame(
            [
                {
                    "Form": f["form"],
                    "Tarih": f["date"],
                    "Link": f["link"],
                }
                for f in filings
            ]
        )

        st.dataframe(simple_filings, use_container_width=True)

        with st.expander("SEC dosyalarını aç"):
            for filing in filings:
                st.markdown(
                    f"- **{filing['form']}** | {filing['date']} | "
                    f"[Aç]({filing['link']})"
                )
    else:
        st.warning("SEC dosyası bulunamadı veya ticker eşleşmedi.")

    st.subheader("Insider / Form 4 Kontrolü")

    if form4_filings:
        st.write("Son SEC listesinde Form 4 kayıtları bulundu. Bunlar insider işlem bildirimleri olabilir.")
        for filing in form4_filings:
            st.markdown(
                f"- **Form 4** | {filing['date']} | [Aç]({filing['link']})"
            )
    else:
        st.info("Son listelenen SEC dosyalarında Form 4 kaydı bulunamadı.")

    st.subheader("Skor Notları")

    for note in score_notes:
        st.write(f"- {note}")

    st.subheader("Kural Tabanlı SWOT Analizi")

    sw1, sw2 = st.columns(2)

    with sw1:
        st.markdown("### Güçlü Yanlar")
        for item in strengths:
            st.write(f"- {item}")

        st.markdown("### Fırsatlar")
        for item in opportunities:
            st.write(f"- {item}")

    with sw2:
        st.markdown("### Zayıf Yanlar")
        for item in weaknesses:
            st.write(f"- {item}")

        st.markdown("### Tehditler")
        for item in threats:
            st.write(f"- {item}")

    st.subheader("Sonuç Yorumu")

    if early_score >= 70 and risk_score <= 50:
        st.success(
            "Ön sinyal güçlü görünüyor. Yine de SEC dosyaları, bilanço ve haberler manuel doğrulanmalı."
        )
    elif early_score >= 60 and risk_score <= 70:
        st.warning(
            "Orta-güçlü sinyal var. Şirket derin araştırmaya alınabilir ama riskler dikkatle incelenmeli."
        )
    elif early_score >= 40:
        st.info(
            "Orta seviye sinyal var. İzleme listesine alınabilir, ancak acele yatırım kararı verilmemeli."
        )
    else:
        st.info(
            "Erken sinyal zayıf veya veri yetersiz. Daha fazla doğrulama gerekir."
        )

    st.caption(
        "Not: Bu uygulama otomatik ve kural tabanlı ön analiz yapar. "
        "Yatırım tavsiyesi değildir."
    )

# --------------------------------------------------
# Mod 2: Sektör tarayıcısı
# --------------------------------------------------

elif mode == "Sektör tarayıcısı" and run_scan:
    companies = THEME_WATCHLISTS.get(theme, [])

    st.header(f"Sektör Tarayıcısı: {theme}")
    st.caption(f"{len(companies)} şirket ücretsiz kaynaklarla taranıyor.")

    results = []
    progress = st.progress(0)

    for i, (ticker_scan, name_scan) in enumerate(companies):
        with st.spinner(f"{ticker_scan} analiz ediliyor..."):
            try:
                info_scan, _ = get_stock_data(ticker_scan)

                search_names_scan = get_official_company_names(info_scan, name_scan)
                contracts_scan = get_usaspending_contracts_smart(search_names_scan)

                cik_scan, sec_name_scan, filings_scan = get_sec_recent_filings(ticker_scan)

                early_score_scan, risk_score_scan, _ = calculate_scores(
                    info=info_scan,
                    contracts=contracts_scan,
                    theme=theme,
                    filings=filings_scan,
                )

                market_cap_scan = info_scan.get("marketCap")
                contract_summary_scan = summarize_contracts(contracts_scan)

                results.append(
                    {
                        "Ticker": ticker_scan,
                        "Şirket": safe_get(info_scan, "longName", name_scan),
                        "Fiyat": format_number(info_scan.get("currentPrice")),
                        "Market Cap": format_number(market_cap_scan),
                        "Kategori": get_market_cap_category(market_cap_scan),
                        "Kontrat Sayısı": contract_summary_scan["contract_count"],
                        "Toplam Kontrat": format_number(contract_summary_scan["total_contract_value"]),
                        "Erken Sinyal": early_score_scan,
                        "Risk Skoru": risk_score_scan,
                    }
                )
            except Exception:
                results.append(
                    {
                        "Ticker": ticker_scan,
                        "Şirket": name_scan,
                        "Fiyat": "Hata",
                        "Market Cap": "Hata",
                        "Kategori": "Hata",
                        "Kontrat Sayısı": 0,
                        "Toplam Kontrat": "N/A",
                        "Erken Sinyal": 0,
                        "Risk Skoru": 0,
                    }
                )

        progress.progress((i + 1) / len(companies))

    if results:
        df = pd.DataFrame(results).sort_values("Erken Sinyal", ascending=False)

        st.dataframe(df, use_container_width=True)

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Sonuçları CSV indir",
            data=csv_data,
            file_name=f"{theme}_sector_scan_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        best = df.iloc[0]

        st.success(
            f"En yüksek Erken Sinyal Skoru: "
            f"**{best['Ticker']}** ({best['Şirket']}) — {best['Erken Sinyal']}/100"
        )

else:
    st.write("Sol menüden analiz modu seçerek başlayabilirsin.")
