import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")

# -------------------------------
# UI 스타일
# -------------------------------
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #111827;
}
section[data-testid="stSidebar"] * {
    color: white !important;
}
div[role="radiogroup"] label {
    font-size: 16px;
    background-color: #1f2937;
    padding: 10px;
    border-radius: 8px;
    margin-bottom: 5px;
}
div[role="radiogroup"] label:has(input:checked) {
    background-color: #2563eb !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 분석 시스템")

# -------------------------------
# 메뉴
# -------------------------------
menu = st.sidebar.radio(
    "기능 선택",
    ["📊 통계 그래프", "📐 ZXY 정렬", "🧮 계산기"]
)

# -------------------------------
# 📊 그래프
# -------------------------------
if menu == "📊 통계 그래프":

    st.warning("⚠️ 반드시 MIN / MAX / VALUE 컬럼 확인하세요!")

    uploaded_file = st.file_uploader("엑셀 업로드", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        def find_column(name):
            for col in df.columns:
                if name.lower() in col.lower():
                    return col
            return df.columns[0]

        min_col = find_column("min")
        max_col = find_column("max")
        val_col = find_column("value")

        col1, col2, col3 = st.columns(3)

        min_col = col1.selectbox("🔵 MIN (선택)", df.columns, index=df.columns.get_loc(min_col))
        max_col = col2.selectbox("🟡 MAX (선택)", df.columns, index=df.columns.get_loc(max_col))
        val_col = col3.selectbox("🟢 VALUE (선택)", df.columns, index=df.columns.get_loc(val_col))

        mins = pd.to_numeric(df[min_col], errors='coerce')
        maxs = pd.to_numeric(df[max_col], errors='coerce')
        values = pd.to_numeric(df[val_col], errors='coerce')

        ng = (values < mins) | (values > maxs)
        ok = ~ng

        # NG 강조 테이블
        def highlight(row):
            if row[val_col] < row[min_col] or row[val_col] > row[max_col]:
                return ["background-color: red"] * len(row)
            return [""] * len(row)

        st.dataframe(df.style.apply(highlight, axis=1))

        # 🔥 데이터 번호 1부터 시작
        x = np.arange(1, len(values) + 1)

        fig, ax = plt.subplots(figsize=(14, 6))

        ax.fill_between(x, mins, maxs, alpha=0.15)
        ax.plot(x, values)

        ax.scatter(x[ok], values[ok])
        ax.scatter(x[ng], values[ng], color='red')

        # 평균선
        ax.axhline(values.mean(), linestyle='--')

        # MIN MAX 표시
        min_line = mins.mean()
        max_line = maxs.mean()

        ax.axhline(min_line, linestyle=':')
        ax.axhline(max_line, linestyle=':')

        ax.text(x[-1], min_line, f"MIN: {min_line:.3f}", ha='right')
        ax.text(x[-1], max_line, f"MAX: {max_line:.3f}", ha='right')

        # 최악 NG
        deviation = np.where(values < mins, mins - values, values - maxs)
        deviation = np.where(ng, deviation, 0)

        if ng.any():
            idx = np.argmax(deviation)
            val = values.iloc[idx]

            ax.scatter(x[idx], val, color='red', s=120)
            ax.text(x[idx], val, f"Worst NG: {val:.3f}", color='red')

        # NG 박스
        for i in range(len(values)):
            if ng.iloc[i]:
                ax.axvspan(x[i]-0.5, x[i]+0.5, color='red', alpha=0.1)

        ax.set_title("Measurement Trend")
        ax.grid(True, linestyle="--", alpha=0.5)

        st.pyplot(fig)

# -------------------------------
# 📐 ZXY 정렬
# -------------------------------
elif menu == "📐 ZXY 정렬":

    st.subheader("Z / X / Y 데이터 정렬")

    st.write("데이터 입력 후 정렬 기준을 선택하세요")

    df_input = pd.DataFrame({
        "Z": [],
        "X": [],
        "Y": []
    })

    edited_df = st.data_editor(df_input, num_rows="dynamic")

    sort_option = st.selectbox(
        "정렬 기준 선택",
        ["Z → X → Y", "X → Y → Z", "Y → Z → X"]
    )

    if st.button("정렬 실행"):

        if sort_option == "Z → X → Y":
            sorted_df = edited_df.sort_values(by=["Z", "X", "Y"])
        elif sort_option == "X → Y → Z":
            sorted_df = edited_df.sort_values(by=["X", "Y", "Z"])
        else:
            sorted_df = edited_df.sort_values(by=["Y", "Z", "X"])

        st.subheader("정렬 결과")
        st.dataframe(sorted_df)

        # 🔥 CSV 저장 기능
        csv = sorted_df.to_csv(index=False).encode('utf-8-sig')

        st.download_button(
            label="📥 CSV 다운로드",
            data=csv,
            file_name="ZXY_sorted.csv",
            mime="text/csv"
        )

# -------------------------------
# 🧮 계산기
# -------------------------------
elif menu == "🧮 계산기":

    tab1, tab2 = st.tabs(["공차 계산", "토크 변환"])

    # 공차 계산
    with tab1:
        st.subheader("공차 계산")

        base = st.number_input("기준값")
        tol = st.number_input("± 공차")

        st.write(f"MIN: {base - tol:.4f}")
        st.write(f"MAX: {base + tol:.4f}")

    # 토크 변환
    with tab2:
        st.subheader("토크 변환")

        value = st.number_input("값 입력")
        unit = st.selectbox("단위", ["kgf·cm", "N·m"])

        if unit == "kgf·cm":
            st.write(f"N·m: {value * 0.0980665:.4f}")
        else:
            st.write(f"kgf·cm: {value / 0.0980665:.4f}")
