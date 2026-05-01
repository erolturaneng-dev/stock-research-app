import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from io import StringIO
from datetime import datetime

st.set_page_config(page_title="US Technology Company Discovery Scanner", layout="wide")

st.title("US Technology Company Discovery Scanner")
st.caption(
    "Scans US-listed companies, matches SEC CIK/ticker IDs, and filters technology candidates "
    "by sector, industry, market cap and company profile."
)

# --------------------------------------------------
# Helper functions
# --------------------------------------------------

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


def get_market_cap_group(market_cap):
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
        else:
            return "Large-cap / Sector Leader"
    except Exception:
        return "Unknown"


def is_technology_candidate(sector, industry, company_name):
    text = f"{sector} {industry} {company_name}".lower()

    keywords = [
        "technology",
        "software",
        "semiconductor",
        "computer",
        "electronic",
        "information",
        "cyber",
        "cloud",
        "data",
        "artificial intelligence",
        " ai ",
        "machine learning",
        "analytics",
        "automation",
        "robotics",
        "quantum",
        "space",
        "aerospace",
        "satellite",
        "defense",
        "internet",
        "communication equipment",
        "scientific",
        "application software",
        "systems software",
        "electronic components",
        "semiconductor equipment",
    ]

    return any(keyword in text for keyword in keywords)


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
    combined = combined.drop_duplicates(subset=["Ticker"])
    combined = combined[~combined["Ticker"].str.contains(r"\$", regex=True, na=False)]
    combined = combined[~combined["Ticker"].str.contains(r"\.", regex=True, na=False)]

    return combined.reset_index(drop=True)


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
    except Exception as e:
        st.warning(f"SEC ticker/CIK listesi çekilemedi: {e}")
        return pd.DataFrame(columns=["Ticker", "SEC Company Name", "CIK"])


@st.cache_data(ttl=3600)
def get_yfinance_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "Ticker": ticker,
            "YF Company Name": info.get("longName") or info.get("shortName"),
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
            "Market Cap Raw": info.get("marketCap"),
            "Price": info.get("currentPrice"),
            "Revenue Growth": info.get("revenueGrowth"),
            "Profit Margin": info.get("profitMargins"),
            "Beta": info.get("beta"),
            "Business Summary": info.get("longBusinessSummary"),
        }
    except Exception:
        return {
            "Ticker": ticker,
            "YF Company Name": None,
            "Sector": None,
            "Industry": None,
            "Market Cap Raw": None,
            "Price": None,
            "Revenue Growth": None,
            "Profit Margin": None,
            "Beta": None,
            "Business Summary": None,
        }


def scan_tickers(base_df, max_scan, market_cap_filter, only_small):
    results = []
    total = min(len(base_df), max_scan)

    progress = st.progress(0)
    status = st.empty()

    for idx in range(total):
        row = base_df.iloc[idx]
        ticker = str(row["Ticker"]).upper().strip()
        company_name = str(row["Company Name"])

        status.write(f"Taranıyor: {ticker} - {company_name}")

        yf_info = get_yfinance_info(ticker)

        sector = yf_info.get("Sector")
        industry = yf_info.get("Industry")
        yf_name = yf_info.get("YF Company Name") or company_name
        market_cap = yf_info.get("Market Cap Raw")

        if is_technology_candidate(sector, industry, yf_name):
            group = get_market_cap_group(market_cap)

            if only_small and group not in ["Nano-cap", "Micro-cap", "Small-cap"]:
                progress.progress((idx + 1) / total)
                continue

            if market_cap_filter == "Small-cap ve altı" and group not in ["Nano-cap", "Micro-cap", "Small-cap"]:
                progress.progress((idx + 1) / total)
                continue

            if market_cap_filter == "Mid-cap ve altı" and group not in ["Nano-cap", "Micro-cap", "Small-cap", "Mid-cap"]:
                progress.progress((idx + 1) / total)
                continue

            results.append(
                {
                    "Ticker": ticker,
                    "Company Name": yf_name,
                    "Exchange": row.get("Exchange"),
                    "Sector": sector,
                    "Industry": industry,
                    "Market Cap": format_number(market_cap),
                    "Market Cap Raw": market_cap,
                    "Market Cap Group": group,
                    "Price": format_number(yf_info.get("Price")),
                    "Revenue Growth": yf_info.get("Revenue Growth"),
                    "Profit Margin": yf_info.get("Profit Margin"),
                    "Beta": yf_info.get("Beta"),
                    "Summary": yf_info.get("Business Summary"),
                }
            )

        progress.progress((idx + 1) / total)

    status.empty()

    return pd.DataFrame(results)


# --------------------------------------------------
# UI
# --------------------------------------------------

st.info(
    "Bu sayfa, ABD borsalarındaki şirketleri tarayıp teknoloji adayı olanları bulur. "
    "Tarama yfinance ile yapıldığı için çok yüksek sayı seçersen yavaş çalışabilir."
)

with st.sidebar:
    st.header("Tarama Ayarları")

    max_scan = st.slider(
        "Kaç ticker taransın?",
        min_value=50,
        max_value=1000,
        value=250,
        step=50,
    )

    market_cap_filter = st.selectbox(
        "Market cap filtresi",
        [
            "Hepsi",
            "Small-cap ve altı",
            "Mid-cap ve altı",
        ],
        index=1,
    )

    only_small = st.checkbox(
        "Sadece küçük şirketleri göster",
        value=True,
    )

    run_scan = st.button("ABD Teknoloji Şirketlerini Tara", type="primary")

st.subheader("Veri Kaynakları")
st.write(
    "- Nasdaq Trader symbol directory: ticker ve şirket adı listesi\n"
    "- SEC company_tickers.json: CIK / şirket ID eşleşmesi\n"
    "- yfinance: sektör, industry, market cap, fiyat ve finansal veri"
)

if run_scan:
    with st.spinner("Ticker listeleri çekiliyor..."):
        symbols_df = load_nasdaq_symbol_directory()
        sec_df = load_sec_company_tickers()

    if symbols_df.empty:
        st.error("Ticker listesi çekilemedi.")
    else:
        st.write(f"Toplam bulunan ticker sayısı: **{len(symbols_df):,}**")

        with st.spinner("Şirketler yfinance üzerinden taranıyor..."):
            tech_df = scan_tickers(
                base_df=symbols_df,
                max_scan=max_scan,
                market_cap_filter=market_cap_filter,
                only_small=only_small,
            )

        if tech_df.empty:
            st.warning("Seçilen aralıkta teknoloji şirketi bulunamadı. Tarama sayısını artırmayı deneyebilirsin.")
        else:
            merged_df = tech_df.merge(sec_df, on="Ticker", how="left")

            merged_df["CIK"] = merged_df["CIK"].fillna("N/A")
            merged_df["SEC Company Name"] = merged_df["SEC Company Name"].fillna("N/A")

            display_cols = [
                "Ticker",
                "Company Name",
                "CIK",
                "Exchange",
                "Sector",
                "Industry",
                "Market Cap",
                "Market Cap Group",
                "Price",
                "Revenue Growth",
                "Profit Margin",
                "Beta",
            ]

            small_df = merged_df[
                merged_df["Market Cap Group"].isin(["Nano-cap", "Micro-cap", "Small-cap"])
            ].sort_values("Market Cap Raw", ascending=True, na_position="last")

            mid_df = merged_df[
                merged_df["Market Cap Group"] == "Mid-cap"
            ].sort_values("Market Cap Raw", ascending=True, na_position="last")

            large_df = merged_df[
                merged_df["Market Cap Group"] == "Large-cap / Sector Leader"
            ].sort_values("Market Cap Raw", ascending=False, na_position="last")

            tab1, tab2, tab3, tab4 = st.tabs(
                [
                    "Small / Micro Tech Companies",
                    "Mid Cap Tech Companies",
                    "Large Tech Leaders",
                    "All Results",
                ]
            )

            with tab1:
                st.subheader("Small / Micro Technology Companies")
                st.caption("Bu bölüm küçük market cap şirketleri bulmak için en önemli bölümdür.")
                if small_df.empty:
                    st.info("Small-cap teknoloji şirketi bulunamadı.")
                else:
                    st.dataframe(small_df[display_cols], use_container_width=True)

            with tab2:
                st.subheader("Mid Cap Technology Companies")
                if mid_df.empty:
                    st.info("Mid-cap teknoloji şirketi bulunamadı.")
                else:
                    st.dataframe(mid_df[display_cols], use_container_width=True)

            with tab3:
                st.subheader("Large Technology Leaders")
                st.caption("Bunlar erken fırsat değil, sektör lideri/benchmark olarak kullanılabilir.")
                if large_df.empty:
                    st.info("Large-cap teknoloji lideri bulunamadı.")
                else:
                    st.dataframe(large_df[display_cols], use_container_width=True)

            with tab4:
                st.subheader("All Technology Candidates")
                st.dataframe(
                    merged_df[display_cols].sort_values(
                        "Market Cap Raw",
                        ascending=True,
                        na_position="last",
                    ),
                    use_container_width=True,
                )

            csv_data = merged_df[display_cols + ["Summary"]].to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Teknoloji şirket listesini CSV indir",
                data=csv_data,
                file_name=f"us_technology_companies_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

            st.success(f"Bulunan teknoloji adayı şirket sayısı: {len(merged_df)}")

else:
    st.write("Sol menüden tarama ayarlarını seçip butona basabilirsin.")
