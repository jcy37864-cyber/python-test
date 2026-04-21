import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from io import BytesIO

# ══════════════════════════════════════════════════════════
# 전역 설정
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Quality Hub Pro v3.0",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# 본 프로그램의 소유권은 제작자에게 있습니다."
    }
)

# ── 글로벌 스타일 (글자 안 보임 현상 완전 해결) ───────────────────
def set_style():
    st.markdown("""
        <style>
        /* 1. 사이드바 배경 및 모든 텍스트/라벨 가시성 확보 */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
        }
        /* 사이드바 내의 라벨, 라디오 버튼 글자, 캡션 등을 모두 흰색으로 */
        [data-testid="stSidebar"] .stText, 
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] .stMarkdown {
            color: #f8fafc !important;
        }
        /* 라디오 버튼 텍스트가 안 보이는 문제 해결 */
        [data-testid="stSidebar"] div[role="radiogroup"] span {
            color: #f8fafc !important;
        }
        
        /* 2. 버튼 및 기타 스타일 유지 */
        .stButton > button {
            background-color: #ef4444 !important; color: white !important;
            font-weight: bold !important; width: 100%; border-radius: 8px;
            height: 3em;
        }
        .ng-box {
            height: 200px; overflow-y: auto; border: 2px solid #ff0000;
            padding: 15px; border-radius: 8px; background-color: #fff5f5;
            color: #000000;
        }
        .ok-box {
            padding: 12px; border-radius: 8px; background-color: #e8f5e9;
            color: #2e7d32; font-weight: bold; text-align: center; font-size: 1.1em;
        }
        .report-card {
            background-color: #f1f5f9; padding: 20px;
            border-left: 8px solid #3b82f6; border-radius: 8px;
            line-height: 2.0; font-size: 1.05em; color: #1e293b;
        }
        </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 공통 유틸 및 파서 (기존 로직 유지)
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

def parse_type_a(raw_input, sc):
    results = []; lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l: continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l else [p.strip() for p in re.split(r'\s{2,}', l) if p.strip()])
        if parts: lines.append(parts)
    i = 0; pt_num = 1
    while i <= len(lines) - 3:
        try:
            pos_line, x_line, y_line = lines[i], lines[i+1], lines[i+2]
            if not is_num(x_line[0]) or not is_num(y_line[0]): i += 1; continue
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', str(pos_line[0])) or f"P{pt_num}"
            pos_nums = [clean_float(v) for v in pos_line[1:] if is_num(v)]
            x_nums, y_nums = [clean_float(v) for v in x_line if is_num(v)], [clean_float(v) for v in y_line if is_num(v)]
            if len(x_nums) < 2 or len(y_nums) < 2: i += 3; continue
            nom_x, nom_y = x_nums[0], y_nums[0]
            ax_v, ay_v = x_nums[1:], y_nums[1:]
            n = min(sc, len(ax_v), len(ay_v))
            for s in range(n):
                ax, ay = ax_v[len(ax_v)-n+s], ay_v[len(ay_v)-n+s]
                pos_val = pos_nums[len(pos_nums)-n+s] if len(pos_nums)>=n else (pos_nums[min(s, len(pos_nums)-1)] if pos_nums else None)
                results.append({"ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y, "AX": ax, "AY": ay, "POS_RAW": pos_val})
            pt_num += 1; i += 3
        except: i += 1
    return results

def parse_type_b(raw_input, sc, tol, m_ref):
    results = []; lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l: continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l else [p.strip() for p in re.split(r'\s{2,}|\t', l) if p.strip()])
        if parts: lines.append(parts)
    def tail(lst, n): return [v for v in lst if v is not None][-n:]
    i = 0; pt_num = 1
    while i < len(lines) - 2:
        try:
            pos_line, mmc_line = lines[i], lines[i+1]
            four_line = (i <= len(lines) - 4 and str(lines[i+2][0]).upper() == 'X' and any('Y' in str(t).upper() for t in lines[i+3]))
            if four_line:
                nom_x, ax_vals = clean_float(lines[i+2][0]) or 0.0, [clean_float(v) for v in lines[i+2][1:] if is_num(v)]
                nom_y, ay_vals = clean_float(lines[i+3][0]) or 0.0, [clean_float(v) for v in lines[i+3][1:] if is_num(v)]
                step = 4
            else:
                nom_x, ax_vals = 0.0, [0.0]*10
                nom_y, ay_vals = clean_float(lines[i+2][0]) or 0.0, [clean_float(v) for v in lines[i+2][1:] if is_num(v)]
                step = 3
            pos_v_list, mmc_v_list = tail([clean_float(v) for v in pos_line if is_num(v)], sc), tail([clean_float(v) for v in mmc_line if is_num(v)], sc)
            ax_v_list, ay_v_list = tail(ax_vals, sc), tail(ay_vals, sc)
            n = min(sc, len(ay_v_list))
            for s in range(n):
                ax, ay = (ax_v_list[s] if s < len(ax_v_list) else nom_x), ay_v_list[s]
                dx, dy = round(ax - nom_x, 4), round(ay - nom_y, 4)
                mmc_v = (mmc_v_list[s] if s < len(mmc_v_list) and mmc_v_list[s]>0 else m_ref)
                pos_r = round(pos_v_list[s], 4) if s < len(pos_v_list) else round(np.sqrt(dx**2 + dy**2)*2, 4)
                results.append({"ID": f"P{pt_num}_S{s+1}", "NX": nom_x, "NY": nom_y, "AX": ax, "AY": ay, "DIA": mmc_v, "POS": pos_r, "BONUS": round(max(0.0, mmc_v-m_ref), 4), "LIMIT": round(tol + max(0.0, mmc_v-m_ref), 4)})
            pt_num += 1; i += step
        except: i += 1
    return results

# ── 줌 인/아웃 가능한 Plotly 산포도 ─────────────────────────────
def draw_plotly_scatter(df, tol):
    df['DX'] = (df['AX'] - df['NX']).round(4)
    df['DY'] = (df['AY'] - df['NY']).round(4)
    
    fig = go.Figure()
    
    # 1. 기본 공차 원 (Ø tol)
    t = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(go.Scatter(x=(tol/2)*np.cos(t), y=(tol/2)*np.sin(t), fill="toself", fillcolor="rgba(52, 152, 219, 0.1)", line=dict(color="#3498db", dash="dash"), name=f"Basic Tol (Ø{tol})", hoverinfo='skip'))
    
    # 2. 측정 점
    for res_type in ['OK', 'NG']:
        sub = df[df['RES'] == res_type]
        fig.add_trace(go.Scatter(
            x=sub['DX'], y=sub['DY'], mode='markers+text',
            name=res_type, text=sub['ID'], textposition="top center",
            marker=dict(size=10, color='#2ecc71' if res_type=='OK' else '#e74c3c', line=dict(width=1, color='white'))
        ))

    # 레이아웃 설정 (줌 가능하도록)
    max_val = max(df['DX'].abs().max(), df['DY'].abs().max(), tol/2) * 1.5
    fig.update_layout(
        title="Position Deviation Scatter (Interactive Zoom)",
        xaxis=dict(title="X Deviation", range=[-max_val, max_val], zeroline=True, zerolinewidth=2, zerolinecolor='black'),
        yaxis=dict(title="Y Deviation", range=[-max_val, max_val], zeroline=True, zerolinewidth=2, zerolinecolor='black'),
        width=700, height=700, template="plotly_white",
        dragmode='pan', # 기본 드래그 모드를 이동(Pan)으로 설정 (휠로 줌인/아웃 가능)
        hovermode='closest'
    )
    return fig

# ══════════════════════════════════════════════════════════
# 메인 분석 실행부
# ══════════════════════════════════════════════════════════
def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")
    
    with st.sidebar:
        st.markdown("### 분석 설정")
        mode = st.radio("성적서 유형", ["유형 A (3줄: 포인트명/X/Y)", "유형 B (자동감지: 위치도/MMC/X?/Y)"])
        sc = st.number_input("시료 수 (Sample)", min_value=1, value=4)
        tol = st.number_input("기본 공차 (Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값 (지름)", value=0.350, format="%.3f")

    raw_input = st.text_area("데이터를 붙여넣으세요", height=200)
    
    if st.button("📊 분석 실행") and raw_input:
        try:
            if "A" in mode:
                data = parse_type_a(raw_input, sc)
                df = pd.DataFrame(data)
                df['LIMIT'] = tol
                df['POS'] = df.apply(lambda r: round(float(r['POS_RAW']), 4) if r['POS_RAW'] is not None else round(np.sqrt((r['AX']-r['NX'])**2 + (r['AY']-r['NY'])**2)*2, 4), axis=1)
            else:
                data = parse_type_b(raw_input, sc, tol, m_ref)
                df = pd.DataFrame(data)
            
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")
            
            # 그래프 출력
            st.plotly_chart(draw_plotly_scatter(df, tol), use_container_width=True)
            st.info("💡 마우스 휠로 줌인/아웃이 가능하며, 그래프를 드래그하여 이동할 수 있습니다.")

            # 통계 및 테이블
            c1, c2 = st.columns([2, 1])
            with c1:
                st.dataframe(df[['ID', 'POS', 'LIMIT', 'RES']].style.applymap(lambda x: 'background-color: #ffbaba' if x=='NG' else '', subset=['RES']), use_container_width=True)
            with c2:
                ng_count = (df['RES'] == 'NG').sum()
                if ng_count > 0: st.error(f"🚩 NG 발생: {ng_count}건")
                else: st.success("✅ ALL PASS")
                
        except Exception as e: st.error(f"분석 중 오류: {e}")

def main():
    set_style()
    st.sidebar.title("QUALITY HUB v3.0")
    menu = st.sidebar.radio("분석 카테고리", ["🎯 위치도 정밀 분석", "📈 멀티 캐비티 분석", "🧮 품질 통합 계산기"])
    
    if st.sidebar.button("🗑️ 데이터 리셋"): st.rerun()

    if menu == "🎯 위치도 정밀 분석": run_position_analysis()
    else: st.info("선택하신 메뉴는 현재 준비 중이거나 기본 로직으로 작동합니다.")

if __name__ == "__main__":
    main()
