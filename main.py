import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="품질 측정 프로그램", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

# =========================
# 🔥 프로그램 선택
# =========================
app_mode = st.selectbox(
    "프로그램 선택",
    ["ZXY 변환기", "통계 / 그래프"]
)

# =========================
# 1️⃣ ZXY 변환기
# =========================
if app_mode == "ZXY 변환기":

    st.subheader("🔄 ZXY 변환기")

    mode = st.radio("입력 방식", ["수동 입력", "엑셀 업로드"])

    # ✅ 수동 입력 (튕김 방지 핵심)
    if mode == "수동 입력":

        if "df_zxy" not in st.session_state:
            st.session_state.df_zxy = pd.DataFrame({
                "X": [""] * 100,
                "Y": [""] * 100,
                "Z": [""] * 100,
            })

        edited_df = st.data_editor(
            st.session_state.df_zxy,
            use_container_width=True,
            key="editor_zxy"
        )

    # ✅ 엑셀 업로드
    else:
        uploaded_file = st.file_uploader("엑셀 업로드 (X,Y,Z 컬럼 필요)", type=["xlsx"])

        if uploaded_file:
            edited_df = pd.read_excel(uploaded_file)
            st.dataframe(edited_df)
        else:
            edited_df = None

    # ✅ 변환 실행
    if st.button("ZXY 변환 실행"):

        if edited_df is None:
            st.warning("데이터 없음")
        else:
            results = []

            for _, row in edited_df.iterrows():
                x = str(row.get("X", "")).strip()
                y = str(row.get("Y", "")).strip()
                z = str(row.get("Z", "")).strip()

                if x and y and z:
                    results.extend([z, x, y])

            if len(results) == 0:
                st.warning("유효한 데이터 없음")
            else:
                st.subheader("📌 결과 (세로 정렬)")

                result_df = pd.DataFrame(results, columns=["결과"])
                st.dataframe(result_df, use_container_width=True)

                # ✅ CSV 다운로드
                csv_data = result_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "CSV 다운로드",
                    data=csv_data,
                    file_name="zxy_result.csv"
                )

                # ✅ 엑셀 다운로드 (openpyxl 사용)
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    result_df.to_excel(writer, index=False)

                st.download_button(
                    "엑셀 다운로드",
                    data=output.getvalue(),
                    file_name="zxy_result.xlsx"
                )

# =========================
# 2️⃣ 통계 / 그래프
# =========================
elif app_mode == "통계 / 그래프":

    st.subheader("📈 통계 / 그래프 분석")

    nums = st.text_area(
        "데이터 입력 (콤마 또는 줄바꿈)",
        "1,2,3,4,5"
    )

    if st.button("분석 실행"):

        try:
            raw = nums.replace("\n", ",").split(",")
            values = [float(x.strip()) for x in raw if x.strip() != ""]

            if len(values) == 0:
                st.warning("데이터 없음")
            else:
                avg = sum(values) / len(values)
                mx = max(values)
                mn = min(values)

                st.success(f"평균: {avg:.4f}")
                st.info(f"최대: {mx} / 최소: {mn}")

                # ✅ 그래프
                fig, ax = plt.subplots()
                ax.hist(values)
                ax.set_title("데이터 분포")
                st.pyplot(fig)

        except:
            st.error("입력 형식 오류")
