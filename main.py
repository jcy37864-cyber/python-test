import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 정밀 분석 (실행 버튼 추가 버전)")

# 2. 데이터 파싱 함수
def parse_smart_data(raw_text, sample_count):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_text)]
    if not nums: return None
    results = []
    step = 1 + sample_count
    set_len = step * 3
    for i in range(len(nums) // set_len):
        base = i * set_len
        try:
            dia_part = nums[base : base + step]
            x_part = nums[base + step : base + step * 2]
            y_part = nums[base + step * 2 : base + step * 3]
            label = chr(65 + i) if i < 26 else f"P{i+1}"
            for s in range(sample_count):
                results.append({
                    "측정포인트": f"{label}_S{s+1}",
                    "도면_X": x_part[0], "도면_Y": y_part[0],
                    "측정_X": x_part[s+1], "측정_Y": y_part[s+1],
                    "지름_MMC": dia_part[s+1]
                })
        except IndexError: break
    return results

# 3. 사이드바
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수 (S1~S4면 4)", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치 (최소경)", value=0.350, format="%.3f")

# 4. 데이터 입력 및 실행 버튼
raw_input = st.text_area("성적서 데이터를 여기에 붙여넣으세요", height=150, placeholder="데이터를 붙여넣고 아래 버튼을 누르세요")
run_btn = st.button("🚀 분석 시작", use_container_width=True)

# 버튼을 누르거나 데이터가 있을 때 실행
if run_btn and raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 📊 그래프 ---
        fig = go.Figure()
        r_base = tol / 2
        max_tol_val = df['최종공차'].max()
        r_max = max_tol_val / 2

        # 가이드 원들
        fig.add_shape(type="circle", x0=-r_base, y0=-r_base, x1=r_base, y1=r_base,
                      line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")
        fig.add_shape(type="circle", x0=-r_max, y0=-r_max, x1=r_max, y1=r_max,
                      line=dict(color="Red", width=1.5, dash="dot"))

        # 점 찍기
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub['편차_X'], y=sub['편차_Y'], mode='markers', name=res,
                    marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white")),
                    text=sub['측정포인트'],
                    customdata=sub['위치도'],
                    hovertemplate="<b>%{text}</b><br>위치도: %{customdata:.3f}<extra></extra>"
                ))

        # 뷰 고정
        limit = max(0.5, r_max * 1.3)
        fig.update_layout(width=700, height=700, xaxis=dict(range=[-limit, limit]), yaxis=dict(range=[-limit, limit]), plot_bgcolor='white')

        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']], use_container_width=True)
    else:
        st.error("데이터 형식이 올바르지 않습니다. 다시 확인해주세요.")
elif run_btn and not raw_input:
    st.warning("데이터를 먼저 입력해주세요.")
