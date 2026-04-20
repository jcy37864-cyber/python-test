import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import platform

# 페이지 설정
st.set_page_config(page_title="품질 측정 도구", layout="wide")

# ---------------------
# 🎨 한글 폰트 깨짐 방지
# ---------------------
if platform.system() == 'Windows':
    plt.rc('font', family='Malgun Gothic')
elif platform.system() == 'Darwin':
    plt.rc('font', family='AppleGothic')
else:
    plt.rc('font', family='NanumGothic')

plt.rcParams['axes.unicode_minus'] = False

# ---------------------
# 🎨 사이드바 스타일
# ---------------------
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #0E1117;
}
[data-testid="stSidebar"] * {
    color: white;
}
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
    st.subheader("🔄 ZXY 변환")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({
            "X": [""] * 10,  # 가독성을 위해 초기값 조정
            "Y": [""] * 10,
            "Z": [""] * 10,
        })

    edited_df = st.data_editor(
        st.session_state.df_zxy,
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("ZXY 생성"):
        results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x and y and z:
                results.extend([z, x, y])

        if results:
            result_df = pd.DataFrame(results, columns=["결과"])
            st.dataframe(result_df)
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("CSV 다운로드", csv, "zxy.csv")
        else:
            st.warning("입력된 데이터가 없습니다.")

# =========================
# 📈 그래프 분석
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")

    # 템플릿 다운로드 섹션
    template = pd.DataFrame({"MIN": [30.1], "MAX": [30.7], "VALUE": [30.3]})
    tmp_buffer = BytesIO()
    with pd.ExcelWriter(tmp_buffer, engine="openpyxl") as writer:
        template.to_excel(writer, index=False)
    st.download_button("📄 템플릿 다운로드", tmp_buffer.getvalue(), "template.xlsx")

    uploaded_file = st.file_uploader("엑셀 또는 CSV 파일 업로드", type=["xlsx", "csv"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 판정 로직
        df["판정"] = df.apply(
            lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1
        )

        # NG 강조 테이블 스타일
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]

        st.dataframe(df.style.apply(highlight_ng, axis=1), use_container_width=True)

        # 📊 그래프 생성
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["VALUE"], marker='o', label="실측값(VALUE)", color='#1f77b4', zorder=3)
        ax.plot(df["MIN"], linestyle='--', label="하한선(MIN)", color='orange', alpha=0.7)
        ax.plot(df["MAX"], linestyle='--', label="상한선(MAX)", color='green', alpha=0.7)

        # 편차 계산 및 Worst 포인트 추출
        df["편차"] = df.apply(
            lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1
        )
        
        worst_idx = df["편차"].idxmax()
        worst_row = df.loc[worst_idx]

        # NG 포인트 시각화
        for i, row in df.iterrows():
            if row["판정"] == "NG":
                ax.scatter(i, row["VALUE"], color='red', s=80, zorder=4)

        # Worst 포인트 강조 (원 테두리 + 텍스트)
        if worst_row["편차"] > 0:
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', 
                       edgecolors='red', s=300, linewidths=3, zorder=5)
            ax.text(worst_idx, worst_row["VALUE"], f"Worst: {worst_row['VALUE']:.3f}", 
                    fontsize=10, ha='center', va='bottom', color='red', fontweight='bold')

        # 수치 표시
        ax.text(len(df)-1, df["MAX"].iloc[-1], f" MAX: {df['MAX'].iloc[-1]:.3f}", color='green', va='center')
        ax.text(len(df)-1, df["MIN"].iloc[-1], f" MIN: {df['MIN'].iloc[-1]:.3f}", color='orange', va='center')

        ax.set_title("품질 경향 분석 보고서")
        ax.set_xlabel("측정 순번")
        ax.set_ylabel("측정치")
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)
        
        st.pyplot(fig)

        # 📸 그래프 이미지 다운로드
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        st.download_button("📸 그래프 이미지 저장", img_buffer.getvalue(), "quality_graph.png", "image/png")

        # 📋 분석 결과 요약
        total = len(df)
        ng_count = len(df[df["판정"] == "NG"])
        ok_count = total - ng_count

        st.markdown("---")
        st.markdown("### 📋 검사 결과 요약")
        col1, col2, col3 = st.columns(3)
        col1.metric("총 데이터", f"{total}개")
        col2.metric("OK", f"{ok_count}개")
        col3.metric("NG", f"{ng_count}개", delta=f"{ng_count}", delta_color="inverse")

        # 상태 메시지
        if ng_count == 0:
            st.success("✅ 전체 양호: 모든 데이터가 규격 내에 있습니다.")
        elif ng_count / total > 0.3:
            st.error("🚨 경고: NG 발생률이 높습니다. 공정을 점검하세요.")
        else:
            st.warning("⚠️ 주의: 일부 NG가 발견되었습니다.")

        # 📄 결과 엑셀 다운로드
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📄 분석 결과 엑셀 다운로드", excel_buffer.getvalue(), 
                           "quality_result.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# =========================
# 🧮 계산기
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")
    
    calc = st.selectbox("기능 선택", ["토크 변환", "합계/평균", "공차 판정"])

    if calc == "토크 변환":
        val = st.number_input("측정값 입력", value=0.0, format="%.4f")
        mode = st.radio("단위 선택", ["N·m → kgf·m", "kgf·m → N·m"])
        if mode == "N·m → kgf·m":
            st.info(f"결과: **{val * 0.101972:.4f}** kgf·m")
        else:
            st.info(f"결과: **{val * 9.80665:.4f}** N·m")

    elif calc == "합계/평균":
        nums = st.text_input("숫자들을 쉼표(,)로 구분하여 입력", "10.2, 10.5, 10.1")
        try:
            vals = [float(x.strip()) for x in nums.split(",") if x.strip()]
            if vals:
                st.success(f"합계: {sum(vals):.4f} / 평균: {sum(vals)/len(vals):.4f}")
        except ValueError:
            st.error("올바른 숫자 형식을 입력해주세요.")

    elif calc == "공차 판정":
        col1, col2, col3 = st.columns(3)
        t = col1.number_input("기준값", value=0.0)
        tol = col2.number_input("공차(±)", value=0.0)
        v = col3.number_input("현재 측정값", value=0.0)

        if t - tol <= v <= t + tol:
            st.success("✅ 판정 결과: OK (규격 내)")
        else:
            st.error("❌ 판정 결과: NG (규격 외)")
