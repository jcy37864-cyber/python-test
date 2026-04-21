import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from io import BytesIO

# ══════════════════════════════════════════════════════════
# 전역 설정 및 스타일 개선
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Quality Hub Pro v3.1",
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# 본 프로그램의 소유권은 제작자에게 있습니다."
    }
)

def set_style():
    st.markdown("""
        <style>
        /* 1. 사이드바 가독성 개선 (글자색 흰색 고정 및 굵게) */
        [data-testid="stSidebar"] { 
            background-color: #0f172a !important; 
        }
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
        .ng-box {
            height: 200px; overflow-y: auto; border: 2px solid #ff0000;
            padding: 15px; border-radius: 8px; background-color: #fff5f5;
        }
        .ok-box {
            padding: 12px; border-radius: 8px; background-color: #e8f5e9;
            color: #2e7d32; font-weight: bold; text-align: center; font-size: 1.1em;
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
        if v.startswith('-'):
            v = '-' + v[1:].replace('-', '')
        else:
            v = v.replace('-', '')
        return float(v) if v and v not in ('-', '.', '-.') else None
    except:
        return None

def is_num(val):
    return clean_float(val) is not None

def apply_style(df_styled, subset):
    def hi(v):
        return 'background-color: #DFF2BF' if 'OK' in str(v) else 'background-color: #FFBABA'
    try:
        return df_styled.map(hi, subset=subset)
    except AttributeError:
        return df_styled.applymap(hi, subset=subset)

# ══════════════════════════════════════════════════════════
# A유형 파서
# ══════════════════════════════════════════════════════════
def parse_type_a(raw_input, sc):
    results = []
    lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l: continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l
                 else [p.strip() for p in re.split(r'\s{2,}', l) if p.strip()])
        if parts: lines.append(parts)
    i = 0
    pt_num = 1
    while i <= len(lines) - 3:
        try:
            pos_line, x_line, y_line = lines[i], lines[i+1], lines[i+2]
            if not re.search(r'[A-Za-z가-힣]', str(pos_line[0])):
                i += 1; continue
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', str(pos_line[0])) or f"P{pt_num}"
            pos_nums = [clean_float(v) for v in pos_line[1:] if is_num(v)]
            x_nums = [clean_float(v) for v in x_line if is_num(v)]
            y_nums = [clean_float(v) for v in y_line if is_num(v)]
            if len(x_nums) < 2 or len(y_nums) < 2:
                i += 3; continue
            nom_x, nom_y = x_nums[0], y_nums[0]
            ax_vals, ay_vals = x_nums[1:], y_nums[1:]
            n = min(sc, len(ax_vals), len(ay_vals))
            for s in range(n):
                pos_val = pos_nums[len(pos_nums) - n + s] if len(pos_nums) >= n else (pos_nums[min(s, len(pos_nums)-1)] if pos_nums else None)
                results.append({"ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y, "AX": ax_vals[s], "AY": ay_vals[s], "POS_RAW": pos_val})
            pt_num += 1; i += 3
        except: i += 1
    return results

# ══════════════════════════════════════════════════════════
# B유형 파서
# ══════════════════════════════════════════════════════════
def parse_type_b(raw_input, sc, tol, m_ref):
    results = []
    lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l: continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l else [p.strip() for p in re.split(r'\s{2,}|\t', l) if p.strip()])
        if parts: lines.append(parts)
    def tail(lst, n):
        lst = [v for v in lst if v is not None]
        return lst[-n:] if len(lst) >= n else lst
    def ft(row): return str(row[0]).strip().upper() if row else ''
    def is_y_row(row):
        if not row: return False
        return ft(row) == 'Y' or (is_num(row[0]) and any(str(t).strip().upper() == 'Y' for t in row))
    def is_x_row(row): return ft(row) == 'X'
    def extract_row(row, label):
        if ft(row) == label: return 0.0, [clean_float(v) for v in row[1:] if is_num(v)]
        try:
            idx = next(j for j, t in enumerate(row) if str(t).strip().upper() == label)
            return (clean_float(row[0]) if is_num(row[0]) else 0.0), [clean_float(v) for v in row[idx+1:] if is_num(v)]
        except StopIteration:
            nums = [clean_float(v) for v in row if is_num(v)]
            return (nums[0] if nums else 0.0), nums[1:]
    def extract_label(pos_line):
        for tok in pos_line:
            m = re.search(r'위치도\s*([A-Za-z0-9_]+)', str(tok))
            if m: return m.group(1)
        for tok in pos_line:
            s = str(tok).strip()
            if re.fullmatch(r'[A-Za-z]{1,4}', s) and s.upper() not in ('X', 'Y'): return s.upper()
        return None
    i, pt_num = 0, 1
    while i < len(lines) - 2:
        try:
            four_line = (i <= len(lines) - 4 and is_x_row(lines[i+2]) and is_y_row(lines[i+3]))
            three_line = (not four_line) and is_y_row(lines[i+2])
            if not four_line and not three_line: i += 1; continue
            lbl = extract_label(lines[i]) or f"P{pt_num}"
            pos_nums, mmc_nums = [clean_float(v) for v in lines[i] if is_num(v)], [clean_float(v) for v in lines[i+1] if is_num(v)]
            if four_line:
                nom_x, ax_vals = extract_row(lines[i+2], 'X')
                nom_y, ay_vals = extract_row(lines[i+3], 'Y')
                step = 4
            else:
                nom_x, ax_vals, (nom_y, ay_vals) = 0.0, [0.0]*len(tail(pos_nums, sc)), extract_row(lines[i+2], 'Y')
                step = 3
            pos_vals, mmc_vals, ax_vals, ay_vals = tail(pos_nums, sc), tail(mmc_nums, sc), tail(ax_vals, sc), tail(ay_vals, sc)
            n = min(sc, len(pos_vals), len(ay_vals))
            for s in range(n):
                mmc_v = mmc_vals[s] if (s < len(mmc_vals) and mmc_vals[s] is not None and mmc_vals[s] > 0) else m_ref
                dx, dy = round((ax_vals[s] if s < len(ax_vals) else nom_x) - nom_x, 4), round(ay_vals[s] - nom_y, 4)
                pos_res = round(pos_vals[s], 4) if s < len(pos_vals) and pos_vals[s] is not None else round(np.sqrt(dx**2 + dy**2) * 2, 4)
                bonus = round(max(0.0, mmc_v - m_ref), 4)
                results.append({"ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y, "AX": (ax_vals[s] if s < len(ax_vals) else nom_x), "AY": ay_vals[s], "DIA": mmc_v, "POS": pos_res, "BONUS": bonus, "LIMIT": round(tol + bonus, 4)})
            pt_num += 1; i += step
        except: i += 1
    return results

# ══════════════════════════════════════════════════════════
# 인터랙티브 산포도 (Plotly 활용 - 줌 기능 포함)
# ══════════════════════════════════════════════════════════
def draw_interactive_plot(df, tol):
    basic_r = tol / 2
    fig = go.Figure()
    theta = np.linspace(0, 2*np.pi, 100)
    fig.add_trace(go.Scatter(x=basic_r*np.cos(theta), y=basic_r*np.sin(theta), fill="toself", fillcolor="rgba(52, 152, 219, 0.1)", line=dict(color="rgba(52, 152, 219, 0.5)", dash="dash"), name=f"기본 공차 (Ø{tol:.3f})", hoverinfo="skip"))
    ok_df, ng_df = df[df['RES'] == 'OK'], df[df['RES'] == 'NG']
    fig.add_trace(go.Scatter(x=ok_df['DX'], y=ok_df['DY'], mode='markers', name='합격 (OK)', marker=dict(color='#2ecc71', size=10, line=dict(width=1, color='white')), text=ok_df['ID'] + "  
위치도: " + ok_df['POS'].astype(str), hovertemplate="<b>%{text}</b>  
X편차: %{x}  
Y편차: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ng_df['DX'], y=ng_df['DY'], mode='markers', name='불합격 (NG)', marker=dict(color='#e74c3c', size=12, symbol='x', line=dict(width=1, color='white')), text=ng_df['ID'] + "  
위치도: " + ng_df['POS'].astype(str), hovertemplate="<b>%{text}</b>  
X편차: %{x}  
Y편차: %{y}<extra></extra>"))
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.add_hline(y=0, line_width=1, line_color="black")
    max_val = max(df['DX'].abs().max() if not df.empty else 0, df['DY'].abs().max() if not df.empty else 0, basic_r) * 1.5
    fig.update_layout(title="위치도 산포도 (마우스 휠로 줌 가능)", xaxis=dict(title="X 편차 (mm)", range=[-max_val, max_val], zeroline=False), yaxis=dict(title="Y 편차 (mm)", range=[-max_val, max_val], scaleanchor="x", scaleratio=1, zeroline=False), height=700, template="plotly_white", dragmode='pan')
    return fig

# ══════════════════════════════════════════════════════════
# 각 메뉴별 실행 함수
# ══════════════════════════════════════════════════════════
def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")
    with st.sidebar:
        st.markdown("### 분석 설정")
        mode = st.radio("성적서 유형", ["유형 A (3줄: 포인트명/X/Y)", "유형 B (자동감지: 위치도/MMC/X?/Y)"])
        sc, tol, m_ref = st.number_input("시료 수", min_value=1, value=4), st.number_input("기본 공차 (Ø)", value=0.350, format="%.3f"), st.number_input("MMC 기준값", value=0.350, format="%.3f")
    raw_input = st.text_area("데이터 붙여넣기", height=280)
    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            if "A" in mode:
                results = parse_type_a(raw_input, sc)
                df = pd.DataFrame(results)
                df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
                df['POS'] = df.apply(lambda r: round(float(r['POS_RAW']), 4) if r['POS_RAW'] is not None else round(np.sqrt(r['DX']**2 + r['DY']**2) * 2, 4), axis=1)
                df['BONUS'], df['LIMIT'] = 0.0, tol
            else:
                df = pd.DataFrame(parse_type_b(raw_input, sc, tol, m_ref))
                df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")
            st.subheader("🎯 위치도 산포도 (줌/이동 가능)")
            st.plotly_chart(draw_interactive_plot(df, tol), use_container_width=True)
            # 통계 요약 및 테이블 생략 없이 출력
            total, ok_n = len(df), (df['RES'] == 'OK').sum()
            st.metric("합격률", f"{(ok_n/total*100):.1f}%", delta=f"-{total-ok_n} NG")
            st.dataframe(apply_style(df[['ID', 'DX', 'DY', 'POS', 'LIMIT', 'RES']].style, subset=['RES']), use_container_width=True)
        except Exception as e: st.error(f"오류: {e}")

def run_cavity_analysis():
    st.title("📈 멀티 캐비티 분석")
    up = st.file_uploader("Excel / CSV 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        for cav in cav_cols:
            df[f"{cav}_판정"] = df.apply(lambda r, c=cav: "OK" if r["SPEC_MIN"] <= r[c] <= r["SPEC_MAX"] else "NG", axis=1)
        fig = go.Figure()
        for i, cav in enumerate(cav_cols):
            fig.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='lines+markers', name=cav))
        st.plotly_chart(fig, use_container_width=True)

def run_quality_calculator():
    st.title("🧮 품질 종합 계산기")
    t1, t2 = st.tabs(["MMC 계산", "단위 변환"])
    with t1:
        b, m, a = st.number_input("기본공차", value=0.05), st.number_input("MMC지름", value=10.0), st.number_input("실측지름", value=10.02)
        st.success(f"최종 허용 공차: Ø{b + max(0.0, a-m):.4f}")

def main():
    set_style()
    menu = st.sidebar.radio("메뉴 선택", ["🎯 위치도 정밀 분석", "📈 멀티 캐비티 분석", "🧮 품질 통합 계산기"])
    if "위치도" in menu: run_position_analysis()
    elif "캐비티" in menu: run_cavity_analysis()
    else: run_quality_calculator()

if __name__ == "__main__":
    main()
