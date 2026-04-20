import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램", layout="wide")

# 2. 그래프 폰트 설정 (그래프 내부 글자 깨짐 방지를 위해 영문 기본 폰트 사용)
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
            "X": [""] * 100,
            "Y": [""] * 100,
            "Z": [""] * 100,
        })

    edited_df = st.data_editor(
        st.session_state.df_zxy,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("ZXY 결과 생성"):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z:
                results.extend([z, x, y]) # 세로 쌓기 방식

        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True)
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📂 CSV 다운로드", csv, "zxy_result.csv")
        else:
            st.warning("데이터를 입력해주세요.")

# =========================
# 📈 그래프 분석
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")

    uploaded_file = st.file_uploader("엑셀 또는 CSV 파일 업로드", type=["xlsx", "csv"])

    # 템플릿 다운로드
    template = pd.DataFrame({"MIN": [30.1], "MAX": [30.7], "VALUE": [30.3]})
    tmp_out = BytesIO()
    with pd.ExcelWriter(tmp_out, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)
    st.download_button("📄 템플릿 다운로드", tmp_out.getvalue(), "template.xlsx")

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

        # NG 강조 테이블
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]
        st.dataframe(df.style.apply(highlight_ng, axis=1), use_container_width=True)

        # 📊 그래프 생성
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df["VALUE"], marker='o', markersize=4, label="VALUE", zorder=3, alpha=0.8)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--', alpha=0.6, label="MAX")
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--', alpha=0.6, label="MIN")

        # NG 및 Worst 강조
        worst_idx = df["편차"].idxmax()
        worst_row = df.loc[worst_idx]

        ng_points = df[df["판정"] == "NG"]
        ax.scatter(ng_points.index, ng_points["VALUE"], color='red', s=40, zorder=4)

        if worst_row["편차"] > 0:
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', 
                       s=450, linewidths=2.5, zorder=5)
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', 
                       s=200, linewidths=1.5, zorder=5, alpha=0.5)

        # 수치 레이블
        ax.text(len(df)-1, df["MAX"].iloc[-1], f"MAX: {df['MAX'].iloc[-1]:.3f}", color='green', ha='right', fontweight='bold')
        ax.text(len(df)-1, df["MIN"].iloc[-1], f"MIN: {df['MIN'].iloc[-1]:.3f}", color='orange', ha='right', fontweight='bold')

        ax.set_title("Quality Trend Analysis (Worst Point Highlighted)")
        ax.set_xlabel("Sample Index")
        ax.set_ylabel("Value")
        ax.legend(loc='lower left')
        ax.grid(True, linestyle=':', alpha=0.4)
        st.pyplot(fig)

        # 이미지 다운로드
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        st.download_button("📸 그래프 이미지 저장", img_buffer.getvalue(), "quality_graph.png", "image/png")

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 검사 결과 요약")
            total, ng = len(df), len(df[df["판정"] == "NG"])
            st.write(f"• 전체 샘플: {total}개 / 양호: {total-ng}개 / **불량: {ng}개**")
            if ng == 0: st.success("✅ 판정: 모든 데이터 규격 만족")
            else: st.error(f"🚨 판정: 규격 이탈 발생 (NG {ng}건)")

            avg_val = df["VALUE"].mean()
            if avg_val > df["MAX"].mean(): st.error("📉 경향: 전체적으로 상한값 초과 추세")
            elif avg_val < df["MIN"].mean(): st.error("📈 경향: 전체적으로 하한값 미달 추세")
            else: st.info("✔ 경향: 전체적인 분포가 규격 내 안정적임")

        with col2:
            st.markdown("### 📍 Worst Point 상세 정보")
            if worst_row["편차"] > 0:
                st.error(f"**최대 편차 측정값: {worst_row['VALUE']:.4f}**")
                st.write(f"• 데이터 순번(Index): {worst_idx}")
                st.write(f"• 규격 대비 편차량: {worst_row['편차']:.4f}")
                st.write(f"• 판정: {worst_row['판정']}")
            else:
                st.info("Worst 포인트가 없습니다. (전체 양호)")

        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📄 결과 엑셀 다운로드", excel_out.getvalue(), "quality_result.xlsx")

# =========================
# 🧮 계산기
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "합계/평균", "공차 판정"])

    if calc == "토크 변환":
        val = st.number_input("수치 입력", 0.0)
        mode = st.selectbox("변환 선택", ["N·m → kgf·m", "kgf·m → N·m"])
        if mode == "N·m → kgf·m": st.success(f"결과: {val * 0.101972:.4f} kgf·m")
        else: st.success(f"결과: {val * 9.80665:.4f} N·m")

    elif calc == "합계/평균":
        nums = st.text_input("값 입력 (쉼표 구분)", "10, 20, 30")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals: st.info(f"합계: {sum(vals):.2f} / 평균: {sum(vals)/len(vals):.2f}")
        except: st.error("입력 형식을 확인하세요.")

    elif calc == "공차 판정":
        st.info("기준값 대비 상한(+) 공차와 하한(-) 공차를 각각 입력하여 판정합니다.")
        
        col1, col2, col3, col4 = st.columns(4)
        
        target = col1.number_input("기준값 (Target)", value=0.0, format="%.4f")
        upper_tol = col2.number_input("상한공차 (+)", value=0.0, format="%.4f")
        lower_tol = col3.number_input("하한공차 (-)", value=0.0, format="%.4f")
        measure = col4.number_input("측정값 (Value)", value=0.0, format="%.4f")
        
        # 합격 범위 계산 (하한은 절댓값을 빼고, 상한은 절댓값을 더함)
        min_limit = target - abs(lower_tol)
        max_limit = target + abs(upper_tol)
        
        st.markdown("---")
        
        res_col1, res_col2 = st.columns(2)
        
        with res_col1:
            st.write(f"**규격 범위:** {min_limit:.4f} ~ {max_limit:.4f}")
            if min_limit <= measure <= max_limit:
                st.success(f"### 판정 결과: OK ✅")
            else:
                st.error(f"### 판정 결과: NG 🚨")
                
        with res_col2:
            if measure > max_limit:
                diff = measure - max_limit
                st.warning(f"상한 초과: +{diff:.4f}")
            elif measure < min_limit:
                diff = min_limit - measure
                st.warning(f"하한 미달: -{diff:.4f}")
            else:
                st.info("규격 이내 안정적")
