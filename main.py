import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -------------------------------
# 한글 설정
# -------------------------------
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(layout="wide")
st.title("📊 품질 분석 통합 프로그램")

# -------------------------------
# 좌측 메뉴
# -------------------------------
menu = st.sidebar.radio(
    "기능 선택",
    ["통계 그래프", "ZXY 변환", "토크 변환"]
)

# -------------------------------
# 🔵 1. 통계 그래프
# -------------------------------
if menu == "통계 그래프":

    uploaded_file = st.file_uploader("엑셀 업로드 (MIN / MAX / VALUE)", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        st.dataframe(df)

        min_col = st.selectbox("MIN", df.columns)
        max_col = st.selectbox("MAX", df.columns)
        val_col = st.selectbox("VALUE", df.columns)

        # 🔥 숫자 변환 (중요)
        mins = pd.to_numeric(df[min_col], errors='coerce')
        maxs = pd.to_numeric(df[max_col], errors='coerce')
        values = pd.to_numeric(df[val_col], errors='coerce')

        # 🔥 NG 판정 (행별 비교로 수정)
        ng = (values < mins) | (values > maxs)
        ok = ~ng

        x = np.arange(len(values))

        fig, ax = plt.subplots(figsize=(14, 6))

        # 공차 영역 (평균이 아니라 실제 범위)
        ax.fill_between(x, mins, maxs, alpha=0.2, label="Spec Range")

        # 선 (트렌드)
        ax.plot(x, values, linewidth=2)

        # 점
        ax.scatter(x[ok], values[ok], s=60, label="OK")
        ax.scatter(x[ng], values[ng], s=80, color='red', label="NG")

        # 평균선
        avg = values.mean()
        ax.axhline(avg, linestyle='--', linewidth=2, label="AVG")

        # 🔥 Y축 자동 스케일
        low = min(values.min(), mins.min())
        high = max(values.max(), maxs.max())
        margin = (high - low) * 0.1
        ax.set_ylim(low - margin, high + margin)

        ax.set_title("Measurement Trend")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.5)

        st.pyplot(fig)

        # -------------------------------
        # 분석
        # -------------------------------
        st.subheader("📊 분석 결과")

        total = len(values)
        ng_count = int(ng.sum())
        ng_rate = (ng_count / total) * 100 if total > 0 else 0

        st.write(f"총 데이터: {total}")
        st.write(f"NG 개수: {ng_count}")
        st.write(f"NG 비율: {ng_rate:.2f}%")

        # 🔥 디버깅 표시 (문제 확인용)
        st.write("NG 데이터 미리보기")
        st.dataframe(df[ng])

# -------------------------------
# 🟢 2. ZXY 변환
# -------------------------------
elif menu == "ZXY 변환":

    st.subheader("Z → X / Y 변환")

    z = st.number_input("Z 값 입력")

    x = z * 0.866
    y = z * 0.5

    st.write(f"X 값: {x:.3f}")
    st.write(f"Y 값: {y:.3f}")

# -------------------------------
# 🟠 3. 토크 변환
# -------------------------------
elif menu == "토크 변환":

    st.subheader("토크 변환기")

    value = st.number_input("값 입력")
    unit = st.selectbox("단위", ["kgf·cm", "N·m"])

    if unit == "kgf·cm":
        result = value * 0.0980665
        st.write(f"N·m: {result:.4f}")
    else:
        result = value / 0.0980665
        st.write(f"kgf·cm: {result:.4f}")
