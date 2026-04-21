import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 초기 설정 및 가독성 높은 스타일 적용
st.set_page_config(page_title="Quality Hub Pro v2.6", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #d32f2f; color: white; }
        .ng-box { height: 180px; overflow-y: auto; border: 2px solid #ff0000; padding: 15px; border-radius: 8px; background-color: #fff5f5; }
        .ok-box { padding: 10px; border-radius: 8px; background-color: #e8f5e9; color: #2e7d32; font-weight: bold; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

def run_analysis():
    set_style()
    st.title("🎯 품질 측정 위치도 분석 리포트")
    st.subheader("상급자 보고 및 공정 능력 확인용")

    with st.sidebar:
        st.header("📋 보고서 설정")
        mode = st.radio("성적서 유형", ["유형 B (가로형)", "유형 A (3줄 세트)"])
        sc = st.number_input("시료 수(Sample)", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값", value=0.060 if mode == "유형 A (3줄 세트)" else 0.350, format="%.3f")
        st.divider()
        st.info("💡 TIP: NG 발생 시 그래프에 빨간색 큰 점으로 표시됩니다.")

    raw_input = st.text_area("성적서 텍스트 데이터를 여기에 붙여넣으세요", height=250)
    
    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            results = []
            
            # --- [유형 B] 파싱: 참조 코드 인덱싱 적용 ---
            if mode == "유형 B (가로형)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    def clean_num(lst, idx):
                        val = re.sub(r'[^0-9\.\-]', '', lst[idx])
                        return float(val) if val and val != '-' else 0.0

                    nx, ny = clean_num(lines[i+2], 0), clean_num(lines[i+3], 0)
                    lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                    
                    for s in range(sc):
                        idx = -(sc - s)
                        try:
                            ax, ay = clean_num(lines[i+2], idx), clean_num(lines[i+3], idx)
                            dv = clean_num(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"ID": f"{lbl}_S{s+1}", "NX": nx, "NY": ny, "AX": ax, "AY": ay, "DIA": dv})
                        except: continue

            # --- [유형 A] 파싱: 3줄 세트 보정 ---
            else:
                lines = [l.strip() for l in raw_input.split('\n') if l.strip()]
                rows = []
                for l in lines:
                    nums = [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    rows.append([v if abs(v) < 150 else v % 100 for v in nums])
                rows = [r for r in rows if r]
                for i in range(0, len(rows) // 3 * 3, 3):
                    for s in range(1, len(rows[i+1])):
                        results.append({"ID": f"P{(i//3)+1}_S{s}", "NX": rows[i+1][0], "NY": rows[i+2][0], "AX": rows[i+1][s], "AY": rows[i+2][s], "DIA": rows[i][s-1] if (s-1) < len(rows[i]) else rows[i][-1]})

            # --- 데이터 계산 및 판정 ---
            df = pd.DataFrame(results)
            if df.empty: return st.error("데이터를 읽을 수 없습니다.")

            df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # --- [시각화] 상급자 보고용 강화 그래프 ---
            max_limit = df['LIMIT'].max()
            v_l = round(max_limit * 0.7, 2) # 공차 원이 꽉 차보이게 스케일 조정
            
            fig = go.Figure()
            
            # 1. 공차 가이드라인 (진한 파랑 & 빨간 점선)
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="#1A237E", width=3), fillcolor="rgba(26, 35, 126, 0.05)")
            fig.add_shape(type="circle", x0=-max_limit/2, y0=-max_limit/2, x1=max_limit/2, y1=max_limit/2, line=dict(color="#D32F2F", width=2, dash="dash"))
            
            # 2
