import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import platform

# 페이지 설정
st.set_page_config(page_title="품질 측정 도구", layout="wide")

# ---------------------
# 🎨 한글 폰트 깨짐 방지 보강
# ---------------------
def set_korean_font():
    plt.rcParams['axes.unicode_minus'] = False
    system_name = platform.system()
    if system_name == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        # 리눅스/Streamlit Cloud 환경용 (폰트가 설치되어 있어야 함)
        plt.rc('font', family='NanumGothic')

set_korean_font()

# ---------------------
# 🎨 사이드바 스타일
# ---------------------
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 측정 통합 프로그램")

menu = st.sidebar.radio("메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 ZXY 변환 (가로 배열 수정)
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 변환")
    st.info("데이터를 입력하고 'ZXY 생성'을 누르면 각 행이 Z, X, Y 순서로 가로로 재배열됩니다.")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 10, "Y": [""] * 10, "Z": [""] * 10})

    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")

    if st.button("ZXY 생성"):
        row_results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x or y or z:  # 하나라도 입력값이 있으면
                row_results.append({"Z": z, "X": x, "Y": y})

        if row_results:
            result_df = pd.DataFrame(row_results)
            st.write("▼ 변환 결과 (Z-X-Y 순서)")
            st.dataframe(result_df, use_container_width=True)
            
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("CSV 다운로드", csv, "zxy_converted.csv")
        else:
            st.warning("입력된 데이터가 없습니다.")

# =========================
# 📈 그래프 분석 (글자 깨짐 & Worst 시인성 수정)
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")

    uploaded_file = st.file_uploader("엑셀 또는 CSV 파일 업로드", type=["xlsx", "csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

        # 📊 그래프 생성
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df["VALUE"], marker='o', label="실측값(VALUE)", zorder=3)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--', label="상한선(MAX)", alpha=0.7)
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--', label="하한선(MIN)", alpha=0.7)

        # NG/Worst 강조 로직
        worst_idx = df["편차"].idxmax()
        worst_row = df.loc[worst_idx]

        for i, row in df.iterrows():
            if row["판정"] == "NG":
                ax.scatter(i, row["VALUE"], color='red', s=80, zorder=4)

        if worst_row["편차"] > 0:
            # 원 강조
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', s=400, linewidths=3, zorder=5)
            # 텍스트 강조 (흰색 박스 배경 추가로 가독성 확보)
            ax.text(worst_idx, worst_row["VALUE"], f" Worst: {worst_row['VALUE']:.3f} ", 
                    fontsize=11, color='black', fontweight='bold',
                    ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.5'),
                    zorder=6)

        # 우측 끝 수치 표시
        ax.text(len(df), df["MAX"].iloc[0], f" MAX: {df['MAX'].iloc[0]:.3f}", color='green', fontweight='bold')
        ax.text(len(df), df["MIN"].iloc[0], f" MIN: {df['MIN'].iloc[0]:.3f}", color='orange', fontweight='bold')

        ax.set_title("품질 경향 분석 보고서", fontsize=15)
        ax.set_xlabel("측정 순번")
        ax.set_ylabel("측정치")
        ax.legend(loc='lower left')
        ax.grid(True, linestyle=':', alpha=0.5)
        
        st.pyplot(fig)

        # 이미지 저장 버튼
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        st.download_button("📸 그래프 이미지 저장", img_buffer.getvalue(), "quality_graph.png", "image/png")

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
