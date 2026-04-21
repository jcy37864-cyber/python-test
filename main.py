import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

st.set_page_config(page_title="Quality Hybrid v2.5", layout="wide")

def run_analysis():
    st.title("🎯 위치도 정밀 분석 시스템 (Hybrid)")

    with st.sidebar:
        st.header("⚙️ 설정")
        mode = st.radio("유형", ["유형 B (가로형)", "유형 A (3줄 세트)"])
        sc = st.number_input("샘플 수", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("기준치", value=0.060 if mode == "유형 A (3줄 세트)" else 0.350, format="%.3f")
        v_mode = st.radio("범위", ["자동", "수동"], horizontal=True)
        v_limit = st.slider("줌", 0.1, 5.0, 0.5) if v_mode == "수동" else 0.5

    raw_input = st.text_area("데이터를 붙여넣으세요", height=250)
    
    if st.button("📊 분석 시작") and raw_input:
        try:
            results = []
            if mode == "유형 B (가로형)":
                # 빈 문자열을 제외하고 리스트화
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    # 숫자만 추출하는 내부 함수 (빈 값 방지)
                    def get_num(lst, idx):
                        val = re.sub(r'[^0-9\.\-]', '', lst[idx])
                        return float(val) if val and val != '-' else 0.0

                    nx = get_num(lines[i+2], 0)
                    ny = get_num(lines[i+3], 0)
                    lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                    
                    for s in range(sc):
                        idx = -(sc - s)
                        try:
                            ax = get_num(lines[i+2], idx)
                            ay = get_num(lines[i+3], idx)
                            dv = get_num(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"ID": f"{lbl}_S{s+1}", "NX": nx, "NY": ny, "AX": ax, "AY": ay, "DIA": dv})
                        except: continue
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

            df = pd.DataFrame(results)
            if df.empty:
                st.error("분석할 수 있는 데이터가 없습니다.")
                return

            df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            mx_lim = df['LIMIT'].max()
            v_l = round((mx_lim / 2) * 1.5, 2) if v_mode == "자동" else v_limit
            
            fig = go.Figure()
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="RoyalBlue", width=2), fillcolor="rgba(65, 105, 225, 0.05)")
            fig.add_shape(type="circle", x0=-mx_lim/2, y0=-mx_lim/2, x1=mx_lim/2, y1=mx_lim/2, line=dict(color="Red", width=1.5, dash="dot"))
            
            for r, c in zip(["✅ OK", "❌ NG"], ["#2ecc71", "#e74c3c"]):
                pdf = df[df['RES'] == r]
                if not pdf.empty:
                    fig.add_trace(go.Scatter(x=pdf['DX'], y=pdf['DY'], mode='markers+text', name=r, text=pdf['ID'], textposition="top center", marker=dict(size=10, color=c, line=dict(width=1, color="white"))))
            
            fig.update_layout(width=700, height=700, template="plotly_white", xaxis=dict(range=[-v_l, v_l], zeroline=True), yaxis=dict(range=[-v_l, v_l], zeroline=True))
            st.plotly_chart(fig, use_container_width=True)

            if not df[df['RES'] == "❌ NG"].empty:
                st.error("🚨 NG 상세 리스트")
                for _, r in df[df['RES'] == "❌ NG"].iterrows():
                    st.write(f"• {r['ID']}: {r['POS']} (공차: {r['LIMIT']})")
            else: st.success("✅ 모든 시료 합격")
            st.dataframe(df[['ID', 'POS', 'BONUS', 'LIMIT', 'RES']], use_container_width=True)
        except Exception as e: st.error(f"오류: {e}")

if __name__ == "__main__":
    run_analysis()
