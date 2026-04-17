import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -------------------------------
# 페이지 설정
# -------------------------------
st.set_page_config(layout="wide")

# -------------------------------
# 🔥 사이드바 스타일 (핵심)
# -------------------------------
st.markdown("""
<style>
/* 사이드바 전체 */
section[data-testid="stSidebar"] {
    background-color: #1f2937;
}

/* 메뉴 글자 크게 */
div[data-testid="stSidebar"] label {
    font-size: 20px !important;
    color: white !important;
    font-weight: bold;
}

/* 라디오 버튼 */
div[role="radiogroup"] > label {
    background-color: #374151;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 8px;
    color: white !important;
}

/* 선택된 메뉴 */
div[role="radiogroup"] > label[data-baseweb="radio"] > div:first-child {
    background-color: #2563eb !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 제목
# -------------------------------
st.title("📊 품질 분석 통합 프로그램")

# -------------------------------
# 메뉴
# -------------------------------
menu = st.sidebar.radio(
    "기능 선택",
    ["📊 통계 그래프", "📐 ZXY 변환", "🔧 토크 변환"]
)

# -------------------------------
# 🔵 통계 그래프
# -------------------------------
if menu == "📊 통계 그래프":

    st.warning("⚠️ 반드시 MIN / MAX / VALUE 컬럼이 올바르게 선택되었는지 확인하세요!")

    uploaded_file = st.file_uploader("엑셀 업로드", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        st.dataframe(df)

        # 🔥 자동 컬럼 찾기
        def find_column(name):
            for col in df.columns:
                if name.lower() in col.lower():
                    return col
            return df.columns[0]

        min_default = find_column("min")
        max_default = find_column("max")
        val_default = find_column("value")

        col1, col2, col3 = st.columns(3)

        min_col = col1.selectbox("MIN", df.columns, index=df.columns.get_loc(min_default))
        max_col = col2.selectbox("MAX", df.columns, index=df.columns.get_loc(max_default))
        val_col = col3.selectbox("VALUE", df.columns, index=df.columns.get_loc(val_default))

        # 숫자 변환
        mins = pd.to_numeric(df[min_col], errors='coerce')
        maxs = pd.to_numeric(df[max_col], errors='coerce')
        values = pd.to_numeric(df[val_col], errors='coerce')

        # NG 판정
        ng = (values < mins) | (values > maxs)
        ok = ~ng

        x = np.arange(len(values))

        fig, ax = plt.subplots(figsize=(14, 6))

        # 공차 영역
        ax.fill_between(x, mins, maxs, alpha=0.2, label="Spec Range")

        # 라인
        ax.plot(x, values, linewidth=2)

        # 점
        ax.scatter(x[ok], values[ok], s=60, label="OK")
        ax.scatter(x[ng], values[ng], s=80, color='red', label="NG")

        # 평균선
        avg = values.mean()
        ax.axhline(avg, linestyle='--', linewidth=2, label="AVG")

        # Y축 자동 스케일
        low = min(values.min(), mins.min())
        high = max(values.max(), maxs.max())
        margin = (high - low) * 0.1
        ax.set_ylim(low - margin, high + margin)

        ax.set_title("Measurement Trend")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)

        st.pyplot(fig)

        # -------------------------------
        # 분석 결과
        # -------------------------------
        st.subheader("📊 자동 분석")

        total = len(values)
        ng_count = int(ng.sum())
        ng_rate = (ng_count / total) * 100 if total > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("총 데이터", total)
        col2.metric("NG 개수", ng_count)
        col3.metric("NG 비율 (%)", f"{ng_rate:.2f}")

        st.write(f"평균: {values.mean():.4f}")
        st.write(f"최소: {values.min():.4f}")
        st.write(f"최대: {values.max():.4f}")

        # 한줄 판단
        if ng_count == 0:
            st.success("✅ 공정 안정")
        elif ng_rate < 5:
            st.warning("⚠️ 일부 NG 발생")
        else:
            st.error("🚨 공정 이상")

# -------------------------------
# 🟢 ZXY 변환
# -------------------------------
elif menu == "📐 ZXY 변환":

    st.subheader("Z → X / Y 변환")

    z = st.number_input("Z 값")

    x = z * 0.866
    y = z * 0.5

    st.write(f"X: {x:.3f}")
    st.write(f"Y: {y:.3f}")

# -------------------------------
# 🟠 토크 변환
# -------------------------------
elif menu == "🔧 토크 변환":

    st.subheader("토크 변환")

    value = st.number_input("값")
    unit = st.selectbox("단위", ["kgf·cm", "N·m"])

    if unit == "kgf·cm":
        st.write(f"N·m: {value * 0.0980665:.4f}")
    else:
        st.write(f"kgf·cm: {value / 0.0980665:.4f}")
