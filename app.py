# ==================================================
# QUICK ANALYSIS RENDERER
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

    if "Güvenlik" in name or "Safety" in name:
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
