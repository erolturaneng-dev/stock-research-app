import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Emerging Tech Stock Research Platform", layout="wide")

MODE_OPTIONS = ["Fırsat Tarayıcısı", "Sektör Tarayıcısı", "Tek Şirket Analizi"]

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "Fırsat Tarayıcısı"
if "mode_radio" not in st.session_state:
    st.session_state.mode_radio = st.session_state.current_mode
if "selected_single_ticker" not in st.session_state:
    st.session_state.selected_single_ticker = "BBAI"
if "auto_run_single" not in st.session_state:
    st.session_state.auto_run_single = False
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "jump_to_single_ticker" in st.session_state:
    st.session_state.selected_single_ticker = str(st.session_state.jump_to_single_ticker).upper().strip()
    st.session_state.current_mode = "Tek Şirket Analizi"
    st.session_state.mode_radio = "Tek Şirket Analizi"
    st.session_state.auto_run_single = True
    del st.session_state.jump_to_single_ticker

st.title("Emerging Tech Stock Research Platform")
st.caption(
    "AI, uzay, savunma teknolojileri, kuantum, siber güvenlik, enerji, robotik ve yarı iletken "
    "şirketlerini ücretsiz halka açık veri kaynaklarıyla tarayan araştırma platformu."
)

SECTOR_UNIVERSE = {
    "AI": [
        ("BBAI", "BigBear.ai"), ("SOUN", "SoundHound AI"), ("AISP", "Airship AI"),
        ("REKR", "Rekor Systems"), ("CXAI", "CXApp"), ("AI", "C3.ai"),
        ("PATH", "UiPath"), ("PLTR", "Palantir"), ("APP", "AppLovin"),
        ("UPST", "Upstart"), ("TEM", "Tempus AI"), ("RXRX", "Recursion Pharmaceuticals"),
        ("VERI", "Veritone"), ("RBRK", "Rubrik"), ("SNOW", "Snowflake"),
        ("DDOG", "Datadog"), ("MDB", "MongoDB"), ("ESTC", "Elastic"),
        ("SMCI", "Super Micro Computer"), ("DELL", "Dell Technologies"),
        ("HPE", "Hewlett Packard Enterprise"), ("ARM", "Arm Holdings"),
        ("AMD", "AMD"), ("AVGO", "Broadcom"), ("NVDA", "Nvidia"),
        ("MSFT", "Microsoft"), ("GOOGL", "Alphabet"), ("AMZN", "Amazon"),
        ("META", "Meta Platforms"), ("ORCL", "Oracle"), ("IBM", "IBM"),
    ],
    "Cybersecurity": [
        ("S", "SentinelOne"), ("TENB", "Tenable"), ("QLYS", "Qualys"),
        ("CYBR", "CyberArk"), ("CRWD", "CrowdStrike"), ("PANW", "Palo Alto Networks"),
        ("ZS", "Zscaler"), ("FTNT", "Fortinet"), ("NET", "Cloudflare"), ("OKTA", "Okta"),
    ],
    "Defense Technology": [
        ("KTOS", "Kratos Defense"), ("AVAV", "AeroVironment"), ("BKSY", "BlackSky Technology"),
        ("SPIR", "Spire Global"), ("RKLB", "Rocket Lab"), ("ACHR", "Archer Aviation"),
        ("JOBY", "Joby Aviation"), ("LDOS", "Leidos"), ("CACI", "CACI International"),
        ("LMT", "Lockheed Martin"), ("NOC", "Northrop Grumman"), ("RTX", "RTX Corporation"),
    ],
    "Space": [
        ("BKSY", "BlackSky Technology"), ("SPIR", "Spire Global"), ("LUNR", "Intuitive Machines"),
        ("RDW", "Redwire"), ("ASTS", "AST SpaceMobile"), ("RKLB", "Rocket Lab"),
        ("PL", "Planet Labs"), ("BA", "Boeing"), ("LMT", "Lockheed Martin"),
        ("NOC", "Northrop Grumman"),
    ],
    "Quantum": [
        ("QUBT", "Quantum Computing Inc"), ("RGTI", "Rigetti Computing"),
        ("QBTS", "D-Wave Quantum"), ("ARQQ", "Arqit Quantum"), ("IONQ", "IonQ"),
        ("IBM", "IBM"), ("GOOGL", "Alphabet"), ("MSFT", "Microsoft"), ("HON", "Honeywell"),
    ],
    "Energy Infrastructure": [
        ("STEM", "Stem Inc"), ("FLNC", "Fluence Energy"), ("SMR", "NuScale Power"),
        ("OKLO", "Oklo"), ("NNE", "Nano Nuclear Energy"), ("CEG", "Constellation Energy"),
        ("VST", "Vistra"), ("GEV", "GE Vernova"), ("ETN", "Eaton"), ("PWR", "Quanta Services"),
    ],
    "Robotics": [
        ("SERV", "Serve Robotics"), ("RR", "Richtech Robotics"), ("IRBT", "iRobot"),
        ("SYM", "Symbotic"), ("TER", "Teradyne"), ("ISRG", "Intuitive Surgical"),
        ("ROK", "Rockwell Automation"), ("ABBNY", "ABB"),
    ],
    "Semiconductor Supply Chain": [
        ("AEHR", "Aehr Test Systems"), ("ICHR", "Ichor Holdings"), ("FORM", "FormFactor"),
        ("ACLS", "Axcelis Technologies"), ("ONTO", "Onto Innovation"), ("AMAT", "Applied Materials"),
        ("LRCX", "Lam Research"), ("ASML", "ASML"), ("TSM", "Taiwan Semiconductor"),
        ("NVDA", "Nvidia"),
    ],
}

STRATEGIC_KEYWORDS = {
    "AI": ["artificial intelligence", "machine learning", "generative ai", "ai platform", "predictive analytics", "data analytics", "computer vision", "natural language", "automation"],
    "Cybersecurity": ["cybersecurity", "zero trust", "cloud security", "identity security", "network security", "endpoint security", "threat intelligence"],
    "Space": ["space", "satellite", "aerospace", "launch", "orbit", "earth observation", "space systems"],
    "Defense": ["defense", "dod", "military", "drone", "unmanned", "radar", "sensor", "surveillance", "mission systems"],
    "Quantum": ["quantum", "quantum computing", "quantum encryption", "qubit"],
    "Semiconductor": ["semiconductor", "chip", "gpu", "wafer", "foundry", "semiconductor equipment", "integrated circuit"],
    "Data Center": ["data center", "cloud", "edge computing", "server", "high performance computing", "hpc"],
    "Robotics": ["robotics", "autonomous", "automation", "industrial automation", "robotic systems"],
    "Energy Tech": ["grid", "energy storage", "battery", "nuclear", "small modular reactor", "power infrastructure", "clean energy"],
}

NAME_PREFILTER_WORDS = [
    "ai", "artificial", "intelligence", "data", "analytics", "software", "cloud", "cyber",
    "security", "space", "satellite", "aerospace", "defense", "systems", "quantum",
    "semiconductor", "robot", "automation", "energy", "nuclear", "power", "storage",
    "micro", "computer", "digital", "technology", "tech", "communications", "network",
    "sensor", "vision", "machine", "electric", "infrastructure"
]


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
        if value is None or pd.isna(value):
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
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "N/A"


def clean_ticker(ticker):
    return str(ticker).upper().strip().replace("/", "-")


def get_market_cap_category(market_cap):
    try:
        if market_cap is None or pd.isna(market_cap):
            return "Bilinmiyor"
        market_cap = float(market_cap)
        if market_cap < 50_000_000:
            return "Nano-cap"
        if market_cap < 300_000_000:
            return "Micro-cap"
        if market_cap < 2_000_000_000:
            return "Small-cap"
        if market_cap < 10_000_000_000:
            return "Mid-cap"
        if market_cap < 200_000_000_000:
            return "Large-cap"
        return "Mega-cap"
    except Exception:
        return "Bilinmiyor"


def get_cap_bucket(market_cap):
    try:
        if market_cap is None or pd.isna(market_cap):
            return "Bilinmiyor"
        market_cap = float(market_cap)
        if market_cap < 2_000_000_000:
            return "Small Cap / Erken Aday"
        if market_cap < 10_000_000_000:
            return "Mid Cap / Büyüme Adayı"
        return "Large Cap / Sektör Lideri"
    except Exception:
        return "Bilinmiyor"


@st.cache_data(ttl=86400)
def load_nasdaq_symbol_directory():
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"
    frames = []

    try:
        nasdaq_text = requests.get(nasdaq_url, timeout=20).text
        nasdaq_df = pd.read_csv(StringIO(nasdaq_text), sep="|")
        nasdaq_df = nasdaq_df[nasdaq_df["Symbol"] != "File Creation Time"]
        nasdaq_df = nasdaq_df.rename(columns={"Symbol": "Hisse Kodu", "Security Name": "Şirket Adı"})
        nasdaq_df["Borsa"] = "NASDAQ"
        frames.append(nasdaq_df[["Hisse Kodu", "Şirket Adı", "Borsa"]])
    except Exception as e:
        st.warning(f"NASDAQ sembol listesi çekilemedi: {e}")

    try:
        other_text = requests.get(other_url, timeout=20).text
        other_df = pd.read_csv(StringIO(other_text), sep="|")
        other_df = other_df[other_df["ACT Symbol"] != "File Creation Time"]
        other_df = other_df.rename(columns={"ACT Symbol": "Hisse Kodu", "Security Name": "Şirket Adı", "Exchange": "Borsa"})
        frames.append(other_df[["Hisse Kodu", "Şirket Adı", "Borsa"]])
    except Exception as e:
        st.warning(f"Diğer borsa sembol listesi çekilemedi: {e}")

    if not frames:
        return pd.DataFrame(columns=["Hisse Kodu", "Şirket Adı", "Borsa"])

    combined = pd.concat(frames, ignore_index=True)
    combined["Hisse Kodu"] = combined["Hisse Kodu"].apply(clean_ticker)
    combined = combined.drop_duplicates(subset=["Hisse Kodu"])
    combined = combined[~combined["Hisse Kodu"].str.contains(r"\$", regex=True, na=False)]
    combined = combined[~combined["Hisse Kodu"].str.contains(r"\.", regex=True, na=False)]
    combined = combined[combined["Hisse Kodu"].str.len() <= 5]
    return combined.sort_values("Hisse Kodu").reset_index(drop=True)


@st.cache_data(ttl=86400)
def load_sec_company_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "stock-research-app contact@example.com"}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        rows = []
        for _, item in data.items():
            ticker = item.get("ticker")
            title = item.get("title")
            cik = item.get("cik_str")
            if ticker and cik:
                rows.append({"Hisse Kodu": ticker.upper(), "SEC Şirket Adı": title, "CIK": str(cik).zfill(10)})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["Hisse Kodu", "SEC Şirket Adı", "CIK"])


@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "Hisse Kodu": ticker,
            "Şirket Adı": info.get("longName") or info.get("shortName"),
            "Sektör": info.get("sector"),
            "Endüstri": info.get("industry"),
            "Piyasa Değeri Raw": info.get("marketCap"),
            "Fiyat Raw": info.get("currentPrice") or info.get("regularMarketPrice"),
            "Gelir Büyümesi Raw": info.get("revenueGrowth"),
            "Kâr Marjı Raw": info.get("profitMargins"),
            "Operasyonel Marj Raw": info.get("operatingMargins"),
            "Free Cash Flow Raw": info.get("freeCashflow"),
            "Toplam Nakit Raw": info.get("totalCash"),
            "Toplam Borç Raw": info.get("totalDebt"),
            "Debt To Equity Raw": info.get("debtToEquity"),
            "Beta Raw": info.get("beta"),
            "Analist Hedef Raw": info.get("targetMeanPrice"),
            "Şirket Özeti": info.get("longBusinessSummary"),
            "Borsa": info.get("exchange"),
        }
    except Exception:
        return {
            "Hisse Kodu": ticker, "Şirket Adı": None, "Sektör": None, "Endüstri": None,
            "Piyasa Değeri Raw": None, "Fiyat Raw": None, "Gelir Büyümesi Raw": None,
            "Kâr Marjı Raw": None, "Operasyonel Marj Raw": None, "Free Cash Flow Raw": None,
            "Toplam Nakit Raw": None, "Toplam Borç Raw": None, "Debt To Equity Raw": None,
            "Beta Raw": None, "Analist Hedef Raw": None, "Şirket Özeti": None, "Borsa": None,
        }


@st.cache_data(ttl=3600)
def get_stock_history(ticker):
    try:
        return yf.Ticker(ticker).history(period="1y")
    except Exception:
        return pd.DataFrame()


def build_strategic_universe(extra_tickers=""):
    rows = []
    seen = set()
    for sector_name, companies in SECTOR_UNIVERSE.items():
        for ticker, name in companies:
            ticker = clean_ticker(ticker)
            if ticker not in seen:
                rows.append({"Hisse Kodu": ticker, "Şirket Adı": name, "Borsa": "Strategic List", "Kaynak": sector_name})
                seen.add(ticker)

    if extra_tickers.strip():
        for ticker in extra_tickers.split(","):
            ticker = clean_ticker(ticker)
            if ticker and ticker not in seen:
                rows.append({"Hisse Kodu": ticker, "Şirket Adı": ticker, "Borsa": "Manual", "Kaynak": "Manual"})
                seen.add(ticker)

    return pd.DataFrame(rows)


def build_broad_tech_universe(symbols_df, max_candidates, extra_tickers=""):
    if symbols_df.empty:
        return pd.DataFrame(columns=["Hisse Kodu", "Şirket Adı", "Borsa", "Kaynak"])
    df = symbols_df.copy()
    df["name_lower"] = df["Şirket Adı"].astype(str).str.lower()
    pattern = "|".join(NAME_PREFILTER_WORDS)
    df = df[df["name_lower"].str.contains(pattern, na=False, regex=True)]
    df = df.drop(columns=["name_lower"], errors="ignore")
    df["Kaynak"] = "Broad Tech Prefilter"
    strategic_df = build_strategic_universe(extra_tickers=extra_tickers)
    combined = pd.concat([strategic_df, df], ignore_index=True)
    combined["Hisse Kodu"] = combined["Hisse Kodu"].apply(clean_ticker)
    combined = combined.drop_duplicates(subset=["Hisse Kodu"])
    return combined.head(int(max_candidates)).reset_index(drop=True)


def is_excluded_sector(sector, industry, exclude_biotech=True):
    text = f"{sector} {industry}".lower()
    excluded = ["bank", "insurance", "reit", "real estate", "asset management", "closed-end", "fund", "shell companies", "blank check", "spac"]
    if exclude_biotech:
        excluded.extend(["biotechnology", "biotech", "pharmaceutical", "drug manufacturers", "healthcare", "medical", "diagnostics", "clinical"])
    return any(word in text for word in excluded)


def detect_strategic_tags(sector, industry, company_name, summary):
    text = f"{sector} {industry} {company_name} {summary}".lower()
    tags = []
    for tag, keywords in STRATEGIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    if not tags:
        weak_words = ["technology", "technology services", "electronic technology", "software", "hardware", "internet", "information technology"]
        if any(word in text for word in weak_words):
            tags.append("General Tech")
    return tags


def calculate_momentum_score(hist):
    score = 50
    notes = []
    if hist is None or hist.empty or len(hist) < 20:
        return score, "Momentum verisi yetersiz."
    close = hist["Close"]

    try:
        current = float(close.iloc[-1])
        start = float(close.iloc[0])
        one_year_return = (current / start) - 1
    except Exception:
        current = None
        one_year_return = None

    try:
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()
        if current is not None and len(close) >= 50 and not pd.isna(ma50.iloc[-1]):
            if current > ma50.iloc[-1]:
                score += 10
                notes.append("MA50 üzerinde")
            else:
                score -= 8
                notes.append("MA50 altında")
        if current is not None and len(close) >= 200 and not pd.isna(ma200.iloc[-1]):
            if current > ma200.iloc[-1]:
                score += 10
                notes.append("MA200 üzerinde")
            else:
                score -= 10
                notes.append("MA200 altında")
    except Exception:
        pass

    try:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_current = float(rsi.iloc[-1])
        if rsi_current > 75:
            score -= 12
            notes.append("RSI çok yüksek")
        elif rsi_current > 70:
            score -= 8
            notes.append("RSI yüksek")
        elif rsi_current < 30:
            score += 5
            notes.append("RSI düşük")
        else:
            notes.append("RSI nötr")
    except Exception:
        pass

    try:
        if one_year_return is not None:
            if one_year_return > 2:
                score -= 8
                notes.append("1 yılda çok yükselmiş")
            elif one_year_return > 0.5:
                score += 8
                notes.append("1 yıllık momentum güçlü")
            elif one_year_return < -0.4:
                score -= 5
                notes.append("1 yılda zayıf performans")
    except Exception:
        pass

    score = max(0, min(100, score))
    return score, " | ".join(notes[:4])


def calculate_opportunity_score(info, hist=None):
    score = 0
    risk_score = 0
    notes = []

    market_cap = info.get("Piyasa Değeri Raw")
    price = info.get("Fiyat Raw")
    revenue_growth = info.get("Gelir Büyümesi Raw")
    profit_margin = info.get("Kâr Marjı Raw")
    operating_margin = info.get("Operasyonel Marj Raw")
    free_cash_flow = info.get("Free Cash Flow Raw")
    total_cash = info.get("Toplam Nakit Raw")
    total_debt = info.get("Toplam Borç Raw")
    debt_to_equity = info.get("Debt To Equity Raw")
    beta = info.get("Beta Raw")
    target_mean_price = info.get("Analist Hedef Raw")

    tags = detect_strategic_tags(info.get("Sektör"), info.get("Endüstri"), info.get("Şirket Adı"), info.get("Şirket Özeti"))

    try:
        if market_cap is not None and not pd.isna(market_cap):
            market_cap = float(market_cap)
            if 50_000_000 <= market_cap <= 300_000_000:
                score += 25
                risk_score += 10
                notes.append("Micro-cap: erken aşama olabilir")
            elif 300_000_000 < market_cap <= 2_000_000_000:
                score += 32
                risk_score += 5
                notes.append("Small-cap: büyüme adayı olabilir")
            elif 2_000_000_000 < market_cap <= 10_000_000_000:
                score += 15
                notes.append("Mid-cap: büyüme potansiyeli olabilir")
            elif market_cap < 50_000_000:
                score += 5
                risk_score += 25
                notes.append("Nano-cap: çok yüksek risk")
            else:
                score -= 5
                notes.append("Large-cap: erken fırsat değil")
        else:
            risk_score += 10
    except Exception:
        pass

    try:
        if price is not None and not pd.isna(price):
            price = float(price)
            if 1 <= price <= 15:
                score += 16
                notes.append("Fiyat erken giriş aralığında")
            elif 15 < price <= 40:
                score += 9
                notes.append("Fiyat orta aralıkta")
            elif 40 < price <= 75:
                score += 3
                notes.append("Fiyat yüksek ama izlenebilir")
            elif price < 1:
                score -= 12
                risk_score += 20
                notes.append("$1 altı: delisting riski olabilir")
    except Exception:
        pass

    if tags:
        score += min(len(tags) * 6, 24)
        notes.append("Stratejik teknoloji etiketi: " + ", ".join(tags[:4]))
    else:
        risk_score += 5

    try:
        if revenue_growth is not None and not pd.isna(revenue_growth):
            revenue_growth = float(revenue_growth)
            if revenue_growth > 0.50:
                score += 20
                notes.append("Gelir büyümesi çok güçlü")
            elif revenue_growth > 0.20:
                score += 14
                notes.append("Gelir büyümesi güçlü")
            elif revenue_growth > 0.05:
                score += 7
                notes.append("Gelir büyümesi pozitif")
            elif revenue_growth < 0:
                risk_score += 10
                score -= 5
                notes.append("Gelir büyümesi negatif")
        else:
            risk_score += 5
    except Exception:
        pass

    try:
        if profit_margin is not None and not pd.isna(profit_margin):
            profit_margin = float(profit_margin)
            if profit_margin > 0.10:
                score += 8
                notes.append("Net marj pozitif")
            elif profit_margin < -0.30:
                score -= 8
                risk_score += 12
                notes.append("Net marj çok negatif")
            elif profit_margin < 0:
                risk_score += 6
    except Exception:
        pass

    try:
        if operating_margin is not None and not pd.isna(operating_margin):
            operating_margin = float(operating_margin)
            if operating_margin > 0.10:
                score += 6
            elif operating_margin < -0.30:
                risk_score += 10
    except Exception:
        pass

    try:
        if free_cash_flow is not None and not pd.isna(free_cash_flow):
            free_cash_flow = float(free_cash_flow)
            if free_cash_flow > 0:
                score += 7
                notes.append("Free cash flow pozitif")
            else:
                risk_score += 10
                notes.append("Free cash flow negatif")
    except Exception:
        pass

    try:
        if total_cash and total_debt:
            total_cash = float(total_cash)
            total_debt = float(total_debt)
            if total_cash > total_debt:
                score += 8
                notes.append("Nakit borçtan yüksek")
            elif total_debt > total_cash * 2:
                risk_score += 12
                notes.append("Borç nakite göre yüksek")
            else:
                risk_score += 5
    except Exception:
        pass

    try:
        if debt_to_equity is not None and not pd.isna(debt_to_equity):
            debt_to_equity = float(debt_to_equity)
            if debt_to_equity > 200:
                risk_score += 15
            elif debt_to_equity > 100:
                risk_score += 8
    except Exception:
        pass

    try:
        if target_mean_price and price:
            target_mean_price = float(target_mean_price)
            price = float(price)
            if target_mean_price > price * 1.5:
                score += 7
                notes.append("Analist hedefi belirgin yukarıda")
            elif target_mean_price > price * 1.15:
                score += 3
    except Exception:
        pass

    try:
        if beta is not None and not pd.isna(beta):
            beta = float(beta)
            if beta > 2.5:
                risk_score += 12
                score -= 5
                notes.append("Beta çok yüksek")
            elif beta > 1.5:
                risk_score += 6
    except Exception:
        pass

    momentum_score = 50
    momentum_note = ""
    if hist is not None:
        momentum_score, momentum_note = calculate_momentum_score(hist)
        if momentum_score >= 70:
            score += 8
        elif momentum_score <= 35:
            risk_score += 8

    opportunity_score = max(0, min(100, score))
    risk_score = max(0, min(100, risk_score))

    if opportunity_score >= 75 and risk_score <= 55:
        label = "High Potential / Derin Araştırma"
    elif opportunity_score >= 60:
        label = "Watchlist Adayı"
    elif opportunity_score >= 45:
        label = "Spekülatif / İzlenebilir"
    else:
        label = "Düşük Öncelik"

    return {
        "Opportunity Score": opportunity_score,
        "Risk Score": risk_score,
        "Research Label": label,
        "Strategic Tags": ", ".join(tags) if tags else "General / Weak Tech",
        "Momentum Score": momentum_score,
        "Momentum Notes": momentum_note,
        "Score Notes": " | ".join(notes[:6]),
    }


@st.cache_data(ttl=3600)
def get_usaspending_contracts_single_name(company_name):
    if not company_name:
        return []
    end_date = datetime.today()
    start_date = end_date - timedelta(days=730)
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    payload = {
        "filters": {
            "time_period": [{"start_date": start_date.strftime("%Y-%m-%d"), "end_date": end_date.strftime("%Y-%m-%d")}],
            "recipient_search_text": [company_name],
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Start Date", "End Date", "Awarding Agency", "Awarding Sub Agency", "Description"],
        "page": 1,
        "limit": 20,
        "sort": "Award Amount",
        "order": "desc",
    }
    try:
        response = requests.post(url, json=payload, timeout=25)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception:
        return []


def get_usaspending_contracts_smart(search_names):
    all_results = []
    seen = set()
    for name in search_names:
        for item in get_usaspending_contracts_single_name(name):
            key = f"{item.get('Award ID')}-{item.get('Recipient Name')}"
            if key not in seen:
                item["Search Name Used"] = name
                all_results.append(item)
                seen.add(key)
    return all_results


def summarize_contracts(contracts):
    summary = {"total_contract_value": 0, "contract_count": 0, "nasa_total": 0, "dod_total": 0, "doe_total": 0, "other_total": 0}
    if not contracts:
        return summary
    for c in contracts:
        amount = float(c.get("Award Amount") or 0)
        agency = str(c.get("Awarding Agency") or "").lower()
        summary["total_contract_value"] += amount
        summary["contract_count"] += 1
        if "national aeronautics" in agency or "nasa" in agency:
            summary["nasa_total"] += amount
        elif "defense" in agency or "air force" in agency or "army" in agency or "navy" in agency:
            summary["dod_total"] += amount
        elif "energy" in agency:
            summary["doe_total"] += amount
        else:
            summary["other_total"] += amount
    return summary


def format_contracts_df(contracts):
    rows = []
    for c in contracts:
        desc = c.get("Description") or "N/A"
        desc_short = desc[:90] + "..." if isinstance(desc, str) and len(desc) > 90 else desc
        rows.append({
            "Award ID": c.get("Award ID", "N/A"),
            "Alıcı": c.get("Recipient Name", "N/A"),
            "Miktar": format_number(c.get("Award Amount")),
            "Başlangıç": c.get("Start Date", "N/A"),
            "Bitiş": c.get("End Date", "N/A"),
            "Kurum": c.get("Awarding Agency", "N/A"),
            "Alt Kurum": c.get("Awarding Sub Agency", "N/A"),
            "Arama Adı": c.get("Search Name Used", "N/A"),
            "Açıklama": desc_short,
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=86400)
def get_sec_company_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "stock-research-app contact@example.com"}
    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def find_cik_for_ticker(ticker):
    data = get_sec_company_tickers()
    ticker = ticker.upper().strip()
    for _, item in data.items():
        if item.get("ticker", "").upper() == ticker:
            return str(item.get("cik_str")).zfill(10), item.get("title", "N/A")
    return None, None


def make_sec_filing_link(cik, accession):
    if not cik or not accession:
        return None
    cik_no_zero = str(int(cik))
    accession_clean = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zero}/{accession_clean}/"


@st.cache_data(ttl=3600)
def get_sec_recent_filings(ticker):
    cik, sec_name = find_cik_for_ticker(ticker)
    if not cik:
        return None, sec_name, []
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": "stock-research-app contact@example.com"}
    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        data = response.json()
        recent = data.get("filings", {}).get("recent", {})
        filings = []
        for form, date, acc in zip(recent.get("form", []), recent.get("filingDate", []), recent.get("accessionNumber", [])):
            if form in ["10-K", "10-Q", "8-K", "4"]:
                filings.append({"Form": form, "Tarih": date, "Link": make_sec_filing_link(cik, acc)})
            if len(filings) >= 12:
                break
        return cik, sec_name, filings
    except Exception:
        return cik, sec_name, []


def generate_price_scenarios(current_price, opportunity_score, risk_score, momentum_score, market_cap):
    if current_price is None:
        return None, "Fiyat verisi yok."
    try:
        current_price = float(current_price)
    except Exception:
        return None, "Fiyat verisi okunamadı."

    bucket = get_cap_bucket(market_cap)
    if risk_score >= 70:
        bear_range, base_range, bull_range = (-50, -20), (-25, 10), (10, 50)
        summary = "Risk yüksek; aşağı yönlü senaryo geniş."
    elif opportunity_score >= 75 and bucket == "Small Cap / Erken Aday":
        bear_range, base_range, bull_range = (-35, -12), (-5, 35), (40, 120)
        summary = "Küçük ölçek + yüksek fırsat skoru; yukarı potansiyel yüksek ama volatilite ciddi."
    elif opportunity_score >= 60:
        bear_range, base_range, bull_range = (-30, -10), (-5, 25), (25, 80)
        summary = "Watchlist adayı; yukarı potansiyel katalizörlere bağlı."
    elif bucket == "Large Cap / Sektör Lideri":
        bear_range, base_range, bull_range = (-25, -8), (-5, 18), (15, 40)
        summary = "Büyük şirket; erken fırsat değil, benchmark olarak değerlendirilmeli."
    else:
        bear_range, base_range, bull_range = (-35, -12), (-10, 18), (18, 55)
        summary = "Karışık görünüm; detaylı araştırma gerekir."

    if momentum_score >= 70:
        base_range = (base_range[0] + 3, base_range[1] + 5)
        bull_range = (bull_range[0] + 5, bull_range[1] + 10)
    elif momentum_score <= 35:
        bear_range = (bear_range[0] - 5, bear_range[1] - 3)
        base_range = (base_range[0] - 5, base_range[1] - 5)

    def convert(pct_range):
        low, high = pct_range
        return f"{low}% to {high}%", f"${current_price * (1 + low / 100):.2f} - ${current_price * (1 + high / 100):.2f}"

    bear_pct, bear_price = convert(bear_range)
    base_pct, base_price = convert(base_range)
    bull_pct, bull_price = convert(bull_range)

    df = pd.DataFrame([
        {"Senaryo": "Bear Case", "Yüzde Aralığı": bear_pct, "Fiyat Aralığı": bear_price, "Mantık": "Finansal risk, zayıf katalizör, piyasa düzeltmesi veya dilution riski."},
        {"Senaryo": "Base Case", "Yüzde Aralığı": base_pct, "Fiyat Aralığı": base_price, "Mantık": "Mevcut görünüm devam eder; büyük yeni katalizör gelmez."},
        {"Senaryo": "Bull Case", "Yüzde Aralığı": bull_pct, "Fiyat Aralığı": bull_price, "Mantık": "Yeni kontrat, güçlü büyüme, büyük partnerlik veya sektör ilgisi artışı."},
    ])
    return df, summary


def calculate_financial_quality_score(info):
    score = 50
    notes = []
    revenue_growth = info.get("Gelir Büyümesi Raw")
    profit_margin = info.get("Kâr Marjı Raw")
    free_cash_flow = info.get("Free Cash Flow Raw")
    total_cash = info.get("Toplam Nakit Raw")
    total_debt = info.get("Toplam Borç Raw")
    debt_to_equity = info.get("Debt To Equity Raw")

    try:
        if revenue_growth is not None and not pd.isna(revenue_growth):
            revenue_growth = float(revenue_growth)
            if revenue_growth > 0.50:
                score += 18; notes.append("Gelir büyümesi çok güçlü")
            elif revenue_growth > 0.20:
                score += 12; notes.append("Gelir büyümesi güçlü")
            elif revenue_growth > 0.05:
                score += 6; notes.append("Gelir büyümesi pozitif")
            elif revenue_growth < 0:
                score -= 10; notes.append("Gelir büyümesi negatif")
    except Exception:
        pass

    try:
        if profit_margin is not None and not pd.isna(profit_margin):
            profit_margin = float(profit_margin)
            if profit_margin > 0.10:
                score += 12; notes.append("Net marj pozitif")
            elif profit_margin < -0.30:
                score -= 15; notes.append("Net marj çok negatif")
            elif profit_margin < 0:
                score -= 8; notes.append("Şirket zarar ediyor olabilir")
    except Exception:
        pass

    try:
        if free_cash_flow is not None and not pd.isna(free_cash_flow):
            free_cash_flow = float(free_cash_flow)
            if free_cash_flow > 0:
                score += 10; notes.append("Free cash flow pozitif")
            else:
                score -= 10; notes.append("Free cash flow negatif")
    except Exception:
        pass

    try:
        if total_cash is not None and total_debt is not None:
            total_cash = float(total_cash)
            total_debt = float(total_debt)
            if total_cash > total_debt:
                score += 10; notes.append("Nakit borçtan yüksek")
            elif total_debt > total_cash * 2:
                score -= 12; notes.append("Borç nakite göre yüksek")
    except Exception:
        pass

    try:
        if debt_to_equity is not None and not pd.isna(debt_to_equity):
            debt_to_equity = float(debt_to_equity)
            if debt_to_equity > 200:
                score -= 12; notes.append("Debt/Equity çok yüksek")
            elif debt_to_equity > 100:
                score -= 6; notes.append("Debt/Equity yüksek")
    except Exception:
        pass

    return max(0, min(100, score)), " | ".join(notes[:4])


def calculate_contract_catalyst_score(info, contract_summary):
    score = 45
    notes = []
    if not contract_summary:
        return score, "Kontrat verisi bulunamadı."

    total_contract_value = contract_summary.get("total_contract_value", 0)
    contract_count = contract_summary.get("contract_count", 0)
    nasa_total = contract_summary.get("nasa_total", 0)
    dod_total = contract_summary.get("dod_total", 0)
    doe_total = contract_summary.get("doe_total", 0)
    market_cap = info.get("Piyasa Değeri Raw")

    if contract_count > 0:
        score += 10; notes.append(f"{contract_count} kontrat bulundu")
    if total_contract_value > 10_000_000:
        score += 10; notes.append("Kontrat değeri anlamlı")
    if total_contract_value > 50_000_000:
        score += 10; notes.append("Kontrat değeri güçlü")

    try:
        if market_cap is not None and not pd.isna(market_cap) and float(market_cap) > 0:
            ratio = total_contract_value / float(market_cap)
            if ratio > 0.10:
                score += 15; notes.append("Kontrat/Market Cap oranı çok güçlü")
            elif ratio > 0.03:
                score += 8; notes.append("Kontrat/Market Cap oranı pozitif")
    except Exception:
        pass

    if nasa_total > 0:
        score += 8; notes.append("NASA bağlantısı var")
    if dod_total > 0:
        score += 10; notes.append("DoD / savunma bağlantısı var")
    if doe_total > 0:
        score += 6; notes.append("DOE / enerji bağlantısı var")

    return max(0, min(100, score)), " | ".join(notes[:4])


def get_overall_score_style(score):
    if score < 40:
        return {"color": "#dc3545", "bg": "#fdecec", "label": "Zayıf / Riskli", "message": "Şirket şu an zayıf görünüyor. Riskler fırsatlardan ağır basıyor."}
    if score < 70:
        return {"color": "#f0ad4e", "bg": "#fff4dd", "label": "İzleme Listesi / Karışık", "message": "Şirket izlenebilir. Potansiyel var ama tablo henüz tam güçlü değil."}
    return {"color": "#28a745", "bg": "#eaf7ee", "label": "Güçlü Aday", "message": "Şirket derin araştırma için güçlü aday görünüyor."}


def calculate_overall_score(info, scoring, contract_summary):
    opportunity_score = float(scoring.get("Opportunity Score", 0))
    risk_score = float(scoring.get("Risk Score", 50))
    momentum_score = float(scoring.get("Momentum Score", 50))
    safety_score = max(0, min(100, 100 - risk_score))
    financial_quality_score, financial_quality_notes = calculate_financial_quality_score(info)
    catalyst_score, catalyst_notes = calculate_contract_catalyst_score(info, contract_summary)
    overall_score = int(round(max(0, min(100, opportunity_score * 0.35 + safety_score * 0.25 + momentum_score * 0.15 + financial_quality_score * 0.15 + catalyst_score * 0.10))))
    style = get_overall_score_style(overall_score)
    components_df = pd.DataFrame([
        {"Bileşen": "Opportunity Score", "Skor": round(opportunity_score, 1), "Ağırlık": "%35"},
        {"Bileşen": "Güvenlik Skoru", "Skor": round(safety_score, 1), "Ağırlık": "%25"},
        {"Bileşen": "Momentum Score", "Skor": round(momentum_score, 1), "Ağırlık": "%15"},
        {"Bileşen": "Finansal Kalite", "Skor": round(financial_quality_score, 1), "Ağırlık": "%15"},
        {"Bileşen": "Kontrat / Katalizör", "Skor": round(catalyst_score, 1), "Ağırlık": "%10"},
    ])
    detail_notes = {"financial_quality_notes": financial_quality_notes, "catalyst_notes": catalyst_notes}
    return overall_score, style, components_df, detail_notes


def create_overall_score_gauge(score):
    style = get_overall_score_style(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "/100", "font": {"size": 36}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": style["color"]},
            "steps": [
                {"range": [0, 40], "color": "#fdecec"},
                {"range": [40, 70], "color": "#fff4dd"},
                {"range": [70, 100], "color": "#eaf7ee"},
            ],
            "threshold": {"line": {"color": "#222", "width": 4}, "thickness": 0.75, "value": score},
        },
    ))
    fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
    return fig


def render_overall_score_card(score, style):
    st.markdown(
        f"""
        <div style="background-color:{style['bg']}; border:2px solid {style['color']}; border-radius:16px; padding:22px; margin-top:10px; box-shadow:0 2px 10px rgba(0,0,0,0.05);">
            <div style="font-size:14px; color:#555; margin-bottom:8px;">Genel Değerlendirme Skoru</div>
            <div style="font-size:42px; font-weight:700; color:{style['color']}; line-height:1.1;">{score}/100</div>
            <div style="font-size:24px; font-weight:600; color:{style['color']}; margin-top:6px;">{style['label']}</div>
            <div style="font-size:15px; color:#333; margin-top:12px;">{style['message']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _score_color(score):
    try:
        score = int(round(float(score)))
    except Exception:
        score = 0
    if score >= 70:
        return "#16a34a", "#dcfce7", "#166534", "Güçlü"
    if score >= 40:
        return "#eab308", "#fef9c3", "#854d0e", "Orta"
    return "#ef4444", "#fee2e2", "#991b1b", "Zayıf"


def _component_comment(name, score):
    if "Opportunity" in name:
        return "Fırsat tarafı güçlü. Derin araştırmaya değer olabilir." if score >= 70 else "Fırsat potansiyeli var ama daha fazla doğrulama gerekiyor." if score >= 40 else "Fırsat tarafı zayıf."
    if "Güvenlik" in na
