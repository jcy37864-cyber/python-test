import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import platform

# =========================
# 🔥 폰트 설정 (한글 깨짐 방지)
# =========================
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'

plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(page_title="품질 측정 프로그램", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

# =========================
# 🔥 좌우 분할
# =========================
left, right = st.columns([2, 1])

# =========================
# 🔥 왼쪽: 메인
# =========================
with left:

    app_mode = st.selectbox(
        "프로그램 선택",
        ["ZXY 변환", "통계 / 그래프"]
    )

    # =========================
    # 🔄 ZXY 변환
    # =========================
    if app_mode == "ZXY 변환":

        st.subheader("🔄 ZXY 변환")

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
    # 📈 통계 / 그래프
    # =========================
    elif app_mode == "통계 / 그래프":

        st.subheader("📈 통계 / 그래프")

        file = st.file_uploader("엑셀 업로드", type=["xlsx"])

        # 템플릿 (MIN → MAX → VALUE)
        template = pd.DataFrame({
            "MIN": [30.25, 30.25, 30.25],
            "MAX": [30.70, 30.70, 30.70],
            "VALUE": [30.5, 30.4, 30.6]
        })

        buf = BytesIO()
        template.to_excel(buf, index=False)

        st.download_button("📥 템플릿 다운로드", buf.getvalue(), "template.xlsx")

        if file:
            df = pd.read_excel(file)
            st.dataframe(df, use_container_width=True)

            min_col = st.selectbox("MIN", df.columns)
            max_col = st.selectbox("MAX", df.columns)
            value_col = st.selectbox("VALUE", df.columns)

            try:
                mins = df[min_col].astype(float)
                maxs = df[max_col].astype(float)
                values = df[value_col].astype(float)

                avg = values.mean()

                df_result = pd.DataFrame({
                    "MIN": mins,
                    "MAX": maxs,
                    "VALUE": values
                })

                df_result["판정"] = df_result.apply(
                    lambda r: "NG" if r["VALUE"] < r["MIN"] or r["VALUE"] > r["MAX"] else "OK",
                    axis=1
                )

                ng = (df_result["판정"] == "NG").sum()
                total = len(df_result)

                # =========================
                # 📊 상태 요약
                # =========================
                st.subheader("📊 상태 요약")

                if ng == 0:
                    st.success("✅ 전체 양호")
                else:
                    st.error(f"❌ NG {ng}개 발생")

                if avg < mins.iloc[0]:
                    st.warning("⬇ 전체적으로 낮은 경향")
                elif avg > maxs.iloc[0]:
                    st.warning("⬆ 전체적으로 높은 경향")
                else:
                    st.info("✔ 공차 범위 내 안정")

                # =========================
                # 📈 그래프 (핵심)
                # =========================
                fig, ax = plt.subplots()

                x = range(len(values))

                # 흐름선
                ax.plot(x, values, linewidth=2)

                # 공차 영역
                ax.fill_between(
                    x,
                    mins.iloc[0],
                    maxs.iloc[0],
                    alpha=0.15
                )

                # NG 강조
                ng_index = df_result[df_result["판정"] == "NG"].index
                ax.scatter(ng_index, values.iloc[ng_index], s=60)

                # 평균선
                ax.axhline(avg, linestyle="--")

                ax.set_title("Measurement Trend")

                st.pyplot(fig)

            except Exception as e:
                st.error(f"데이터 오류: {e}")

# =========================
# 🔧 오른쪽: 계산기
# =========================
with right:

    st.subheader("🔧 계산 도구")

    tool = st.selectbox(
        "선택",
        ["토크 변환", "공차 계산"]
    )

    # 토크 변환
    if tool == "토크 변환":
        val = st.number_input("값", value=0.0)

        mode = st.radio(
            "변환",
            ["N·m → kgf·cm", "kgf·cm → N·m"]
        )

        if mode == "N·m → kgf·cm":
            res = val * 10.1972
        else:
            res = val / 10.1972

        st.success(f"결과: {res:.3f}")

    # 공차 계산
    elif tool == "공차 계산":
        t = st.number_input("목표값", value=0.0)
        u = st.number_input("상한", value=0.0)
        l = st.number_input("하한", value=0.0)

        st.write(f"공차: {u-l}")
        st.write(f"+편차: {u-t}")
        st.write(f"-편차: {t-l}")
