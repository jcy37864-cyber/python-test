import streamlit as st
import pandas as pd

st.set_page_config(page_title="데이터 입력", layout="wide")

# ✅ 최초 1회 로드
if "df" not in st.session_state:
    df = pd.read_excel("data.xlsm")

    # 🔥 컬럼 이름 정리 (핵심)
    df.rename(columns={
        "Unnamed: 6": "선택값",
        "Unnamed: 7": "결과"
    }, inplace=True)

    st.session_state.df = df

# ✅ 계산 함수
def calculate(df):
    df["결과"] = df.apply(
        lambda row: row["Z"] if str(row.get("선택값", "")).strip().upper() == "Z"
        else row["X"] if str(row.get("선택값", "")).strip().upper() == "X"
        else row["Y"] if str(row.get("선택값", "")).strip().upper() == "Y"
        else None,
        axis=1
    )
    return df

st.title("데이터 입력")

# ✅ 데이터 입력 UI (드롭다운으로 오류 방지)
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    num_rows="dynamic",
    key="editor",
    column_config={
        "선택값": st.column_config.SelectboxColumn(
            "선택값",
            options=["X", "Y", "Z"]
        )
    }
)

# ✅ 수정된 값 저장
st.session_state.df = edited_df

# 🔥 항상 계산 실행 (핵심)
st.session_state.df = calculate(st.session_state.df)

# ✅ 결과 표시
st.subheader("결과")
st.dataframe(st.session_state.df[["결과"]], use_container_width=True)

# ✅ 전체 데이터도 보고 싶으면
with st.expander("전체 데이터 보기"):
    st.dataframe(st.session_state.df, use_container_width=True)

# ✅ 엑셀 저장
if st.button("엑셀 저장"):
    # 다시 원래 컬럼명으로 저장 (필요하면)
    save_df = st.session_state.df.rename(columns={
        "선택값": "Unnamed: 6",
        "결과": "Unnamed: 7"
    })
    save_df.to_excel("data.xlsm", index=False)
    st.success("저장 완료!")

# ✅ CSV 다운로드
st.download_button(
    label="CSV 다운로드",
    data=st.session_state.df.to_csv(index=False).encode("utf-8-sig"),
    file_name="result.csv",
    mime="text/csv"
)
