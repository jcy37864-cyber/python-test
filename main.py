import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 시스템 v4.6", layout="wide")

# 2. 커스텀 CSS (누락된 스타일 및 버튼 색상 복구)
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    
    /* [복구] 초기화 버튼 빨간색 강제 지정 */
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }

    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); margin-bottom: 24px; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; }
    
    /* 요약 브리핑 박스 스타일 */
    .summary-box { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False

st.title("📊 품질 측정 통합 시스템")

# 사이드바 메뉴
st.sidebar.title("🚀 주요 기능")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 데이터 변환기", "📈 그래프 분석", "🧮 계산기"])

if st.sidebar.button("🧹 데이터 초기화 (Reset)", use_container_width=True):
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()

# --- 🔄 1. 데이터 변환기 (CSV 다운로드 버튼 복구) ---
if menu == "🔄 데이터 변환기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 데이터 형식 변환기")
    
    # 템플릿 유지용 세션 상태
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
    
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key="editor_v46")
    
    if st.button("🚀 ZXY 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
            if x and y and z: results.extend([z, x, y])
        
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            res_df.index += 1
            st.success(f"✅ {len(results)}개 변환 완료")
            st.dataframe(res_df, use_container_width=True)
            
            # [복구] CSV 다운로드 및 복사 영역
            st.markdown("### 📋 결과 출력")
            st.text_area("드래그 복사용", "\n".join(map(str, results)), height=150)
            st.download_button(
                label="📂 변환 결과 CSV 다운로드",
                data=res_df.to_csv(index=True).encode("utf-8-sig"),
                file_name="zxy_conversion_result.csv",
                mime="text/csv",
                use_container_width=True
            )
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📈 2. 그래프 분석 (요약/그래프 2종/Worst 강조 복구) ---
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("파일 업로드 (XLSX, CSV)", type=["xlsx", "csv"])
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]
        ng_df = df[df["판정"] == "NG"]
        avg_v = df['VALUE'].mean()

        # 화면용 그래프
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📈 실시간 측정 추세")
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='정상', line=dict(color='#3b82f6')))
        if not ng_df.empty: 
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=12)))
        # [복구] Worst 포인트 강조
        fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', 
                                    marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        st.plotly_chart(fig_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [복구] 품질 분석 대시보드 및 요약
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📊 품질 분석 대시보드")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 전체 샘플", f"{len(df)} EA")
        c2.metric("✅ 합격 (OK)", f"{len(df)-len(ng_df)} EA", delta=f"{((len(df)-len(ng_df))/len(df))*100:.1f}%")
        c3.metric("🚨 불량 (NG)", f"{len(ng_df)} EA", delta=f"-{len(ng_df)}", delta_color="inverse")
        c4.metric("🎯 Worst", f"{worst_val:.3f}", f"Idx: {worst_idx}")

        # [복구] 요약 내용 브리핑
        st.markdown("### 📝 분석 요약 브리핑")
        if len(ng_df) == 0:
            st.markdown(f'<div class="summary-box" style="border-left-color: #10b981;"><b>✅ 공정 안정:</b> 모든 데이터가 규격 내에 있으며, 평균은 {avg_v:.4f}입니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="summary-box" style="border-left-color: #ef4444;"><b>🚨 품질 경보:</b> {len(ng_df)}건의 불량이 발견되었습니다. <b>No.{worst_idx} ({worst_val:.4f})</b> 지점의 집중 점검이 필요합니다.</div>', unsafe_allow_html=True)

        # --- [복구] 엑셀용 그래프 2종 (Line + Bar) ---
        fig_l, ax_l = plt.subplots(figsize=(10, 4))
        ax_l.plot(df.index, df["VALUE"], marker='o', color='#3b82f6', zorder=1)
        ax_l.axhline(y=df["MAX"].iloc[0], color='green', ls='--')
        ax_l.axhline(y=df["MIN"].iloc[0], color='orange', ls='--')
        if not ng_df.empty: ax_l.scatter(ng_df.index, ng_df["VALUE"], color='red', s=60, zorder=5)
        ax_l.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=250, lw=2, zorder=6) # Worst 원 강조
        img_l = BytesIO(); fig_l.savefig(img_l, format='png', bbox_inches='tight'); plt.close(fig_l)

        fig_b, ax_b = plt.subplots(figsize=(10, 4))
        ax_b.bar(df.index, df["VALUE"], color=['red' if p == "NG" else '#3b82f6' for p in df["판정"]])
        ax_b.axhline(y=df["MAX"].iloc[0], color='green', ls='--')
        ax_b.axhline(y=df["MIN"].iloc[0], color='orange', ls='--')
        img_b = BytesIO(); fig_b.savefig(img_b, format='png', bbox_inches='tight'); plt.close(fig_b)

        # 엑셀 저장
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook, worksheet = writer.book, writer.sheets['Report']
            red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            num_fmt = workbook.add_format({'num_format': '0.0000'})
            for i in range(len(df)):
                fmt = red_fmt if df.iloc[i]["판정"] == "NG" else num_fmt
                worksheet.set_row(i + 1, None, fmt)
            # [복구] 그래프 2개 입력
            worksheet.insert_image('H2', 'line.png', {'image_data': img_l, 'x_scale': 0.5, 'y_scale': 0.5})
            worksheet.insert_image('H22', 'bar.png', {'image_data': img_b, 'x_scale': 0.5, 'y_scale': 0.5})

        st.markdown("<br>", unsafe_allow_html=True)
        dc1, dc2 = st.columns(2)
        dc1.download_button("📂 엑셀 보고서 다운로드 (그래프 2종)", excel_out.getvalue(), "Quality_Report_v46.xlsx", use_container_width=True)
        dc2.download_button("🖼️ 추세 그래프 이미지 저장", img_l.getvalue(), "Trend_Line.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 🧮 3. 계산기 (전체 기능 유지) ---
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 계산 도구")
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크 변환", "📏 단위 변환", "📊 데이터 산포"])
    with tabs[0]:
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("종류", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True)
        m_geo = mc2.number_input("도면 기하공차", value=0.05, format="%.4f")
        m_mmc, m_act = st.number_input("MMC 규격", value=10.0), st.number_input("실측치", value=10.02)
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        st.metric("최종 허용 공차", f"{m_geo + bonus:.4f}")
    with tabs[1]:
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준"), p2.number_input("상한"), p3.number_input("하한"), p4.number_input("측정")
        if (base-abs(l_t)) <= ms <= (base+abs(u_t)): st.success("✅ OK")
        else: st.error("🚨 NG")
    with tabs[2]:
        v = st.number_input("수치")
        m = st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"])
        st.write(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")
    with tabs[3]:
        u_i = st.selectbox("항목", ["mm/inch", "mm/μm"])
        u_v = st.number_input("값")
        st.info(f"결과: {u_v/25.4 if 'inch' in u_i else u_v*1000:.4f}")
    with tabs[4]:
        s_t = st.text_area("데이터 입력 (쉼표 구분)")
        try:
            l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f} | 범위(R): {max(l)-min(l):.4f}")
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
