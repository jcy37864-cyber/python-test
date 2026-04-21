import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 위치도 정밀 분석 (시인성 최적화 버전)")

# 2. 데이터 파싱 함수 (숫자만 추출)
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
    mmc_ref = st.number_input("MMC 기준치", value=0.350, format="%.3f")

# 4. 메인 화면
raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=150)

if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        # 위치도 계산
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['최종공차'] = (tol + (df['지름_MMC'] - mmc_ref).clip(lower=0)).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 📊 시인성 강조 그래프 ---
        fig = go.Figure()

        # [1] 공차 원 (파란색 영역)
        r = tol / 2
        fig.add_shape(type="circle", x0=-r, y0=-r, x1=r, y1=r,
                      line=dict(color="RoyalBlue", width=2),
                      fillcolor="rgba(65, 105, 225, 0.2)", layer="below")

        # [2] 측정 점 표시
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            fig.add_trace(go.Scatter(
                x=sub['편차_X'], y=sub['편차_Y'],
                mode='markers+text',
                name=res,
                text=sub['측정포인트'] if res == "✅ OK" else "", # OK 시료만 이름 표시 (NG는 너무 멀 수 있음)
                textposition="top center",
                marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", 
                            line=dict(width=1, color="white")),
                hovertemplate="<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>"
            ))

        # [3] 시인성 고정 레이아웃 (핵심!)
        # 데이터가 아무리 커도 그래프는 공차의 약 1.5배~2배 수준인 ±0.5mm로 고정합니다.
        graph_limit = 0.5  
        
        fig.update_layout(
            width=600, height=600,
            xaxis=dict(range=[-graph_limit, graph_limit], title="X 편차", zeroline=True, gridcolor='lightgrey'),
            yaxis=dict(range=[-graph_limit, graph_limit], title="Y 편차", zeroline=True, gridcolor='lightgrey'),
            title=f"🎯 위치도 분석 (과녁 중심 고정: Ø{tol})",
            showlegend=True,
            plot_bgcolor='white'
        )

        # UI 배치
        col1, col2 = st.columns([2, 1])
        with col1:
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.info(f"💡 **참고**: 편차가 ±{graph_limit}mm를 벗어나는 데이터는 그래프 영역 밖으로 숨겨집니다. 아래 상세 표에서 전체 결과를 확인하세요.")
            st.metric("전체 시료", f"{len(df)} 개")
            st.metric("합격(OK)", f"{len(df[df['판정']=='✅ OK'])} 개")
            st.error(f"불합격(NG) : {len(df[df['판정']=='❌ NG'])} 개")

        # 상세 데이터 표
        st.subheader("📋 상세 분석 결과")
        st.dataframe(df[['측정포인트', '편차_X', '편차_Y', '위치도', '최종공차', '판정']], use_container_width=True)
