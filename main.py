import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# -------------------------------
# 한글 깨짐 방지
# -------------------------------
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

st.set_page_config(layout="wide")
st.title("📊 품질 데이터 분석 시스템")

# -------------------------------
# 엑셀 업로드
# -------------------------------
uploaded_file = st.file_uploader("엑셀 파일 업로드 (MIN / MAX / VALUE)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("📄 데이터 미리보기")
    st.dataframe(df)

    # 컬럼 선택
    min_col = st.selectbox("MIN 컬럼", df.columns)
    max_col = st.selectbox("MAX 컬럼", df.columns)
    val_col = st.selectbox("VALUE 컬럼", df.columns)

    mins = df[min_col]
    maxs = df[max_col]
    values = df[val_col]

    # -------------------------------
    # NG 판정
    # -------------------------------
    ng = (values < mins) | (values > maxs)
    ok = ~ng

    x = np.arange(len(values))

    # -------------------------------
    # 그래프
    # -------------------------------
    fig, ax = plt.subplots(figsize=(14, 6))

    # 공차 영역
    ax.fill_between(
        x,
        mins.iloc[0],
        maxs.iloc[0],
        alpha=0.2,
        label="Spec Range"
    )

    # 라인 (트렌드)
    ax.plot(x, values, linewidth=2)

    # OK / NG 점
    ax.scatter(x[ok], values[ok], s=60, label="OK")
    ax.scatter(x[ng], values[ng], s=80, label="NG")

    # 평균선
    avg = values.mean()
    ax.axhline(avg, linestyle='--', linewidth=2, label="AVG")

    # -------------------------------
    # 🔥 Y축 자동 확대 (핵심)
    # -------------------------------
    low = min(values.min(), mins.min())
    high = max(values.max(), maxs.max())
    margin = (high - low) * 0.15

    ax.set_ylim(low - margin, high + margin)

    # 스타일
    ax.set_title("Measurement Trend")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)

    st.pyplot(fig)

    # -------------------------------
    # 📊 분석 결과
    # -------------------------------
    st.subheader("📊 자동 분석 결과")

    total = len(values)
    ng_count = ng.sum()
    ok_count = ok.sum()
    ng_rate = (ng_count / total) * 100

    # 트렌드 분석 (기울기)
    slope = np.polyfit(x, values, 1)[0]

    if slope > 0.001:
        trend = "📈 상승 경향"
    elif slope < -0.001:
        trend = "📉 하락 경향"
    else:
        trend = "➖ 안정 상태"

    # 공차 중심 대비 위치
    center = (mins.mean() + maxs.mean()) / 2
    if values.mean() > center:
        position = "상한쪽 치우침"
    else:
        position = "하한쪽 치우침"

    # -------------------------------
    # 결과 출력
    # -------------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("총 데이터", total)
    col2.metric("NG 개수", ng_count)
    col3.metric("NG 비율 (%)", f"{ng_rate:.2f}")

    st.write(f"📌 평균: {values.mean():.4f}")
    st.write(f"📌 최소: {values.min():.4f}")
    st.write(f"📌 최대: {values.max():.4f}")

    st.write(f"📌 트렌드: {trend}")
    st.write(f"📌 위치: {position}")

    # -------------------------------
    # 🔥 한줄 요약 (현업 핵심)
    # -------------------------------
    if ng_count == 0:
        summary = "✅ 전체 공정 안정 (NG 없음)"
    elif ng_rate < 5:
        summary = "⚠️ 일부 NG 발생 (관리 필요)"
    else:
        summary = "🚨 NG 다수 발생 (공정 이상 가능)"

    st.subheader("🧠 종합 판단")
    st.success(summary)
