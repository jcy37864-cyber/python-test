import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import platform

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
# 🔄 ZXY 변환 (기존 세로 쌓기 로직)
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
            x = str(row["X"]).strip()
            y = str(row["Y"]).strip()
            z = str(row["Z"]).strip()

            if x and y and z:
                # 초기 요청 로직: Z, X, Y 순으로 리스트에 순차 추가 (세로 출력용)
                results.extend([z, x, y])

        if results:
            result_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(result_df, use_container_width=True)
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📂 CSV 다운로드", csv, "zxy_result.csv")
        else:
            st.warning("변환할 데이터를 입력해주세요.")

# =========================
# 📈 그래프 분석 (기능 완전 복구 + 그래프 영문 표기)
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
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 판정 및 편차 계산
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

        # NG 강조 테이블 (한글 판정 유지)
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]
        st.dataframe(df.style.apply(highlight_ng, axis=1), use_container_width=True)

        # 📊 그래프 생성 (내부 텍스트는 깨짐 방지를 위해 영문 유지)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["VALUE"], marker='o', label="VALUE", zorder=3)
        ax.plot(df["MIN"], linestyle='--', color='orange', label="MIN")
        ax.plot(df["MAX"], linestyle='--', color='green', label="MAX")

        # NG 및 Worst 포인트 강조
        worst_idx = df["편차"].idxmax()
        worst_row = df.loc[worst_idx]

        for i, row in df.iterrows():
            if row["판정"] == "NG":
                ax.scatter(i, row["VALUE"], color='red', s=80, zorder=4)

        if worst_row["편차"] > 0:
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', s=300, linewidths=3, zorder=5)
            # 워스트 포인트 말풍선 (가독성 개선)
            ax.text(worst_idx, worst_row["VALUE"], f" Worst: {worst_row['VALUE']:.3f} ", 
                    fontsize=10, color='black', fontweight='bold', ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.9, edgecolor='red', boxstyle='round,pad=0.5'), zorder=6)

        # 수치 표시
        ax.text(len(df)-1, df["MAX"].iloc[-1], f"MAX: {df['MAX'].iloc[-1]:.3f}", color='green', ha='right')
        ax.text(len(df)-1, df["MIN"].iloc[-1], f"MIN: {df['MIN'].iloc[-1]:.3f}", color='orange', ha='right')

        ax.set_title("Quality Trend Analysis")
        ax.set_xlabel("Sample Index")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        st.pyplot(fig)

        # 이미지 다운로드
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        st.download_button("📸 그래프 이미지 저장", img_buffer.getvalue(), "quality_graph.png", "image/png")

        # 🔥 [완전 복구] 검사 결과 요약 (한글)
        st.markdown("---")
        st.markdown("### 📋 검사 결과 요약")
        total = len(df)
        ng_count = len(df[df["판정"] == "NG"])
        ok_count = total - ng_count

        st.write(f"▶ **총 데이터:** {total}개 / **양호(OK):** {ok_count}개 / **불량(NG):** {ng_count}개")

        if ng_count == 0:
            st.success("✅ 판정: 전체 양호 (모든 값이 규격 내에 있음)")
        elif ng_count / total > 0.3:
            st.error("🚨 판정: NG 다수 발생 → 공정 이상 가능성 높음")
        else:
            st.warning("⚠️ 판정: 일부 NG 발생 → 공정 편차 확인 필요")

        # [완전 복구] 평균 경향 분석 (한글)
        avg_val = df["VALUE"].mean()
        avg_max = df["MAX"].mean()
        avg_min = df["MIN"].mean()

        if avg_val > avg_max:
            st.error("📉 경향: 전체적으로 상한 규격을 초과하는 경향이 있음")
        elif avg_val < avg_min:
            st.error("📈 경향: 전체적으로 하한 규격에 미달하는 경향이 있음")
        else:
            st.info("✔ 경향: 전체적으로 규격 내 분포가 안정적임")

        # 📄 결과 엑셀 다운로드
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📄 결과 엑셀 다운로드", excel_buffer.getvalue(), "quality_result.xlsx")

# =========================
# 🧮 계산기 (한글 복구)
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "합계", "평균", "공차 판정"])

    if calc == "토크 변환":
        val = st.number_input("수치 입력", 0.0)
        mode = st.selectbox("단위 변환 선택", ["N·m → kgf·m", "kgf·m → N·m"])
        if mode == "N·m → kgf·m":
            st.success(f"결과: {val * 0.101972:.4f} kgf·m")
        else:
            st.success(f"Result: {val * 9.80665:.4f} N·m")

    elif calc == "합계":
        a = st.number_input("값 A", 0.0)
        b = st.number_input("값 B", 0.0)
        st.success(f"합계 결과: {a + b}")

    elif calc == "평균":
        nums = st.text_input("값 입력 (쉼표로 구분)", "1, 2, 3")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals: st.success(f"평균 결과: {sum(vals)/len(vals):.4f}")
        except:
            st.error("입력 형식이 올바르지 않습니다.")

    elif calc == "공차 판정":
        col1, col2, col3 = st.columns(3)
        t = col1.number_input("기준값", value=0.0)
        tol = col2.number_input("공차(±)", value=0.0)
        v = col3.number_input("측정값", value=0.0)
        if t - tol <= v <= t + tol:
            st.success("결과: OK (합격)")
        else:
            st.error("결과: NG (불합격)")
