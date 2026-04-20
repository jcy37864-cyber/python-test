import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 시스템 v4.4", layout="wide")

# 2. 커스텀 CSS
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .stBox { background-color: #ffffff; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); margin-bottom: 24px; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 15px 20px; border-radius: 12px; }
    .summary-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 6px solid #3b82f6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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
    convert_mode = st.selectbox("📝 변환 방식을 선택하세요", ["ZXY 변환 (표준)", "XYZ 변환 (추가 예정)"], index=0)
    if convert_mode == "ZXY 변환 (표준)":
        if "df_zxy" not in st.session_state: st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
        edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key="editor_v44")
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
                st.text_area("📋 간편 복사", "\n".join(map(str, results)), height=150)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 📈 2. 그래프 분석 (기능 완전 복구) ---
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
        avg_v, std_v = df['VALUE'].mean(), df['VALUE'].std()

        # 화면용 대화형 그래프
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='정상', line=dict(color='#3b82f6')))
        if not ng_df.empty: fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=12)))
        fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        fig_p.update_layout(hoverlabel=dict(bgcolor="black", font_size=20))
        st.plotly_chart(fig_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 요약 대시보드
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📊 품질 분석 대시보드")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📦 전체 샘플", f"{len(df)} EA")
        c2.metric("✅ 합격 (OK)", f"{len(df)-len(ng_df)} EA", delta=f"{((len(df)-len(ng_df))/len(df))*100:.1f}%")
        c3.metric("🚨 불량 (NG)", f"{len(ng_df)} EA", delta=f"-{len(ng_df)}", delta_color="inverse")
        c4.metric("🎯 Worst", f"{worst_val:.3f}", f"Idx: {worst_idx}")

        # --- [중요] 엑셀용 정적 그래프 2종 생성 ---
        # 1. Line 그래프
        fig_l, ax_l = plt.subplots(figsize=(10, 4))
        ax_l.plot(df.index, df["VALUE"], marker='o', color='#3b82f6', zorder=1)
        ax_l.axhline(y=df["MAX"].iloc[0], color='green', ls='--')
        ax_l.axhline(y=df["MIN"].iloc[0], color='orange', ls='--')
        if not ng_df.empty: ax_l.scatter(ng_df.index, ng_df["VALUE"], color='red', s=60, zorder=5)
        ax_l.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=250, lw=2, zorder=6) # Worst 강조
        img_l = BytesIO(); fig_l.savefig(img_l, format='png', bbox_inches='tight'); plt.close(fig_l)

        # 2. Bar 그래프
        fig_b, ax_b = plt.subplots(figsize=(10, 4))
        colors = ['red' if p == "NG" else '#3b82f6' for p in df["판정"]]
        ax_b.bar(df.index, df["VALUE"], color=colors)
        ax_b.axhline(y=df["MAX"].iloc[0], color='green', ls='--')
        ax_b.axhline(y=df["MIN"].iloc[0], color='orange', ls='--')
        y_min, y_max = min(df["VALUE"].min(), df["MIN"].min()) * 0.99, max(df["VALUE"].max(), df["MAX"].max()) * 1.01
        ax_b.set_ylim(y_min, y_max)
        img_b = BytesIO(); fig_b.savefig(img_b, format='png', bbox_inches='tight'); plt.close(fig_b)

        # --- [중요] 엑셀 파일 생성 (2종 그래프 + 시트 강조) ---
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            workbook = writer.book
            worksheet = writer.sheets['Report']
            red_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            num_fmt = workbook.add_format({'num_format': '0.0000'})
            
            for i in range(len(df)):
                fmt = red_fmt if df.iloc[i]["판정"] == "NG" else num_fmt
                worksheet.set_row(i + 1, None, fmt)
            
            worksheet.insert_image('H2', 'line.png', {'image_data': img_l, 'x_scale': 0.5, 'y_scale': 0.5})
            worksheet.insert_image('H22', 'bar.png', {'image_data': img_b, 'x_scale': 0.5, 'y_scale': 0.5})

        st.markdown("<br>", unsafe_allow_html=True)
        dc1, dc2 = st.columns(2)
        dc1.download_button("📂 엑셀 보고서 다운로드 (그래프 2종)", excel_out.getvalue(), "Quality_Report_v44.xlsx", use_container_width=True)
        dc2.download_button("🖼️ 라인 그래프 저장", img_l.getvalue(), "Trend_Line.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- 🧮 3. 계산기 (코드 누락 없이 전체 복구) ---
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 계산 도구")
    tabs = st.tabs(["🎯 MMC 보너스", "⚖️ 공차 판정", "🔧 토크 변환", "📏 단위 변환", "📊 데이터 산포"])
    with tabs[0]:
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("종류", ["구멍 (Hole)", "축 (Shaft)"], horizontal=True)
        m_geo = mc2.number_input("도면 기하공차", value=0.05, format="%.4f")
        mc3, mc4, mc5 = st.columns(3)
        m_mmc, m_act = mc3.number_input("MMC 규격", value=10.0), mc4.number_input("실측치", value=10.02)
        bonus = max(0.0, m_act - m_mmc if "구멍" in m_type else m_mmc - m_act)
        mc5.metric("최종 허용 공차", f"{m_geo + bonus:.4f}")
    with tabs[1]:
        p1, p2, p3, p4 = st.columns(4)
        base, u_t, l_t, ms = p1.number_input("기준"), p2.number_input("상한"), p3.number_input("하한"), p4.number_input("측정")
        lo, up = base - abs(l_t), base + abs(u_t)
        if lo <= ms <= up: st.success("✅ OK")
        else: st.error("🚨 NG")
    with tabs[2]:
        v, m = st.number_input("수치"), st.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"])
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
