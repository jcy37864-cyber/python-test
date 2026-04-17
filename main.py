import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")

# -------------------------------
# 🔥 UI 스타일 최종
# -------------------------------
st.markdown("""
<style>

/* 사이드바 */
section[data-testid="stSidebar"] {
    background-color: #111827;
}

/* 사이드바 텍스트 */
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* 라디오 버튼 */
div[role="radiogroup"] label {
    font-size: 16px;
    background-color: #1f2937;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 5px;
}

/* 선택 강조 */
div[role="radiogroup"] label:has(input:checked) {
    background-color: #2563eb !important;
    font-weight: bold;
}

/* 컬럼 박스 색상 */
div[data-testid="column"]:nth-child(1) {
    background-color: #e0f2fe;
    padding: 10px;
    border-radius: 10px;
}
div[data-testid="column"]:nth-child(2) {
    background-color: #fef9c3;
    padding: 10px;
    border-radius: 10px;
}
div[data-testid="column"]:nth-child(3) {
    background-color: #dcfce7;
    padding: 10px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

st.title("📊 품질 분석 시스템")

# -------------------------------
# 메뉴
# -------------------------------
menu = st.sidebar.radio(
    "기능 선택",
    ["📊 통계 그래프", "📐 ZXY 변환", "🔧 토크 변환"]
)

# -------------------------------
# 📊 통계 그래프
# -------------------------------
if menu == "📊 통계 그래프":

    st.warning("⚠️ 반드시 MIN / MAX / VALUE 컬럼 확인하세요!")

    uploaded_file = st.file_uploader("엑셀 업로드", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.dataframe(df)

        # 자동 컬럼 찾기
        def find_column(name):
            for col in df.columns:
                if name.lower() in col.lower():
                    return col
            return df.columns[0]

        min_default = find_column("min")
        max_default = find_column("max")
        val_default = find_column("value")

        col1, col2, col3 = st.columns(3)

        min_col = col1.selectbox("🔵 MIN (선택)", df.columns, index=df.columns.get_loc(min_default))
        max_col = col2.selectbox("🟡 MAX (선택)", df.columns, index=df.columns.get_loc(max_default))
        val_col = col3.selectbox("🟢 VALUE (선택)", df.columns, index=df.columns.get_loc(val_default))

        mins = pd.to_numeric(df[min_col], errors='coerce')
        maxs = pd.to_numeric(df[max_col], errors='coerce')
        values = pd.to_numeric(df[val_col], errors='coerce')

        ng = (values < mins) | (values > maxs)
        ok = ~ng

        x = np.arange(len(values))

        fig, ax = plt.subplots(figsize=(14, 6))

        # 공차 영역
        ax.fill_between(x, mins, maxs, alpha=0.15, label="Spec Range")

        # 트렌드 라인
        ax.plot(x, values, linewidth=2)

        # 점
        ax.scatter(x[ok], values[ok], s=60, label="OK")
        ax.scatter(x[ng], values[ng], s=80, color='red', label="NG")

        # 평균선
        avg = values.mean()
        ax.axhline(avg, linestyle='--', linewidth=2, label="AVG")

        # 🔥 MIN / MAX 라인 + 숫자 표시
        min_line = mins.mean()
        max_line = maxs.mean()

        ax.axhline(min_line, linestyle=':', linewidth=2)
        ax.axhline(max_line, linestyle=':', linewidth=2)

        ax.text(len(x)-1, min_line, f"MIN: {min_line:.3f}", color='blue', ha='right')
        ax.text(len(x)-1, max_line, f"MAX: {max_line:.3f}", color='blue', ha='right')

        # 🔥 NG 구간 빨간 박스
        for i in range(len(values)):
            if ng.iloc[i]:
                ax.axvspan(i-0.5, i+0.5, color='red', alpha=0.15)

        # Y축 자동
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

        col1, col2, col3 = st.columns(3)
        col1.metric("총 데이터", total)
        col2.metric("NG 개수", ng_count)
        col3.metric("NG 비율 (%)", f"{ng_rate:.2f}")

        if ng_count == 0:
            st.success("✅ 공정 안정")
        elif ng_rate < 5:
            st.warning("⚠️ 일부 NG 발생")
        else:
            st.error("🚨 공정 이상")

# -------------------------------
# ZXY 변환
# -------------------------------
elif menu == "📐 ZXY 변환":

    st.subheader("Z → X / Y 변환")

    z = st.number_input("Z 값")
    st.write(f"X: {z * 0.866:.3f}")
    st.write(f"Y: {z * 0.5:.3f}")

# -------------------------------
# 토크 변환
# -------------------------------
elif menu == "🔧 토크 변환":

    st.subheader("토크 변환")

    value = st.number_input("값")
    unit = st.selectbox("단위", ["kgf·cm", "N·m"])

    if unit == "kgf·cm":
        st.write(f"N·m: {value * 0.0980665:.4f}")
    else:
        st.write(f"kgf·cm: {value / 0.0980665:.4f}")
