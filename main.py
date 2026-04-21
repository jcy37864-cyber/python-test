import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 정밀 분석 (이중 공차 가이드)")

# 2. 데이터 파싱 함수 (성적서에서 숫자 데이터 추출)
def parse_smart_data(raw_text, sample_count):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_text)]
    results = []
    step = 1 + sample_count
    set_len = step * 3
    for i in range(len(nums) // set_len):
        base = i * set_len
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
    return results

# 3. 사이드바 설정
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수 (S1~S4면 4)", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치 (구멍 최소경)", value=0.350, format="%.3f")
    st.divider()
    st.markdown("### 🔵 **파란색 실선**\n보너스 없는 기본 공차")
    st.markdown("### 🔴 **빨간색 점선**\n보너스 포함 최대 합격선")

# 4. 데이터 입력
raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        # 위치도 및 보너스 계산
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        
        # MMC 보너스 계산
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 📊 이중 과녁 그래프 그리기 ---
        fig = go.Figure()

        # [A] 기본 공차 원 (파란색 실선)
        r_base = tol / 2
        fig.add_shape(type="circle", x0=-r_base, y0=-r_base, x1=r_base, y1=r_base,
                      line=dict(color="RoyalBlue", width=2),
                      fillcolor="rgba(65, 105, 225, 0.1)", layer="below")

        # [B] 최대 합격 경계선 (빨간색 점선)
        max_tol_val = df['최종공차'].max()
        r_max = max_tol_val / 2
        fig.add_shape(type="circle", x0=-r_max, y0=-r_max, x1=r_max, y1=r_max,
                      line=dict(color="Red", width=1.5, dash="dot"), layer="below")

        # [C] 데이터 점
