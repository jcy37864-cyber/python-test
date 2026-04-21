import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re
from io import BytesIO

# ==========================================
# 1. 전역 스타일 및 초기화
# ==========================================
st.set_page_config(page_title="Quality Hub Hybrid v10.0", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
        .ng-box { height: 180px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; background-color: #fff5f5; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 유형별 핵심 로직 (A: 정밀파싱, B: 기존호환)
# ==========================================

def run_integrated_analysis():
    st.title("🎯 위치도 정밀 분석 (Hybrid A/B)")
    
    # [사이드바] 유형 선택 스위치
    with st.sidebar:
        st.header("🛠️ 시스템 설정")
        mode = st.radio("데이터 유형 선택", ["유형 B (기존/십자형)", "유형 A (3줄세트/오류보정)"])
        st.divider()
        if mode == "유형 B (기존/십자형)":
            sc = st.number_input("샘플(캐비티) 수", 1, 20, 4)
            tol_default = 0.350
        else:
            sc = st.number_input("데이터 세트 크기", 1, 20, 4)
            tol_default = 0.350
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")

    # 분석 설정
    col1, col2 = st.columns(2)
    with col1:
        tol = st.number_input("기본 공차(Ø)", value=tol_default, format="%.3f")
    with col2:
        view_mode = st.radio("그래프 범위", ["자동", "수동"], horizontal=True)

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250)
    
    if st.button("🚀 데이터 분석 및 그래프 생성", type="primary"):
        if not raw_input:
            st.warning("데이터를 입력해 주세요.")
            return

        try:
            results = []
            # -------------------------------------------
            # 유형 A 로직: 3줄 세트 정밀 파싱 (200 초과 방지)
            # -------------------------------------------
            if mode == "유형 A (3줄세트/오류보정)":
                lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
                rows = []
                for line in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    # 유형 A의 고질적 문제인 '200' 근처의 값 보정 (필요시)
                    nums = [n if abs(n) < 150 else n % 100 for n in nums] 
                    if nums: rows.append(nums)

                for i in range(0, len(rows) // 3 * 3, 3):
                    dia_vals, x_vals, y_vals = rows[i], rows[i+1], rows[i+2]
                    label = f"P{(i//3)+1}"
                    for s in range(1, len(x_vals)):
                        results.append({
                            "POINT": f"{label}_S{s}",
                            "NOM_X": x_vals[0], "NOM_Y": y_vals[0],
                            "ACT_X": x_vals[s], "ACT_Y": y_vals[s],
                            "DIA_MMC": dia_vals[s-1] if (s-1) < len(dia_vals) else dia_vals[-1]
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
                    nom_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][0]))
                    nom_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][0]))
                    for s in range(sc):
                        idx = -(sc - s)
                        results.append({
                            "POINT": f"{pin_name}_S{s+1}",
                            "NOM_X": nom_x, "NOM_Y": nom_y,
                            "ACT_X": float(re.sub(r'[^0-9\.\-]', '', lines[i+2][idx])),
                            "ACT_Y": float(re.sub(r'[^0-9\.\-]', '', lines[i+3][idx])),
                            "DIA_MMC": float(re.sub(r'[^0-9\.\-]', '', lines[i+1][idx])) if len(lines[i+1]) > abs(idx) else 0.35
                        })

            # 공통 계산 로직
            df = pd.DataFrame(results)
            df['DEV_X'] = (df['ACT_X'] - df['NOM_X']).round(4)
            df['DEV_Y'] = (df['ACT_Y'] - df['NOM_Y']).round(4)
            df['POSITION'] = (np.sqrt(df['DEV_X']**2 + df['DEV_Y']**2) * 2).round(4)
            
            # 유형별 보너스 공차 적용 차이
            if mode == "유형 A (3줄세트/오류보정)":
                df['BONUS'] = (df['DIA_MMC'] - mmc_ref).clip(lower=0).round(4)
            else:
                df['BONUS'] = (df['DIA_MMC'] - 0.35).clip(lower=0).round(4) # B유형 기본값
            
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RESULT'] = np.where(df['POSITION'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # 그래프 그리기 (Plotly 사용 - 데옥인님이 원하던 그 모양)
            fig = go.Figure()
            max_limit = df['LIMIT'].max()
            r_blue, r_red = tol / 2, max_limit / 2
            
            # 공차 영역 시각화
            fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue, line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.1)")
            fig.add_shape(type="circle", x0=-r_red, y0=-r_red, x1=r_red, y1=r_red, line=dict(color="Red", width=1.5, dash="dot"))

            # 점 찍기
            for res, color in zip(["✅ OK", "❌ NG"], ["#2ecc71", "#e74c3c"]):
                sub = df[df['RESULT'] == res]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['DEV_X'], y=sub['DEV_Y'], mode='markers+text', name=res,
                                             text=sub['POINT'], textposition="top center",
                                             marker=dict(size=10, color=color, line=dict(width=1, color="white"))))

            # 레이아웃 설정
            v_lim = (max_limit / 2) * 1.5 if view_mode == "자동" else 0.5
            fig.update_layout(width=700, height=700, template="plotly_white",
                              xaxis=dict(range=[-v_lim, v_lim], zeroline=True, title="X Deviation"),
                              yaxis=dict(range=[-v_lim, v_lim], zeroline=True, title="Y Deviation"))
            
            st.plotly_chart(fig, use_container_width=True)

            # 결과표 및 NG 리스트
            st.dataframe(df[['POINT', 'POSITION', 'BONUS', 'LIMIT', 'RESULT']], use_container_width=True)
            
            ng_df = df[df['RESULT'] == "❌ NG"]
            if not ng_df.empty:
                st.error("🚨 규격 이탈(NG) 상세 정보")
                ng_html = "".join([f"<p>• <b>{r['POINT']}</b>: {r['POSITION']} (허용: {r['LIMIT']})</p>" for _, r in ng_df.iterrows()])
                st.markdown(f"<div class='ng-box'>{ng_html}</div>", unsafe_allow_html=True)
            else:
                st.success("✅ 모든 포인트 합격!")

        except Exception as e:
            st.error(f"오류 발생: 데이터 형식을 확인해 주세요. ({e})")

if __name__ == "__main__":
    set_style()
    run_integrated_analysis()
