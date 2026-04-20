import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v3.2", layout="wide")

# 2. 커스텀 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #0E1117 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .stBox {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-bottom: 25px;
    }
    .summary-box {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #1f77b4;
        color: #333 !important;
    }
    </style>
""", unsafe_allow_html=True)

plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 프로그램")
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 1. ZXY 변환 (No. 1부터 시작 적용)
# =========================
if menu == "🔄 ZXY 변환":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 ZXY 데이터 입력 및 변환")
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    
    if st.button("🚀 ZXY 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            # [수정] 인덱스를 1부터 시작하도록 설정
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            result_df.index = result_df.index + 1
            st.dataframe(result_df, use_container_width=True, height=400)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=True).encode("utf-8-sig"), "zxy_result.csv")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 2. 그래프 분석 (강조 및 다운로드 완벽 복구)
# =========================
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📁 분석 준비")
    template_df = pd.DataFrame({"MIN": [10.0], "MAX": [10.5], "VALUE": [10.25]})
    template_out = BytesIO()
    with pd.ExcelWriter(template_out, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, index=False)
    st.download_button("📥 분석용 엑셀 양식 다운로드", template_out.getvalue(), "품질분석_양식.xlsx")
    st.markdown("---")
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

        # [화면용 그래프]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값'))
        fig_p.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_p.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_p.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_p.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst', 
                                        marker=dict(color='rgba(0,0,0,0)', size=20, line=dict(color='red', width=3))))
        st.plotly_chart(fig_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [다운로드용 이미지 및 엑셀 버튼 생성]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("💾 데이터 저장 (엑셀/이미지)")
        
        # [핵심] Matplotlib 이미지 생성 (NG/Worst 강조 포함)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', color='#1f77b4', alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: 
            ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=40, label='NG', zorder=5)
        if df.loc[worst_idx, "편차"] > 0: 
            ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2, label='Worst', zorder=6)
        
        img_buf = BytesIO()
        fig_mpl.savefig(img_buf, format='png', bbox_inches='tight')
        plt.close(fig_mpl)

        cd1, cd2 = st.columns(2)
        with cd1:
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                red_fmt = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                num_fmt = workbook.add_format({'num_format': '0.0000'})
                for i in range(len(df)):
                    fmt = red_fmt if df.iloc[i]["판정"] == "NG" else num_fmt
                    worksheet.set_row(i + 1, None, fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buf, 'x_scale': 0.6, 'y_scale': 0.6})
            st.download_button("📂 결과 엑셀 다운로드", excel_buf.getvalue(), "Quality_Report.xlsx", use_container_width=True)
        with cd2:
            st.download_button("🖼️ 그래프 이미지 다운로드", img_buf.getvalue(), "Quality_Graph.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [리포트 및 한글 요약]
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📋 종합 분석 리포트")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda r: ['background-color: #FFCCCC; color: #9C0006' if r["판정"] == "NG" else '' for _ in r], axis=1), use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        avg_v = df['VALUE'].mean()
        with c1:
            st.info("📊 **데이터 요약**")
            st.metric("샘플 / NG", f"{len(df)}개", f"{len(ng_df)}개")
            msg = f"✅ 안정적입니다." if not len(ng_df) else f"🚨 No.{worst_idx} 부근 확인 필요."
            st.markdown(f'<div class="summary-box">{msg}</div>', unsafe_allow_html=True)
        with c2: st.metric("평균값", f"{avg_v:.4f}")
        with c3: st.metric("최대 이탈", f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 3. 계산기 (안정화)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 및 MMC 정밀 계산기")
    
    # 탭 구성 (MMC 계산기 추가)
    tabs = st.tabs(["🎯 MMC 보너스 공차", "⚖️ 공차 정밀 판정", "🔧 토크 변환", "📏 단위 변환", "📊 데이터 산포"])
    
    # 1. MMC 보너스 공차 계산기 (신규 추가)
    with tabs[0]:
        st.write("### 🎯 MMC(최대 실체 조건) 및 보너스 공차 계산")
        st.caption("가공 치수가 MMC에서 벗어난 만큼 기하 공차에 보너스가 가산됩니다.")
        
        mc1, mc2 = st.columns(2)
        m_type = mc1.radio("항목 종류", ["구멍 (Internal/Hole)", "축 (External/Shaft)"], horizontal=True, key="mmc_type")
        m_geo_tol = mc2.number_input("도면 기하공차 (위치도/직도 등)", value=0.05, format="%.4f", key="mmc_geo")
        
        mc3, mc4, mc5 = st.columns(3)
        if m_type == "구멍 (Internal/Hole)":
            m_mmc = mc3.number_input("MMC 치수 (규격 최소값)", value=10.00, format="%.4f", key="mmc_val_h")
            m_act = mc4.number_input("실제 측정 치수", value=10.02, format="%.4f", key="mmc_act_h")
            bonus = max(0.0, m_act - m_mmc)
        else:
            m_mmc = mc3.number_input("MMC 치수 (규격 최대값)", value=10.00, format="%.4f", key="mmc_val_s")
            m_act = mc4.number_input("실제 측정 치수", value=9.98, format="%.4f", key="mmc_act_s")
            bonus = max(0.0, m_mmc - m_act)
            
        total_tol = m_geo_tol + bonus
        mc5.metric("최종 허용 공차", f"{total_tol:.4f}", f"Bonus: +{bonus:.4f}")
        
        st.info(f"**해설:** 실제 치수가 MMC에서 {bonus:.4f}만큼 벗어났으므로, 기하 공차는 기존 {m_geo_tol:.4f}에서 **{total_tol:.4f}**까지 허용됩니다.")

    # 2. 공차 정밀 판정 (로직 보강)
    with tabs[1]:
        st.write("### ⚖️ 상하한 공차 정밀 판정")
        p1, p2, p3, p4 = st.columns(4)
        base = p1.number_input("기준치", value=0.0, format="%.4f", key="p_base")
        u_tol = p2.number_input("상한(+)", value=0.0, format="%.4f", key="p_u_tol")
        l_tol = p3.number_input("하한(-)", value=0.0, format="%.4f", key="p_l_tol")
        measure = p4.number_input("실측치", value=0.0, format="%.4f", key="p_measure")
        
        low_lim, upp_lim = base - abs(l_tol), base + abs(u_tol)
        st.markdown("---")
        if low_lim <= measure <= upp_lim:
            st.success(f"### ✅ 판정: OK (규격: {low_lim:.4f} ~ {upp_lim:.4f})")
            st.write(f"중심 대비 편차: {measure - base:+.4f}")
        else:
            st.error(f"### 🚨 판정: NG (이탈: {measure - upp_lim if measure > upp_lim else measure - low_lim:+.4f})")

    # 3. 토크 변환
    with tabs[2]:
        st.write("### 🔧 토크 단위 변환")
        tc1, tc2 = st.columns(2)
        t_v = tc1.number_input("토크 수치", value=0.0, format="%.4f", key="t_v_c")
        t_m = tc2.selectbox("방향", ["N·m → kgf·m", "kgf·m → N·m"], key="t_m_c")
        t_r = t_v * 0.101972 if "kgf" in t_m else t_v * 9.80665
        st.success(f"**결과: {t_r:.4f}**")

    # 4. 단위 변환 (mm/um 포함)
    with tabs[3]:
        st.write("### 📏 길이/정밀 단위 변환")
        u1, u2, u3 = st.columns([2, 2, 1])
        u_i = u1.selectbox("항목", ["길이 (mm/inch)", "정밀 길이 (mm/μm)", "무게 (kg/lb)"], key="u_i_c")
        u_v = u2.number_input("수치", value=0.0, format="%.4f", key="u_v_c")
        if "mm/inch" in u_i:
            u_d = u3.selectbox("방향", ["mm → inch", "inch → mm"], key="ud1")
            u_res = u_v / 25.4 if "inch" in u_d else u_v * 25.4
        elif "mm/μm" in u_i:
            u_d = u3.selectbox("방향", ["mm → μm", "μm → mm"], key="ud2")
            u_res = u_v * 1000 if "μm" in u_d else u_v / 1000
        else:
            u_d = u3.selectbox("방향", ["kg → lb", "lb → kg"], key="ud3")
            u_res = u_v * 2.20462 if "lb" in u_d else u_v / 2.20462
        st.info(f"**결과: {u_res:.4f}**")

    # 5. 데이터 산포
    with tabs[4]:
        st.write("### 📊 데이터 산포 분석")
        s_t = st.text_area("숫자 입력 (쉼표 구분)", "10.002, 10.005, 9.998", key="s_t_c")
        try:
            s_l = [float(x.strip()) for x in s_t.split(",") if x.strip()]
            if s_l:
                sc1, sc2 = st.columns(2)
                sc1.metric("평균", f"{sum(s_l)/len(s_l):.4f}")
                sc2.metric("편차(Max-Min)", f"{max(s_l)-min(s_l):.4f}")
        except: st.error("형식을 확인하세요.")
        
    st.markdown('</div>', unsafe_allow_html=True)
