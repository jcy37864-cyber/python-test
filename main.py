import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re
from io import BytesIO

# ==========================================
# 1. 전역 스타일 및 초기화 (성능 최대치)
# ==========================================
st.set_page_config(page_title="Quality Hub Hybrid v10.0", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #d32f2f; color: white; }
        .ng-box { height: 180px; overflow-y: auto; border: 2px solid #ff0000; padding: 15px; border-radius: 8px; background-color: #fff5f5; }
        .ok-box { padding: 10px; border-radius: 8px; background-color: #e8f5e9; color: #2e7d32; font-weight: bold; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 유형별 핵심 로직 (A: 정밀파싱, B: 기존호환)
# ==========================================

def run_integrated_analysis():
    st.title("🎯 위치도 정밀 분석 시스템 (Hybrid)")
    st.subheader("상급자 보고 및 공정 능력 확인용")
    
    # [사이드바] 유형 선택 스위치
    with st.sidebar:
        st.header("🛠️ 시스템 설정")
        mode = st.radio("데이터 성적서 유형 선택", ["유형 B (기존/십자형)", "유형 A (3줄세트/정밀분석)"])
        st.divider()
        sc = st.number_input("샘플(캐비티) 수", min_value=1, value=4)
        tol_default = 0.350
        tol = st.number_input("기본 공차(Ø)", value=tol_default, format="%.3f")
        
        mmc_ref = 0.350 # 유형 B 기본값
        if mode == "유형 A (3줄세트/정밀분석)":
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")

        st.divider()
        st.info("💡 TIP: NG 발생 시 그래프에 빨간색 다이아몬드로 크게 표시됩니다.")

    raw_input = st.text_area("성적서 텍스트 데이터를 여기에 붙여넣으세요", height=250)
    
    if st.button("🚀 데이터 분석 및 보고서 생성", type="primary"):
        if not raw_input:
            st.warning("데이터를 입력해 주세요.")
            return

        try:
            results = []
            # -------------------------------------------
            # 유형 A 로직: 3줄 세트 정밀 파싱
            # -------------------------------------------
            if mode == "유형 A (3줄세트/정밀분석)":
                lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
                rows = []
                for line in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    # 좌표 튐 현상 보정 로직 제거 (실제 가공상태 왜곡 방지)
                    if nums: rows.append(nums)

                for i in range(0, len(rows) // 3 * 3, 3):
                    dia_vals, x_vals, y_vals = rows[i], rows[i+1], rows[i+2]
                    label = f"P{(i//3)+1}"
                    for s in range(1, len(x_vals)):
                        results.append({
                            "측정포인트": f"{label}_S{s}",
                            "도면_X": x_vals[0], "도면_Y": y_vals[0],
                            "측정_X": x_vals[s], "측정_Y": y_vals[s],
                            "지름_MMC": dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]
                        })

            # -------------------------------------------
            # 유형 B 로직: 기존의 넓은 데이터 시트 파싱
            # -------------------------------------------
            else:
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i+3 >= len(lines): break
                    pin_name = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                    # 유형 B는 첫 번째 숫자가 도면치수(Nominal)
                    try:
                        nom_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][0]))
                        nom_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][0]))
                        for s in range(sc):
                            # [핵심] 이전에 잘 나오던 '뒤에서부터 샘플 가져오기' 인덱스 방식 적용
                            idx = -(sc - s)
                            results.append({
                                "측정포인트": f"{pin_label}_S{s+1}",
                                "도면_X": nom_x, "도면_Y": nom_y,
                                "측정_X": float(re.sub(r'[^0-9\.\-]', '', lines[i+2][idx])),
                                "측정_Y": float(re.sub(r'[^0-9\.\-]', '', lines[i+3][idx])),
                                "지름_MMC": float(re.sub(r'[^0-9\.\-]', '', lines[i+1][idx])) if len(lines[i+1]) > abs(idx) else 0.35
                            })
                    except (IndexError, ValueError):
                        continue # 데이터 부족 시 건너뜀

            # --- 데이터 계산 및 판정 ---
            df = pd.DataFrame(results)
            if df.empty: return st.error("데이터를 읽을 수 없습니다.")

            df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
            df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
            df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
            df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
            df['최종공차'] = (tol + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # --- [시각화] 상급자 보고용 강화 그래프 ---
            max_limit = df['최종공차'].max()
            v_l = round(max_limit * 0.7, 2) # 공차 원이 화면에 꽉 차보이게 스케일 조정 (그림 2처럼)
            
            fig = go.Figure()
            
            # 1. 공차 가이드라인 (진한 파랑 & 빨간 점선)
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="#1A237E", width=3), fillcolor="rgba(26, 35, 126, 0.05)")
            fig.add_shape(type="circle", x0=-max_limit/2, y0=-max_limit/2, x1=max_limit/2, y1=max_limit/2, line=dict(color="#D32F2F", width=2, dash="dash"))
            
            # 2. 타점 (NG는 크고, 다이아몬드 형태로, 검정 테두리 추가)
            for r, c, sz, sym in zip(["✅ OK", "❌ NG"], ["#4CAF50", "#FF0000"], [10, 16], ["circle", "diamond"]):
                pdf = df[df['판정'] == r]
                if not pdf.empty:
                    fig.add_trace(go.Scatter(
                        x=pdf['편차_X'], y=pdf['편차_Y'], mode='markers+text', name=r,
                        text=pdf['측정포인트'], textposition="top center",
                        marker=dict(size=sz, color=c, symbol=sym, line=dict(width=1.5, color="white" if r=="✅ OK" else "black"))
                    ))
            
            fig.update_layout(
                width=800, height=800, template="plotly_white",
                title=dict(text=f"<b>위치도 분포 산점도 (기본공차: Ø{tol:.3f})</b>", x=0.5, font=dict(size=20)),
                xaxis=dict(range=[-v_l, v_l], zeroline=True, gridcolor='lightgray', title="X Deviation"),
                yaxis=dict(range=[-v_l, v_l], zeroline=True, gridcolor='lightgray', title="Y Deviation")
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- [하단 결과창] 직관적인 리포트 ---
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(df[['측정포인트', '위치도', '보너스', '최종공차', '판정']], use_container_width=True)
            
            with col2:
                ng_df = df[df['판정'] == "❌ NG"]
                if not ng_df.empty:
                    st.markdown(f"<div class='ng-box'>🚩 <b>불합격(NG) {len(ng_df)}건 발생</b><br>" + 
                                "".join([f"• {r['측정포인트']}: {r['위치도']:.3f} (규격 {r['최종공차']:.3f})<br>" for _, r in ng_df.iterrows()]) + "</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ 모든 데이터 규격 만족 (ALL PASS)</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"데이터 형식을 확인해 주세요. ({e})")

if __name__ == "__main__":
    set_style()
    run_integrated_analysis()
