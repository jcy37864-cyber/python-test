import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# ==========================================
# 1. 초기 설정 및 스타일
# ==========================================
st.set_page_config(page_title="Quality Analysis Hybrid v2.1", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
        .ng-box { height: 180px; overflow-y: auto; border: 1px solid #ff4b4b; padding: 12px; border-radius: 5px; background-color: #fff5f5; }
        </style>
    """, unsafe_allow_html=True)

def run_integrated_analysis():
    set_style()
    st.title("🎯 위치도 정밀 분석 시스템 (Hybrid)")

    # -------------------------------------------
    # [사이드바] 설정 영역
    # -------------------------------------------
    with st.sidebar:
        st.header("⚙️ 시스템 설정")
        mode = st.radio("데이터 성적서 유형", ["유형 B (가로 데이터)", "유형 A (3줄 세트)"])
        st.divider()
        sc = st.number_input("샘플(캐비티) 수", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        
        if mode == "유형 A (3줄 세트)":
            mmc_ref = st.number_input("MMC 기준치", value=0.060, format="%.3f")
        
        view_mode = st.radio("그래프 범위", ["자동(권장)", "수동 조절"], horizontal=True)
        if view_mode == "수동 조절":
            view_limit = st.slider("줌 조절 (±mm)", 0.1, 5.0, 0.5, step=0.1)

    # -------------------------------------------
    # [메인] 데이터 입력
    # -------------------------------------------
    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250, placeholder="이미지 표의 텍스트를 복사하여 입력")
    analyze_button = st.button("📊 데이터 분석 시작", type="primary")

    if analyze_button:
        if not raw_input:
            st.warning("⚠️ 입력된 데이터가 없습니다.")
            return

        try:
            results = []
            
            # 유형 B 로직 (참조 코드의 황금 인덱스 복구)
            if mode == "유형 B (가로 데이터)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i+3 >= len(lines): break
                    try:
                        nom_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][0]))
                        nom_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][0]))
                        pin_label = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                        
                        for s in range(sc):
                            idx = -(sc - s)
                            act_x = float(re.sub(r'[^0-9\.\-]', '', lines[i+2][idx]))
                            act_y = float(re.sub(r'[^0-9\.\-]', '', lines[i+3][idx]))
                            dia_val = float(re.sub(r'[^0-9\.\-]', '', lines[i+1][idx])) if len(lines[i+1]) > abs(idx) else 0.35
                            
                            results.append({
                                "측정포인트": f"{pin_label}_S{s+1}",
                                "도면_X": nom_x, "도면_Y": nom_y,
                                "측정_X": act_x, "측정_Y": act_y,
                                "지름_MMC": dia_val
                            })
                    except (IndexError, ValueError):
                        continue

            # 유형 A 로직
            else:
                lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
                rows = []
                for line in lines:
                    nums = [float(n) for n in re.findall(r'[-+]?\d*\.\d+|\d+', line)]
                    nums = [n if abs(n) < 150 else n % 100 for n in nums]
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

            # 데이터 가공 및 계산
            df = pd.DataFrame(results)
            df['편차_X'] = (df['측정_X'] - df['도면_X']).round(4)
            df['편차_Y'] = (df['측정_Y'] - df['도면_Y']).round(4)
            df['위치도'] = (np.sqrt(df['편차_X']**2 + df['편차_Y']**2) * 2).round(4)
            
            # --- 에러 발생했던 지점 수정 완료 ---
            if mode == "유형 A (3줄 세트)":
                df['보너스'] = (df['지름_MMC'] - mmc_ref).clip(lower=0).round(4)
            else:
                df['보너스'] = (df['지름_MMC'] - 0.35).clip(lower=0).round(4)
            # ---------------------------------
                
            df['최종공차'] = (tol + df['보너스']).round(4)
            df['판정'] = np.where(df['위치도'] <= df['최종공차'], "✅ OK", "❌ NG")

            # 시각화 (Plotly)
            max_total_tol = df['최종공차'].max()
            if view_mode == "자동(권장)":
                view_limit = round((max_total_tol / 2) * 1.5, 2)

            fig = go.Figure()
            r_blue, r_red = tol / 2, max_total_tol / 2
            
            fig.add_shape(type="circle", x0=-r_blue, y0=-r_blue, x1=r_blue, y1=r_blue, line=dict(color="RoyalBlue", width=2.5), fillcolor="rgba(65, 105, 225, 0.05)")
            fig.add_shape(type="circle", x0=-r_red, y0=-r_red, x1=r_red, y1=r_red, line=dict(color="Red", width=2, dash="dot"))

            for res, color in zip(["✅ OK", "❌ NG"], ["#2ecc71", "#e74c3c"]):
                sub = df[df['판정'] == res]
                if not sub.empty:
                    fig.add_trace(go.Scatter(x=sub['편차_X'], y=sub['편차_Y'], mode='markers+text', name=res,
                                             text=sub['측정포인트'], textposition="top center",
                                             marker=dict(size=12, color=color, line=dict(width=1, color="white"))))

            fig.update_layout(width=750, height=750, template="plotly_white",
                              xaxis=dict(range=[-view_limit, view_limit], zeroline=True, title="X Deviation"),
                              yaxis=dict(range=[-view_limit, view_limit], zeroline=True, title="Y Deviation"))
            
            st.plotly_chart(fig, use_container_width=True)

            # 결과 리포트
            st.info(f"📌 **품질 요약** | 기본공차: Ø{tol:.3f} / 최대합격원: Ø{max_total_tol:.3f}")
            
            ng_list = df[df['판정'] == "❌ NG"]
            if not ng_list.empty:
                st.error(f"🚨 **규격 이탈(NG) 상세 리스트**")
                ng_html = "".join([f"<p style='color: #d32f2f; margin: 4px 0;'>• <b>{r['측정포인트']}</b>: {r['위치도']:.3f} (규격 Ø{r['최종공차']:.3f} 대비 <b>{r['위치도']-r['
