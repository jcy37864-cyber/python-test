import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.1", layout="wide")

# 2. 그래프 및 표시 설정
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 
pd.options.display.float_format = '{:.4f}'.format # 데이터프레임 기본 소수점 설정

# 3. 사이드바 스타일
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 측정 통합 프로그램")

menu = st.sidebar.radio(
    "메뉴 선택",
    ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"]
)

# =========================
# 🔄 ZXY 변환
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 데이터 변환")
    st.info("X, Y, Z를 입력하면 [Z -> X -> Y] 순서로 데이터가 세로로 쌓여 결과가 생성됩니다.")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({
            "X": [""] * 100, "Y": [""] * 100, "Z": [""] * 100,
        })

    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")

    if st.button("ZXY 결과 생성"):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z:
                results.extend([z, x, y])

        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True)
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📂 CSV 다운로드", csv, "zxy_result.csv")
        else:
            st.warning("데이터를 입력해주세요.")

# =========================
# 📈 그래프 분석 (최종 수정판)
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")

    uploaded_file = st.file_uploader("엑셀 또는 CSV 파일 업로드", type=["xlsx", "csv"])

    # 템플릿 다운로드 (소수점 4자리 예시)
    template = pd.DataFrame({"MIN": [30.1000], "MAX": [30.7000], "VALUE": [30.3521]})
    tmp_out = BytesIO()
    with pd.ExcelWriter(tmp_out, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)
    st.download_button("📄 템플릿 다운로드", tmp_out.getvalue(), "template.xlsx")

    if uploaded_file:
        # 데이터 로드
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        
        # 소수점 4자리 반올림 적용
        df = df.round(4)
        
        # 판정 및 편차 계산
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1).round(4)

        # 1. 화면용 Plotly 대화형 그래프
        st.markdown("#### 🔍 대화형 추이 분석 (마우스 오버 시 샘플번호 확인 가능)")
        fig_plotly = go.Figure()
        fig_plotly.add_trace(go.Scatter(
            x=df.index, y=df["VALUE"], mode='lines+markers', name='측정값',
            text=[f"샘플: {i}<br>판정: {p}" for i, p in zip(df.index, df["판정"])],
            hovertemplate="<b>%{text}</b><br>수치: %{y:.4f}<extra></extra>",
            line=dict(color='#1f77b4', width=2)
        ))
        fig_plotly.add_hline(y=df["MAX"].iloc[0], line_dash="dash", line_color="green", annotation_text="MAX")
        fig_plotly.add_hline(y=df["MIN"].iloc[0], line_dash="dash", line_color="orange", annotation_text="MIN")
        
        ng_points_df = df[df["판정"] == "NG"]
        if not ng_points_df.empty:
            fig_plotly.add_trace(go.Scatter(
                x=ng_points_df.index, y=ng_points_df["VALUE"], mode='markers', name='불량(NG)',
                marker=dict(color='red', size=10),
                hovertemplate="<b>🚨 NG 샘플: %{x}</b><br>수치: %{y:.4f}<extra></extra>"
            ))
        
        fig_plotly.update_layout(hovermode="closest", template="plotly_white", margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_plotly, use_container_width=True)

        # 2. 데이터 테이블 표시 (소수점 4자리 강제 포맷팅)
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]
        st.dataframe(df.style.format(subset=["MIN", "MAX", "VALUE", "편차"], formatter="{:.4f}").apply(highlight_ng, axis=1), use_container_width=True)

        # 3. 엑셀 저장용 Matplotlib 그래프 (NG 빨간점 및 Worst 강조 복구)
        fig_mpl, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df.index, df["VALUE"], marker='o', markersize=4, color='#1f77b4', label="Value", alpha=0.7)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--', alpha=0.6)
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--')
        
        # NG 지점 빨간색 점 표시 (복구)
        if not ng_points_df.empty:
            ax.scatter(ng_points_df.index, ng_points_df["VALUE"], color='red', s=30, zorder=5, label="NG")
        
        # Worst 지점 강조
        worst_idx = df["편차"].idxmax()
        if df.loc[worst_idx, "편차"] > 0:
            ax.scatter(worst_idx, df.loc[worst_idx, "VALUE"], facecolors='none', edgecolors='red', s=300, linewidths=2, zorder=6)
        
        ax.set_title("Quality Trend (Excel Attachment)")
        ax.grid(True, linestyle=':', alpha=0.5)
        
        img_buffer = BytesIO()
        fig_mpl.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close(fig_mpl)

        # 4. 결과 엑셀 다운로드 (소수점 서식 포함)
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Result')
            workbook, worksheet = writer.book, writer.sheets['Result']
            
            # 소수점 4자리 서식 정의
            num_format = workbook.add_format({'num_format': '0.0000'})
            red_format = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006', 'num_format': '0.0000'})
            
            # 열 전체에 소수점 4자리 적용 및 NG 행 강조
            for row_num in range(1, len(df) + 1):
                is_ng = df.iloc[row_num-1]["판정"] == "NG"
                current_format = red_format if is_ng else num_format
                worksheet.set_row(row_num, None, current_format)
            
            # 헤더 제외한 수치 열(A~E 등)에 포맷 강제 적용
            worksheet.set_column('A:E', 12, num_format)
            
            # 그래프 이미지 삽입
            worksheet.insert_image('H2', 'graph.png', {'image_data': img_buffer, 'x_scale': 0.65, 'y_scale': 0.65})

        st.download_button("📸 결과 엑셀 다운로드 (소수점 4자리+이미지)", excel_out.getvalue(), "quality_report_final.xlsx")

        # 5. 요약 섹션 (소수점 4자리)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 검사 결과 요약")
            total, ng_count = len(df), len(df[df["판정"] == "NG"])
            st.write(f"• 전체 샘플: {total} / 양호: {total-ng_count} / 불량: {ng_count}")
            
            avg_val = df["VALUE"].mean()
            if ng_count == 0: st.success(f"✅ 모든 데이터 규격 만족 (평균: {avg_val:.4f})")
            else: st.error(f"🚨 규격 이탈 발생 (총 {ng_count}건 / 평균: {avg_val:.4f})")
            
            if avg_val > df["MAX"].mean(): st.error(f"📉 경향 분석: 평균이 상한에 치우쳐 있습니다.")
            elif avg_val < df["MIN"].mean(): st.error(f"📈 경향 분석: 평균이 하한에 치우쳐 있습니다.")
            else: st.info(f"✔ 경향 분석: 공정이 규격 중앙에서 안정적입니다.")

        with col2:
            st.markdown("### 📍 Worst Point 상세")
            worst_row = df.loc[worst_idx]
            if worst_row["편차"] > 0:
                st.error(f"**최대 편차 값: {worst_row['VALUE']:.4f}**")
                st.write(f"• 샘플 번호: {worst_idx} / 편차량: {worst_row['편차']:.4f}")
            else: st.info("✅ 특이사항 없음 (전체 양호)")

# =========================
# 🧮 계산기 (소수점 4자리)
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "합계/평균", "공차 판정"])
    
    if calc == "토크 변환":
        val = st.number_input("수치 입력", 0.0, format="%.4f")
        mode = st.selectbox("변환 선택", ["N·m → kgf·m", "kgf·m → N·m"])
        res = val * 0.101972 if "kgf" in mode else val * 9.80665
        st.success(f"결과: {res:.4f}")

    elif calc == "합계/평균":
        nums = st.text_input("값 입력 (쉼표 구분)", "10.1234, 20.5678")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals: st.info(f"합계: {sum(vals):.4f} / 평균: {sum(vals)/len(vals):.4f}")
        except: st.error("입력 형식을 확인하세요.")

    elif calc == "공차 판정":
        st.info("상하한 공차 분리 판정 (소수점 4자리)")
        c1, c2, c3, c4 = st.columns(4)
        target = c1.number_input("기준값", 0.0, format="%.4f")
        u_tol = c2.number_input("상한(+)", 0.0, format="%.4f")
        l_tol = c3.number_input("하한(-)", 0.0, format="%.4f")
        meas = c4.number_input("측정값", 0.0, format="%.4f")
        mi, ma = target - abs(l_tol), target + abs(u_tol)
        
        st.markdown("---")
        if mi <= meas <= ma:
            st.success(f"### 판정 결과: OK ✅ ({mi:.4f} ~ {ma:.4f})")
        else:
            diff = meas - ma if meas > ma else meas - mi
            st.error(f"### 판정 결과: NG 🚨 (이탈: {diff:.4f})")
