import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 1. 초기 설정 및 테마 적용
st.set_page_config(page_title="Quality Hub Pro v2.8", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #D32F2F; color: white; }
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
        st.info("💡 TIP: NG 발생 시 그래프에 빨간색 다이아몬드로 크게 표시됩니다.")

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250)
    
    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            results = []
            
            if mode == "유형 B (가로형)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    
                    # --- [복구 핵심] 데이터 왜곡 보정 로직 (그림 2처럼 뭉치게) ---
                    def clean_v(lst, idx):
                        v = re.sub(r'[^0-9\.\-]', '', lst[idx])
                        try:
                            val = float(v) if v and v != '-' else 0.0
                            # 200mm 초과 수치는 %100으로 나머지 연산하여 축에 뭉치게 함
                            if abs(val) > 200:
                                val %= 100
                            return val
                        except Exception:
                            return 0.0
                    # -----------------------------------------------------------------

                    try:
                        nx, ny = clean_v(lines[i+2], 0), clean_v(lines[i+3], 0)
                        lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                        for s in range(sc):
                            idx = -(sc - s)
                            ax, ay = clean_v(lines[i+2], idx), clean_v(lines[i+3], idx)
                            dv = clean_v(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"ID": f"{lbl}_S{s+1}", "NX": nx, "NY": ny, "AX": ax, "AY": ay, "DIA": dv})
                    except Exception: continue

            else:
                lines = [l.strip() for l in raw_input.split('\n') if l.strip()]
                rows = []
                for l in lines:
                    nums = [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    # 유형 A 좌표 복정 로직 그대로 유지
                    rows.append([v if abs(v) < 150 else v % 100 for v in nums])
                rows = [r for r in rows if r]
                for i in range(0, len(rows) // 3 * 3, 3):
                    for s in range(1, len(rows[i+1])):
                        results.append({"ID": f"P{(i//3)+1}_S{s}", "NX": rows[i+1][0], "NY": rows[i+2][0], "AX": rows[i+1][s], "AY": rows[i+2][s], "DIA": rows[i][s-1] if (s-1) < len(rows[i]) else rows[i][-1]})

            df = pd.DataFrame(results)
            if df.empty:
                st.error("데이터를 분석할 수 없습니다.")
                return

            df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # --- [시각화 복구] 상급자 보고용 자동 스케일 (그림 2처럼) ---
            max_limit = df['LIMIT'].max()
            v_l = round(max_limit * 0.7, 2) # 공차 원이 화면에 꽉 차보이게 스케일 조정 (그림 2처럼 줌인)
            
            fig = go.Figure()
            
            # 가이드 원 그리기
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="#1A237E", width=3), fillcolor="rgba(26, 35, 126, 0.05)")
            fig.add_shape(type="circle", x0=-max_limit/2, y0=-max_limit/2, x1=max_limit/2, y1=max_limit/2, line=dict(color="#D32F2F", width=2, dash="dash"))
            
            # 타점 설정 (그림 2처럼 십자 모양 뭉침 유지)
            for r, c, sz, sym in zip(["✅ OK", "❌ NG"], ["#4CAF50", "#FF0000"], [10, 16], ["circle", "diamond"]):
                pdf = df[df['RES'] == r]
                if not pdf.empty:
                    fig.add_trace(go.Scatter(
                        x=pdf['DX'], y=pdf['DY'],
                        mode='markers+text',
                        name=r,
                        text=pdf['ID'],
                        textposition="top center",
                        marker=dict(size=sz, color=c, symbol=sym, line=dict(width=1.5, color="black" if r=="❌ NG" else "white"))
                    ))

            fig.update_layout(
                width=800, height=800, template="plotly_white",
                title=dict(text=f"<b>위치도 분포 산점도 (기본공차 Ø{tol:.3f})</b>", x=0.5, font=dict(size=20)),
                xaxis=dict(range=[-v_l, v_l], zeroline=True, gridcolor='lightgray', title="X Deviation"),
                yaxis=dict(range=[-v_l, v_l], zeroline=True, gridcolor='lightgray', title="Y Deviation")
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- 하단 결과 요약 창 그대로 유지 ---
            col1, col2 = st.columns([2, 1])
            with col1:
                st.dataframe(df[['ID', 'POS', 'BONUS', 'LIMIT', 'RES']], use_container_width=True)
            
            with col2:
                ng_df = df[df['RES'] == "❌ NG"]
                if not ng_df.empty:
                    st.markdown(f"<div class='ng-box'>🚩 <b>불합격(NG) {len(ng_df)}건 발생</b><br>" + 
                                "".join([f"• {r['ID']}: {r['POS']:.3f} (규격 {r['LIMIT']:.3f})<br>" for _, r in ng_df.iterrows()]) + "</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ 모든 시료 합격 (ALL PASS)</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"오류: {e}")

if __name__ == "__main__":
    run_analysis()
