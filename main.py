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
# 🔥 왼쪽: 메인 프로그램
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

        st.subheader("🔄 ZXY 변환 (직접 입력)")

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

            if len(results) == 0:
                st.warning("데이터 없음")
            else:
                result_df = pd.DataFrame(results, columns=["결과"])

                st.subheader("결과")
                st.dataframe(result_df, use_container_width=True)

                csv = result_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("CSV 다운로드", csv, "zxy_result.csv")

    # =========================
    # 📈 통계 / 그래프 (엑셀 기반)
    # =========================
    elif app_mode == "통계 / 그래프":

        st.subheader("📈 통계 / 그래프 (엑셀 업로드)")

        file = st.file_uploader("엑셀 업로드", type=["xlsx"])

        # ✅ 템플릿 (샘플 포함)
        template = pd.DataFrame({
            "ID": [1, 2, 3],
            "VALUE": [10.1, 9.9, 10.3],
            "MIN": [9.5, 9.5, 9.5],
            "MAX": [10.5, 10.5, 10.5]
        })

        buf = BytesIO()
        template.to_excel(buf, index=False)

        st.download_button("📥 템플릿 다운로드", buf.getvalue(), "template.xlsx")

        if file:
            df = pd.read_excel(file)
            st.dataframe(df, use_container_width=True)

            # 🔥 컬럼 선택
            value_col = st.selectbox("VALUE 컬럼 선택", df.columns)
            min_col = st.selectbox("MIN 컬럼 선택", df.columns)
            max_col = st.selectbox("MAX 컬럼 선택", df.columns)

            try:
                values = df[value_col].astype(float)
                mins = df[min_col].astype(float)
                maxs = df[max_col].astype(float)

                avg = values.mean()

                # NG 판정
                df_result = pd.DataFrame({
                    "값": values,
                    "MIN": mins,
                    "MAX": maxs
                })

                df_result["판정"] = df_result.apply(
                    lambda r: "NG" if r["값"] < r["MIN"] or r["값"] > r["MAX"] else "OK",
                    axis=1
                )

                ng = (df_result["판정"] == "NG").sum()

                st.success(f"평균: {avg:.4f}")
                st.warning(f"NG 개수: {ng} / {len(values)}")

                # 🔥 NG 빨간색 표시
                def color(val):
                    return "background-color:red;color:white" if val == "NG" else ""

                st.dataframe(
                    df_result.style.applymap(color, subset=["판정"]),
                    use_container_width=True
                )

                # =========================
                # 🔥 그래프 (시인성 개선)
                # =========================
                fig, ax = plt.subplots()

                ok = df_result[df_result["판정"] == "OK"]
                ngv = df_result[df_result["판정"] == "NG"]

                # OK / NG 분리 표시
                ax.scatter(ok.index, ok["값"], label="OK")
                ax.scatter(ngv.index, ngv["값"], label="NG")

                # 평균선
                ax.axhline(avg, linestyle="--", label="AVG")

                # 공차선 (평균 기준)
                ax.axhline(mins.mean(), linestyle="--", label="MIN(avg)")
                ax.axhline(maxs.mean(), linestyle="--", label="MAX(avg)")

                ax.set_title("측정값 분포 (NG 강조)")
                ax.legend()

                st.pyplot(fig)

            except Exception as e:
                st.error(f"데이터 오류: {e}")

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
        st.write(f"+편차: {upper - target}")
        st.write(f"-편차: {target - lower}")
