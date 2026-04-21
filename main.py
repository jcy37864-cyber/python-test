import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from io import BytesIO

# ══════════════════════════════════════════════════════════
# 1. 스타일 설정 (글자 가독성 개선)
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
# 2. 공통 유틸리티
# ══════════════════════════════════════════════════════════
def clean_float(val):
    try:
        v = re.sub(r'[^0-9.\-]', '', str(val))
        v = re.sub(r'-+', '-', v)
        if v.startswith('-'):
            v = '-' + v[1:].replace('-', '')
        else:
            v = v.replace('-', '')
        return float(v) if v and v not in ('-', '.', '-.') else None
    except:
        return None

def is_num(val):
    return clean_float(val) is not None

# ══════════════════════════════════════════════════════════
# 3. 인터랙티브 산포도 (오류 수정 완료)
# ══════════════════════════════════════════════════════════
def draw_interactive_plot(df, tol):
    basic_r = tol / 2
    fig = go.Figure()
    
    # 공차 원 (파란색 반투명)
    theta = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(go.Scatter(
        x=basic_r * np.cos(theta), 
        y=basic_r * np.sin(theta),
        fill="toself", 
        fillcolor="rgba(52, 152, 219, 0.1)",
        line=dict(color="rgba(52, 152, 219, 0.5)", dash="dash"),
        name="기본 공차", 
        hoverinfo="skip"
    ))

    # 데이터 포인트 처리
    for res_type, color, name in [('OK', '#2ecc71', '합격'), ('NG', '#e74c3c', '불합격')]:
        sub_df = df[df['RES'] == res_type]
        if not sub_df.empty:
            # 툴팁 텍스트에서 줄바꿈 오류 수정 (<br> 태그 사용)
            texts = [f"ID: {r['ID']}<br>위치도: {r['POS']}" for _, r in sub_df.iterrows()]
            
            fig.add_trace(go.Scatter(
                x=sub_df['DX'], 
                y=sub_df['DY'],
                mode='markers', 
                name=name,
                marker=dict(color=color, size=10, line=dict(width=1, color='white')),
                text=texts,
                hovertemplate="<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>"
            ))

    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.add_hline(y=0, line_width=1, line_color="black")
    
    # 축 범위 설정 (중심으로부터 균형 잡힌 뷰)
    max_d = max(df['DX'].abs().max() if not df.empty else 0, 
                df['DY'].abs().max() if not df.empty else 0, 
                basic_r) * 1.3
    
    fig.update_layout(
        title="위치도 산포도 (줌/이동 가능)",
        xaxis=dict(title="X편차", range=[-max_d, max_d]),
        yaxis=dict(title="Y편차", range=[-max_d, max_d], scaleanchor="x", scaleratio=1),
        height=700, 
        template="plotly_white", 
        dragmode='pan'
    )
    return fig

# ══════════════════════════════════════════════════════════
# 4. 데이터 파서
# ══════════════════════════════════════════════════════════
def parse_type_a(raw_input, sc):
    results = []
    lines = [re.split(r'\s{2,}|\t', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
    i, pt_num = 0, 1
    while i <= len(lines) - 3:
        try:
            p_l, x_l, y_l = lines[i], lines[i+1], lines[i+2]
            # 첫 번째 요소가 숫자가 아닌 경우(라벨인 경우) 처리
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', str(p_l[0])) or f"P{pt_num}"
            
            x_n = [clean_float(v) for v in x_l if is_num(v)]
            y_n = [clean_float(v) for v in y_l if is_num(v)]
            
            if len(x_n) >= 2 and len(y_n) >= 2:
                nom_x, nom_y = x_n[0], y_n[0]
                # 실측치 루프
                for s in range(min(sc, len(x_n)-1, len(y_n)-1)):
                    results.append({
                        "ID": f"{lbl}_S{s+1}", 
                        "NX": nom_x, "NY": nom_y, 
                        "AX": x_n[s+1], "AY": y_n[s+1]
                    })
                pt_num += 1
            i += 3
        except:
            i += 1
    return results

# ══════════════════════════════════════════════════════════
# 5. 페이지 실행 로직
# ══════════════════════════════════════════════════════════
def run_position_analysis():
    st.title("🎯 위치도 정밀 분석")
    with st.sidebar:
        st.subheader("분석 설정")
        mode = st.radio("데이터 유형", ["유형 A (3줄: 항목/X/Y)"])
        sc = st.number_input("시료 수 (Sample Count)", min_value=1, value=4)
        tol = st.number_input("공차(Ø) 기준값", value=0.350, format="%.3f", step=0.010)
    
    st.markdown("#### 📥 데이터 입력")
    raw_data = st.text_area("측정 데이터를 붙여넣으세요 (항목명, X데이터줄, Y데이터줄 순서)", height=200, 
                           placeholder="Point_1\n0.000  0.012  -0.005  0.020\n0.000  -0.010  0.008  0.015")
    
    if st.button("분석 실행"):
        if raw_data:
            res = parse_type_a(raw_data, sc)
            if res:
                df = pd.DataFrame(res)
                # 편차 및 위치도 계산 (위치도 = 2 * SQRT(DX^2 + DY^2))
                df['DX'] = (df['AX'] - df['NX']).round(4)
                df['DY'] = (df['AY'] - df['NY']).round(4)
                df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
                df['LIMIT'] = tol
                df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")
                
                # 결과 레이아웃
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.plotly_chart(draw_interactive_plot(df, tol), use_container_width=True)
                with col2:
                    st.markdown("### 📊 분석 요약")
                    ok_count = len(df[df['RES'] == 'OK'])
                    total = len(df)
                    st.metric("합격률", f"{(ok_count/total*100):.1f}%", f"{ok_count}/{total}")
                    st.dataframe(df[['ID', 'POS', 'RES']].style.apply(
                        lambda x: ['background-color: #ffcccc' if v == 'NG' else '' for v in x], subset=['RES']
                    ), use_container_width=True, height=550)
                
                st.markdown("### 📑 상세 데이터 테이블")
                st.dataframe(df, use_container_width=True)
            else:
                st.error("데이터 파싱에 실패했습니다. 입력 형식을 확인해주세요.")
        else:
            st.warning("데이터를 입력해주세요.")

def run_cavity_analysis():
    st.title("📈 멀티 캐비티 분석")
    st.info("준비 중인 기능입니다.")

def run_quality_calculator():
    st.title("🧮 품질 계산기")
    st.info("준비 중인 기능입니다.")

def main():
    set_style()
    menu = st.sidebar.radio("메뉴 선택", ["🎯 위치도 분석", "📈 캐비티 분석", "🧮 계산기"])
    
    if "위치도" in menu:
        run_position_analysis()
    elif "캐비티" in menu:
        run_cavity_analysis()
    else:
        run_quality_calculator()

if __name__ == "__main__":
    main()
