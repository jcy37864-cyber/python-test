import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(page_title="품질 측정 프로그램", layout="wide")

st.title("📊 품질 측정 통합 프로그램")

col1, col2 = st.columns(2)

# =========================
# 🔄 ZXY 변환
# =========================
with col1:
    st.subheader("🔄 ZXY 변환")

    file_zxy = st.file_uploader("엑셀 업로드 (X,Y,Z)", type=["xlsx"], key="zxy")

    template_zxy = pd.DataFrame({"X": [], "Y": [], "Z": []})
    buf = BytesIO()
    template_zxy.to_excel(buf, index=False)

    st.download_button("📥 템플릿 다운로드", buf.getvalue(), "zxy_template.xlsx")

    if file_zxy:
        df = pd.read_excel(file_zxy)
        st.dataframe(df, use_container_width=True)

        if st.button("ZXY 변환 실행"):
            results = []

            for _, row in df.iterrows():
                x = str(row.get("X", "")).strip()
                y = str(row.get("Y", "")).strip()
                z = str(row.get("Z", "")).strip()

                if x and y and z:
                    results.extend([z, x, y])

            result_df = pd.DataFrame(results, columns=["결과"])

            st.dataframe(result_df)

            csv = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("CSV 다운로드", csv, "zxy_result.csv")

# =========================
# 📈 통계 / 그래프
# =========================
with col2:
    st.subheader("📈 통계 / 그래프")

    file_graph = st.file_uploader("엑셀 업로드", type=["xlsx"], key="graph")

    template_graph = pd.DataFrame({"값": []})
    buf2 = BytesIO()
    template_graph.to_excel(buf2, index=False)

    st.download_button("📥 템플릿 다운로드", buf2.getvalue(), "graph_template.xlsx")

    st.markdown("### 📏 공차 입력")
    lsl = st.number_input("LSL", value=0.0)
    usl = st.number_input("USL", value=10.0)

    if file_graph:
        df = pd.read_excel(file_graph)

        try:
            values = df.iloc[:, 0].dropna().astype(float)

            avg = values.mean()
            mx = values.max()
            mn = values.min()

            # NG 판정
            df_result = pd.DataFrame({"값": values})
            df_result["판정"] = df_result["값"].apply(
                lambda x: "NG" if x < lsl or x > usl else "OK"
            )

            ng_count = (df_result["판정"] == "NG").sum()

            st.success(f"평균: {avg:.4f}")
            st.info(f"최대: {mx} / 최소: {mn}")
            st.warning(f"NG 개수: {ng_count} / {len(values)}")

            # =========================
            # 🔥 표에서 NG 빨간색 표시
            # =========================
            def highlight_ng(val):
                return "background-color: red; color: white" if val == "NG" else ""

            st.dataframe(
                df_result.style.applymap(highlight_ng, subset=["판정"]),
                use_container_width=True
            )

            # =========================
            # 🔥 그래프 (NG 강조)
            # =========================
            fig, ax = plt.subplots()

            ok_values = df_result[df_result["판정"] == "OK"]["값"]
            ng_values = df_result[df_result["판정"] == "NG"]["값"]

            ax.hist(ok_values, bins=15, alpha=0.7, label="OK")
            ax.hist(ng_values, bins=15, alpha=0.7, label="NG")

            ax.axvline(avg, linestyle="--", label=f"AVG: {avg:.2f}")
            ax.axvline(lsl, linestyle="--", label="LSL")
            ax.axvline(usl, linestyle="--", label="USL")

            ax.set_title("데이터 분포 + NG 강조")
            ax.legend()

            st.pyplot(fig)

        except:
            st.error("숫자 데이터 확인 필요")
