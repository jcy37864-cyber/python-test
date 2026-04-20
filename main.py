import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.4", layout="wide")

# 2. 그래프 설정
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

# 3. 사이드바 스타일
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 측정 통합 프로그램")

menu = st.sidebar.radio("메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 ZXY 변환
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 데이터 변환")
    st.info("X, Y, Z를 입력하면 [Z -> X -> Y] 순서로 데이터가 세로로 쌓여 결과가 생성됩니다.")
    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100})
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    if st.button("ZXY 결과 생성"):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z: results.extend([z, x, y])
        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True)
            st.download_button("📂 CSV 다운로드", result_df.to_csv(index=False).encode("utf-8-sig"), "zxy_result.csv")

# =========================
# 📈 그래프 분석 (요약부 대폭 보강)
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")
    uploaded_file = st.file_uploader("파일 업로드", type=["xlsx", "csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df = df.round(4)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)
        
        worst_idx = df["편차"].idxmax()
        worst_val = df.loc[worst_idx, "VALUE"]
        ng_df = df[df["판정"] == "NG"]

        # 1. 화면용 Plotly 그래프
        st.markdown("#### 🔍 대화형 추이 분석 (Worst Point 원 강조)")
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(
            x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값',
            text=[f"샘플: {i}<br>판정: {p}" for i, p in zip(df.index, df["판정"])],
            hovertemplate="<b>%{text}</b><br>수치: %{y:.4f}<extra></extra>",
            line=dict(color='#1f77b4', width=2)
        ))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        if not ng_df.empty:
            fig_plotly.add_trace(go.Scatter(x=ng_df.index, y=ng_df["VALUE"], mode='markers', name='불량(NG)', marker=dict(color='red', size=10)))
        if df.loc[worst_idx, "편차"] > 0:
            fig_plotly.add_trace(go.Scatter(x=[worst_idx], y=[worst_val], mode='markers', name='Worst',
                marker=dict(color='rgba(0,0,0,0)', size=25, line=dict(color='red', width=3))))
        fig_plotly.update_layout(hovermode="closest", template="plotly_white", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_plotly, use_container_width=True)

        # 2. 다운로드 버튼 섹션
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', markersize=4, color='#1f77b4', alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--')
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        if not ng_df.empty: ax.scatter(ng_df.index, ng_df["VALUE"], color='red', s=30, zorder=5)
        if df.loc[worst_idx, "편차"] > 0: ax.scatter(worst_idx, worst_val, facecolors='none', edgecolors='red', s=300, linewidths=2)
        
        img_buffer = BytesIO()
        fig_mpl.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close(fig_mpl)

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            excel_out = BytesIO()
            with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Result')
                workbook, worksheet = writer.book, writer.sheets['Result']
                num_fmt = workbook.add_format({'num_format': '0.0000'})
                red_fmt = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
                for r_n in range(1, len(df) + 1):
                    f = red_fmt if df.iloc[r_n-1]["판정"] == "NG" else num_fmt
                    worksheet.set_row(r_n, None, f)
                worksheet.set_column('A:E', 12, num_fmt)
                worksheet.insert_image('H2', 'graph.png', {'image_data': img_buffer, 'x_scale': 0.65, 'y_scale': 0.65})
            st.download_button("📂 결과 엑셀 다운로드", excel_out.getvalue(), "quality_report.xlsx", use_container_width=True)
        with c_d2:
            st.download_button("🖼️ 그래프 이미지 다운로드", img_buffer.getvalue(), "quality_graph.png", use_container_width=True)

        # 3. 데이터 테이블 및 보강된 요약부
        st.markdown("---")
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(
            lambda row: ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row], axis=1), use_container_width=True)

        st.markdown("### 📋 검사 결과 정밀 분석")
        col_sum1, col_sum2, col_sum3 = st.columns(3)
        
        with col_sum1:
            st.info("🏠 **데이터 기본 정보**")
            st.write(f"• 전체 샘플 수: **{len(df)}개**")
            st.write(f"• 양호(OK): {len(df)-len(ng_df)}개 / 불량(NG): {len(ng_df)}개")
            st.write(f"• 불량률: **{(len(ng_df)/len(df)*100):.2f}%**")
            if len(ng_df) == 0: st.success("✅ 최종 판정: **PASS**")
            else: st.error("🚨 최종 판정: **FAIL**")

        with col_sum2:
            st.info("📏 **통계 및 경향 분석**")
            avg_v = df["VALUE"].mean()
            std_v = df["VALUE"].std()
            max_v, min_v = df["VALUE"].max(), df["VALUE"].min()
            st.write(f"• 평균값: **{avg_v:.4f}**")
            st.write(f"• 표준편차(σ): {std_v:.4f}")
            st.write(f"• 범위(R): {max_v - min_v:.4f} ({min_v:.4f} ~ {max_v:.4f})")
            
            # 경향 상세 분석
            target_center = (df["MAX"].iloc[0] + df["MIN"].iloc[0]) / 2
            bias = avg_v - target_center
            if abs(bias) > (df["MAX"].iloc[0] - df["MIN"].iloc[0]) * 0.2:
                dir_txt = "상한" if bias > 0 else "하한"
                st.warning(f"⚠️ 경향: 중심 대비 **{dir_txt}** 편중됨")
            else: st.success("✔ 경향: 중심부 분포 안정적")

        with col_sum3:
            st.info("📍 **최대 이탈(Worst) 정보**")
            if df.loc[worst_idx, "편차"] > 0:
                st.error(f"• 최대 편차 수치: **{worst_val:.4f}**")
                st.write(f"• 해당 데이터 순번: **{worst_idx}번**")
                st.write(f"• 규격 대비 이탈량: {df.loc[worst_idx, '편차']:.4f}")
                st.write(f"• 이탈 방향: {'상한 초과' if worst_val > df['MAX'].iloc[0] else '하한 미달'}")
            else: st.write("✅ 규격 이탈 데이터가 없습니다.")

# =========================
# 🧮 계산기 (토크 변환 로직 수리 완료)
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "합계/평균", "공차 판정"])
    
    if calc == "토크 변환":
        st.info("N·m와 kgf·m 단위를 상호 변환합니다.")
        c1, c2 = st.columns(2)
        val = c1.number_input("입력 수치", value=0.0, format="%.4f")
        mode = c2.selectbox("변환 방향", ["N·m → kgf·m", "kgf·m → N·m"])
        
        # 변환 로직 (작동 확인 완료)
        if mode == "N·m → kgf·m":
            res = val * 0.101972
            st.success(f"### 결과: {res:.4f} kgf·m")
        else:
            res = val * 9.80665
            st.success(f"### 결과: {res:.4f} N·m")

    elif calc == "합계/평균":
        nums = st.text_input("값 입력 (쉼표 구분)", "10, 20.5, 30.1234")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals: st.info(f"합계: {sum(vals):.4f} / 평균: {sum(vals)/len(vals):.4f} / 샘플수: {len(vals)}")
        except: st.error("입력 형식을 확인하세요 (예: 10, 20, 30.5)")

    elif calc == "공차 판정":
        st.info("기준값 대비 상하한 공차 분리 판정 (소수점 4자리)")
        c1, c2, c3, c4 = st.columns(4)
        target = c1.number_input("기준값", 0.0, format="%.4f")
        u_tol = c2.number_input("상한(+)", 0.0, format="%.4f")
        l_tol = c3.number_input("하한(-)", 0.0, format="%.4f")
        meas = c4.number_input("측정값", 0.0, format="%.4f")
        mi, ma = target - abs(l_tol), target + abs(u_tol)
        
        st.markdown("---")
        if mi <= meas <= ma: st.success(f"### 판정 결과: OK ✅ ({mi:.4f} ~ {ma:.4f})")
        else:
            diff = meas - ma if meas > ma else meas - mi
            st.error(f"### 판정 결과: NG 🚨 (이탈량: {diff:.4f})")
