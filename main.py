import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")

# --- 1. 기준 설정 (사이드바) ---
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수", min_value=1, value=4)
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
    mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
    
    st.divider()
    
    # [핵심] 표준 구간 가이드
    std_range = round((tol / 2) * 2, 2) # 기본 공차 반지름의 2배를 표준으로 설정
    st.write(f"📍 **권장 표준 범위: ±{std_range}mm**")
    
    zoom_mode = st.radio("그래프 보기 모드", ["표준(권장)", "사용자 정의"])
    
    if zoom_mode == "표준(권장)":
        view_limit = std_range
    else:
        view_limit = st.slider("범위 수동 조절(±mm)", 0.1, 5.0, std_range, step=0.1)

# --- 2. 데이터 분석 및 그래프 로직 ---
# (데이터 파싱 및 계산 로직은 이전과 동일)
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

raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        # ... (계산식 생략: 위치도, 보너스, 최종공차 계산) ...
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        fig = go.Figure()
        
        # 파란 원 (기본)
        fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2,
                      line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")

        # 빨간 원 (보너스 포함 합격선) - 화면 밖으로 나가면 테두리에 고정
        actual_max_r = df['최종공차'].max() / 2
        display_max_r = min(actual_max_r, view_limit * 0.98)
        fig.add_shape(type="circle", x0=-display_max_r, y0=-display_max_r, x1=display_max_r, y1=display_max_r,
                      line=dict(color="Red", width=2, dash="dot"))

        # 데이터 점 찍기
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            # 화면 안에 있는 점들만 그래프에 표시
            visible = sub[(sub['편차_X'].abs() <= view_limit) & (sub['편차_Y'].abs() <= view_limit)]
            if not visible.empty:
                fig.add_trace(go.Scatter(
                    x=visible['편차_X'], y=visible['편차_Y'], mode='markers+text', name=res,
                    text=visible['측정포인트'], textposition="top center",
                    marker=dict(size=10, color="#2ecc71" if res=="✅ OK" else "#e74c3c")
                ))

        fig.update_layout(
            width=700, height=700,
            xaxis=dict(range=[-view_limit, view_limit], title="X 편차"),
            yaxis=dict(range=[-view_limit, view_limit], title="Y 편차"),
            title=f"🎯 위치도 분석 (현재 보기 범위: ±{view_limit}mm)"
        )
        st.plotly_chart(fig)
        
        if actual_max_r > view_limit:
            st.warning(f"⚠️ 실제 합격 한계(Ø{df['최종공차'].max():.3f})가 보기 범위보다 큽니다. 빨간 점선은 화면 테두리에 표시되었습니다.")
