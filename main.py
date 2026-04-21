import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re

# 초기 설정
st.set_page_config(page_title="Quality Hub", layout="wide")

def run_analysis():
    st.title("🎯 위치도 정밀 분석 리포트")
    
    with st.sidebar:
        st.header("⚙️ 설정")
        mode = st.radio("유형", ["유형 B", "유형 A"])
        sc = st.number_input("시료 수", min_value=1, value=4)
        tol = st.number_input("기본 공차", value=0.350, format="%.3f")
        m_ref = st.number_input("기준값", value=0.060 if mode == "유형 A" else 0.350, format="%.3f")

    raw_data = st.text_area("데이터 붙여넣기", height=200)
    
    if st.button("📊 분석 시작") and raw_data:
        try:
            results = []
            # --- 데이터 파싱 ---
            if mode == "유형 B":
                lines = [re.split(r'\s+', l.strip()) for l in raw_data.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break
                    def gv(l, idx):
                        v = re.sub(r'[^0-9\.\-]', '', l[idx])
                        return float(v) if v and v != '-' else 0.0
                    nx, ny = gv(lines[i+2], 0), gv(lines[i+3], 0)
                    lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                    for s in range(sc):
                        idx = -(sc - s)
                        try:
                            ax, ay = gv(lines[i+2], idx), gv(lines[i+3], idx)
                            dv = gv(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
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
                        results.append({"ID":f"P{(i//3)+1}_S{s}","NX":x_r[0],"NY":y_r[0],"AX":x_r[s],"AY":y_r[s],"DIA":d_r[s-1] if (s-1)<len(d_r) else d_r[-1]})

            df = pd.DataFrame(results)
            if df.empty: return st.error("데이터 없음")

            # 계산
            df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")

            # 시각화 (잘림 방지를 위해 줄바꿈 세분화)
            m_lim = df['LIMIT'].max()
            v_r = round(m_lim * 0.75, 2)
            fig = go.Figure()
            
            # 가이드 원
            fig.add_shape(type="circle", x0=-tol/2, y0=-tol/2, x1=tol/2, y1=tol/2, line=dict(color="Blue", width=2))
            fig.add_shape(type="circle", x0=-m_lim/2, y0=-m_lim/2, x1=m_lim/2, y1=m_lim/2, line=dict(color="Red", width=2, dash="dash"))
            
            # 타점 설정 (문제의 marker 부분 수정)
            for r, c, sz in zip(["OK", "NG"], ["green", "red"], [10, 18]):
                pdf = df[df['RES'] == r]
                if not pdf.empty:
                    fig.add_trace(go.Scatter(
                        x=pdf['DX'], 
                        y=pdf['DY'], 
                        mode='markers+text', 
                        name=r,
                        text=pdf['ID'],
                        marker=dict(
                            size=sz,
                            color=c,
                            line=dict(
                                width=2,
                                color="black"
                            )
                        )
                    ))

            fig.update_layout(
                width=700, 
                height=700, 
                xaxis=dict(range=[-v_r, v_r], zeroline=True),
                yaxis=dict(range=[-v_r, v_r], zeroline=True)
            )
            st.plotly_chart(fig)

            # 결과 리스트
            ng_list = df[df['RES'] == "NG"]
            if not ng_list.empty:
                st.error(f"🚨 NG {len(ng_list)}건")
                st.write(ng_list[['ID', 'POS', 'LIMIT']])
            else:
                st.success("✅ ALL PASS")
            st.dataframe(df)

        except Exception as e:
            st.error(f"오류: {e}")

if __name__ == "__main__":
    run_analysis()
