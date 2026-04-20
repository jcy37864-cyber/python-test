import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 시스템 v5.1", layout="wide")

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
    .guide-box { 
        background-color: #eff6ff; padding: 15px; border-radius: 10px; 
        border: 1px solid #bfdbfe; color: #1e40af; font-size: 0.95em; margin-bottom: 20px;
    }
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
    st.markdown("""
        <div class="guide-box">
            <b>💡 사용 가이드:</b> X, Y, Z 좌표 데이터를 입력하면 <b>Z → X → Y</b> 순서로 자동 정렬하여 1열로 변환해줍니다. 
            측정 장비 데이터를 템플릿에 맞게 복사할 때 사용하세요.
        </div>
    """, unsafe_allow_html=True)
    
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

# --- 📈 2. 그래프 분석 ---
elif menu == "📈 그래프 분석":
    st.markdown("""
        <div class="guide-box">
            <b>💡 사용 가이드:</b> 엑셀 양식을 다운로드하여 데이터를 입력한 후 업로드하세요. 
            <b>정밀 Y축 범위</b>가 적용된 추세선과 막대 그래프, 그리고 품질 요약 보고서를 즉시 생성합니다.
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📁 분석 파일 업로드")
    
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

        y_min, y_max = df["VALUE"].min(), df["VALUE"].max()
        margin = (y_max - y_min) * 0.5 if y_max != y_min else 0.1
        y_range = [y_min - margin, y_max + margin]

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📈 측정 분석 그래프 (Line & Bar)")
        
        # Line Chart
        fig_l = go.Figure()
        fig_l.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='Data', line=dict(color='#3b82f6')))
        if not ng_df.empty:
            fig_l.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', marker=dict(color='red', size=12), name='NG'))
        fig_l.update_layout(yaxis_range=y_range)
        st.plotly_chart(fig_l, use_container_width=True)

        # Bar Chart
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(x=df.index, y=df["VALUE"], marker_color=['red' if p == "NG" else '#3b82f6' for p in df["판정"]]))
        fig_b.update_layout(yaxis_range=y_range)
        st.plotly_chart(fig_b, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📊 분석 결과 요약")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 샘플 수", f"{len(df)} EA")
        c2.metric("✅ 합격", f"{len(df)-len(ng_df)} EA")
        c3.metric("🚨 불량", f"{len(ng_df)} EA", delta_color="inverse")
        c4.metric("🎯 Worst", f"{worst_val:.4f}", f"Idx: {worst_idx}")
        
        if len(ng_df) == 0:
            st.markdown('<div class="summary-box" style="border-left-color: #10b981;"><b>✅ 공정 안정:</b> 이상 수치가 발견되지 않았습니다.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="summary-box" style="border-left-color: #ef4444;"><b>🚨 품질 경보:</b> {len(ng_df)}건의 규격 이탈이 감지되었습니다.</div>', unsafe_allow_html=True)

        # 엑셀/이미지용 정적 그래프
        fig_xl, ax_xl = plt.subplots(figsize=(10, 4))
        ax_xl.plot(df.index, df["VALUE"], marker='o', color='#3b82f6')
        if not ng_df.empty: ax_xl.scatter(ng_df.index, ng_df["VALUE"], color='red', s=80)
        ax_xl.set_ylim(y_range)
        img_l = BytesIO(); fig_xl.savefig(img_l, format='png', bbox_inches='tight'); plt.close(fig_xl)

        fig_xb, ax_xb = plt.subplots(figsize=(10, 4))
        ax_xb.bar(df.index, df["VALUE"], color=['red' if p == "NG" else '#3b82f6' for p in df["판정"]])
        ax_xb.set_ylim(y_range)
        img_b = BytesIO(); fig_xb.savefig(img_b, format='png', bbox_inches='tight'); plt.close(fig_xb)

        st.markdown("### 📥 결과 다운로드")
        d_col1, d_col2, d_col3 = st.columns(3)
        
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook, worksheet = writer.book, writer.sheets['Report']
            red_fmt = workbook.add_format({'bg_color': '#FFC7CE'})
            for i in range(len(df)):
                if df.iloc[i]["판정"] == "NG": worksheet.set_row(i + 1, None, red_fmt)
            worksheet.insert_image('H2', 'line.png', {'image_data': img_l, 'x_scale': 0.5, 'y_scale': 0.5})
            worksheet.insert_image('H22', 'bar.png', {'image_data': img_b, 'x_scale': 0.5, 'y_scale': 0.5})

        d_col1.download_button("📂 엑셀 보고서 다운로드", excel_out.getvalue(), "Quality_Report.xlsx", use_container_width=True)
        d_col2.download_button("🖼️ 추세 이미지 저장", img_l.getvalue(), "Trend_Line.png", use_container_width=True)
        d_col3.download_button("🖼️ 막대 이미지 저장", img_b.getvalue(), "Bar_Chart.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 🧮 3. 계산기 ---
elif menu == "🧮 계산기":
    st.markdown("""
        <div class="guide-box">
            <b>💡 사용 가이드:</b> 품질 현장에서 자주 쓰이는 계산기 모음입니다. 
            <b>MMC 보너스 공차, 공차 판정, 토크/단위 변환, 기초 통계</b>를 빠르게 계산하세요.
        </div>
    """, unsafe_allow_html=True)
    
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
