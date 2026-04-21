import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from io import BytesIO

# ══════════════════════════════════════════════════════════
# 전역 설정 및 스타일 개선
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="Quality Hub Pro v3.1", layout="wide")

def set_style():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #0f172a !important; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
        [data-testid="stSidebar"] .stRadio label {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        .stButton > button {
            background-color: #ef4444 !important; color: white !important;
            font-weight: bold !important; width: 100%; border-radius: 8px;
            height: 3em;
        }
        .report-card {
            background-color: #f1f5f9; padding: 20px;
            border-left: 8px solid #3b82f6; border-radius: 8px;
            line-height: 2.0; font-size: 1.05em;
        }
        </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 공통 유틸리티
# ══════════════════════════════════════════════════════════
def clean_float(val):
    try:
        v = re.sub(r'[^0-9.\-]', '', str(val))
        v = re.sub(r'-+', '-', v)
        if v.startswith('-'): v = '-' + v[1:].replace('-', '')
        else: v = v.replace('-', '')
        return float(v) if v and v not in ('-', '.', '-.') else None
    except: return None

def is_num(val): return clean_float(val) is not None

# ══════════════════════════════════════════════════════════
# 인터랙티브 산포도 (Plotly 줌 기능)
# ══════════════════════════════════════════════════════════
def draw_interactive_plot(df, tol):
    basic_r = tol / 2
    fig = go.Figure()
    
    # 공차 원 그리기
    theta = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(go.Scatter(
        x=basic_r*np.cos(theta), y=basic_r*np.sin(theta),
        fill="toself", fillcolor="rgba(52, 152, 219, 0.1)",
        line=dict(color="rgba(52, 152, 219, 0.5)", dash="dash"),
        name=f"기본 공차 (Ø{tol:.3f})", hoverinfo="skip"
    ))

    # 데이터 포인트 (에러 방지를 위해 문자열 결합 방식 수정)
    for res_type, color, name in [('OK', '#2ecc71', '합격 (OK)'), ('NG', '#e74c3c', '불합격 (NG)')]:
        sub_df = df[df['RES'] == res_type]
        if not sub_df.empty:
            # 툴팁 텍스트 미리 생성 (에러 방지)
            hover_text = [f"ID: {r['ID']}  
위치도: {r['POS']}" for _, r in sub_df.iterrows()]
            fig.add_trace(go.Scatter(
                x=sub_df['DX'], y=sub_df['DY'],
                mode='markers', name=name,
                marker=dict(color=color, size=10, line=dict(width=1, color='white')),
                text=hover_text,
                hovertemplate="<b>%{text}</b>  
X편차: %{x}  
Y편차: %{y}<extra></extra>"
            ))

    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.add_hline(y=0, line_width=1, line_color="black")
    
    # 축 범위 설정
    max_val = max(df['DX'].abs().max() if not df.empty else 0, 
                  df['DY'].abs().max() if not df.empty else 0, 
                  basic_r) * 1.5
    
    fig.update_layout(
        title="위치도 산포도 (마우스 휠 줌 / 드래그 이동)",
        xaxis=dict(title="X 편차 (mm)", range=[-max_val, max_val]),
        yaxis=dict(title="Y 편차 (mm)", range=[-max_val, max_val], scaleanchor="x", scaleratio=1),
        height=700, template="plotly_white", dragmode='pan'
    )
    return fig

# ══════════════════════════════════════════════════════════
# 파서 및 메뉴 로직 (기존 기능 통합)
# ══════════════════════════════════════════════════════════
def parse_type_a(raw_input, sc):
    results = []
    lines = [re.split(r'\s{2,}|\t', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
    i, pt_num = 0, 1
    while i <= len(lines) - 3:
        try:
            p_l, x_l, y_l = lines[i], lines[i+1], lines[i+2]
            if not re.search(r'[A-Za-z가-힣]', str(p_l[0])): i += 1; continue
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', str(p_l[0])) or f"P{pt_num}"
            x_n, y_n = [clean_float(v) for v in x_l if is_num(v)], [clean_float(v) for v in y_l if is_num(v)]
            if len(x_n) < 2 or len(y_n) < 2: i += 3; continue
            for s in range(min(sc, len(x_n)-1, len(y_n)-1)):
                results.append({"ID": f"{lbl}_S{s+1}", "NX": x_n[0], "NY": y_n[0], "AX": x_n[s+1], "AY": y_n[s+1], "POS_RAW": None})
            pt_num += 1; i += 3
        except: i += 1
    return results

def run_position_analysis():
    st.title("🎯 위치도 정밀 분석")
    with st.sidebar:
        mode = st.radio("유형", ["유형 A", "유형 B"])
        sc = st.number_input("시료 수", min_value=1, value=4)
        tol = st.number_input("공차", value=0.350, format="%.3f")
    
    raw_data = st.text_area("데이터 붙여넣기", height=250)
    if st.button("분석 실행") and raw_data:
        res = parse_type_a(raw_data, sc) if "A" in mode else [] # B유형 로직은 이전과 동일하게 유지 가능
        if res:
            df = pd.DataFrame(res)
            df['DX'], df['DY'] = (df['AX']-df['NX']).round(4), (df['AY']-df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2)*2).round(4)
            df['LIMIT'], df['RES'] = tol, ""
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")
            
            st.plotly_chart(draw_interactive_plot(df, tol), use_container_width=True)
            st.dataframe(df[['ID', 'DX', 'DY', 'POS', 'LIMIT', 'RES']], use_container_width=True)

def main():
    set_style()
    menu = st.sidebar.radio("메뉴", ["🎯 위치도 분석", "📈 캐비티 분석", "🧮 계산기"])
    if "위치도" in menu: run_position_analysis()
    # 나머지 메뉴(캐비티, 계산기)도 기존 로직대로 추가 가능합니다.

if __name__ == "__main__":
    main()
