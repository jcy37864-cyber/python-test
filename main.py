import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="품질 측정 프로그램", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

# =========================
# 🔥 좌우 분할
# =========================
left, right = st.columns([2, 1])

# =========================
# 🔥 메인 프로그램 선택
# =========================
with left:

    app_mode = st.selectbox(
        "프로그램 선택",
        ["ZXY 변환", "통계 / 그래프"]
    )

    # =========================
    # 🔄 ZXY 변환 (입력형)
    # =========================
    if app_mode == "ZXY 변환":

        st.subheader("🔄 ZXY 변환 (데이터 입력)")

        if "zxy_df" not in st.session_state:
            st.session_state.zxy_df = pd.DataFrame({
                "X": [""] * 50,
                "Y": [""] * 50,
                "Z": [""] * 50
            })

        edited_df = st.data_editor(
            st.session_state.zxy_df,
            use_container_width=True
        )

        if st.button("변환 실행"):
            results = []

            for _, row in edited_df.iterrows():
                x = str(row["X"]).strip()
                y = str(row["Y"]).strip()
                z = str(row["Z"]).strip()

                if x and y and z:
                    results.extend([z, x, y])

            result_df = pd.DataFrame(results, columns=["결과"])

            st.subheader("결과")
            st.dataframe(result_df, use_container_width=True)

            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("CSV 다운로드", csv, "zxy_result.csv")

    # =========================
    # 📈 통계 / 그래프 (엑셀)
    # =========================
    elif app_mode == "통계 / 그래프":

        st.subheader("📈 통계 / 그래프")

        file = st.file_uploader("엑셀 업로드", type=["xlsx"])

        # 템플릿
        template = pd.DataFrame({"값": []})
        buf = BytesIO()
        template.to_excel(buf, index=False)

        st.download_button("📥 템플릿 다운로드", buf.getvalue(), "template.xlsx")

        if file:
            df = pd.read_excel(file)

            try:
                values = df.iloc[:, 0].dropna().astype(float)

                avg = values.mean()
                st.write(f"평균: {avg:.4f}")

                # 공차 입력
                lsl = st.number_input("LSL", value=0.0)
                usl = st.number_input("USL", value=10.0)

                df_result = pd.DataFrame({"값": values})
                df_result["판정"] = df_result["값"].apply(
                    lambda x: "NG" if x < lsl or x > usl else "OK"
                )

                ng = (df_result["판정"] == "NG").sum()
                st.write(f"NG: {ng}")

                # 표 색상
                def color(val):
                    return "background-color:red;color:white" if val == "NG" else ""

                st.dataframe(
                    df_result.style.applymap(color, subset=["판정"]),
                    use_container_width=True
                )

                # 그래프
                fig, ax = plt.subplots()

                ok = df_result[df_result["판정"] == "OK"]["값"]
                ngv = df_result[df_result["판정"] == "NG"]["값"]

                ax.hist(ok, alpha=0.7, label="OK")
                ax.hist(ngv, alpha=0.7, label="NG")

                ax.axvline(avg, linestyle="--", label="AVG")
                ax.axvline(lsl, linestyle="--", label="LSL")
                ax.axvline(usl, linestyle="--", label="USL")

                ax.legend()
                st.pyplot(fig)

            except:
                st.error("데이터 오류")

# =========================
# 🔧 오른쪽: 계산 / 기타 기능
# =========================
with right:

    st.subheader("🔧 계산 / 변환 도구")

    tool = st.selectbox(
        "도구 선택",
        ["토크 변환", "공차 계산"]
    )

    # =========================
    # 🔩 토크 변환
    # =========================
    if tool == "토크 변환":

        st.markdown("### 🔩 토크 변환")

        value = st.number_input("값 입력", value=0.0)

        mode = st.radio(
            "변환 선택",
            ["N·m → kgf·cm", "kgf·cm → N·m"]
        )

        if mode == "N·m → kgf·cm":
            result = value * 10.1972
        else:
            result = value / 10.1972

        st.success(f"결과: {result:.4f}")

    # =========================
    # 📏 공차 계산
    # =========================
    elif tool == "공차 계산":

        st.markdown("### 📏 공차 계산")

        target = st.number_input("목표값", value=0.0)
        upper = st.number_input("상한", value=0.0)
        lower = st.number_input("하한", value=0.0)

        tol = upper - lower

        st.info(f"공차: {tol}")
        st.write(f"편차(+): {upper - target}")
        st.write(f"편차(-): {target - lower}")
