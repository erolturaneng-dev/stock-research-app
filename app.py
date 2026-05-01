import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Emerging Tech Stock Research Platform", layout="wide")

st.title("Emerging Tech Stock Research Platform")
st.caption(
    "AI, Space, Defense, Quantum, Cybersecurity, Energy and Semiconductor stock discovery "
    "using free public data sources: yfinance + USAspending + SEC EDGAR."
)

# --------------------------------------------------
# Sektör evrenleri
# --------------------------------------------------

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

# --------------------------------------------------
# Genel yardımcı fonksiyonlar
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


def get_cap_bucket(market_cap):
    if market_cap is None:
        return "Unknown"

    try:
        market_cap = float(market_cap)
    except Exception:
        return "Unknown"

    if market_cap < 2_000_000_000:
        return "Small Cap / Early Candidates"
    elif market_cap < 10_000_000_000:
        return "Mid Cap / Growth Candidates"
    else:
        return "Large Cap / Sector Leaders"


def get_company_role(market_cap, priority_score, risk_score):
    bucket = get_cap_bucket(market_cap)

    if bucket == "Large Cap / Sector Leaders":
        return "Sector Leader / Benchmark"
    if risk_score >= 70:
        return "High Risk / Needs Review"
    if priority_score >= 70 and bucket == "Small Cap / Early Candidates":
        return "Early Candidate"
    if priority_score >= 60 and bucket == "Mid Cap / Growth Candidates":
        return "Growth Candidate"
    if priority_score >= 50:
        return "Watchlist Candidate"
    return "Low Priority / Monitor"


@st.cache_data(ttl=3600)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist
    except Exception:
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
        return None, None, None, None

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

    try:
        one_year_return = (close.iloc[-1] / close.iloc[0]) - 1
    except Exception:
        one_year_return = None

    return ma50, ma200, rsi_current, one_year_return


def calculate_momentum_score(hist):
    ma50, ma200, rsi_current, one_year_return = calculate_technical_indicators(hist)

    score = 50
    notes = []

    if hist.empty:
        return 50, ["Fiyat geçmişi bulunamadı; momentum nötr varsayıldı."]

    try:
        current_price = float(hist["Close"].iloc[-1])

        if ma50 is not None and not pd.isna(ma50.iloc[-1]):
            if current_price > ma50.iloc[-1]:
                score += 10
                notes.append("Fiyat MA50 üzerinde; kısa/orta vadeli momentum pozitif olabilir.")
            else:
                score -= 8
                notes.append("Fiyat MA50 altında; kısa/orta vadeli momentum zayıf olabilir.")

        if ma200 is not None and not pd.isna(ma200.iloc[-1]):
            if current_price > ma200.iloc[-1]:
                score += 10
                notes.append("Fiyat MA200 üzerinde; uzun vadeli trend pozitif olabilir.")
            else:
                score -= 10
                notes.append("Fiyat MA200 altında; uzun vadeli trend zayıf olabilir.")
    except Exception:
        pass

    if rsi_current is not None:
        if rsi_current > 75:
            score -= 12
            notes.append("RSI çok yüksek; aşırı alım riski olabilir.")
        elif rsi_current > 70:
            score -= 8
            notes.append("RSI yüksek; kısa vadede düzeltme riski olabilir.")
        elif rsi_current < 30:
            score += 6
            notes.append("RSI düşük; aşırı satım sonrası tepki ihtimali olabilir.")
        else:
            notes.append("RSI nötr bölgede.")

    if one_year_return is not None:
        if one_year_return > 2:
            score -= 10
            notes.append("Son 1 yılda çok güçlü yükseliş var; beklentiler fiyata yansımış olabilir.")
        elif one_year_return > 0.5:
            score += 5
            notes.append("Son 1 yılda güçlü fiyat momentumu var.")
        elif one_year_return < -0.4:
            score -= 5
            notes.append("Son 1 yılda ciddi düşüş var; piyasa güveni zayıf olabilir.")

    score = max(0, min(100, score))
    return score, notes


# --------------------------------------------------
# USAspending
# --------------------------------------------------

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
        }

    total = 0
    nasa_total = 0
    dod_total = 0
    doe_total = 0
    other_total = 0

    for contract in contracts:
        amount = float(contract.get("Award Amount") or 0)
        agency_raw = str(contract.get("Awarding Agency") or "")
        agency = agency_raw.lower()

        total += amount

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

@st.cache_data(ttl=86400)
def get_sec_company_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {
        "User-Agent": "stock-research-app contact@example.com"
    }

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

    except Exception:
        return cik, sec_name, []


def get_insider_form4_filings(filings):
    return [f for f in filings if f.get("form") == "4"][:5]


# --------------------------------------------------
# Skorlar
# --------------------------------------------------

def calculate_financial_health_score(info):
    score = 50
    notes = []

    revenue_growth = info.get("revenueGrowth")
    profit_margins = info.get("profitMargins")
    operating_margins = info.get("operatingMargins")
    free_cashflow = info.get("freeCashflow")
    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")
    debt_to_equity = info.get("debtToEquity")

    if revenue_growth is not None:
        if revenue_growth > 0.30:
            score += 15
            notes.append("Gelir büyümesi güçlü.")
        elif revenue_growth > 0.10:
            score += 8
            notes.append("Gelir büyümesi pozitif.")
        elif revenue_growth < 0:
            score -= 12
            notes.append("Gelir büyümesi negatif.")

    if profit_margins is not None:
        if profit_margins > 0.10:
            score += 12
            notes.append("Net kâr marjı pozitif ve sağlıklı görünüyor.")
        elif profit_margins < 0:
            score -= 15
            notes.append("Net kâr marjı negatif; kârlılık riski var.")

    if operating_margins is not None:
        if operating_margins > 0.10:
            score += 10
            notes.append("Operasyonel marj pozitif.")
        elif operating_margins < 0:
            score -= 10
            notes.append("Operasyonel marj negatif.")

    if free_cashflow is not None:
        if free_cashflow > 0:
            score += 10
            notes.append("Free cash flow pozitif.")
        else:
            score -= 15
            notes.append("Free cash flow negatif; nakit yakma riski olabilir.")

    if total_cash and total_debt:
        if total_cash > total_debt:
            score += 8
            notes.append("Nakit borçtan yüksek.")
        elif total_debt > total_cash:
            score -= 10
            notes.append("Borç nakitten yüksek.")

    if debt_to_equity is not None:
        try:
            if debt_to_equity > 200:
                score -= 15
                notes.append("Debt/equity çok yüksek.")
            elif debt_to_equity > 100:
                score -= 8
                notes.append("Debt/equity yüksek.")
        except Exception:
            pass

    score = max(0, min(100, score))
    return score, notes


def calculate_catalyst_score(contracts, filings, sector):
    score = 30
    notes = []

    contract_summary = summarize_contracts(contracts)

    if contracts:
        score += 20
        notes.append("Hükümet kontratı/eşleşmesi bulundu.")

        if contract_summary["nasa_total"] > 0:
            score += 10
            notes.append("NASA bağlantılı kontrat var.")

        if contract_summary["dod_total"] > 0:
            score += 10
            notes.append("DoD / savunma bağlantılı kontrat var.")

        if contract_summary["doe_total"] > 0:
            score += 8
            notes.append("DOE / enerji bağlantılı kontrat var.")

    recent_8k = [f for f in filings if f.get("form") == "8-K"]
    if recent_8k:
        score += 5
        notes.append("Son SEC listesinde 8-K dosyaları var; güncel şirket gelişmeleri izlenebilir.")

    if sector in ["AI", "Quantum", "Space", "Defense Technology", "Cybersecurity", "Energy Infrastructure"]:
        score += 10
        notes.append(f"{sector} stratejik büyüme sektörlerinden biri.")

    score = max(0, min(100, score))
    return score, notes


def calculate_research_priority_score(info, contracts, sector, filings):
    score = 0
    risk_score = 0
    notes = []

    market_cap = info.get("marketCap")
    revenue_growth = info.get("revenueGrowth")
    beta = info.get("beta")

    financial_score, financial_notes = calculate_financial_health_score(info)
    catalyst_score, catalyst_notes = calculate_catalyst_score(contracts, filings, sector)

    if market_cap:
        bucket = get_cap_bucket(market_cap)

        if bucket == "Small Cap / Early Candidates":
            score += 25
            notes.append("Small-cap veya daha küçük; erken araştırma adayı olabilir.")
        elif bucket == "Mid Cap / Growth Candidates":
            score += 14
            notes.append("Mid-cap; büyüme adayı olabilir ama çok erken aşama değildir.")
        elif bucket == "Large Cap / Sector Leaders":
            score -= 5
            notes.append("Large-cap / mega-cap; erken fırsat değil, sektör lideri olarak değerlendirilmelidir.")
        else:
            risk_score += 8

        if market_cap < 50_000_000:
            risk_score += 25
            notes.append("Çok düşük market cap; likidite ve manipülasyon riski yüksek olabilir.")
    else:
        risk_score += 10
        notes.append("Market cap verisi bulunamadı.")

    contract_summary = summarize_contracts(contracts)
    total_contract_value = contract_summary["total_contract_value"]

    if contracts:
        score += 18
        notes.append("USAspending üzerinde kontrat/eşleşme bulundu.")

        if contract_summary["nasa_total"] > 0:
            score += 7
        if contract_summary["dod_total"] > 0:
            score += 7
        if contract_summary["doe_total"] > 0:
            score += 5

        try:
            ratio = total_contract_value / market_cap if market_cap else 0
            if ratio >= 0.10:
                score += 25
                notes.append("Kontrat toplamı market cap'e göre çok anlamlı.")
            elif ratio >= 0.03:
                score += 15
                notes.append("Kontrat toplamı market cap'e göre orta düzeyde anlamlı.")
            elif ratio >= 0.005:
                score += 7
                notes.append("Kontrat toplamı market cap'e göre sınırlı ama izlenebilir.")
            else:
                score += 2
                risk_score += 5
                notes.append("Kontrat toplamı market cap'e göre çok küçük.")
        except Exception:
            pass
    else:
        risk_score += 5
        notes.append("USAspending üzerinde kontrat bulunamadı.")

    if sector in list(SECTOR_UNIVERSE.keys()):
        score += 10
        notes.append(f"{sector} sektörü stratejik büyüme alanı olarak işaretlendi.")

    if revenue_growth is not None:
        try:
            if revenue_growth > 0.30:
                score += 12
            elif revenue_growth > 0.10:
                score += 6
            elif revenue_growth < 0:
                risk_score += 10
        except Exception:
            pass

    if financial_score < 35:
        risk_score += 18
    elif financial_score < 50:
        risk_score += 8
    elif financial_score > 70:
        score += 7

    if catalyst_score > 70:
        score += 8
    elif catalyst_score < 35:
        risk_score += 5

    try:
        if beta is not None:
            if beta > 2:
                risk_score += 10
            elif beta > 1.5:
                risk_score += 5
    except Exception:
        pass

    if filings:
        score += 3
    else:
        risk_score += 8

    score = max(0, min(100, score))
    risk_score = max(0, min(100, risk_score))

    notes.extend(financial_notes[:3])
    notes.extend(catalyst_notes[:3])

    return score, risk_score, notes


# --------------------------------------------------
# Fiyat senaryo analizi
# --------------------------------------------------

def generate_price_scenarios(current_price, priority_score, risk_score, momentum_score, financial_score, catalyst_score, market_cap):
    if current_price is None:
        return None, "Fiyat verisi bulunamadığı için senaryo üretilemedi."

    try:
        current_price = float(current_price)
    except Exception:
        return None, "Fiyat verisi okunamadığı için senaryo üretilemedi."

    bucket = get_cap_bucket(market_cap)

    if risk_score >= 70:
        bear_range = (-45, -20)
        base_range = (-20, 10)
        bull_range = (10, 45)
        summary = "Risk yüksek; senaryolar daha geniş ve aşağı yönlü risk daha belirgin."
    elif priority_score >= 70 and catalyst_score >= 60 and bucket == "Small Cap / Early Candidates":
        bear_range = (-35, -12)
        base_range = (-5, 30)
        bull_range = (35, 100)
        summary = "Küçük ölçek + güçlü katalizör sinyali varsa yukarı potansiyel yüksek, fakat volatilite de yüksek."
    elif priority_score >= 60 and bucket == "Mid Cap / Growth Candidates":
        bear_range = (-30, -10)
        base_range = (-5, 25)
        bull_range = (25, 70)
        summary = "Büyüme adayı görünümü var; yukarı potansiyel katalizörlere bağlı."
    elif bucket == "Large Cap / Sector Leaders":
        bear_range = (-25, -8)
        base_range = (-5, 18)
        bull_range = (15, 40)
        summary = "Büyük şirketlerde erken fırsat sınırlı; senaryo daha çok sektör liderliği ve momentumla ilgilidir."
    else:
        bear_range = (-35, -12)
        base_range = (-10, 20)
        bull_range = (20, 60)
        summary = "Karışık görünüm; detaylı araştırma gerekir."

    if momentum_score >= 70:
        base_range = (base_range[0] + 3, base_range[1] + 5)
        bull_range = (bull_range[0] + 5, bull_range[1] + 10)
    elif momentum_score <= 35:
        bear_range = (bear_range[0] - 5, bear_range[1] - 3)
        base_range = (base_range[0] - 5, base_range[1] - 5)

    if financial_score <= 35:
        bear_range = (bear_range[0] - 8, bear_range[1] - 5)
        bull_range = (bull_range[0] - 5, bull_range[1] - 10)
    elif financial_score >= 70:
        bear_range = (bear_range[0] + 5, bear_range[1] + 5)
        base_range = (base_range[0] + 3, base_range[1] + 5)

    def price_range(pct_range):
        low_pct, high_pct = pct_range
        low_price = current_price * (1 + low_pct / 100)
        high_price = current_price * (1 + high_pct / 100)
        return f"{low_pct}% to {high_pct}%", f"${low_price:.2f} - ${high_price:.2f}"

    bear_pct, bear_price = price_range(bear_range)
    base_pct, base_price = price_range(base_range)
    bull_pct, bull_price = price_range(bull_range)

    scenarios = pd.DataFrame(
        [
            {
                "Senaryo": "Bear Case",
                "Yüzde Aralığı": bear_pct,
                "Fiyat Aralığı": bear_price,
                "Mantık": "Finansal riskler, zayıf katalizörler, piyasa düzeltmesi veya sermaye artırımı riski.",
            },
            {
                "Senaryo": "Base Case",
                "Yüzde Aralığı": base_pct,
                "Fiyat Aralığı": base_price,
                "Mantık": "Mevcut büyüme ve sektör ilgisi devam eder, fakat büyük yeni katalizör gelmez.",
            },
            {
                "Senaryo": "Bull Case",
                "Yüzde Aralığı": bull_pct,
                "Fiyat Aralığı": bull_price,
                "Mantık": "Yeni kontrat, güçlü finansal ilerleme, büyük partnerlik veya sektör momentumu güçlenir.",
            },
        ]
    )

    return scenarios, summary


def get_outlook_label(priority_score, risk_score, momentum_score, financial_score, catalyst_score):
    if priority_score >= 70 and risk_score <= 50 and catalyst_score >= 60:
        return "Positive / Research Candidate"
    if risk_score >= 70:
        return "High Risk"
    if priority_score >= 60:
        return "Speculative Positive"
    if momentum_score >= 70 and financial_score >= 50:
        return "Momentum Positive"
    if financial_score < 35:
        return "Financially Risky"
    return "Neutral / Monitor"


# --------------------------------------------------
# SWOT
# --------------------------------------------------

def generate_rule_based_swot(info, contracts, sector, priority_score, risk_score):
    strengths = []
    weaknesses = []
    opportunities = []
    threats = []

    market_cap = info.get("marketCap")
    sector_info = safe_get(info, "sector")
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

    if sector in ["AI", "Cybersecurity", "Defense Technology", "Space", "Quantum", "Energy Infrastructure"]:
        opportunities.append(f"{sector} sektörü uzun vadeli stratejik büyüme alanlarından biri olabilir.")

    if market_cap:
        bucket = get_cap_bucket(market_cap)

        if bucket == "Small Cap / Early Candidates":
            strengths.append("Şirket küçük ölçekli olduğu için büyüme potansiyeli yüksek olabilir.")
            threats.append("Küçük ölçekli şirketlerde likidite, sermaye artırımı ve volatilite riski daha yüksektir.")
        elif bucket == "Large Cap / Sector Leaders":
            weaknesses.append("Şirket büyük ölçekli; erken aşama getiri potansiyeli sınırlanmış olabilir.")
            opportunities.append("Büyük şirketler sektör lideri/benchmark olarak kullanılabilir.")

    if sector_info != "N/A":
        strengths.append(f"Şirketin sektörü: {sector_info}.")
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

    if priority_score >= 70:
        opportunities.append("Araştırma Öncelik Skoru güçlü; derin araştırma listesine alınabilir.")

    if risk_score >= 60:
        threats.append("Risk skoru yüksek; bilanço, nakit ve borç durumu ayrıca incelenmelidir.")

    weaknesses.append("Bu SWOT, ücretsiz veri ve kural tabanlı sistemle üretilmiştir; AI analizi değildir.")
    threats.append("Veriler eksik, gecikmeli veya hatalı olabilir; yatırım kararı öncesi SEC dosyaları ve bilanço manuel kontrol edilmelidir.")

    return strengths, weaknesses, opportunities, threats


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
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.header("Araştırma Ayarları")

    mode = st.radio(
        "Mod seçin",
        ["Sektör tarayıcısı", "Tek şirket analizi"],
        index=0,
    )

    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    if mode == "Sektör tarayıcısı":
        selected_sector = st.selectbox("Sektör seçin", list(SECTOR_UNIVERSE.keys()), index=0)
        run_scan = st.button("Sektörü Tara", type="primary")
    else:
        ticker = st.text_input("Ticker girin", value="RKLB")
        company_name = st.text_input("Şirket adı girin", value="Rocket Lab")
        selected_sector = st.selectbox("Sektör seçin", list(SECTOR_UNIVERSE.keys()), index=3)
        run_analysis = st.button("Ücretsiz Verilerle Analiz Et", type="primary")

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
    "Ücretsiz ve açık kaynak/veri kaynaklarıyla ön araştırma ve senaryo analizi yapar."
)

# --------------------------------------------------
# Sektör tarayıcısı
# --------------------------------------------------

if mode == "Sektör tarayıcısı" and run_scan:
    companies = SECTOR_UNIVERSE.get(selected_sector, [])

    st.header(f"{selected_sector} Sektörü Tarama Sonuçları")
    st.caption(
        "Şirketler market cap'e göre Small Cap / Mid Cap / Large Cap olarak ayrılır. "
        "Büyük şirketler erken fırsat değil, sektör lideri/benchmark olarak gösterilir."
    )

    results = []
    progress = st.progress(0)

    for i, (ticker_scan, name_scan) in enumerate(companies):
        with st.spinner(f"{ticker_scan} analiz ediliyor..."):
            try:
                info_scan, hist_scan = get_stock_data(ticker_scan)

                search_names_scan = get_official_company_names(info_scan, name_scan)
                contracts_scan = get_usaspending_contracts_smart(search_names_scan)

                cik_scan, sec_name_scan, filings_scan = get_sec_recent_filings(ticker_scan)

                priority_score, risk_score, _ = calculate_research_priority_score(
                    info=info_scan,
                    contracts=contracts_scan,
                    sector=selected_sector,
                    filings=filings_scan,
                )

                momentum_score, _ = calculate_momentum_score(hist_scan)
                financial_score, _ = calculate_financial_health_score(info_scan)
                catalyst_score, _ = calculate_catalyst_score(contracts_scan, filings_scan, selected_sector)

                market_cap_scan = info_scan.get("marketCap")
                contract_summary_scan = summarize_contracts(contracts_scan)

                role = get_company_role(market_cap_scan, priority_score, risk_score)
                outlook = get_outlook_label(
                    priority_score,
                    risk_score,
                    momentum_score,
                    financial_score,
                    catalyst_score,
                )

                results.append(
                    {
                        "Ticker": ticker_scan,
                        "Şirket": safe_get(info_scan, "longName", name_scan),
                        "Fiyat": format_number(info_scan.get("currentPrice")),
                        "Market Cap": format_number(market_cap_scan),
                        "Market Cap Raw": market_cap_scan,
                        "Kategori": get_market_cap_category(market_cap_scan),
                        "Grup": get_cap_bucket(market_cap_scan),
                        "Rol": role,
                        "Kontrat Sayısı": contract_summary_scan["contract_count"],
                        "Toplam Kontrat": format_number(contract_summary_scan["total_contract_value"]),
                        "Araştırma Öncelik Skoru": priority_score,
                        "Risk Skoru": risk_score,
                        "Momentum": momentum_score,
                        "Finansal Sağlık": financial_score,
                        "Katalizör": catalyst_score,
                        "6-12 Ay Görünüm": outlook,
                    }
                )
            except Exception:
                results.append(
                    {
                        "Ticker": ticker_scan,
                        "Şirket": name_scan,
                        "Fiyat": "Hata",
                        "Market Cap": "Hata",
                        "Market Cap Raw": None,
                        "Kategori": "Hata",
                        "Grup": "Unknown",
                        "Rol": "Needs Review",
                        "Kontrat Sayısı": 0,
                        "Toplam Kontrat": "N/A",
                        "Araştırma Öncelik Skoru": 0,
                        "Risk Skoru": 0,
                        "Momentum": 0,
                        "Finansal Sağlık": 0,
                        "Katalizör": 0,
                        "6-12 Ay Görünüm": "Unknown",
                    }
                )

        progress.progress((i + 1) / len(companies))

    if results:
        df = pd.DataFrame(results)

        display_cols = [
            "Ticker",
            "Şirket",
            "Fiyat",
            "Market Cap",
            "Kategori",
            "Rol",
            "Kontrat Sayısı",
            "Toplam Kontrat",
            "Araştırma Öncelik Skoru",
            "Risk Skoru",
            "Momentum",
            "Finansal Sağlık",
            "Katalizör",
            "6-12 Ay Görünüm",
        ]

        small_df = df[df["Grup"] == "Small Cap / Early Candidates"].sort_values(
            "Araştırma Öncelik Skoru",
            ascending=False,
        )

        mid_df = df[df["Grup"] == "Mid Cap / Growth Candidates"].sort_values(
            "Araştırma Öncelik Skoru",
            ascending=False,
        )

        large_df = df[df["Grup"] == "Large Cap / Sector Leaders"].sort_values(
            "Market Cap Raw",
            ascending=False,
        )

        unknown_df = df[df["Grup"] == "Unknown"]

        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "Small Cap / Early Candidates",
                "Mid Cap / Growth Candidates",
                "Large Cap / Sector Leaders",
                "Tüm Sonuçlar",
            ]
        )

        with tab1:
            st.subheader("Small Cap / Early Candidates")
            st.caption("Bu bölüm senin stratejin için en önemli bölüm: küçük piyasa değerli, erken araştırma adayı şirketler.")
            if not small_df.empty:
                st.dataframe(small_df[display_cols], use_container_width=True)
            else:
                st.info("Bu sektörde small-cap aday bulunamadı.")

        with tab2:
            st.subheader("Mid Cap / Growth Candidates")
            st.caption("Bu şirketler artık çok erken aşama olmayabilir, fakat büyüme potansiyeli devam edebilir.")
            if not mid_df.empty:
                st.dataframe(mid_df[display_cols], use_container_width=True)
            else:
                st.info("Bu sektörde mid-cap aday bulunamadı.")

        with tab3:
            st.subheader("Large Cap / Sector Leaders")
            st.caption("Bu şirketler erken fırsat olarak değil, sektör lideri ve benchmark olarak değerlendirilmelidir.")
            if not large_df.empty:
                st.dataframe(large_df[display_cols], use_container_width=True)
            else:
                st.info("Bu sektörde large-cap lider bulunamadı.")

        with tab4:
            st.subheader("Tüm Sonuçlar")
            all_df = df.sort_values("Araştırma Öncelik Skoru", ascending=False)
            st.dataframe(all_df[display_cols], use_container_width=True)

            if not unknown_df.empty:
                with st.expander("Verisi eksik / bilinmeyen şirketler"):
                    st.dataframe(unknown_df[display_cols], use_container_width=True)

        csv_data = df[display_cols].to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Tüm sonuçları CSV indir",
            data=csv_data,
            file_name=f"{selected_sector}_sector_scan_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        sorted_df = df.sort_values("Araştırma Öncelik Skoru", ascending=False)

        if not sorted_df.empty:
            best = sorted_df.iloc[0]
            st.success(
                f"En yüksek Araştırma Öncelik Skoru: "
                f"**{best['Ticker']}** ({best['Şirket']}) — "
                f"{best['Araştırma Öncelik Skoru']}/100"
            )

# --------------------------------------------------
# Tek şirket analizi
# --------------------------------------------------

elif mode == "Tek şirket analizi" and run_analysis:
    ticker = ticker.upper().strip()
    manual_company_name = company_name.strip()

    with st.spinner("Veriler çekiliyor..."):
        info, hist = get_stock_data(ticker)

        search_names = get_official_company_names(info, manual_company_name)
        contracts = get_usaspending_contracts_smart(search_names)

        cik, sec_name, filings = get_sec_recent_filings(ticker)
        form4_filings = get_insider_form4_filings(filings)

        priority_score, risk_score, score_notes = calculate_research_priority_score(
            info=info,
            contracts=contracts,
            sector=selected_sector,
            filings=filings,
        )

        momentum_score, momentum_notes = calculate_momentum_score(hist)
        financial_score, financial_notes = calculate_financial_health_score(info)
        catalyst_score, catalyst_notes = calculate_catalyst_score(contracts, filings, selected_sector)

        strengths, weaknesses, opportunities, threats = generate_rule_based_swot(
            info=info,
            contracts=contracts,
            sector=selected_sector,
            priority_score=priority_score,
            risk_score=risk_score,
        )

        contract_summary = summarize_contracts(contracts)
        ma50, ma200, rsi_current, one_year_return = calculate_technical_indicators(hist)

        scenarios_df, scenario_summary = generate_price_scenarios(
            current_price=info.get("currentPrice"),
            priority_score=priority_score,
            risk_score=risk_score,
            momentum_score=momentum_score,
            financial_score=financial_score,
            catalyst_score=catalyst_score,
            market_cap=info.get("marketCap"),
        )

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
    cap_bucket = get_cap_bucket(market_cap)

    total_contract_value = contract_summary["total_contract_value"]

    try:
        contract_to_market_cap = total_contract_value / market_cap if market_cap else None
    except Exception:
        contract_to_market_cap = None

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Fiyat", format_number(info.get("currentPrice")))
    col2.metric("Market Cap", format_number(market_cap))
    col3.metric("Araştırma Öncelik Skoru", f"{priority_score}/100")
    col4.metric("Risk Skoru", f"{risk_score}/100")

    score_cols = st.columns(3)
    score_cols[0].metric("Momentum Skoru", f"{momentum_score}/100")
    score_cols[1].metric("Finansal Sağlık Skoru", f"{financial_score}/100")
    score_cols[2].metric("Katalizör Skoru", f"{catalyst_score}/100")

    st.markdown("### Piyasa Değeri ve Rol")
    st.write(f"**Kategori:** {market_cap_category}")
    st.write(f"**Grup:** {cap_bucket}")
    st.write(f"**Rol:** {get_company_role(market_cap, priority_score, risk_score)}")

    if cap_bucket == "Large Cap / Sector Leaders":
        st.warning(
            "Bu şirket büyük ölçekli görünüyor. Erken fırsat olarak değil, sektör lideri/benchmark olarak değerlendirilmelidir."
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
    profile_cols[3].write(f"**Uygulama Sektörü:** {selected_sector}")

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

    st.subheader("6-12 Aylık Fiyat Senaryo Analizi")

    st.caption(
        "Bu bölüm otomatik ve kural tabanlıdır. Kesin hedef fiyat veya yatırım tavsiyesi değildir."
    )

    if scenarios_df is not None:
        st.write(scenario_summary)
        st.dataframe(scenarios_df, use_container_width=True)
    else:
        st.warning(scenario_summary)

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

    with st.expander("Araştırma Öncelik Skoru Notları"):
        for note in score_notes:
            st.write(f"- {note}")

    with st.expander("Momentum Notları"):
        for note in momentum_notes:
            st.write(f"- {note}")

    with st.expander("Finansal Sağlık Notları"):
        for note in financial_notes:
            st.write(f"- {note}")

    with st.expander("Katalizör Notları"):
        for note in catalyst_notes:
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

    outlook = get_outlook_label(
        priority_score,
        risk_score,
        momentum_score,
        financial_score,
        catalyst_score,
    )

    st.write(f"**6-12 Ay Genel Görünüm:** {outlook}")

    if priority_score >= 70 and risk_score <= 50:
        st.success(
            "Araştırma önceliği güçlü görünüyor. Yine de SEC dosyaları, bilanço ve haberler manuel doğrulanmalı."
        )
    elif priority_score >= 60 and risk_score <= 70:
        st.warning(
            "Orta-güçlü sinyal var. Şirket derin araştırmaya alınabilir ama riskler dikkatle incelenmeli."
        )
    elif priority_score >= 40:
        st.info(
            "Orta seviye sinyal var. İzleme listesine alınabilir, ancak acele yatırım kararı verilmemeli."
        )
    else:
        st.info(
            "Araştırma önceliği zayıf veya veri yetersiz. Daha fazla doğrulama gerekir."
        )

    st.caption(
        "Not: Bu uygulama otomatik ve kural tabanlı ön analiz yapar. "
        "Yatırım tavsiyesi değildir."
    )

else:
    st.write("Sol menüden sektör seçerek tarama başlatabilir veya tek şirket analizi yapabilirsin.")
