import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 앱 설정
st.set_page_config(page_title="덕인 위치도 분석기", layout="wide")
st.title("🎯 덕인 위치도 정밀 분석 (시인성 완전 해결 버전)")

# 2. 데이터 파싱 함수 (강화됨)
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
                # 데이터 매칭 안정성 확인 (IndexError 방지)
                if len(dia_p) <= s+1 or len(x_p) <= s+1 or len(y_p) <= s+1: break
                results.append({
                    "측정포인트": f"{label}_S{s+1}",
                    "도면_X": x_part[0] if 'x_part' in locals() else x_p[0], 
                    "도면_Y": y_part[0] if 'y_part' in locals() else y_p[0],
                    "측정_X": x_part[s+1] if 'x_part' in locals() else x_p[s+1], 
                    "측정_Y": y_part[s+1] if 'y_part' in locals() else y_p[s+1],
                    "지름_MMC": dia_part[s+1] if 'dia_part' in locals() else dia_p[s+1]
                })
        except: break
    return results

# 3. 사이드바 기준 설정
with st.sidebar:
    st.header("⚙️ 기준 설정")
    sc = st.number_input("샘플 수 (S1~S4면 4)", min_value=1, value=4, key="samples")
    tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f", key="tol_ref")
    mmc_ref = st.number_input("MMC 기준치 (최소경)", value=0.350, format="%.3f", key="mmc_ref")

# 4. 메인 화면: 데이터 입력
raw_input = st.text_area("성적서 데이터를 여기에 붙여넣으세요", height=150, placeholder="Nominal 열부터 실측값 끝까지 모두 복사해 붙여넣으세요.")

# Control + Enter 혹은 텍스트 입력 후 실행되도록 데이터 존재 유무 확인
if raw_input:
    data = parse_smart_data(raw_input, sc)
    if data:
        df = pd.DataFrame(data)
        # 위치도 계산 및 판정
        df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
        df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
        df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
        df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
        df['최종공차'] = (tol + df['보너스']).round(4)
        df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

        # --- 📊 이중 과녁 그래프 (시인성 극대화) ---
        fig = go.Figure()
        r_base = tol / 2
        r_max = df['최종공차'].max() / 2

        # 가이드 원 (기본공차 파란원, 최대공차 빨간점선)
        fig.add_shape(type="circle", x0=-r_base, y0=-r_base, x1=r_base, y1=r_base,
                      line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")
        fig.add_shape(type="circle", x0=-r_max, y0=-r_max, x1=r_max, y1=r_max,
                      line=dict(color="Red", width=1.5, dash="dot"))

        # 점 찍기 (OK/NG 색상 및 이름 표시)
        for res in ["✅ OK", "❌ NG"]:
            sub = df[df['판정'] == res]
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub['편차_X'], y=sub['편차_Y'],
                    mode='markers+text',
                    name=res,
                    text=sub['측정포인트'] if res == "✅ OK" else "", # NG는 너무 멀 수 있어 이름 생략
                    textposition="top center",
                    marker=dict(size=12, color="#2ecc71" if res=="✅ OK" else "#e74c3c", 
                                line=dict(width=1, color="white")),
                    hovertemplate="<b>%{text}</b><br>위치도: %{customdata:.3f}<extra></extra>",
                    customdata=sub['위치도']
                ))

        # [해결책] 시인성 고정 (Fixed Zoom): 데이터 크기와 무관하게 과녁 주변만 보여줌
        # 공차 0.35 기준, ±0.7mm 정도 범위만 표시
        fixed_limit = max(0.7, r_max * 1.3)
        
        fig.update_layout(
            width=700, height=700,
            xaxis=dict(range=[-fixed_limit, fixed_limit], title="X 편차", zeroline=True, gridcolor='lightgrey'),
            yaxis=dict(range=[-fixed_limit, fixed_limit], title="Y 편차", zeroline=True, gridcolor='lightgrey'),
            title=f"🎯 과녁 중심부 확대 (공차: Ø{tol} / 최대합격선: Ø{df['최종공차'].max():.3f})",
            showlegend=True, plot_bgcolor='white'
        )

        # 결과 요약 ( metric )
        col1, col2, col3 = st.columns(3)
        col1.metric("전체 시료", f"{len(df)} 개")
        col2.success(f"합격(OK): {len(df[df['판정']=='✅ OK'])} 개")
        col3.error(f"불합격(NG): {len(df[df['판정']=='❌ NG'])} 개")

        # 그래프 및 표 출력
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("📋 상세 데이터")
        st.dataframe(df[['측정포인트', '편차_X', '편차_Y', '위치도', '보너스', '최종공차', '판정']], use_container_width=True)
