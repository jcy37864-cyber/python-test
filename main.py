import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="통합 변환기", layout="wide")

st.title("📊 통합 변환 프로그램")

# 👉 화면 분할
col1, col2 = st.columns([1, 1])

# =========================
# 📊 왼쪽: 변환기 선택
# =========================
with col1:

    st.subheader("변환기 선택")

    selected = st.selectbox(
        "사용할 기능을 선택하세요",
        [
            "ZXY 변환",
            "토크 변환",
            "기능 추가 예정 1",
            "기능 추가 예정 2"
        ]
    )

    # =========================
    # 🔵 1. ZXY 변환기
    # =========================
    if selected == "ZXY 변환":

        st.markdown("### Z → X → Y 변환")

        if "df" not in st.session_state:
            st.session_state.df = pd.DataFrame({
                "X": [""] * 100,
                "Y": [""] * 100,
                "Z": [""] * 100,
            })

        edited_df = st.data_editor(
            st.session_state.df,
            num_rows="fixed",
            use_container_width=True,
            key="editor"
        )

        if st.button("결과 생성"):

            df = edited_df.copy()
            results = []

            for _, row in df.iterrows():
                x = str(row["X"]).strip()
                y = str(row["Y"]).strip()
                z = str(row["Z"]).strip()

                if x and y and z:
                    results.extend([z, x, y])

            st.subheader("결과")

            for r in results:
                st.write(r)

            # CSV 다운로드
            csv_data = "\n".join(results)
            st.download_button("CSV 다운로드", data=csv_data)

            # 엑셀 다운로드
            output = BytesIO()
            df_result = pd.DataFrame(results, columns=["결과"])

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_result.to_excel(writer, index=False)

            st.download_button("엑셀 다운로드", data=output.getvalue())

    # =========================
    # 🔧 2. 토크 변환기
    # =========================
    elif selected == "토크 변환":

        st.markdown("### 🔧 토크 변환기")

        val = st.number_input("값 입력", value=0.0)

        mode = st.selectbox(
            "변환 선택",
            ["N·m → kgf·m", "kgf·m → N·m"]
        )

        if st.button("변환 실행"):

            if mode == "N·m → kgf·m":
                result = val * 0.101972
                st.success(f"{result:.4f} kgf·m")
            else:
                result = val * 9.80665
                st.success(f"{result:.4f} N·m")

    # =========================
    # 🧩 3. 확장 슬롯 1
    # =========================
    elif selected == "기능 추가 예정 1":

        st.info("👉 여기에 새로운 기능을 추가하면 됩니다")

    # =========================
    # 🧩 4. 확장 슬롯 2
    # =========================
    elif selected == "기능 추가 예정 2":

        st.info("👉 여기에 또 다른 기능 추가 가능")

# =========================
# 🧩 오른쪽: 메모 & 확장
# =========================
with col2:

    st.subheader("🧩 작업 공간")

    st.markdown("### 📝 메모")

    note = st.text_area(
        "필요한 기능 기록",
        placeholder="예: 공차 계산, 평균, 합불 판정 등",
        height=200
    )

    st.markdown("---")

    st.markdown("### 📌 아이디어")

    st.write("""
    ✔ 공차 계산기  
    ✔ 평균 / 표준편차  
    ✔ 합격 / 불합격 자동 판정  
    ✔ 엑셀 업로드 자동 처리  
    """)
