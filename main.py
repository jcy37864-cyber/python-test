import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 시스템 v4.9", layout="wide")

# 2. 커스텀 CSS
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important;
        color: white !important;
        font-weight: bold !important;
    }
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); margin-bottom: 24px; }
    .summary-box { 
        background-color: #ffffff; padding: 20px; border-radius: 12px; 
        border-left: 6px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False

st.title("📊 품질 측정 통합 시스템")

# 사이드바
st.sidebar.title("🚀 주요 기능")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 데이터 변환기", "📈 그래프 분석", "🧮 계산기"])

if st.sidebar.button("🧹 데이터 초기화 (Reset)", use_container_width=True):
    for key in st.session_state.keys(): del st.session_state[key]
    st.rerun()

# --- 🔄 1. 데이터 변환기 ---
if menu == "🔄 데이터 변환기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 데이터 형식 변환기")
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    if st.button("🚀 ZXY 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row.get("X","")).strip(), str(row.get("Y","")).strip(), str(row.get("Z","")).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(res_df, use_container_width=True)
            st.download_button("📂 CSV 다운로드", res_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📈 2. 그래프 분석 (NG 빨간색 & 데이터 레이블 복구) ---
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📁 분석 파일 업로드")
    
    # 템플릿 생성
    sample_data = pd.DataFrame({"VALUE": [10.02, 10.15, 9.98, 9.85, 10.03], "MIN": [9.90]*5, "MAX": [10.10]*5})
    template_out = BytesIO()
    with pd.ExcelWriter(template_out, engine='xlsxwriter') as writer: sample_data.to_excel(writer, index=False)
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1: st.download_button("📄 업로드 양식 다운로드", template_out.getvalue(), "Template.xlsx", use_container_width=True)
    with col_t2: uploaded_file = st.file_uploader("파일 선택", type=["xlsx", "csv"], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]
        ng_df = df[df["판정"] == "NG"]

        # 정밀 Y축 범위
        y_min, y_max = df["VALUE"].min(), df["VALUE"].max()
        margin = (y_max - y_min) * 0.4 if y_max != y_min else 0.1
        y_range = [y_min - margin, y_max + margin]

        # [화면 그래프] NG 강조 및 데이터 표시
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📈 실시간 품질 분석 (NG & 데이터 강조)")
        
        fig = go.Figure()
        # 기본 라인
        fig.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers+text', 
                                 text=df["VALUE"], textposition="top center", 
                                 name='측정값', line=dict(color='#3b82f6')))
        # NG 포인트 빨간색 중첩
        if not ng_df.empty:
            fig.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers+text', 
                                     text=ng_df["VALUE"], textposition="top center",
                                     marker=dict(color='red', size=12), name='NG 이탈',
                                     textfont=dict(color='red', size=14)))
        # Worst 원형 강조
        fig.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', 
                                 marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        fig.update_layout(yaxis_range=y_range)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 품질 분석 대시보드
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📊 분석 결과 요약")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 샘플 수", f"{len(df)} EA")
        c2.metric("✅ 합격", f"{len(df)-len(ng_df)} EA")
        c3.metric("🚨 불량", f"{len(ng_df)} EA", delta_color="inverse")
        c4.metric("🎯 Worst", f"{worst_val:.4f}", f"Idx: {worst_idx}")

        st.markdown("### 📝 분석 브리핑")
        if len(ng_df) == 0:
            st.markdown('<div class="summary-box" style="border-left-color: #10b981;"><b>✅ 공정 양호:</b> 모든 데이터가 규격 내에 관리되고 있습니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="summary-box" style="border-left-color: #ef4444;"><b>🚨 품질 경보:</b> {len(ng_df)}건의 규격 이탈이 감지되었습니다. Worst 지점({worst_val:.4f}) 확인 필요.</div>', unsafe_allow_html=True)

        # [엑셀용 정적 그래프] NG 빨간색 & 데이터 레이블 적용
        # 1. Line
        fig_l, ax_l = plt.subplots(figsize=(10, 4))
        ax_l.plot(df.index, df["VALUE"], marker='o', color='#3b82f6', label='Value')
        for i, val in enumerate(df["VALUE"]):
            color = 'red' if df.iloc[i]["판정"] == "NG" else 'black'
            ax_l.text(i, val, f'{val:.2f}', color=color, ha='center', va='bottom', fontsize=9, fontweight='bold')
            if df.iloc[i]["판정"] == "NG":
                ax_l.plot(i, val, 'ro', markersize=8) # NG 지점 빨간색 점
        ax_l.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=250, lw=2)
        ax_l.set_ylim(y_range)
        img_l = BytesIO(); fig_l.savefig(img_l, format='png', bbox_inches='tight'); plt.close(fig_l)

        # 2. Bar
        fig_b, ax_b = plt.subplots(figsize=(10, 4))
        bar_colors = ['red' if p == "NG" else '#3b82f6' for p in df["판정"]]
        bars = ax_b.bar(df.index, df["VALUE"], color=bar_colors)
        ax_b.bar_label(bars, fmt='%.2f', padding=3, fontsize=8, fontweight='bold')
        ax_b.set_ylim(y_range)
        img_b = BytesIO(); fig_b.savefig(img_b, format='png', bbox_inches='tight'); plt.close(fig_b)

        # 엑셀 파일 생성
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook, worksheet = writer.book, writer.sheets['Report']
            red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            for i in range(len(df)):
                if df.iloc[i]["판정"] == "NG": worksheet.set_row(i + 1, None, red_fmt)
            worksheet.insert_image('H2', 'line.png', {'image_data': img_l, 'x_scale': 0.5, 'y_scale': 0.5})
            worksheet.insert_image('H22', 'bar.png', {'image_data': img_b, 'x_scale': 0.5, 'y_scale': 0.5})

        st.download_button("📂 엑셀 보고서 다운로드 (강조 적용)", excel_out.getvalue(), "Quality_Report_Final.xlsx", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 🧮 3. 계산기 ---
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 계산기")
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
        v, m = st.number_input("수치"), st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"])
        st.write(f"결과: {v * 0.101972 if 'kgf' in m else v * 9.80665:.4f}")
    with tabs[3]:
        u_i, u_v = st.selectbox("항목", ["mm/inch", "mm/μm"]), st.number_input("값")
        st.info(f"결과: {u_v/25.4 if 'inch' in u_i else u_v*1000:.4f}")
    with tabs[4]:
        s_t = st.text_area("데이터 입력 (쉼표 구분)")
        try:
            l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if l: st.write(f"평균: {sum(l)/len(l):.4f} | 범위(R): {max(l)-min(l):.4f}")
        except: pass
    st.markdown('</div>', unsafe_allow_html=True)
