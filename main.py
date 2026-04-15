import streamlit as st
import pandas as pd

st.set_page_config(page_title="데이터 입력", layout="wide")

# ✅ 최초 1회만 파일 로드
if "df" not in st.session_state:
    st.session_state.df = pd.read_excel("data.xlsm")

# ✅ 계산 함수 (핵심)
def calculate():
    df = st.session_state.df

    df["Unnamed: 7"] = df.apply(
        lambda row: row["Z"] if str(row.get("변환값", "")).strip().upper() == "Z"
        else row["X"] if str(row.get("변환값", "")).strip().upper() == "X"
        else row["Y"] if str(row.get("변환값", "")).strip().upper() == "Y"
        else None,
        axis=1
    )

# 👉 앱 시작할 때 1번 계산
calculate()

st.title("데이터 입력")

# ✅ 데이터 입력 UI (입력하면 자동 반영)
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    num_rows="dynamic",
    key="editor"
)

# 👉 수정된 값 저장 (중요)
st.session_state.df = edited_df

# 👉 항상 다시 계산 (🔥 핵심)
calculate()

# ✅ 결과 출력
st.subheader("결과 (Unnamed: 7)")
st.dataframe(st.session_state.df[["Unnamed: 7"]], use_container_width=True)

# ✅ 저장 버튼
if st.button("엑셀 저장"):
    st.session_state.df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")

# ✅ 다운로드 버튼
st.download_button(
    label="CSV 다운로드",
    data=st.session_state.df.to_csv(index=False).encode("utf-8-sig"),
    file_name="result.csv",
    mime="text/csv"
)

# 🔍 디버깅용 (필요하면 주석 해제)
# st.write(st.session_state.df)
# st.write(st.session_state.df.columns)
