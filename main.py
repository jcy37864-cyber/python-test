import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 초기 설정 및 가독성 테마
st.set_page_config(page_title="Quality Analysis Pro", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #D32F2F; color: white; }
        .ng-card { border: 2px solid #FF0000; padding: 15px; border-radius: 10px; background-color: #FFF5F5; color: #D32F2F; font-weight: bold; }
        .ok-card { border: 2px solid #2E7D32; padding: 15px; border-radius: 10px; background-color: #E8F5E9; color: #2E7D32; font-weight: bold; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

def run_analysis():
    set_style()
    st.title("🎯 위치도 정밀 분석 결과 보고서")
    
    with st.sidebar:
        st.header("⚙️ 분석 설정")
        mode = st.radio("성적서 유형", ["유형 B (가로형)", "유형 A (3줄 세트)"])
        sc = st.number_input("시료(Sample) 수", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("기준값", value=0.060 if mode == "유형 A (3줄 세트)" else 0.350, format="%.3f")

    raw_data = st.text_area("데이터를 여기에 붙여넣으세요", height=200)
    
    if st.button("📊 보고서 생성 및 분석 시작") and raw_data:
        try:
            results = []
            # --- 파싱 로직 (잘림 방지용 줄바꿈 적용) ---
            if mode == "유형 B (가로형)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_data.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    def get_v(lst, idx):
                        v = re.sub(r'[^0-9\.\-]', '', lst[idx])
                        return float(v) if v and v != '-' else 0.0
                    nx, ny = get_v(lines[i+2], 0), get_v(lines[i+3], 0)
                    lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                    for s in range(sc):
                        idx = -(sc - s)
                        try:
                            ax, ay = get_v(lines[i+2], idx), get_v(lines[i+3], idx)
                            dv = get_v(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"ID": f"{lbl}_S{s+1}", "NX": nx, "NY": ny, "AX": ax, "AY": ay, "DIA": dv})
                        except: continue
            else:
                raw_lines = [l.strip() for l in raw_data.split('\n') if l.strip()]
                rows = []
                for l in raw_lines:
                    n = [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    rows.append([v if abs(v) < 150 else v % 100 for v in n])
                rows = [r for r in rows if r]
                for i in range(0, len(rows) // 3 * 3, 3):
                    d_r, x_r, y_r = rows[i], rows[i+1], rows[i+2]
                    for s in range(1, len(x_r)):
                        results.append({
                            "ID": f"P{(i//3)+1}_S{s}",
                            "NX": x_r[0], "NY": y_r[0],
                            "AX": x_r[s], "AY": y_r[s],
                            "DIA": d_r[s-1] if (s-1) < len(d_r) else d_r[-1]
                        })

            df = pd.DataFrame(results)
            if df.empty: return st.error("데이터 인식 실패")

            # --- 수치 계산 ---
            df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # --- 상급자 보고용 시각화 ---
            m_limit = df['LIMIT'].max()
            v_range = round(m_limit * 0.75, 2)
            
            fig = go.Figure()
            # 공차원 가이드
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, 
                          line=dict(color="#1A237E", width=3), fillcolor="rgba(26,35,126,0.05)")
            fig.add_shape(type="circle", x0=-m_limit/2, y0=-m_limit/2, x1=m_limit/2, y1=m_limit/2, 
                          line=dict(color="#FF0000", width=2, dash="dash"))
            
            # NG 포인트 강조 (크고 검정 테두리)
            for r, c, sz in zip(["✅ OK", "❌ NG"], ["#4CAF50", "#FF0000"], [10, 18]):
                pdf = df[df['RES'] == r]
                if not pdf.empty:
                    fig.add_trace(go.Scatter(
                        x=pdf['DX'], y=pdf['DY'], mode='markers+text', name=r,
                        text=pdf['ID'], textposition="top center",
                        marker=dict(size=sz, color=c, line=dict(width=2, color
