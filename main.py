import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.7", layout="wide")

# 2. 커스텀 CSS (사이드바 가독성 및 영역 구분 강화)
st.markdown("""
    <style>
    /* 메인 배경색 */
    .main { background-color: #f8f9fa; }
    
    /* [핵심] 사이드바 검정 배경에 흰색 글자 강제 설정 */
    [data-testid="stSidebar"] {
        background-color: #0E1117 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    /* 라디오 버튼 선택된 항목 강조 */
    [data-testid="stSidebar"] .st-emotion-cache-17l6i46 {
        font-weight: bold;
        border-right: 3px solid #1f77b4;
    }

    /* 섹션별 카드 스타일 (영역 구분) */
    .stBox {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-bottom: 25px;
    }
    
    /* 제목 및 강조 스타일 */
    h2 { color: #1f77b4; border-bottom: 2.5px solid #1f77b4; padding-bottom: 12px; }
    .stMetric { background-color: #f1f3f5; padding: 10px; border-radius: 8px; }
    
    /* 데이터 에디터 경계 */
    .stDataEditor { border: 1px solid #ced4da !important; }
    </style>
""", unsafe_allow_html=True)

# 폰트 및 그래프 설정
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 프로그램")

# 사이드바 메뉴 (이제 글씨가 선명하게 보입니다)
menu = st.sidebar.radio("📋 메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 ZXY 변환
# =========================
if menu == "🔄 ZXY 변환":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🔄 ZXY 데이터 입력 및 변환")
    st.info("X, Y, Z 데이터를 입력하면 [Z -> X -> Y] 순서로 세로 배열 결과를 생성합니다.")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})

    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic", key="zxy_editor")
    
    if st.button("🚀 ZXY 결과 생성", use_container_width=True):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z: results.extend([z, x, y])
        
        if results:
            st.markdown("---")
            st.subheader("📥 변환 결과 리스트")
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True, height=400)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=False).encode("utf-8-sig"), "zxy_result.csv")
        else:
            st.warning("데이터를 입력해 주세요.")
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 📈 그래프 분석 (최종 보강 버전)
# =========================
elif menu == "📈 그래프 분석":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("📈 데이터 업로드 및 추이 분석")
    uploaded_file = st.file_uploader("엑셀(XLSX) 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file:
        # 데이터 처리
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]
        ng_df = df[df["판정"] == "NG"]

        # 1. 화면용 대화형 그래프 (Plotly)
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.markdown("#### 🔍 실시간 추이 분석 (Worst Point 강조)")
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값',
            text=[f"샘플: {i}<br>판정: {p}" for i, p in zip(df.index, df["판정"])],
            hovertemplate="<b>%{text}</b><br>수치: %{y:.4f}<extra></extra>",
            line=dict(color='#1f77b4', width=2)))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        
        if not ng_df.empty:
            fig_plotly.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='NG(불량)', marker=dict(color='red', size=10)))
        
        if df.loc[worst_idx, "편차"] > 0:
            fig_plotly.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst Point',
                marker=dict(color='rgba(0,0,0,0)', size=25, line=dict(color='red', width=3))))
        
        fig_plotly.update_layout(hovermode="closest", template="plotly_white", height=500)
        st.plotly_chart(fig_plotly, use_container_width=True)
        
        # 2. 다운로드 준비 (Matplotlib)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', markersize=4, color='#1f77b4', alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=30, zorder=5)
        if df.loc[worst_idx, "편차"] > 0: ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2, zorder=6)
        
        img_buf = BytesIO()
        fig_mpl.savefig(img_buf, format='png', bbox_inches='tight', dpi=120)
        plt.close(fig_mpl)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            excel_out = BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                num_fmt = workbook.add_format({'num_format': '0.0000'})
                red_fmt = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                for r_n in range(1, len(df) + 1):
                    fmt = red_fmt if df.iloc[r_n-1]["판정"] == "NG" else num_fmt
                    worksheet.set_row(r_n, None, fmt)
                worksheet.set_column('A:E', 13, num_fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buf, 'x_scale': 0.65, 'y_scale': 0.65})
            st.download_button("📂 결과 엑셀 다운로드 (.xlsx)", excel_out.getvalue(), "Quality_Report.xlsx", use_container_width=True)
        with col_d2:
            st.download_button("🖼️ 그래프 이미지 다운로드 (.png)", img_buf.getvalue(), "Quality_Graph.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. 보강된 분석 리포트 영역
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("📋 종합 분석 리포트")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda row: ['background-color: #fff4f4' if row["판정"] == "NG" else '' for _ in row], axis=1), use_container_width=True)
        
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        avg_v = df["VALUE"].mean()
        std_v = df["VALUE"].std()
        
        with c1:
            st.info("📊 **기본 통계**")
            st.metric("전체 샘플 / NG", f"{len(df)}개", f"{len(ng_df)}개", delta_color="inverse")
            st.write(f"• 불량률: **{(len(ng_df)/len(df)*100):.2f}%**")
        with c2:
            st.info("📏 **경향 분석**")
            st.metric("측정 평균값", f"{avg_v:.4f}", f"σ: {std_v:.4f}")
            st.write(f"• 범위(R): {df['VALUE'].max()-df['VALUE'].min():.4f}")
        with c3:
            st.info("📍 **Worst 분석**")
            worst_status = f"{worst_val:.4f}" if df.loc[worst_idx, "편차"] > 0 else "N/A"
            st.metric("Worst 측정값", worst_status, f"Index: {worst_idx}")
            if df.loc[worst_idx, "편차"] > 0:
                st.write(f"• 규격 이탈량: **{df.loc[worst_idx, '편차']:.4f}**")
        st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 🧮 계산기 (정상 작동 로직)
# =========================
elif menu == "🧮 계산기":
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🧮 품질 보조 계산기")
    
    # 탭 구성 (기초 단위 변환 추가)
    tabs = st.tabs(["🔧 토크 변환", "📏 기초 단위 변환", "📊 합계/평균", "⚖️ 공차 판정"])
    
    # 1. 토크 변환 탭
    with tabs[0]:
        st.write("### 토크 단위 상호 변환")
        col_t1, col_t2 = st.columns(2)
        val_t = col_t1.number_input("토크 수치 입력", value=0.0, format="%.4f", key="torque_input")
        mode_t = col_t2.selectbox("변환 방향", ["N·m → kgf·m", "kgf·m → N·m"], key="torque_mode")
        
        # N·m <-> kgf·m 변환 로직
        res_t = val_t * 0.101972 if "kgf" in mode_t else val_t * 9.80665
        st.success(f"**변환 결과: {res_t:.4f} {'kgf·m' if 'kgf' in mode_t else 'N·m'}**")

    # 2. 기초 단위 변환 탭 (새로 추가)
    with tabs[1]:
        st.write("### 실무 기초 단위 변환")
        c_u1, c_u2, c_u3 = st.columns([2, 2, 1])
        
        unit_type = c_u1.selectbox("측정 항목", ["길이 (mm/inch)", "무게 (kg/lb)", "압력 (MPa/psi/bar)"])
        val_u = c_u2.number_input("수치 입력", value=0.0, format="%.4f", key="unit_val")
        
        if "길이" in unit_type:
            u_mode = c_u3.selectbox("방향", ["mm → inch", "inch → mm"])
            res_u = val_u / 25.4 if "inch" in u_mode else val_u * 25.4
            unit_label = "inch" if "inch" in u_mode else "mm"
            
        elif "무게" in unit_type:
            u_mode = c_u3.selectbox("방향", ["kg → lb", "lb → kg"])
            res_u = val_u * 2.20462 if "lb" in u_mode else val_u / 2.20462
            unit_label = "lb" if "lb" in u_mode else "kg"
            
        elif "압력" in unit_type:
            u_mode = c_u3.selectbox("방향", ["MPa → psi", "psi → MPa", "MPa → bar", "bar → MPa"])
            if u_mode == "MPa → psi": res_u = val_u * 145.038
            elif u_mode == "psi → MPa": res_u = val_u / 145.038
            elif u_mode == "MPa → bar": res_u = val_u * 10
            elif u_mode == "bar → MPa": res_u = val_u / 10
            unit_label = u_mode.split("→")[1].strip()

        st.info(f"**변환 결과: {res_u:.4f} {unit_label}**")

    # 3. 합계/평균 탭
    with tabs[2]:
        st.write("### 데이터 합계 및 평균")
        txt = st.text_area("숫자들을 쉼표(,)로 구분하여 입력", "10.5, 20.1234, 15.7", key="stat_input")
        try:
            v_list = [float(x.strip()) for x in txt.split(",") if x.strip()]
            if v_list:
                st.info(f"합계: **{sum(v_list):.4f}** |  평균: **{sum(v_list)/len(v_list):.4f}** |  샘플수: {len(v_list)}")
        except: st.error("올바른 숫자 형식을 입력하세요.")

    # 4. 공차 판정 탭
    with tabs[3]:
        st.write("### 상하한 분리 공차 판정")
        cc1, cc2, cc3, cc4 = st.columns(4)
        tar = cc1.number_input("기준값", 0.0, format="%.4f", key="tol_tar")
        ut = cc2.number_input("상한(+)", 0.0, format="%.4f", key="tol_ut")
        lt = cc3.number_input("하한(-)", 0.0, format="%.4f", key="tol_lt")
        ms = cc4.number_input("측정값", 0.0, format="%.4f", key="tol_ms")
        mi, ma = tar - abs(lt), tar + abs(ut)
        if mi <= ms <= ma: st.success(f"**✅ OK** (규격: {mi:.4f} ~ {ma:.4f})")
        else: st.error(f"**🚨 NG** (이탈량: {ms-ma if ms>ma else ms-mi:.4f})")
        
    st.markdown('</div>', unsafe_allow_html=True)
