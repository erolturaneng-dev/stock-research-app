import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(
    page_title="Emerging Tech Stock Research Platform",
    layout="wide"
)

# ==================================================
# PAGE ROUTING STATE
# ==================================================

MODE_OPTIONS = [
    "Fırsat Tarayıcısı",
    "Sektör Tarayıcısı",
    "Tek Şirket Analizi",
]

if "current_mode" not in st.session_state:
    st.session_state.current_mode = "Fırsat Tarayıcısı"

if "mode_radio" not in st.session_state:
    st.session_state.mode_radio = st.session_state.current_mode

if "selected_single_ticker" not in st.session_state:
    st.session_state.selected_single_ticker = "BBAI"

if "auto_run_single" not in st.session_state:
    st.session_state.auto_run_single = False

if "jump_to_single_ticker" in st.session_state:
    st.session_state.selected_single_ticker = str(st.session_state.jump_to_single_ticker).upper().strip()
    st.session_state.current_mode = "Tek Şirket Analizi"
    st.session_state.mode_radio = "Tek Şirket Analizi"
    st.session_state.auto_run_single = True
    del st.session_state.jump_to_single_ticker
# ==================================================
# CORE SECTOR LISTS
# ==================================================

SECTOR_UNIVERSE = {
    "AI": [
        ("BBAI", "BigBear.ai"),
        ("SOUN", "SoundHound AI"),
        ("AISP", "Airship AI"),
        ("REKR", "Rekor Systems"),
        ("CXAI", "CXApp"),
        ("AI", "C3.ai"),
        ("PATH", "UiPath"),
        ("PLTR", "Palantir"),
        ("APP", "AppLovin"),
        ("UPST", "Upstart"),
        ("TEM", "Tempus AI"),
        ("RXRX", "Recursion Pharmaceuticals"),
        ("VERI", "Veritone"),
        ("RBRK", "Rubrik"),
        ("SNOW", "Snowflake"),
        ("DDOG", "Datadog"),
        ("MDB", "MongoDB"),
        ("ESTC", "Elastic"),
        ("SMCI", "Super Micro Computer"),
        ("DELL", "Dell Technologies"),
        ("HPE", "Hewlett Packard Enterprise"),
        ("ARM", "Arm Holdings"),
        ("AMD", "AMD"),
        ("AVGO", "Broadcom"),
        ("NVDA", "Nvidia"),
        ("MSFT", "Microsoft"),
        ("GOOGL", "Alphabet"),
        ("AMZN", "Amazon"),
        ("META", "Meta Platforms"),
        ("ORCL", "Oracle"),
        ("IBM", "IBM"),
    ],
    "Cybersecurity": [
        ("S", "SentinelOne"),
        ("TENB", "Tenable"),
        ("QLYS", "Qualys"),
        ("CYBR", "CyberArk"),
        ("CRWD", "CrowdStrike"),
        ("PANW", "Palo Alto Networks"),
        ("ZS", "Zscaler"),
        ("FTNT", "Fortinet"),
        ("NET", "Cloudflare"),
        ("OKTA", "Okta"),
    ],
    "Defense Technology": [
        ("KTOS", "Kratos Defense"),
        ("AVAV", "AeroVironment"),
        ("BKSY", "BlackSky Technology"),
        ("SPIR", "Spire Global"),
        ("RKLB", "Rocket Lab"),
        ("ACHR", "Archer Aviation"),
        ("JOBY", "Joby Aviation"),
        ("LDOS", "Leidos"),
        ("CACI", "CACI International"),
        ("LMT", "Lockheed Martin"),
        ("NOC", "Northrop Grumman"),
        ("RTX", "RTX Corporation"),
    ],
    "Space": [
        ("BKSY", "BlackSky Technology"),
        ("SPIR", "Spire Global"),
        ("LUNR", "Intuitive Machines"),
        ("RDW", "Redwire"),
        ("ASTS", "AST SpaceMobile"),
        ("RKLB", "Rocket Lab"),
        ("PL", "Planet Labs"),
        ("BA", "Boeing"),
        ("LMT", "Lockheed Martin"),
        ("NOC", "Northrop Grumman"),
    ],
    "Quantum": [
        ("QUBT", "Quantum Computing Inc"),
        ("RGTI", "Rigetti Computing"),
        ("QBTS", "D-Wave Quantum"),
        ("ARQQ", "Arqit Quantum"),
        ("IONQ", "IonQ"),
        ("IBM", "IBM"),
        ("GOOGL", "Alphabet"),
        ("MSFT", "Microsoft"),
        ("HON", "Honeywell"),
    ],
    "Energy Infrastructure": [
        ("STEM", "Stem Inc"),
        ("FLNC", "Fluence Energy"),
        ("SMR", "NuScale Power"),
        ("OKLO", "Oklo"),
        ("NNE", "Nano Nuclear Energy"),
        ("CEG", "Constellation Energy"),
        ("VST", "Vistra"),
        ("GEV", "GE Vernova"),
        ("ETN", "Eaton"),
        ("PWR", "Quanta Services"),
    ],
    "Robotics": [
        ("SERV", "Serve Robotics"),
        ("RR", "Richtech Robotics"),
        ("IRBT", "iRobot"),
        ("SYM", "Symbotic"),
        ("TER", "Teradyne"),
        ("ISRG", "Intuitive Surgical"),
        ("ROK", "Rockwell Automation"),
        ("ABBNY", "ABB"),
    ],
    "Semiconductor Supply Chain": [
        ("AEHR", "Aehr Test Systems"),
        ("ICHR", "Ichor Holdings"),
        ("FORM", "FormFactor"),
        ("ACLS", "Axcelis Technologies"),
        ("ONTO", "Onto Innovation"),
        ("AMAT", "Applied Materials"),
        ("LRCX", "Lam Research"),
        ("ASML", "ASML"),
        ("TSM", "Taiwan Semiconductor"),
        ("NVDA", "Nvidia"),
    ],
}

STRATEGIC_KEYWORDS = {
    "AI": [
        "artificial intelligence", "machine learning", "generative ai",
        "ai platform", "predictive analytics", "data analytics",
        "computer vision", "natural language", "automation"
    ],
    "Cybersecurity": [
        "cybersecurity", "zero trust", "cloud security", "identity security",
        "network security", "endpoint security", "threat intelligence"
    ],
    "Space": [
        "space", "satellite", "aerospace", "launch", "orbit",
        "earth observation", "space systems"
    ],
    "Defense": [
        "defense", "dod", "military", "drone", "unmanned",
        "radar", "sensor", "surveillance", "mission systems"
    ],
    "Quantum": [
        "quantum", "quantum computing", "quantum encryption", "qubit"
    ],
    "Semiconductor": [
        "semiconductor", "chip", "gpu", "wafer", "foundry",
        "semiconductor equipment", "integrated circuit"
    ],
    "Data Center": [
        "data center", "cloud", "edge computing", "server",
        "high performance computing", "hpc"
    ],
    "Robotics": [
        "robotics", "autonomous", "automation", "industrial automation",
        "robotic systems"
    ],
    "Energy Tech": [
        "grid", "energy storage", "battery", "nuclear", "small modular reactor",
        "power infrastructure", "clean energy"
    ],
}

NAME_PREFILTER_WORDS = [
    "ai", "artificial", "intelligence", "data", "analytics", "software",
    "cloud", "cyber", "security", "space", "satellite", "aerospace",
    "defense", "systems", "quantum", "semiconductor", "robot", "automation",
    "energy", "nuclear", "power", "storage", "micro", "computer",
    "digital", "technology", "tech", "communications", "network",
    "sensor", "vision", "machine", "electric", "infrastructure"
]

# ==================================================
# FORMAT HELPERS
# ==================================================

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
    ticker = str(ticker).upper().strip()
    ticker = ticker.replace("/", "-")
    return ticker


def get_market_cap_category(market_cap):
    try:
        if market_cap is None or pd.isna(market_cap):
            return "Bilinmiyor"

        market_cap = float(market_cap)

        if market_cap < 50_000_000:
            return "Nano-cap"
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
    except Exception:
        return "Bilinmiyor"


def get_cap_bucket(market_cap):
    try:
        if market_cap is None or pd.isna(market_cap):
            return "Bilinmiyor"

        market_cap = float(market_cap)

        if market_cap < 2_000_000_000:
            return "Small Cap / Erken Aday"
        elif market_cap < 10_000_000_000:
            return "Mid Cap / Büyüme Adayı"
        else:
            return "Large Cap / Sektör Lideri"
    except Exception:
        return "Bilinmiyor"


# ==================================================
# DATA SOURCES
# ==================================================

@st.cache_data(ttl=86400)
def load_nasdaq_symbol_directory():
    nasdaq_url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
    other_url = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"

    frames = []

    try:
        nasdaq_text = requests.get(nasdaq_url, timeout=20).text
        nasdaq_df = pd.read_csv(StringIO(nasdaq_text), sep="|")
        nasdaq_df = nasdaq_df[nasdaq_df["Symbol"] != "File Creation Time"]
        nasdaq_df = nasdaq_df.rename(
            columns={
                "Symbol": "Hisse Kodu",
                "Security Name": "Şirket Adı",
            }
        )
        nasdaq_df["Borsa"] = "NASDAQ"
        frames.append(nasdaq_df[["Hisse Kodu", "Şirket Adı", "Borsa"]])
    except Exception as e:
        st.warning(f"NASDAQ sembol listesi çekilemedi: {e}")

    try:
        other_text = requests.get(other_url, timeout=20).text
        other_df = pd.read_csv(StringIO(other_text), sep="|")
        other_df = other_df[other_df["ACT Symbol"] != "File Creation Time"]
        other_df = other_df.rename(
            columns={
                "ACT Symbol": "Hisse Kodu",
                "Security Name": "Şirket Adı",
                "Exchange": "Borsa",
            }
        )
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
    combined = combined.sort_values("Hisse Kodu").reset_index(drop=True)

    return combined


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
                rows.append(
                    {
                        "Hisse Kodu": ticker.upper(),
                        "SEC Şirket Adı": title,
                        "CIK": str(cik).zfill(10),
                    }
                )

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
            "Fiyat Raw": info.get("currentPrice"),
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
            "Hisse Kodu": ticker,
            "Şirket Adı": None,
            "Sektör": None,
            "Endüstri": None,
            "Piyasa Değeri Raw": None,
            "Fiyat Raw": None,
            "Gelir Büyümesi Raw": None,
            "Kâr Marjı Raw": None,
            "Operasyonel Marj Raw": None,
            "Free Cash Flow Raw": None,
            "Toplam Nakit Raw": None,
            "Toplam Borç Raw": None,
            "Debt To Equity Raw": None,
            "Beta Raw": None,
            "Analist Hedef Raw": None,
            "Şirket Özeti": None,
            "Borsa": None,
        }


@st.cache_data(ttl=3600)
def get_stock_history(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        return hist
    except Exception:
        return pd.DataFrame()


# ==================================================
# UNIVERSE BUILDERS
# ==================================================

def build_strategic_universe(extra_tickers=""):
    rows = []
    seen = set()

    for sector_name, companies in SECTOR_UNIVERSE.items():
        for ticker, name in companies:
            ticker = clean_ticker(ticker)
            if ticker not in seen:
                rows.append(
                    {
                        "Hisse Kodu": ticker,
                        "Şirket Adı": name,
                        "Borsa": "Strategic List",
                        "Kaynak": sector_name,
                    }
                )
                seen.add(ticker)

    if extra_tickers.strip():
        for ticker in extra_tickers.split(","):
            ticker = clean_ticker(ticker)
            if ticker and ticker not in seen:
                rows.append(
                    {
                        "Hisse Kodu": ticker,
                        "Şirket Adı": ticker,
                        "Borsa": "Manual",
                        "Kaynak": "Manual",
                    }
                )
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


# ==================================================
# FILTERING + SCORING
# ==================================================

def is_excluded_sector(sector, industry, exclude_biotech=True):
    text = f"{sector} {industry}".lower()

    excluded = [
        "bank", "insurance", "reit", "real estate",
        "asset management", "closed-end", "fund",
        "shell companies", "blank check", "spac"
    ]

    if exclude_biotech:
        excluded.extend(
            [
                "biotechnology", "biotech", "pharmaceutical",
                "drug manufacturers", "healthcare", "medical",
                "diagnostics", "clinical"
            ]
        )

    return any(word in text for word in excluded)


def detect_strategic_tags(sector, industry, company_name, summary):
    text = f"{sector} {industry} {company_name} {summary}".lower()
    tags = []

    for tag, keywords in STRATEGIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)

    if not tags:
        weak_words = [
            "technology", "technology services", "electronic technology",
            "software", "hardware", "internet", "information technology"
        ]

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
        one_year_return = None
        current = None

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

    sector = info.get("Sektör")
    industry = info.get("Endüstri")
    name = info.get("Şirket Adı")
    summary = info.get("Şirket Özeti")

    tags = detect_strategic_tags(sector, industry, name, summary)

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
        tag_score = min(len(tags) * 6, 24)
        score += tag_score
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


# ==================================================
# USA SPENDING
# ==================================================

@st.cache_data(ttl=3600)
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
    seen = set()

    for name in search_names:
        results = get_usaspending_contracts_single_name(name)

        for item in results:
            award_id = item.get("Award ID")
            recipient = item.get("Recipient Name")
            key = f"{award_id}-{recipient}"

            if key not in seen:
                item["Search Name Used"] = name
                all_results.append(item)
                seen.add(key)

    return all_results


def summarize_contracts(contracts):
    summary = {
        "total_contract_value": 0,
        "contract_count": 0,
        "nasa_total": 0,
        "dod_total": 0,
        "doe_total": 0,
        "other_total": 0,
    }

    if not contracts:
        return summary

    for c in contracts:
        amount = float(c.get("Award Amount") or 0)
        agency_raw = str(c.get("Awarding Agency") or "")
        agency = agency_raw.lower()

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

        rows.append(
            {
                "Award ID": c.get("Award ID", "N/A"),
                "Alıcı": c.get("Recipient Name", "N/A"),
                "Miktar": format_number(c.get("Award Amount")),
                "Başlangıç": c.get("Start Date", "N/A"),
                "Bitiş": c.get("End Date", "N/A"),
                "Kurum": c.get("Awarding Agency", "N/A"),
                "Alt Kurum": c.get("Awarding Sub Agency", "N/A"),
                "Arama Adı": c.get("Search Name Used", "N/A"),
                "Açıklama": desc_short,
            }
        )

    return pd.DataFrame(rows)


# ==================================================
# SEC EDGAR
# ==================================================

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
            cik = str(item.get("cik_str")).zfill(10)
            return cik, item.get("title", "N/A")

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
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])

        filings = []

        for form, date, acc in zip(forms, dates, accessions):
            if form in ["10-K", "10-Q", "8-K", "4"]:
                filings.append(
                    {
                        "Form": form,
                        "Tarih": date,
                        "Link": make_sec_filing_link(cik, acc),
                    }
                )

            if len(filings) >= 12:
                break

        return cik, sec_name, filings
    except Exception:
        return cik, sec_name, []


# ==================================================
# SCENARIO ANALYSIS
# ==================================================

def generate_price_scenarios(current_price, opportunity_score, risk_score, momentum_score, market_cap):
    if current_price is None:
        return None, "Fiyat verisi yok."

    try:
        current_price = float(current_price)
    except Exception:
        return None, "Fiyat verisi okunamadı."

    bucket = get_cap_bucket(market_cap)

    if risk_score >= 70:
        bear_range = (-50, -20)
        base_range = (-25, 10)
        bull_range = (10, 50)
        summary = "Risk yüksek; aşağı yönlü senaryo geniş."
    elif opportunity_score >= 75 and bucket == "Small Cap / Erken Aday":
        bear_range = (-35, -12)
        base_range = (-5, 35)
        bull_range = (40, 120)
        summary = "Küçük ölçek + yüksek fırsat skoru; yukarı potansiyel yüksek ama volatilite ciddi."
    elif opportunity_score >= 60:
        bear_range = (-30, -10)
        base_range = (-5, 25)
        bull_range = (25, 80)
        summary = "Watchlist adayı; yukarı potansiyel katalizörlere bağlı."
    elif bucket == "Large Cap / Sektör Lideri":
        bear_range = (-25, -8)
        base_range = (-5, 18)
        bull_range = (15, 40)
        summary = "Büyük şirket; erken fırsat değil, benchmark olarak değerlendirilmeli."
    else:
        bear_range = (-35, -12)
        base_range = (-10, 18)
        bull_range = (18, 55)
        summary = "Karışık görünüm; detaylı araştırma gerekir."

    if momentum_score >= 70:
        base_range = (base_range[0] + 3, base_range[1] + 5)
        bull_range = (bull_range[0] + 5, bull_range[1] + 10)
    elif momentum_score <= 35:
        bear_range = (bear_range[0] - 5, bear_range[1] - 3)
        base_range = (base_range[0] - 5, base_range[1] - 5)

    def convert(pct_range):
        low, high = pct_range
        low_price = current_price * (1 + low / 100)
        high_price = current_price * (1 + high / 100)
        return f"{low}% to {high}%", f"${low_price:.2f} - ${high_price:.2f}"

    bear_pct, bear_price = convert(bear_range)
    base_pct, base_price = convert(base_range)
    bull_pct, bull_price = convert(bull_range)

    df = pd.DataFrame(
        [
            {
                "Senaryo": "Bear Case",
                "Yüzde Aralığı": bear_pct,
                "Fiyat Aralığı": bear_price,
                "Mantık": "Finansal risk, zayıf katalizör, piyasa düzeltmesi veya dilution riski.",
            },
            {
                "Senaryo": "Base Case",
                "Yüzde Aralığı": base_pct,
                "Fiyat Aralığı": base_price,
                "Mantık": "Mevcut görünüm devam eder; büyük yeni katalizör gelmez.",
            },
            {
                "Senaryo": "Bull Case",
                "Yüzde Aralığı": bull_pct,
                "Fiyat Aralığı": bull_price,
                "Mantık": "Yeni kontrat, güçlü büyüme, büyük partnerlik veya sektör ilgisi artışı.",
            },
        ]
    )

    return df, summary


# ==================================================
# OVERALL SCORE SYSTEM
# ==================================================

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
                score += 18
                notes.append("Gelir büyümesi çok güçlü")
            elif revenue_growth > 0.20:
                score += 12
                notes.append("Gelir büyümesi güçlü")
            elif revenue_growth > 0.05:
                score += 6
                notes.append("Gelir büyümesi pozitif")
            elif revenue_growth < 0:
                score -= 10
                notes.append("Gelir büyümesi negatif")
    except Exception:
        pass

    try:
        if profit_margin is not None and not pd.isna(profit_margin):
            profit_margin = float(profit_margin)
            if profit_margin > 0.10:
                score += 12
                notes.append("Net marj pozitif")
            elif profit_margin < -0.30:
                score -= 15
                notes.append("Net marj çok negatif")
            elif profit_margin < 0:
                score -= 8
                notes.append("Şirket zarar ediyor olabilir")
    except Exception:
        pass

    try:
        if free_cash_flow is not None and not pd.isna(free_cash_flow):
            free_cash_flow = float(free_cash_flow)
            if free_cash_flow > 0:
                score += 10
                notes.append("Free cash flow pozitif")
            else:
                score -= 10
                notes.append("Free cash flow negatif")
    except Exception:
        pass

    try:
        if total_cash is not None and total_debt is not None:
            total_cash = float(total_cash)
            total_debt = float(total_debt)

            if total_cash > total_debt:
                score += 10
                notes.append("Nakit borçtan yüksek")
            elif total_debt > total_cash * 2:
                score -= 12
                notes.append("Borç nakite göre yüksek")
    except Exception:
        pass

    try:
        if debt_to_equity is not None and not pd.isna(debt_to_equity):
            debt_to_equity = float(debt_to_equity)
            if debt_to_equity > 200:
                score -= 12
                notes.append("Debt/Equity çok yüksek")
            elif debt_to_equity > 100:
                score -= 6
                notes.append("Debt/Equity yüksek")
    except Exception:
        pass

    score = max(0, min(100, score))
    return score, " | ".join(notes[:4])


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
        score += 10
        notes.append(f"{contract_count} kontrat bulundu")

    if total_contract_value > 10_000_000:
        score += 10
        notes.append("Kontrat değeri anlamlı")
    if total_contract_value > 50_000_000:
        score += 10
        notes.append("Kontrat değeri güçlü")

    try:
        if market_cap is not None and not pd.isna(market_cap) and float(market_cap) > 0:
            ratio = total_contract_value / float(market_cap)
            if ratio > 0.10:
                score += 15
                notes.append("Kontrat/Market Cap oranı çok güçlü")
            elif ratio > 0.03:
                score += 8
                notes.append("Kontrat/Market Cap oranı pozitif")
    except Exception:
        pass

    if nasa_total > 0:
        score += 8
        notes.append("NASA bağlantısı var")
    if dod_total > 0:
        score += 10
        notes.append("DoD / savunma bağlantısı var")
    if doe_total > 0:
        score += 6
        notes.append("DOE / enerji bağlantısı var")

    score = max(0, min(100, score))
    return score, " | ".join(notes[:4])


def get_overall_score_style(score):
    if score < 40:
        return {
            "color": "#dc3545",
            "bg": "#fdecec",
            "label": "Zayıf / Riskli",
            "message": "Şirket şu an zayıf görünüyor. Riskler fırsatlardan ağır basıyor."
        }
    elif score < 70:
        return {
            "color": "#f0ad4e",
            "bg": "#fff4dd",
            "label": "İzleme Listesi / Karışık",
            "message": "Şirket izlenebilir. Potansiyel var ama tablo henüz tam güçlü değil."
        }
    else:
        return {
            "color": "#28a745",
            "bg": "#eaf7ee",
            "label": "Güçlü Aday",
            "message": "Şirket derin araştırma için güçlü aday görünüyor."
        }


def calculate_overall_score(info, scoring, contract_summary):
    opportunity_score = float(scoring.get("Opportunity Score", 0))
    risk_score = float(scoring.get("Risk Score", 50))
    momentum_score = float(scoring.get("Momentum Score", 50))
    safety_score = max(0, min(100, 100 - risk_score))

    financial_quality_score, financial_quality_notes = calculate_financial_quality_score(info)
    catalyst_score, catalyst_notes = calculate_contract_catalyst_score(info, contract_summary)

    overall_score = (
        opportunity_score * 0.35
        + safety_score * 0.25
        + momentum_score * 0.15
        + financial_quality_score * 0.15
        + catalyst_score * 0.10
    )

    overall_score = int(round(max(0, min(100, overall_score))))
    style = get_overall_score_style(overall_score)

    components_df = pd.DataFrame(
        [
            {"Bileşen": "Opportunity Score", "Skor": round(opportunity_score, 1), "Ağırlık": "%35"},
            {"Bileşen": "Güvenlik Skoru", "Skor": round(safety_score, 1), "Ağırlık": "%25"},
            {"Bileşen": "Momentum Score", "Skor": round(momentum_score, 1), "Ağırlık": "%15"},
            {"Bileşen": "Finansal Kalite", "Skor": round(financial_quality_score, 1), "Ağırlık": "%15"},
            {"Bileşen": "Kontrat / Katalizör", "Skor": round(catalyst_score, 1), "Ağırlık": "%10"},
        ]
    )

    detail_notes = {
        "financial_quality_notes": financial_quality_notes,
        "catalyst_notes": catalyst_notes,
    }

    return overall_score, style, components_df, detail_notes


def create_overall_score_gauge(score):
    style = get_overall_score_style(score)

    fig = go.Figure(
        go.Indicator(
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
                "threshold": {
                    "line": {"color": "#222", "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )

    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
    )

    return fig


def render_overall_score_card(score, style):
    st.markdown(
        f"""
        <div style="
            background-color:{style['bg']};
            border:2px solid {style['color']};
            border-radius:16px;
            padding:22px;
            margin-top:10px;
            box-shadow:0 2px 10px rgba(0,0,0,0.05);
        ">
            <div style="font-size:14px; color:#555; margin-bottom:8px;">
                Genel Değerlendirme Skoru
            </div>
            <div style="font-size:42px; font-weight:700; color:{style['color']}; line-height:1.1;">
                {score}/100
            </div>
            <div style="font-size:24px; font-weight:600; color:{style['color']}; margin-top:6px;">
                {style['label']}
            </div>
            <div style="font-size:15px; color:#333; margin-top:12px;">
                {style['message']}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# COLORED SCORE COMPONENT CARDS
# ==================================================

def _score_color(score):
    try:
        score = int(round(float(score)))
    except Exception:
        score = 0

    if score >= 70:
        return "#16a34a", "#dcfce7", "#166534", "Güçlü"
    elif score >= 40:
        return "#eab308", "#fef9c3", "#854d0e", "Orta"
    else:
        return "#ef4444", "#fee2e2", "#991b1b", "Zayıf"


def _component_comment(name, score):
    try:
        score = int(round(float(score)))
    except Exception:
        score = 0

    if "Opportunity" in name:
        if score >= 70:
            return "Fırsat tarafı güçlü. Derin araştırmaya değer olabilir."
        elif score >= 40:
            return "Fırsat potansiyeli var ama daha fazla doğrulama gerekiyor."
        return "Fırsat tarafı zayıf."

    if "Güvenlik" in name:
        if score >= 70:
            return "Risk daha kontrollü görünüyor."
        elif score >= 40:
            return "Risk seviyesi orta. Dikkatli takip edilmeli."
        return "Risk yüksek görünüyor."

    if "Momentum" in name:
        if score >= 70:
            return "Teknik görünüm ve fiyat momentumu güçlü."
        elif score >= 40:
            return "Momentum karışık / nötr."
        return "Momentum zayıf."

    if "Finansal" in name:
        if score >= 70:
            return "Finansal kalite güçlü."
        elif score >= 40:
            return "Finansal kalite karışık."
        return "Finansal kalite zayıf."

    if "Kontrat" in name:
        if score >= 70:
            return "Katalizör / kontrat tarafı güçlü."
        elif score >= 40:
            return "Katalizör tarafı orta."
        return "Katalizör desteği zayıf."

    return ""


def render_component_score_cards(components_df):
    st.markdown("#### Skor Bileşenleri")
    st.caption("Yeşil güçlü, sarı orta, kırmızı zayıf alanları gösterir.")

    cols = st.columns(2)

    for i, row in components_df.iterrows():
        name = str(row["Bileşen"])
        score = row["Skor"]
        weight = row["Ağırlık"]

        try:
            score_int = max(0, min(100, int(round(float(score)))))
        except Exception:
            score_int = 0

        color, bg, text_color, level = _score_color(score_int)
        comment = _component_comment(name, score_int)

        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="
                    background-color:{bg};
                    border:2px solid {color};
                    border-radius:14px;
                    padding:16px;
                    margin-bottom:14px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);
                ">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                        gap:10px;
                    ">
                        <div style="font-size:18px; font-weight:700; color:#111;">
                            {name}
                        </div>
                        <div style="
                            font-size:13px;
                            font-weight:700;
                            color:{text_color};
                            background:rgba(255,255,255,0.65);
                            padding:4px 10px;
                            border-radius:999px;
                            white-space:nowrap;
                        ">
                            {level} · {weight}
                        </div>
                    </div>

                    <div style="
                        font-size:34px;
                        font-weight:800;
                        color:{color};
                        margin-top:8px;
                    ">
                        {score_int}/100
                    </div>

                    <div style="
                        height:10px;
                        background-color:white;
                        border-radius:99px;
                        overflow:hidden;
                        margin:8px 0 10px 0;
                    ">
                        <div style="
                            width:{score_int}%;
                            height:10px;
                            background-color:{color};
                            border-radius:99px;
                        "></div>
                    </div>

                    <div style="
                        font-size:14px;
                        color:{text_color};
                        line-height:1.45;
                    ">
                        {comment}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ==================================================
# OPPORTUNITY RESULT CARDS
# ==================================================

def get_opportunity_card_style(opportunity_score, risk_score):
    try:
        opportunity_score = float(opportunity_score)
        risk_score = float(risk_score)
    except Exception:
        opportunity_score = 0
        risk_score = 100

    if opportunity_score >= 70 and risk_score <= 60:
        return {
            "border": "#16a34a",
            "bg": "#ecfdf3",
            "text": "#166534",
            "label": "Güçlü Fırsat",
            "emoji": "🟢",
        }
    elif opportunity_score >= 50 and risk_score <= 75:
        return {
            "border": "#eab308",
            "bg": "#fef9c3",
            "text": "#854d0e",
            "label": "İzlenebilir Aday",
            "emoji": "🟡",
        }
    else:
        return {
            "border": "#ef4444",
            "bg": "#fee2e2",
            "text": "#991b1b",
            "label": "Riskli / Zayıf",
            "emoji": "🔴",
        }


def render_opportunity_candidate_cards(df):
    st.markdown("---")
    st.markdown("## Fırsat Listesi")
    st.caption(
        "Adaylar fırsat skoruna göre sıralanır. Yeşil güçlü, sarı izlenebilir, kırmızı daha riskli/zayıf görünümü gösterir."
    )

    display_df = df.copy()
    display_df = display_df.sort_values(
        ["Opportunity Score", "Risk Score", "Piyasa Değeri Raw"],
        ascending=[False, True, True],
        na_position="last",
    ).reset_index(drop=True)

    for i, row in display_df.iterrows():
        ticker = str(row.get("Hisse Kodu", "N/A"))
        company = str(row.get("Şirket Adı", "N/A"))
        price = row.get("Hisse Fiyatı", "N/A")
        market_cap = row.get("Piyasa Değeri", "N/A")
        tags = row.get("Stratejik Etiket", "N/A")
        opportunity = row.get("Opportunity Score", 0)
        risk = row.get("Risk Score", 0)
        momentum = row.get("Momentum Score", 0)
        research_label = row.get("Araştırma Etiketi", "N/A")
        notes = row.get("Skor Notları", "")

        style = get_opportunity_card_style(opportunity, risk)

        card_html = f"""
        <div style="
            background:{style['bg']};
            border:2px solid {style['border']};
            border-radius:16px;
            padding:18px;
            margin:14px 0 8px 0;
            box-shadow:0 1px 6px rgba(0,0,0,0.06);
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:flex-start;
                gap:12px;
                flex-wrap:wrap;
            ">
                <div>
                    <div style="font-size:22px; font-weight:800; color:#111;">
                        {style['emoji']} {ticker} — {company}
                    </div>
                    <div style="font-size:14px; color:#555; margin-top:4px;">
                        {tags}
                    </div>
                </div>
                <div style="
                    background:white;
                    color:{style['text']};
                    border:1px solid {style['border']};
                    border-radius:999px;
                    padding:6px 12px;
                    font-weight:700;
                    white-space:nowrap;
                ">
                    {style['label']}
                </div>
            </div>

            <div style="
                display:grid;
                grid-template-columns:repeat(5, minmax(120px, 1fr));
                gap:12px;
                margin-top:16px;
            ">
                <div>
                    <div style="font-size:12px; color:#666;">Fiyat</div>
                    <div style="font-size:20px; font-weight:700;">{price}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#666;">Piyasa Değeri</div>
                    <div style="font-size:20px; font-weight:700;">{market_cap}</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#666;">Opportunity</div>
                    <div style="font-size:20px; font-weight:700; color:{style['text']};">{opportunity}/100</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#666;">Risk</div>
                    <div style="font-size:20px; font-weight:700;">{risk}/100</div>
                </div>
                <div>
                    <div style="font-size:12px; color:#666;">Momentum</div>
                    <div style="font-size:20px; font-weight:700;">{momentum}/100</div>
                </div>
            </div>

            <div style="margin-top:12px; font-size:14px; color:#333;">
                <b>Etiket:</b> {research_label}
            </div>

            <div style="margin-top:8px; font-size:13px; color:#555; line-height:1.45;">
                {notes}
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        if st.button(f"{ticker} için Tek Şirket Analizine Git", key=f"go_single_{ticker}_{i}"):
            st.session_state.jump_to_single_ticker = ticker
            st.rerun()


# ==================================================
# QUICK ANALYSIS RENDERER
# ==================================================

def render_quick_company_analysis(selected_ticker):
    with st.spinner(f"{selected_ticker} detaylı analiz ediliyor..."):
        selected_info = get_stock_info(selected_ticker)
        selected_hist = get_stock_history(selected_ticker)
        selected_scoring = calculate_opportunity_score(selected_info, selected_hist)

        selected_search_names = []
        if selected_info.get("Şirket Adı"):
            selected_search_names.append(selected_info.get("Şirket Adı"))

        selected_contracts = get_usaspending_contracts_smart(selected_search_names)
        selected_contract_summary = summarize_contracts(selected_contracts)

        selected_cik, selected_sec_name, selected_filings = get_sec_recent_filings(selected_ticker)

        selected_scenario_df, selected_scenario_summary = generate_price_scenarios(
            current_price=selected_info.get("Fiyat Raw"),
            opportunity_score=selected_scoring["Opportunity Score"],
            risk_score=selected_scoring["Risk Score"],
            momentum_score=selected_scoring["Momentum Score"],
            market_cap=selected_info.get("Piyasa Değeri Raw"),
        )

        selected_overall_score, selected_overall_style, selected_components_df, selected_detail_notes = calculate_overall_score(
            info=selected_info,
            scoring=selected_scoring,
            contract_summary=selected_contract_summary,
        )

    st.subheader(f"{selected_info.get('Şirket Adı') or selected_ticker} ({selected_ticker})")

    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Hisse fiyatı", format_number(selected_info.get("Fiyat Raw")))
    a2.metric("Piyasa değeri", format_number(selected_info.get("Piyasa Değeri Raw")))
    a3.metric("Opportunity", f"{selected_scoring['Opportunity Score']}/100")
    a4.metric("Risk", f"{selected_scoring['Risk Score']}/100")
    a5.metric("Genel Skor", f"{selected_overall_score}/100")

    st.markdown("### Genel Değerlendirme")

    gg1, gg2 = st.columns([1.2, 1])

    with gg1:
        selected_gauge = create_overall_score_gauge(selected_overall_score)
        st.plotly_chart(selected_gauge, use_container_width=True)

    with gg2:
        render_overall_score_card(selected_overall_score, selected_overall_style)

    render_component_score_cards(selected_components_df)

    n1, n2 = st.columns(2)

    with n1:
        st.markdown("**Finansal kalite notları**")
        st.info(selected_detail_notes["financial_quality_notes"] or "Ek not yok")

    with n2:
        st.markdown("**Kontrat / katalizör notları**")
        st.info(selected_detail_notes["catalyst_notes"] or "Ek not yok")

    st.markdown("### Şirket Profili")
    st.write(selected_info.get("Şirket Özeti") or "Şirket özeti bulunamadı.")

    p1, p2, p3, p4 = st.columns(4)
    p1.write(f"**Sektör:** {selected_info.get('Sektör')}")
    p2.write(f"**Endüstri:** {selected_info.get('Endüstri')}")
    p3.write(f"**Stratejik etiketler:** {selected_scoring['Strategic Tags']}")
    p4.write(f"**Borsa:** {selected_info.get('Borsa')}")

    st.markdown("### Finansal Görünüm")

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Gelir büyümesi", format_percent(selected_info.get("Gelir Büyümesi Raw")))
    q2.metric("Kâr marjı", format_percent(selected_info.get("Kâr Marjı Raw")))
    q3.metric("Free cash flow", format_number(selected_info.get("Free Cash Flow Raw")))
    q4.metric("Beta", safe_get(selected_info, "Beta Raw"))

    st.markdown("### 1 Yıllık Fiyat Grafiği")

    if selected_hist is not None and not selected_hist.empty:
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=selected_hist.index,
                y=selected_hist["Close"],
                mode="lines",
                name="Kapanış",
            )
        )

        if len(selected_hist) >= 50:
            ma50 = selected_hist["Close"].rolling(50).mean()
            fig2.add_trace(
                go.Scatter(
                    x=selected_hist.index,
                    y=ma50,
                    mode="lines",
                    name="MA50",
                )
            )

        if len(selected_hist) >= 200:
            ma200 = selected_hist["Close"].rolling(200).mean()
            fig2.add_trace(
                go.Scatter(
                    x=selected_hist.index,
                    y=ma200,
                    mode="lines",
                    name="MA200",
                )
            )

        fig2.update_layout(height=420, xaxis_title="Tarih", yaxis_title="Fiyat")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Fiyat geçmişi bulunamadı.")

    st.markdown("### 6-12 Aylık Senaryo")
    st.caption("Bu bölüm kesin hedef fiyat değildir; otomatik ve kural tabanlı senaryodur.")

    if selected_scenario_df is not None:
        st.write(selected_scenario_summary)
        st.dataframe(selected_scenario_df, use_container_width=True)
    else:
        st.warning(selected_scenario_summary)

    st.markdown("### Hükümet Kontratları")

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Kontrat sayısı", selected_contract_summary["contract_count"])
    h2.metric("Toplam kontrat", format_number(selected_contract_summary["total_contract_value"]))
    h3.metric("NASA", format_number(selected_contract_summary["nasa_total"]))
    h4.metric("DoD", format_number(selected_contract_summary["dod_total"]))

    if selected_contracts:
        st.dataframe(format_contracts_df(selected_contracts), use_container_width=True)
    else:
        st.info("USAspending üzerinde net kontrat eşleşmesi bulunamadı.")

    st.markdown("### SEC EDGAR Son Dosyalar")

    if selected_cik:
        st.write(f"**SEC şirket adı:** {selected_sec_name}")
        st.write(f"**CIK:** {selected_cik}")

    if selected_filings:
        st.dataframe(pd.DataFrame(selected_filings), use_container_width=True)
    else:
        st.info("SEC dosyası bulunamadı veya eşleşmedi.")

    st.markdown("### Sonuç Yorumu")

    if selected_overall_score >= 85:
        st.success(
            "Çok güçlü aday. Şirket hem fırsat hem genel kalite açısından güçlü görünüyor. "
            "Yine de bilanço, SEC dosyaları ve haber akışı manuel doğrulanmalı."
        )
    elif selected_overall_score >= 70:
        st.success(
            "Güçlü aday. Derin araştırmaya değer görünüyor ve watchlist içinde üst sıralarda tutulabilir."
        )
    elif selected_overall_score >= 40:
        st.warning(
            "Karışık görünüm. Şirket izlenebilir ama tablo henüz tam güçlü değil. "
            "Özellikle finansal kalite ve risk tarafı dikkatle incelenmeli."
        )
    else:
        st.error(
            "Zayıf / riskli görünüm. Şu aşamada öncelikli aday gibi görünmüyor."
        )


# ==================================================
# MAIN SIDEBAR
# ==================================================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

mode_options = [
    "Fırsat Tarayıcısı",
    "Sektör Tarayıcısı",
    "Tek Şirket Analizi",
]

with st.sidebar:
    st.header("Araştırma Ayarları")

    mode = st.radio(
        "Mod seçin",
        mode_options,
        index=mode_options.index(st.session_state.current_mode),
    )

    st.session_state.current_mode = mode

    st.markdown("---")

    if st.session_state.watchlist:
        st.subheader("Watchlist")
        for item in st.session_state.watchlist:
            st.write(f"- {item}")

        wl_df = pd.DataFrame({"Hisse Kodu": st.session_state.watchlist})
        st.download_button(
            "Watchlist CSV indir",
            data=wl_df.to_csv(index=False).encode("utf-8"),
            file_name="watchlist.csv",
            mime="text/csv",
        )

        if st.button("Watchlist temizle"):
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.subheader("Watchlist")
        st.caption("Henüz şirket eklenmedi.")

st.info(
    "Bu platform yatırım tavsiyesi değildir. Amaç; erken aşama teknoloji hisselerini "
    "filtrelemek, riskleri görmek ve derin araştırma adayları oluşturmaktır."
)

# ==================================================
# MODE 1: OPPORTUNITY SCANNER
# ==================================================

if mode == "Fırsat Tarayıcısı":
    st.header("Fırsat Tarayıcısı")
    st.write(
        "Bu bölüm, BBAI / erken dönem PLTR benzeri potansiyel teknoloji hisselerini bulmak için "
        "fiyat, piyasa değeri, büyüme, momentum, sektör etiketi ve finansal risk filtreleri kullanır."
    )

    with st.sidebar:
        st.markdown("### Tarama Ayarları")

        scan_scope = st.selectbox(
            "Tarama kapsamı",
            [
                "Stratejik teknoloji aday listesi",
                "Geniş ABD teknoloji taraması",
            ],
            index=0,
            help=(
                "Stratejik liste hızlıdır ve AI, uzay, savunma, kuantum, siber güvenlik, enerji, robotik "
                "ve yarı iletken adaylarını tarar. Geniş tarama ABD borsa listesinden teknolojiyle alakalı "
                "görünen daha fazla şirketi tarar ama daha yavaştır."
            )
        )

        scan_preset = st.selectbox(
            "Filtre tipi",
            [
                "Dengeli fırsat avı",
                "Agresif küçük hisse avı",
                "Daha güvenli small/mid cap",
                "AI / savunma / uzay odaklı",
                "Özel ayarlar",
            ],
            index=0,
        )

        if scan_preset == "Dengeli fırsat avı":
            min_price, max_price = 1.0, 50.0
            min_cap, max_cap = 50_000_000, 5_000_000_000
            exclude_biotech = True
        elif scan_preset == "Agresif küçük hisse avı":
            min_price, max_price = 0.75, 25.0
            min_cap, max_cap = 10_000_000, 2_000_000_000
            exclude_biotech = True
        elif scan_preset == "Daha güvenli small/mid cap":
            min_price, max_price = 3.0, 75.0
            min_cap, max_cap = 300_000_000, 10_000_000_000
            exclude_biotech = True
        elif scan_preset == "AI / savunma / uzay odaklı":
            min_price, max_price = 1.0, 60.0
            min_cap, max_cap = 50_000_000, 8_000_000_000
            exclude_biotech = True
        else:
            min_price = st.number_input("Minimum hisse fiyatı ($)", min_value=0.0, value=1.0, step=0.5)
            max_price = st.number_input("Maksimum hisse fiyatı ($)", min_value=1.0, value=50.0, step=1.0)
            min_cap = st.number_input("Minimum piyasa değeri ($)", min_value=0, value=50_000_000, step=10_000_000)
            max_cap = st.number_input("Maksimum piyasa değeri ($)", min_value=1, value=5_000_000_000, step=100_000_000)
            exclude_biotech = st.checkbox("Biotech / sağlık şirketlerini dışla", value=True)

        max_scan = st.slider(
            "Geniş taramada en fazla kaç şirket incelensin?",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            help="Bu ayar sadece geniş ABD teknoloji taramasında kullanılır."
        )

        extra_tickers = st.text_input(
            "Her zaman eklenecek hisse kodları",
            value="BBAI,SOUN,AISP,PLTR,RKLB,RDW,LUNR,QUBT,RGTI,IONQ",
            help="Özellikle takip etmek istediğin hisse kodlarını virgülle yaz."
        )

        run_opportunity_scan = st.button("Fırsatları Tara", type="primary")

    if not run_opportunity_scan:
        st.markdown("## Platform Özeti")

        st.write(
            "Bu platform; AI, uzay, savunma teknolojileri, kuantum, siber güvenlik, enerji altyapısı, "
            "robotik ve yarı iletken sektörlerindeki halka açık ABD şirketlerini araştırmak için tasarlanmıştır."
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("#### Fırsat Tarayıcısı")
            st.write(
                "Erken aşama teknoloji fırsatlarını bulmak için fiyat, piyasa değeri, büyüme, momentum, "
                "stratejik etiket ve finansal risk filtreleri kullanır."
            )

        with c2:
            st.markdown("#### Sektör Tarayıcısı")
            st.write(
                "AI, Space, Defense, Quantum, Cybersecurity, Energy, Robotics ve Semiconductor alanlarını "
                "Small Cap, Mid Cap ve Large Cap olarak ayırır."
            )

        with c3:
            st.markdown("#### Tek Şirket Analizi")
            st.write(
                "Bir hisse kodu için finansal durum, fiyat grafiği, momentum, kontratlar, SEC dosyaları "
                "ve 6-12 aylık senaryo analizi üretir."
            )

        st.markdown("### Üretilen Skorlar")

        s1, s2, s3, s4 = st.columns(4)

        with s1:
            st.metric("Opportunity Score", "0-100")
            st.caption("Şirket derin araştırmaya değer mi?")

        with s2:
            st.metric("Risk Score", "0-100")
            st.caption("Finansal, volatilite, borç ve nano-cap riskleri.")

        with s3:
            st.metric("Momentum Score", "0-100")
            st.caption("MA50, MA200, RSI ve 1 yıllık fiyat trendi.")

        with s4:
            st.metric("Genel Skor", "0-100")
            st.caption("Fırsat + risk + momentum + finansal kalite + katalizör.")

        st.info(
            "Başlamak için sol menüden **Tarama kapsamı** seç. "
            "Önerilen başlangıç: **Stratejik teknoloji aday listesi** + **Dengeli fırsat avı**."
        )

    if run_opportunity_scan:
        with st.spinner("Tarama listesi hazırlanıyor..."):
            if scan_scope == "Stratejik teknoloji aday listesi":
                scan_df = build_strategic_universe(extra_tickers=extra_tickers)
            else:
                symbols_df = load_nasdaq_symbol_directory()
                scan_df = build_broad_tech_universe(
                    symbols_df=symbols_df,
                    max_candidates=max_scan,
                    extra_tickers=extra_tickers,
                )

            sec_df = load_sec_company_tickers()

        if scan_df.empty:
            st.error("Tarama listesi oluşturulamadı.")
        else:
            st.write(f"Taranacak aday şirket sayısı: **{len(scan_df):,}**")
            st.caption(f"Tarama kapsamı: **{scan_scope}**")

            rows = []
            progress = st.progress(0)
            status = st.empty()

            total_scan = len(scan_df)

            for count, (_, row) in enumerate(scan_df.iterrows(), start=1):
                ticker = clean_ticker(row["Hisse Kodu"])
                status.write(f"İnceleniyor: {ticker}")

                info = get_stock_info(ticker)
                hist = get_stock_history(ticker)

                sector = info.get("Sektör")
                industry = info.get("Endüstri")
                company_name = info.get("Şirket Adı") or row.get("Şirket Adı")
                market_cap = info.get("Piyasa Değeri Raw")
                price = info.get("Fiyat Raw")

                if sector is None and industry is None:
                    progress.progress(count / total_scan)
                    continue

                if is_excluded_sector(sector, industry, exclude_biotech=exclude_biotech):
                    progress.progress(count / total_scan)
                    continue

                tags = detect_strategic_tags(sector, industry, company_name, info.get("Şirket Özeti"))

                if not tags:
                    progress.progress(count / total_scan)
                    continue

                try:
                    if price is None or pd.isna(price):
                        progress.progress(count / total_scan)
                        continue

                    price_float = float(price)
                    if price_float < min_price or price_float > max_price:
                        progress.progress(count / total_scan)
                        continue
                except Exception:
                    progress.progress(count / total_scan)
                    continue

                try:
                    if market_cap is None or pd.isna(market_cap):
                        progress.progress(count / total_scan)
                        continue

                    cap_float = float(market_cap)
                    if cap_float < min_cap or cap_float > max_cap:
                        progress.progress(count / total_scan)
                        continue
                except Exception:
                    progress.progress(count / total_scan)
                    continue

                scoring = calculate_opportunity_score(info, hist)

                result = {
                    "Hisse Kodu": ticker,
                    "Şirket Adı": company_name,
                    "CIK": "N/A",
                    "Borsa": row.get("Borsa") or info.get("Borsa"),
                    "Kaynak": row.get("Kaynak", scan_scope),
                    "Sektör": sector,
                    "Endüstri": industry,
                    "Stratejik Etiket": scoring["Strategic Tags"],
                    "Piyasa Değeri": format_number(market_cap),
                    "Piyasa Değeri Raw": market_cap,
                    "Piyasa Değeri Grubu": get_market_cap_category(market_cap),
                    "Hisse Fiyatı": format_number(price),
                    "Fiyat Raw": price,
                    "Gelir Büyümesi": format_percent(info.get("Gelir Büyümesi Raw")),
                    "Kâr Marjı": format_percent(info.get("Kâr Marjı Raw")),
                    "Free Cash Flow": format_number(info.get("Free Cash Flow Raw")),
                    "Toplam Nakit": format_number(info.get("Toplam Nakit Raw")),
                    "Toplam Borç": format_number(info.get("Toplam Borç Raw")),
                    "Beta": info.get("Beta Raw"),
                    "Opportunity Score": scoring["Opportunity Score"],
                    "Risk Score": scoring["Risk Score"],
                    "Momentum Score": scoring["Momentum Score"],
                    "Araştırma Etiketi": scoring["Research Label"],
                    "Skor Notları": scoring["Score Notes"],
                    "Şirket Özeti": info.get("Şirket Özeti"),
                }

                rows.append(result)
                progress.progress(count / total_scan)

            status.empty()

            if not rows:
                st.warning(
                    "Bu taramada filtrelere uyan aday bulunamadı. Filtreleri genişletmeyi veya diğer tarama kapsamını seçmeyi deneyebilirsin."
                )
            else:
                df = pd.DataFrame(rows)
                df = df.merge(sec_df, on="Hisse Kodu", how="left", suffixes=("", "_sec"))

                if "CIK_sec" in df.columns:
                    df["CIK"] = df["CIK_sec"].fillna(df["CIK"])
                    df = df.drop(columns=["CIK_sec"], errors="ignore")

                df["CIK"] = df["CIK"].fillna("N/A")

                df = df.sort_values(
                    ["Opportunity Score", "Risk Score", "Piyasa Değeri Raw"],
                    ascending=[False, True, True],
                    na_position="last",
                )

                display_cols = [
                    "Hisse Kodu",
                    "Şirket Adı",
                    "CIK",
                    "Borsa",
                    "Kaynak",
                    "Sektör",
                    "Endüstri",
                    "Stratejik Etiket",
                    "Piyasa Değeri",
                    "Piyasa Değeri Grubu",
                    "Hisse Fiyatı",
                    "Gelir Büyümesi",
                    "Kâr Marjı",
                    "Free Cash Flow",
                    "Toplam Nakit",
                    "Toplam Borç",
                    "Beta",
                    "Opportunity Score",
                    "Risk Score",
                    "Momentum Score",
                    "Araştırma Etiketi",
                    "Skor Notları",
                ]

                high_df = df[df["Opportunity Score"] >= 65].copy()
                watch_df = df[(df["Opportunity Score"] >= 50) & (df["Opportunity Score"] < 65)].copy()
                small_df = df[df["Piyasa Değeri Grubu"].isin(["Nano-cap", "Micro-cap", "Small-cap"])].copy()

                tab1, tab2, tab3, tab4 = st.tabs(
                    [
                        "High Potential",
                        "Watchlist",
                        "Small / Micro",
                        "Tüm Sonuçlar",
                    ]
                )

                with tab1:
                    st.subheader("High Potential / Derin Araştırma")
                    st.caption("Opportunity Score 65+ olan adaylar. Bu liste yatırım tavsiyesi değildir; derin araştırma başlangıcıdır.")
                    if high_df.empty:
                        st.info("Yüksek skorlu aday bulunamadı.")
                    else:
                        st.dataframe(high_df[display_cols], use_container_width=True)

                with tab2:
                    st.subheader("Watchlist Adayları")
                    if watch_df.empty:
                        st.info("Watchlist adayı bulunamadı.")
                    else:
                        st.dataframe(watch_df[display_cols], use_container_width=True)

                with tab3:
                    st.subheader("Small / Micro Adaylar")
                    if small_df.empty:
                        st.info("Small / micro aday bulunamadı.")
                    else:
                        st.dataframe(small_df[display_cols], use_container_width=True)

                with tab4:
                    st.subheader("Tüm Sonuçlar")
                    st.dataframe(df[display_cols], use_container_width=True)

                csv_cols = display_cols + ["Şirket Özeti", "Piyasa Değeri Raw", "Fiyat Raw"]
                csv_data = df[csv_cols].to_csv(index=False).encode("utf-8")

                st.download_button(
                    label="Adayları CSV indir",
                    data=csv_data,
                    file_name=f"opportunity_candidates_{datetime.today().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )

                st.success(f"Bulunan aday sayısı: {len(df)}")

                top = df.iloc[0]
                st.info(
                    f"En yüksek skorlu aday: **{top['Hisse Kodu']} - {top['Şirket Adı']}** "
                    f"Opportunity Score: **{top['Opportunity Score']}/100**, Risk Score: **{top['Risk Score']}/100**"
                )

                st.warning(
                    "Düşük fiyat tek başına fırsat değildir. Nano-cap, zarar eden ve nakit yakan şirketlerde "
                    "dilution, delisting, likidite ve manipülasyon riski yüksek olabilir."
                )

                render_opportunity_candidate_cards(df)


# ==================================================
# MODE 2: SECTOR SCANNER
# ==================================================

elif mode == "Sektör Tarayıcısı":
    st.header("Sektör Tarayıcısı")

    with st.sidebar:
        selected_sector = st.selectbox("Sektör seçin", list(SECTOR_UNIVERSE.keys()), index=0)
        run_sector_scan = st.button("Sektörü Tara", type="primary")

    if not run_sector_scan:
        st.write("Sol menüden sektör seçip tarama başlatabilirsin.")

    if run_sector_scan:
        companies = SECTOR_UNIVERSE.get(selected_sector, [])
        rows = []
        progress = st.progress(0)

        for idx, (ticker, name) in enumerate(companies):
            with st.spinner(f"{ticker} analiz ediliyor..."):
                info = get_stock_info(ticker)
                hist = get_stock_history(ticker)
                scoring = calculate_opportunity_score(info, hist)

                rows.append(
                    {
                        "Hisse Kodu": ticker,
                        "Şirket Adı": info.get("Şirket Adı") or name,
                        "Sektör": info.get("Sektör"),
                        "Endüstri": info.get("Endüstri"),
                        "Stratejik Etiket": scoring["Strategic Tags"],
                        "Piyasa Değeri": format_number(info.get("Piyasa Değeri Raw")),
                        "Piyasa Değeri Raw": info.get("Piyasa Değeri Raw"),
                        "Piyasa Değeri Grubu": get_cap_bucket(info.get("Piyasa Değeri Raw")),
                        "Hisse Fiyatı": format_number(info.get("Fiyat Raw")),
                        "Gelir Büyümesi": format_percent(info.get("Gelir Büyümesi Raw")),
                        "Kâr Marjı": format_percent(info.get("Kâr Marjı Raw")),
                        "Opportunity Score": scoring["Opportunity Score"],
                        "Risk Score": scoring["Risk Score"],
                        "Momentum Score": scoring["Momentum Score"],
                        "Araştırma Etiketi": scoring["Research Label"],
                        "Skor Notları": scoring["Score Notes"],
                    }
                )

            progress.progress((idx + 1) / len(companies))

        df = pd.DataFrame(rows)

        display_cols = [
            "Hisse Kodu",
            "Şirket Adı",
            "Sektör",
            "Endüstri",
            "Stratejik Etiket",
            "Piyasa Değeri",
            "Piyasa Değeri Grubu",
            "Hisse Fiyatı",
            "Gelir Büyümesi",
            "Kâr Marjı",
            "Opportunity Score",
            "Risk Score",
            "Momentum Score",
            "Araştırma Etiketi",
            "Skor Notları",
        ]

        small_df = df[df["Piyasa Değeri Grubu"] == "Small Cap / Erken Aday"].sort_values(
            "Opportunity Score", ascending=False
        )
        mid_df = df[df["Piyasa Değeri Grubu"] == "Mid Cap / Büyüme Adayı"].sort_values(
            "Opportunity Score", ascending=False
        )
        large_df = df[df["Piyasa Değeri Grubu"] == "Large Cap / Sektör Lideri"].sort_values(
            "Piyasa Değeri Raw", ascending=False
        )

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "Small Cap / Early",
                "Mid Cap / Growth",
                "Large Cap / Leaders",
                "Tümü",
            ]
        )

        with tab1:
            st.subheader("Small Cap / Early Candidates")
            st.dataframe(small_df[display_cols], use_container_width=True)

        with tab2:
            st.subheader("Mid Cap / Growth Candidates")
            st.dataframe(mid_df[display_cols], use_container_width=True)

        with tab3:
            st.subheader("Large Cap / Sector Leaders")
            st.caption("Bunlar erken fırsat değil, sektör lideri / benchmark olarak kullanılmalı.")
            st.dataframe(large_df[display_cols], use_container_width=True)

        with tab4:
            st.subheader("Tüm Sonuçlar")
            st.dataframe(
                df.sort_values("Opportunity Score", ascending=False)[display_cols],
                use_container_width=True,
            )

        st.download_button(
            label="Sektör sonuçlarını CSV indir",
            data=df[display_cols].to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_sector}_sector_scan_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )


# ==================================================
# MODE 3: SINGLE COMPANY ANALYSIS
# ==================================================

elif mode == "Tek Şirket Analizi":
    st.header("Tek Şirket Analizi")

    with st.sidebar:
        ticker = st.text_input(
            "Hisse kodu girin",
            value=st.session_state.selected_single_ticker,
        )
        company_name_manual = st.text_input("Şirket adı girin", value="")
        selected_sector = st.selectbox("Sektör seçin", list(SECTOR_UNIVERSE.keys()), index=0)
        run_single = st.button("Şirketi Analiz Et", type="primary")

    should_auto_run = st.session_state.auto_run_single
    st.session_state.auto_run_single = False

    if not run_single and not should_auto_run:
        st.write("Sol menüden hisse kodu girip analiz başlatabilirsin.")
        st.info("Örnek: BBAI, SOUN, RKLB, RDW, RGTI, QUBT, PLTR")

    if run_single or should_auto_run:
        ticker = clean_ticker(ticker)
        st.session_state.selected_single_ticker = ticker
        render_quick_company_analysis(ticker)
