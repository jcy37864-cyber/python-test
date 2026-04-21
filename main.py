import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 분석 (빨간 점선 가이드 강화)")

# 2. 데이터 파싱 함수
def parse_smart_data(raw_text, sc):
    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', raw_text)]
    if not nums: return None
    results = []
    step = 1 + sc
    set_len = step * 3
    for i in range(len(nums) // set_len):
        base = i * set_len
        try:
            dia_p = nums[base : base + step]
            x_p = nums[base + step : base + step * 2]
            y_p = nums[base + step * 2 : base + step * 3]
            label = chr(65 + i) if i < 26 else f"P{i+1}"
            for s in range(sc):
                results.append({
                    "측정포인트": f"{label}_S{s+1}",
                    "도면_X": x_p[0], "도면_Y": y_p[0],
                    "측정_X": x_p[s+1], "측정_Y": y_p[s+1],
                    "지름_MMC": dia_p[s+1]
                })
        except: break
    return results

# 3. 사이드바 설정
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치", value=0.350, format="%.3f")

# 4. 데이터 입력
raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 📊 빨간 점선 강제 표시 로직 ---
        view_limit = 0.7 
        fig = go.Figure()
        
        # [1] 기본 공차 (파란 실선)
        r_base = tol / 2
        fig.add_shape(type="circle", x0=-r_base, y0=-r_base, x1=r_base, y1=r_base,
                      line=dict(color="RoyalBlue", width=2), name="기본공차")
        
        # [2] '최대' 보너스 합격선 (빨간 점선) - 파란선과 겹치지 않을 때만 표시
        max_tol = df['최종공차'].max()
        if max_tol > tol:
            r_max = max_tol / 2
            fig.add_shape(type="circle", x0=-r_max, y0=-r_max, x1=r_max, y1=r_max,
                          line=dict(color="Red", width=2, dash="dot"), name="최대허용")
            st.info(f"📢 빨간 점선 표시 중: 현재 보너스 포함 최대 허용치는 Ø{max_tol:.3f}입니다.")
        else:
            st.warning("⚠️ 모든 시료의 보너스 공차가 0입니다. (실제 지름이 MMC 기준치와 같음)")

        # 데이터 점 표시
        in_bounds = df[(df['편차_X'].abs() <= view_limit) & (df['편차_Y'].abs() <= view_limit)]
        for res in ["✅ OK", "❌ NG"]:
            sub = in_bounds[in_bounds['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res,
                    text=sub['측정포인트'], textposition="top center",
                    marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", line=dict(width=1, color="white")),
                    customdata=sub['최종공차'],
                    hovertemplate="위치도: %{y}<br>이 시료의 합격한계: Ø%{customdata:.3f}<extra></extra>"
                ))

        fig.update_layout(width=700, height=700, xaxis=dict(range=[-view_limit, view_limit]), yaxis=dict(range=[-view_limit, view_limit]))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']])
