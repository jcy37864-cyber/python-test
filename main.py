import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import platform

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 도구", layout="wide")

# 2. 한글 폰트 설정 (글자 깨짐 방지)
def set_korean_font():
    plt.rcParams['axes.unicode_minus'] = False
    system_name = platform.system()
    if system_name == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        # 리눅스/Streamlit Cloud 환경
        plt.rc('font', family='NanumGothic')

set_korean_font()

# 3. 사이드바 스타일 정의
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
</style>
""", unsafe_allow_html=True)

# 4. 사이드바 메뉴
st.sidebar.title("🛠 품질 도구함")
menu = st.sidebar.radio("메뉴를 선택하세요", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

st.title("📊 품질 측정 통합 프로그램")

# =========================
# 메뉴 1: 🔄 ZXY 변환
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 데이터 가로 변환")
    st.info("입력한 X, Y, Z 데이터를 한 행에 [Z, X, Y] 순서로 나란히 배치합니다.")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 10, "Y": [""] * 10, "Z": [""] * 10})

    # 데이터 입력 에디터
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")

    if st.button("ZXY 생성하기"):
        row_results = []
        for _, row in edited_df.iterrows():
            x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
            if x or y or z:
                # 요청하신 대로 옆으로(가로로) Z, X, Y 순서 배치
                row_results.append({"Z": z, "X": x, "Y": y})

        if row_results:
            result_df = pd.DataFrame(row_results)
            st.success("✅ 변환 완료!")
            st.dataframe(result_df, use_container_width=True)
            
            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📂 변환 데이터 CSV 다운로드", csv, "zxy_converted.csv")
        else:
            st.warning("데이터를 입력해주세요.")

# =========================
# 메뉴 2: 📈 그래프 분석
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 경향 분석 (글자 깨짐 방지 적용)")

    uploaded_file = st.file_uploader("엑셀(.xlsx) 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])

    if uploaded_file:
        # 데이터 로드
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 판정 로직
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

        # NG 강조 테이블
        def highlight_ng(row):
            return ['background-color: #ffcccc' if row["판정"] == "NG" else '' for _ in row]
        
        st.dataframe(df.style.apply(highlight_ng, axis=1), use_container_width=True)

        # 그래프 그리기
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df["VALUE"], marker='o', label="실측값(VALUE)", zorder=3)
        ax.axhline(y=df["MAX"].iloc[0], color='green', linestyle='--', label="상한(MAX)", alpha=0.7)
        ax.axhline(y=df["MIN"].iloc[0], color='orange', linestyle='--', label="하한(MIN)", alpha=0.7)

        # Worst 강조
        worst_idx = df["편차"].idxmax()
        worst_row = df.loc[worst_idx]

        for i, row in df.iterrows():
            if row["판정"] == "NG":
                ax.scatter(i, row["VALUE"], color='red', s=80, zorder=4)

        if worst_row["편차"] > 0:
            ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', s=400, linewidths=3, zorder=5)
            # 글자 시인성 개선 (하얀 배경 추가)
            ax.text(worst_idx, worst_row["VALUE"], f" Worst: {worst_row['VALUE']:.3f} ", 
                    fontsize=11, color='black', fontweight='bold',
                    ha='center', va='bottom',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='red', boxstyle='round,pad=0.5'),
                    zorder=6)

        # 우측 수치 표시
        ax.text(len(df), df["MAX"].iloc[0], f" MAX: {df['MAX'].iloc[0]:.3f}", color='green', fontweight='bold')
        ax.text(len(df), df["MIN"].iloc[0], f" MIN: {df['MIN'].iloc[0]:.3f}", color='orange', fontweight='bold')

        ax.set_title("품질 경향 분석 보고서", fontsize=15)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend()
        
        st.pyplot(fig)

        # 파일 다운로드 섹션
        col1, col2 = st.columns(2)
        with col1:
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            st.download_button("📸 그래프 이미지 저장", img_buffer.getvalue(), "quality_graph.png", "image/png")
        with col2:
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📄 결과 엑셀 다운로드", excel_buffer.getvalue(), "quality_result.xlsx")

# =========================
# 메뉴 3: 🧮 계산기
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 품질 보조 계산기")

    calc_type = st.selectbox("사용할 기능을 선택하세요", ["토크 변환", "평균 및 합계", "공차 판정"])

    if calc_type == "토크 변환":
        val = st.number_input("변환할 값 입력", value=0.0, format="%.4f")
        mode = st.radio("변환 방향", ["N·m → kgf·m", "kgf·m → N·m"])
        if mode == "N·m → kgf·m":
            st.success(f"결과: {val * 0.101972:.4f} kgf·m")
        else:
            st.success(f"결과: {val * 9.80665:.4f} N·m")

    elif calc_type == "평균 및 합계":
        nums_str = st.text_input("숫자들을 쉼표(,)로 구분해서 입력하세요 (예: 10.1, 10.2, 9.8)", "0")
        try:
            nums = [float(n.strip()) for n in nums_str.split(",") if n.strip()]
            if nums:
                st.info(f"합계: {sum(nums):.4f} / 평균: {sum(nums)/len(nums):.4f}")
        except:
            st.error("입력 형식이 잘못되었습니다.")

    elif calc_type == "공차 판정":
        col1, col2, col3 = st.columns(3)
        target = col1.number_input("기준값", value=0.0)
        tol = col2.number_input("공차(±)", value=0.0)
        measure = col3.number_input("실측치", value=0.0)
        
        if (target - tol) <= measure <= (target + tol):
            st.success("✅ 결과: OK")
        else:
            st.error("❌ 결과: NG")
