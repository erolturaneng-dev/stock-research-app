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

st.title("Emerging Tech Stock Research Platform")
st.caption(
    "AI, uzay, savunma teknolojileri, kuantum, siber güvenlik, enerji, robotik ve yarı iletken "
    "şirketlerini ücretsiz halka açık veri kaynaklarıyla tarayan araştırma platformu."
)

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
            return "Unknown"

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
        return "Unknown"


def get_cap_bucket(market_cap):
    try:
        if market_cap is None or pd.isna(market_cap):
            return "Unknown"

        market_cap = float(market_cap)

        if market_cap < 2_000_000_000:
            return "Small Cap / Early Candidates"
        elif market_cap < 10_000_000_000:
            return "Mid Cap / Growth Candidates"
        else:
            return "Large Cap / Sector Leaders"
    except Exception:
        return "Unknown"


def get_company_role(market_cap, opportunity_score, risk_score):
    bucket = get_cap_bucket(market_cap)

    if bucket == "Large Cap / Sector Leaders":
        return "Sector Leader / Benchmark"
    if risk_score >= 70:
        return "High Risk / Needs Review"
    if opportunity_score >= 70 and bucket == "Small Cap / Early Candidates":
        return "Early Candidate"
    if opportunity_score >= 60:
        return "Watchlist Candidate"
    if opportunity_score >= 45:
        return "Speculative / Monitor"
    return "Low Priority"


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
                "Symbol": "Ticker",
                "Security Name": "Company Name",
            }
        )
        nasdaq_df["Exchange"] = "NASDAQ"
        frames.append(nasdaq_df[["Ticker", "Company Name", "Exchange"]])
    except Exception as e:
        st.warning(f"NASDAQ sembol listesi çekilemedi: {e}")

    try:
        other_text = requests.get(other_url, timeout=20).text
        other_df = pd.read_csv(StringIO(other_text), sep="|")
        other_df = other_df[other_df["ACT Symbol"] != "File Creation Time"]
        other_df = other_df.rename(
            columns={
                "ACT Symbol": "Ticker",
                "Security Name": "Company Name",
                "Exchange": "Exchange",
            }
        )
        frames.append(other_df[["Ticker", "Company Name", "Exchange"]])
    except Exception as e:
        st.warning(f"Diğer borsa sembol listesi çekilemedi: {e}")

    if not frames:
        return pd.DataFrame(columns=["Ticker", "Company Name", "Exchange"])

    combined = pd.concat(frames, ignore_index=True)
    combined["Ticker"] = combined["Ticker"].apply(clean_ticker)
    combined = combined.drop_duplicates(subset=["Ticker"])
    combined = combined[~combined["Ticker"].str.contains(r"\$", regex=True, na=False)]
    combined = combined[~combined["Ticker"].str.contains(r"\.", regex=True, na=False)]
    combined = combined[combined["Ticker"].str.len() <= 5]
    combined = combined.sort_values("Ticker").reset_index(drop=True)

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
                        "Ticker": ticker.upper(),
                        "SEC Company Name": title,
                        "CIK": str(cik).zfill(10),
                    }
                )

        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=["Ticker", "SEC Company Name", "CIK"])


@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "Ticker": ticker,
            "Company Name": info.get("longName") or info.get("shortName"),
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
            "Market Cap Raw": info.get("marketCap"),
            "Price Raw": info.get("currentPrice"),
            "Revenue Growth Raw": info.get("revenueGrowth"),
            "Profit Margin Raw": info.get("profitMargins"),
            "Operating Margin Raw": info.get("operatingMargins"),
            "Free Cash Flow Raw": info.get("freeCashflow"),
            "Total Cash Raw": info.get("totalCash"),
            "Total Debt Raw": info.get("totalDebt"),
            "Debt To Equity Raw": info.get("debtToEquity"),
            "Beta Raw": info.get("beta"),
            "Target Mean Price Raw": info.get("targetMeanPrice"),
            "Summary": info.get("longBusinessSummary"),
            "Exchange": info.get("exchange"),
        }
    except Exception:
        return {
            "Ticker": ticker,
            "Company Name": None,
            "Sector": None,
            "Industry": None,
            "Market Cap Raw": None,
            "Price Raw": None,
            "Revenue Growth Raw": None,
            "Profit Margin Raw": None,
            "Operating Margin Raw": None,
            "Free Cash Flow Raw": None,
            "Total Cash Raw": None,
            "Total Debt Raw": None,
            "Debt To Equity Raw": None,
            "Beta Raw": None,
            "Target Mean Price Raw": None,
            "Summary": None,
            "Exchange": None,
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
                notes.append("MA50 üzerinde.")
            else:
                score -= 8
                notes.append("MA50 altında.")

        if current is not None and len(close) >= 200 and not pd.isna(ma200.iloc[-1]):
            if current > ma200.iloc[-1]:
                score += 10
                notes.append("MA200 üzerinde.")
            else:
                score -= 10
                notes.append("MA200 altında.")
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
            notes.append("RSI çok yüksek.")
        elif rsi_current > 70:
            score -= 8
            notes.append("RSI yüksek.")
        elif rsi_current < 30:
            score += 5
            notes.append("RSI düşük.")
        else:
            notes.append("RSI nötr.")
    except Exception:
        pass

    try:
        if one_year_return is not None:
            if one_year_return > 2:
                score -= 8
                notes.append("1 yılda çok yükselmiş.")
            elif one_year_return > 0.5:
                score += 8
                notes.append("1 yıllık momentum güçlü.")
            elif one_year_return < -0.4:
                score -= 5
                notes.append("1 yılda zayıf performans.")
    except Exception:
        pass

    score = max(0, min(100, score))
    return score, " | ".join(notes[:4])


def calculate_opportunity_score(info, hist=None):
    score = 0
    risk_score = 0
    notes = []

    market_cap = info.get("Market Cap Raw")
    price = info.get("Price Raw")
    revenue_growth = info.get("Revenue Growth Raw")
    profit_margin = info.get("Profit Margin Raw")
    operating_margin = info.get("Operating Margin Raw")
    free_cash_flow = info.get("Free Cash Flow Raw")
    total_cash = info.get("Total Cash Raw")
    total_debt = info.get("Total Debt Raw")
    debt_to_equity = info.get("Debt To Equity Raw")
    beta = info.get("Beta Raw")
    target_mean_price = info.get("Target Mean Price Raw")

    sector = info.get("Sector")
    industry = info.get("Industry")
    name = info.get("Company Name")
    summary = info.get("Summary")

    tags = detect_strategic_tags(sector, industry, name, summary)

    try:
        if market_cap is not None and not pd.isna(market_cap):
            market_cap = float(market_cap)

            if 50_000_000 <= market_cap <= 300_000_000:
                score += 25
                risk_score += 10
                notes.append("Micro-cap: erken aşama olabilir.")
            elif 300_000_000 < market_cap <= 2_000_000_000:
                score += 32
                risk_score += 5
                notes.append("Small-cap: büyüme adayı olabilir.")
            elif 2_000_000_000 < market_cap <= 10_000_000_000:
                score += 15
                notes.append("Mid-cap: büyüme potansiyeli olabilir.")
            elif market_cap < 50_000_000:
                score += 5
                risk_score += 25
                notes.append("Nano-cap: çok yüksek risk.")
            else:
                score -= 5
                notes.append("Large-cap: erken fırsat değil.")
        else:
            risk_score += 10
    except Exception:
        pass

    try:
        if price is not None and not pd.isna(price):
            price = float(price)

            if 1 <= price <= 15:
                score += 16
                notes.append("Fiyat erken giriş aralığında.")
            elif 15 < price <= 40:
                score += 9
                notes.append("Fiyat orta aralıkta.")
            elif 40 < price <= 75:
                score += 3
                notes.append("Fiyat yüksek ama izlenebilir.")
            elif price < 1:
                score -= 12
                risk_score += 20
                notes.append("$1 altı: delisting riski olabilir.")
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
                notes.append("Gelir büyümesi çok güçlü.")
            elif revenue_growth > 0.20:
                score += 14
                notes.append("Gelir büyümesi güçlü.")
            elif revenue_growth > 0.05:
                score += 7
                notes.append("Gelir büyümesi pozitif.")
            elif revenue_growth < 0:
                risk_score += 10
                score -= 5
                notes.append("Gelir büyümesi negatif.")
        else:
            risk_score += 5
    except Exception:
        pass

    try:
        if profit_margin is not None and not pd.isna(profit_margin):
            profit_margin = float(profit_margin)

            if profit_margin > 0.10:
                score += 8
                notes.append("Net marj pozitif.")
            elif profit_margin < -0.30:
                score -= 8
                risk_score += 12
                notes.append("Net marj çok negatif.")
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
                notes.append("Free cash flow pozitif.")
            else:
                risk_score += 10
                notes.append("Free cash flow negatif.")
    except Exception:
        pass

    try:
        if total_cash and total_debt:
            total_cash = float(total_cash)
            total_debt = float(total_debt)

            if total_cash > total_debt:
                score += 8
                notes.append("Nakit borçtan yüksek.")
            elif total_debt > total_cash * 2:
                risk_score += 12
                notes.append("Borç nakite göre yüksek.")
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
                notes.append("Analist hedefi belirgin yukarıda.")
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
                notes.append("Beta çok yüksek.")
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
        label = "High Potential / Deep Research"
    elif opportunity_score >= 60:
        label = "Watchlist Candidate"
    elif opportunity_score >= 45:
        label = "Speculative / Monitor"
    else:
        label = "Low Priority"

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
                "Recipient": c.get("Recipient Name", "N/A"),
                "Amount": format_number(c.get("Award Amount")),
                "Start": c.get("Start Date", "N/A"),
                "End": c.get("End Date", "N/A"),
                "Agency": c.get("Awarding Agency", "N/A"),
                "Sub Agency": c.get("Awarding Sub Agency", "N/A"),
                "Search Name": c.get("Search Name Used", "N/A"),
                "Description": desc_short,
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
                        "form": form,
                        "date": date,
                        "link": make_sec_filing_link(cik, acc),
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
    elif opportunity_score >= 75 and bucket == "Small Cap / Early Candidates":
        bear_range = (-35, -12)
        base_range = (-5, 35)
        bull_range = (40, 120)
        summary = "Küçük ölçek + yüksek fırsat skoru; yukarı potansiyel yüksek ama volatilite ciddi."
    elif opportunity_score >= 60:
        bear_range = (-30, -10)
        base_range = (-5, 25)
        bull_range = (25, 80)
        summary = "Watchlist adayı; yukarı potansiyel katalizörlere bağlı."
    elif bucket == "Large Cap / Sector Leaders":
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
                "Scenario": "Bear Case",
                "Percent Range": bear_pct,
                "Price Range": bear_price,
                "Logic": "Finansal risk, zayıf katalizör, piyasa düzeltmesi veya dilution riski.",
            },
            {
                "Scenario": "Base Case",
                "Percent Range": base_pct,
                "Price Range": base_price,
                "Logic": "Mevcut görünüm devam eder; büyük yeni katalizör gelmez.",
            },
            {
                "Scenario": "Bull Case",
                "Percent Range": bull_pct,
                "Price Range": bull_price,
                "Logic": "Yeni kontrat, güçlü büyüme, büyük partnerlik veya sektör ilgisi artışı.",
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

    revenue_growth = info.get("Revenue Growth Raw")
    profit_margin = info.get("Profit Margin Raw")
    free_cash_flow = info.get("Free Cash Flow Raw")
    total_cash = info.get("Total Cash Raw")
    total_debt = info.get("Total Debt Raw")
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
    market_cap = info.get("Market Cap Raw")

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
            {"Bileşen": "Safety Score (100 - Risk)", "Skor": round(safety_score, 1), "Ağırlık": "%25"},
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
# MAIN SIDEBAR
# ==================================================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

with st.sidebar:
    st.header("Araştırma Ayarları")

    mode = st.radio(
        "Mod seçin",
        [
            "Fırsat Tarayıcısı",
            "Sektör Tarayıcısı",
            "Tek Şirket Analizi",
        ],
        index=0,
    )

    st.markdown("---")

    if st.session_state.watchlist:
        st.subheader("Watchlist")
        for item in st.session_state.watchlist:
            st.write(f"- {item}")

        wl_df = pd.DataFrame({"Ticker": st.session_state.watchlist})
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
        "fiyat, market cap, büyüme, momentum, sektör etiketi ve finansal risk filtreleri kullanır."
    )

    with st.sidebar:
        st.markdown("### Fırsat Tarayıcısı Ayarları")

        scan_preset = st.selectbox(
            "Tarama profili",
            [
                "Dengeli Fırsat Avı",
                "Agresif Küçük Hisse Avı",
                "Daha Güvenli Small/Mid Cap",
                "AI / Defense / Space Odaklı",
                "Özel Ayarlar",
            ],
            index=0,
        )

        if scan_preset == "Dengeli Fırsat Avı":
            min_price, max_price = 1.0, 50.0
            min_cap, max_cap = 50_000_000, 5_000_000_000
            exclude_biotech = True
        elif scan_preset == "Agresif Küçük Hisse Avı":
            min_price, max_price = 0.75, 25.0
            min_cap, max_cap = 10_000_000, 2_000_000_000
            exclude_biotech = True
        elif scan_preset == "Daha Güvenli Small/Mid Cap":
            min_price, max_price = 3.0, 75.0
            min_cap, max_cap = 300_000_000, 10_000_000_000
            exclude_biotech = True
        elif scan_preset == "AI / Defense / Space Odaklı":
            min_price, max_price = 1.0, 60.0
            min_cap, max_cap = 50_000_000, 8_000_000_000
            exclude_biotech = True
        else:
            min_price = st.number_input("Minimum fiyat", min_value=0.0, value=1.0, step=0.5)
            max_price = st.number_input("Maksimum fiyat", min_value=1.0, value=50.0, step=1.0)
            min_cap = st.number_input("Minimum market cap", min_value=0, value=50_000_000, step=10_000_000)
            max_cap = st.number_input("Maksimum market cap", min_value=1, value=5_000_000_000, step=100_000_000)
            exclude_biotech = st.checkbox("Healthcare / biotech dışla", value=True)

        start_index = st.number_input(
            "Başlangıç sırası",
            min_value=0,
            max_value=12000,
            value=0,
            step=500,
            help="Liste alfabetik geldiği için farklı aralıkları sırayla tara: 0, 500, 1000, 1500..."
        )

        max_scan = st.slider(
            "Kaç ticker taransın?",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
        )

        extra_tickers = st.text_input(
            "Ek tickerlar",
            value="BBAI,SOUN,AISP,PLTR,RKLB,RDW,LUNR,QUBT,RGTI,IONQ",
            help="Bunlar taranan aralığa eklenir. Virgülle yaz."
        )

        run_opportunity_scan = st.button("Fırsatları Tara", type="primary")

    if not run_opportunity_scan:
        st.markdown("## Platform Özeti")

        st.write(
            "Bu platform; AI, uzay, savunma teknolojileri, kuantum, siber güvenlik, enerji altyapısı, "
            "robotik ve yarı iletken sektörlerindeki halka açık ABD şirketlerini araştırmak için tasarlanmıştır."
        )

        st.markdown("### Ana Modlar")

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("#### Fırsat Tarayıcısı")
            st.write(
                "BBAI veya erken dönem PLTR benzeri potansiyel teknoloji hisselerini bulmak için "
                "fiyat, market cap, büyüme, momentum, sektör etiketi ve finansal risk filtreleri kullanır."
            )

        with c2:
            st.markdown("#### Sektör Tarayıcısı")
            st.write(
                "AI, Space, Defense, Quantum, Cybersecurity, Energy, Robotics ve Semiconductor alanlarında "
                "şirketleri Small Cap, Mid Cap ve Large Cap olarak ayırır."
            )

        with c3:
            st.markdown("#### Tek Şirket Analizi")
            st.write(
                "Bir ticker için finansal durum, fiyat grafiği, momentum, kontratlar, SEC dosyaları, "
                "risk skoru ve 6-12 aylık senaryo analizi üretir."
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

        st.markdown("### Kullanılan Ücretsiz Veri Kaynakları")

        st.write(
            "- **yfinance:** fiyat, market cap, finansal metrikler ve şirket profili\n"
            "- **USAspending:** ABD hükümet kontratları, NASA / DoD / DOE bağlantıları\n"
            "- **SEC EDGAR:** 10-K, 10-Q, 8-K ve Form 4 dosyaları\n"
            "- **Nasdaq Trader / SEC ticker listeleri:** ABD borsa ticker evreni ve CIK eşleşmeleri"
        )

        st.markdown("### Hızlı Başlangıç")

        st.info(
            "Sol menüden **Fırsat Tarayıcısı** modunu seç. "
            "**Dengeli Fırsat Avı** profiliyle başla. "
            "Başlangıç sırasını 0, 500, 1000, 1500 şeklinde değiştirerek farklı ticker aralıklarını tara."
        )

        ex1, ex2 = st.columns(2)

        with ex1:
            st.markdown("#### Fırsat tarama örneği")
            st.code(
                "Mod: Fırsat Tarayıcısı\n"
                "Profil: Dengeli Fırsat Avı\n"
                "Başlangıç sırası: 0\n"
                "Kaç ticker: 500\n"
                "Ek tickerlar: BBAI,SOUN,AISP,PLTR,RKLB,RDW,LUNR,QUBT,RGTI,IONQ",
                language="text",
            )

        with ex2:
            st.markdown("#### Tek şirket analizi örneği")
            st.code(
                "Mod: Tek Şirket Analizi\n"
                "Ticker: BBAI\n"
                "Şirket adı: BigBear.ai\n"
                "Sektör: AI",
                language="text",
            )

        st.warning(
            "Bu platform yatırım tavsiyesi vermez. Sonuçlar otomatik, kural tabanlı ve ön araştırma amaçlıdır. "
            "Yatırım kararı öncesinde SEC dosyaları, bilanço, haberler, şirket sunumları ve riskler manuel doğrulanmalıdır."
        )

    if run_opportunity_scan:
        with st.spinner("Ticker listesi yükleniyor..."):
            symbols_df = load_nasdaq_symbol_directory()
            sec_df = load_sec_company_tickers()

        if symbols_df.empty:
            st.error("Ticker listesi yüklenemedi.")
        else:
            manual = []
            if extra_tickers.strip():
                for t in extra_tickers.split(","):
                    t = clean_ticker(t)
                    if t:
                        manual.append(
                            {
                                "Ticker": t,
                                "Company Name": t,
                                "Exchange": "Manual",
                            }
                        )

            scan_df = symbols_df.iloc[int(start_index): int(start_index) + int(max_scan)].copy()

            if manual:
                manual_df = pd.DataFrame(manual)
                scan_df = pd.concat([manual_df, scan_df], ignore_index=True)
                scan_df = scan_df.drop_duplicates(subset=["Ticker"])

            st.write(f"Taranacak ticker sayısı: **{len(scan_df):,}**")

            rows = []
            progress = st.progress(0)
            status = st.empty()

            total_scan = len(scan_df)

            for count, (_, row) in enumerate(scan_df.iterrows(), start=1):
                ticker = clean_ticker(row["Ticker"])
                status.write(f"Taranıyor: {ticker}")

                info = get_stock_info(ticker)
                hist = get_stock_history(ticker)

                sector = info.get("Sector")
                industry = info.get("Industry")
                company_name = info.get("Company Name") or row.get("Company Name")
                market_cap = info.get("Market Cap Raw")
                price = info.get("Price Raw")

                if sector is None and industry is None:
                    progress.progress(count / total_scan)
                    continue

                if is_excluded_sector(sector, industry, exclude_biotech=exclude_biotech):
                    progress.progress(count / total_scan)
                    continue

                tags = detect_strategic_tags(sector, industry, company_name, info.get("Summary"))

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
                    "Ticker": ticker,
                    "Company Name": company_name,
                    "Exchange": row.get("Exchange") or info.get("Exchange"),
                    "Sector": sector,
                    "Industry": industry,
                    "Strategic Tags": scoring["Strategic Tags"],
                    "Market Cap": format_number(market_cap),
                    "Market Cap Raw": market_cap,
                    "Market Cap Group": get_market_cap_category(market_cap),
                    "Price": format_number(price),
                    "Price Raw": price,
                    "Revenue Growth": format_percent(info.get("Revenue Growth Raw")),
                    "Profit Margin": format_percent(info.get("Profit Margin Raw")),
                    "Free Cash Flow": format_number(info.get("Free Cash Flow Raw")),
                    "Total Cash": format_number(info.get("Total Cash Raw")),
                    "Total Debt": format_number(info.get("Total Debt Raw")),
                    "Beta": info.get("Beta Raw"),
                    "Opportunity Score": scoring["Opportunity Score"],
                    "Risk Score": scoring["Risk Score"],
                    "Momentum Score": scoring["Momentum Score"],
                    "Research Label": scoring["Research Label"],
                    "Score Notes": scoring["Score Notes"],
                    "Summary": info.get("Summary"),
                }

                rows.append(result)

                progress.progress(count / total_scan)

            status.empty()

            if not rows:
                st.warning(
                    "Bu aralıkta filtrelere uyan aday bulunamadı. Başlangıç sırasını değiştir veya filtreleri genişlet."
                )
            else:
                df = pd.DataFrame(rows)
                df = df.merge(sec_df, on="Ticker", how="left")
                df["CIK"] = df["CIK"].fillna("N/A")
                df["SEC Company Name"] = df["SEC Company Name"].fillna("N/A")

                df = df.sort_values(
                    ["Opportunity Score", "Risk Score", "Market Cap Raw"],
                    ascending=[False, True, True],
                    na_position="last",
                )

                display_cols = [
                    "Ticker",
                    "Company Name",
                    "CIK",
                    "Exchange",
                    "Sector",
                    "Industry",
                    "Strategic Tags",
                    "Market Cap",
                    "Market Cap Group",
                    "Price",
                    "Revenue Growth",
                    "Profit Margin",
                    "Free Cash Flow",
                    "Total Cash",
                    "Total Debt",
                    "Beta",
                    "Opportunity Score",
                    "Risk Score",
                    "Momentum Score",
                    "Research Label",
                    "Score Notes",
                ]

                high_df = df[df["Opportunity Score"] >= 65].copy()
                watch_df = df[(df["Opportunity Score"] >= 50) & (df["Opportunity Score"] < 65)].copy()
                small_df = df[df["Market Cap Group"].isin(["Nano-cap", "Micro-cap", "Small-cap"])].copy()

                tab1, tab2, tab3, tab4 = st.tabs(
                    [
                        "High Potential",
                        "Watchlist",
                        "Small / Micro",
                        "All Results",
                    ]
                )

                with tab1:
                    st.subheader("High Potential / Deep Research")
                    st.caption("Opportunity Score 65+ olan adaylar. Bu liste yatırım tavsiyesi değildir; derin araştırma başlangıcıdır.")
                    if high_df.empty:
                        st.info("Yüksek skorlu aday bulunamadı.")
                    else:
                        st.dataframe(high_df[display_cols], use_container_width=True)

                with tab2:
                    st.subheader("Watchlist Candidates")
                    if watch_df.empty:
                        st.info("Watchlist adayı bulunamadı.")
                    else:
                        st.dataframe(watch_df[display_cols], use_container_width=True)

                with tab3:
                    st.subheader("Small / Micro Candidates")
                    if small_df.empty:
                        st.info("Small / micro aday bulunamadı.")
                    else:
                        st.dataframe(small_df[display_cols], use_container_width=True)

                with tab4:
                    st.subheader("All Results")
                    st.dataframe(df[display_cols], use_container_width=True)

                csv_cols = display_cols + ["Summary", "Market Cap Raw", "Price Raw"]
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
                    f"En yüksek skorlu aday: **{top['Ticker']} - {top['Company Name']}** "
                    f"Opportunity Score: **{top['Opportunity Score']}/100**, Risk Score: **{top['Risk Score']}/100**"
                )

                st.warning(
                    "Düşük fiyat tek başına fırsat değildir. Nano-cap, zarar eden ve nakit yakan şirketlerde "
                    "dilution, delisting, likidite ve manipülasyon riski yüksek olabilir."
                )

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
                        "Ticker": ticker,
                        "Company Name": info.get("Company Name") or name,
                        "Sector": info.get("Sector"),
                        "Industry": info.get("Industry"),
                        "Strategic Tags": scoring["Strategic Tags"],
                        "Market Cap": format_number(info.get("Market Cap Raw")),
                        "Market Cap Raw": info.get("Market Cap Raw"),
                        "Market Cap Group": get_cap_bucket(info.get("Market Cap Raw")),
                        "Price": format_number(info.get("Price Raw")),
                        "Revenue Growth": format_percent(info.get("Revenue Growth Raw")),
                        "Profit Margin": format_percent(info.get("Profit Margin Raw")),
                        "Opportunity Score": scoring["Opportunity Score"],
                        "Risk Score": scoring["Risk Score"],
                        "Momentum Score": scoring["Momentum Score"],
                        "Research Label": scoring["Research Label"],
                        "Score Notes": scoring["Score Notes"],
                    }
                )

            progress.progress((idx + 1) / len(companies))

        df = pd.DataFrame(rows)

        display_cols = [
            "Ticker",
            "Company Name",
            "Sector",
            "Industry",
            "Strategic Tags",
            "Market Cap",
            "Market Cap Group",
            "Price",
            "Revenue Growth",
            "Profit Margin",
            "Opportunity Score",
            "Risk Score",
            "Momentum Score",
            "Research Label",
            "Score Notes",
        ]

        small_df = df[df["Market Cap Group"] == "Small Cap / Early Candidates"].sort_values(
            "Opportunity Score", ascending=False
        )
        mid_df = df[df["Market Cap Group"] == "Mid Cap / Growth Candidates"].sort_values(
            "Opportunity Score", ascending=False
        )
        large_df = df[df["Market Cap Group"] == "Large Cap / Sector Leaders"].sort_values(
            "Market Cap Raw", ascending=False
        )

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "Small Cap / Early",
                "Mid Cap / Growth",
                "Large Cap / Leaders",
                "All",
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
            st.subheader("All Results")
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
        ticker = st.text_input("Ticker girin", value="BBAI")
        company_name_manual = st.text_input("Şirket adı girin", value="BigBear.ai")
        selected_sector = st.selectbox("Sektör seçin", list(SECTOR_UNIVERSE.keys()), index=0)
        run_single = st.button("Şirketi Analiz Et", type="primary")

    if not run_single:
        st.write("Sol menüden ticker girip analiz başlatabilirsin.")
        st.info("Örnek: BBAI, SOUN, RKLB, RDW, RGTI, QUBT, PLTR")

    if run_single:
        ticker = clean_ticker(ticker)

        with st.spinner("Şirket verileri çekiliyor..."):
            info = get_stock_info(ticker)
            hist = get_stock_history(ticker)
            scoring = calculate_opportunity_score(info, hist)

            search_names = []
            if company_name_manual.strip():
                search_names.append(company_name_manual.strip())
            if info.get("Company Name"):
                search_names.append(info.get("Company Name"))

            search_names = list(dict.fromkeys(search_names))

            contracts = get_usaspending_contracts_smart(search_names)
            contract_summary = summarize_contracts(contracts)

            cik, sec_name, filings = get_sec_recent_filings(ticker)

            scenario_df, scenario_summary = generate_price_scenarios(
                current_price=info.get("Price Raw"),
                opportunity_score=scoring["Opportunity Score"],
                risk_score=scoring["Risk Score"],
                momentum_score=scoring["Momentum Score"],
                market_cap=info.get("Market Cap Raw"),
            )

            overall_score, overall_style, overall_components_df, overall_detail_notes = calculate_overall_score(
                info=info,
                scoring=scoring,
                contract_summary=contract_summary,
            )

        company_name = info.get("Company Name") or company_name_manual or ticker

        st.subheader(f"{company_name} ({ticker})")

        if ticker not in st.session_state.watchlist:
            if st.button(f"+ Watchlist'e ekle ({ticker})"):
                st.session_state.watchlist.append(ticker)
                st.success(f"{ticker} watchlist'e eklendi.")
        else:
            st.success(f"{ticker} zaten watchlist içinde.")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Price", format_number(info.get("Price Raw")))
        c2.metric("Market Cap", format_number(info.get("Market Cap Raw")))
        c3.metric("Opportunity Score", f"{scoring['Opportunity Score']}/100")
        c4.metric("Risk Score", f"{scoring['Risk Score']}/100")
        c5.metric("Genel Skor", f"{overall_score}/100")

        c6, c7, c8 = st.columns(3)
        c6.metric("Momentum Score", f"{scoring['Momentum Score']}/100")
        c7.metric("Market Cap Group", get_cap_bucket(info.get("Market Cap Raw")))
        c8.metric("Research Label", scoring["Research Label"])

        st.markdown("### Genel Değerlendirme")

        g1, g2 = st.columns([1.2, 1])

        with g1:
            gauge_fig = create_overall_score_gauge(overall_score)
            st.plotly_chart(gauge_fig, use_container_width=True)

        with g2:
            render_overall_score_card(overall_score, overall_style)

        st.markdown("#### Skor Bileşenleri")
        st.dataframe(overall_components_df, use_container_width=True, hide_index=True)

        d1, d2 = st.columns(2)

        with d1:
            st.markdown("**Finansal kalite notları**")
            st.info(overall_detail_notes["financial_quality_notes"] or "Ek not yok")

        with d2:
            st.markdown("**Kontrat / katalizör notları**")
            st.info(overall_detail_notes["catalyst_notes"] or "Ek not yok")

        st.markdown("### Şirket Profili")
        st.write(info.get("Summary") or "Şirket özeti bulunamadı.")

        p1, p2, p3, p4 = st.columns(4)
        p1.write(f"**Sector:** {info.get('Sector')}")
        p2.write(f"**Industry:** {info.get('Industry')}")
        p3.write(f"**Strategic Tags:** {scoring['Strategic Tags']}")
        p4.write(f"**Exchange:** {info.get('Exchange')}")

        st.markdown("### Finansal Görünüm")

        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Revenue Growth", format_percent(info.get("Revenue Growth Raw")))
        f2.metric("Profit Margin", format_percent(info.get("Profit Margin Raw")))
        f3.metric("Operating Margin", format_percent(info.get("Operating Margin Raw")))
        f4.metric("Free Cash Flow", format_number(info.get("Free Cash Flow Raw")))

        f5, f6, f7, f8 = st.columns(4)
        f5.metric("Total Cash", format_number(info.get("Total Cash Raw")))
        f6.metric("Total Debt", format_number(info.get("Total Debt Raw")))
        f7.metric("Debt / Equity", safe_get(info, "Debt To Equity Raw"))
        f8.metric("Beta", safe_get(info, "Beta Raw"))

        st.markdown("### Fiyat Grafiği")

        if hist is not None and not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", name="Close"))

            if len(hist) >= 50:
                ma50 = hist["Close"].rolling(50).mean()
                fig.add_trace(go.Scatter(x=hist.index, y=ma50, mode="lines", name="MA50"))

            if len(hist) >= 200:
                ma200 = hist["Close"].rolling(200).mean()
                fig.add_trace(go.Scatter(x=hist.index, y=ma200, mode="lines", name="MA200"))

            fig.update_layout(height=420, xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Fiyat geçmişi bulunamadı.")

        st.markdown("### 6-12 Aylık Fiyat Senaryo Analizi")
        st.caption("Bu bölüm otomatik ve kural tabanlıdır. Kesin hedef fiyat veya yatırım tavsiyesi değildir.")

        if scenario_df is not None:
            st.write(scenario_summary)
            st.dataframe(scenario_df, use_container_width=True)
        else:
            st.warning(scenario_summary)

        st.markdown("### USAspending Hükümet Kontratları")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Contract Count", contract_summary["contract_count"])
        k2.metric("Total Contracts", format_number(contract_summary["total_contract_value"]))
        k3.metric("NASA Total", format_number(contract_summary["nasa_total"]))
        k4.metric("DoD Total", format_number(contract_summary["dod_total"]))

        if info.get("Market Cap Raw"):
            try:
                ratio = contract_summary["total_contract_value"] / float(info.get("Market Cap Raw"))
                st.write(f"**Contract / Market Cap:** {ratio * 100:.4f}%")
            except Exception:
                pass

        if contracts:
            st.dataframe(format_contracts_df(contracts), use_container_width=True)
        else:
            st.info("USAspending üzerinde net kontrat eşleşmesi bulunamadı.")

        st.markdown("### SEC EDGAR Son Dosyalar")

        if cik:
            st.write(f"**SEC Company:** {sec_name}")
            st.write(f"**CIK:** {cik}")

        if filings:
            filings_df = pd.DataFrame(filings)
            st.dataframe(filings_df, use_container_width=True)

            with st.expander("SEC dosyalarını aç"):
                for f in filings:
                    st.markdown(f"- **{f['form']}** | {f['date']} | [Aç]({f['link']})")
        else:
            st.info("SEC dosyası bulunamadı veya eşleşmedi.")

        st.markdown("### Skor Notları")
        st.write(f"**Score Notes:** {scoring['Score Notes']}")
        st.write(f"**Momentum Notes:** {scoring['Momentum Notes']}")

        st.markdown("### Sonuç Yorumu")

        if overall_score >= 85:
            st.success(
                "Çok güçlü aday. Şirket hem fırsat hem genel kalite açısından güçlü görünüyor. "
                "Yine de bilanço, SEC dosyaları ve haber akışı manuel doğrulanmalı."
            )
        elif overall_score >= 70:
            st.success(
                "Güçlü aday. Derin araştırmaya değer görünüyor ve watchlist içinde üst sıralarda tutulabilir."
            )
        elif overall_score >= 40:
            st.warning(
                "Karışık görünüm. Şirket izlenebilir ama tablo henüz tam güçlü değil. "
                "Özellikle finansal kalite ve risk tarafı dikkatle incelenmeli."
            )
        else:
            st.error(
                "Zayıf / riskli görünüm. Şu aşamada öncelikli aday gibi görünmüyor."
            )

else:
    st.write("Sol menüden bir mod seçerek başlayabilirsin.")
