import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
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

# ── 한글 폰트 ──────────────────────────────────────────────
def set_korean_font():
    try:
        font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        fm.fontManager.addfont(font_path)
        prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        try:
            system_fonts = fm.findSystemFonts()
            korean_keywords = ['noto', 'cjk', 'gothic', 'gulim', 'batang', 'malgun']
            found = next((fp for fp in system_fonts
                          if any(k in fp.lower() for k in korean_keywords)), None)
            if found:
                fm.fontManager.addfont(found)
                plt.rcParams['font.family'] = fm.FontProperties(fname=found).get_name()
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass

set_korean_font()

# ── 글로벌 스타일 (글자 안 보임 현상 수정) ──────────────────────────
def set_style():
    st.markdown("""
        <style>
        /* 사이드바 배경 및 글자색 강제 지정 */
        [data-testid="stSidebar"] { 
            background-color: #0f172a !important; 
        }
        /* 입력 필드 라벨(시료수 등)이 배경에 묻히지 않게 흰색 처리 */
        [data-testid="stSidebar"] label, 
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stNumberInput div { 
            color: #f8fafc !important; 
        }
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
            line-height: 2.0; font-size: 1.05em;
            color: #1e293b;
        }
        </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 공통 유틸
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
    except Exception:
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
# 파서 및 분석 로직 (유형 A/B)
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
            first_tok = str(pos_line[0]) if pos_line else ''
            if not re.search(r'[A-Za-z가-힣]', first_tok): i += 1; continue
            if not is_num(x_line[0]) or not is_num(y_line[0]): i += 1; continue
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', first_tok) or f"P{pt_num}"
            pos_nums = [clean_float(v) for v in pos_line[1:] if is_num(v)]
            x_nums, y_nums = [clean_float(v) for v in x_line if is_num(v)], [clean_float(v) for v in y_line if is_num(v)]
            if len(x_nums) < 2 or len(y_nums) < 2: i += 3; continue
            nom_x, nom_y = x_nums[0], y_nums[0]
            ax_vals, ay_vals = x_nums[1:], y_nums[1:]
            n = min(sc, len(ax_vals), len(ay_vals))
            for s in range(n):
                si = len(ax_vals) - n + s
                ax, ay = ax_vals[si], ay_vals[si]
                pos_val = pos_nums[len(pos_nums) - n + s] if len(pos_nums) >= n else (pos_nums[min(s, len(pos_nums)-1)] if pos_nums else None)
                results.append({"ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y, "AX": ax, "AY": ay, "POS_RAW": pos_val})
            pt_num += 1; i += 3
        except Exception: i += 1
    return results

def parse_type_b(raw_input, sc, tol, m_ref):
    results = []
    lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l: continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l else [p.strip() for p in re.split(r'\s{2,}|\t', l) if p.strip()])
        if parts: lines.append(parts)

    def tail(lst, n): return [v for v in lst if v is not None][-n:]
    def ft(row): return str(row[0]).strip().upper() if row else ''
    def is_y_row(row): return ft(row) == 'Y' or (row and is_num(row[0]) and any(str(t).strip().upper() == 'Y' for t in row))
    def is_x_row(row): return ft(row) == 'X'
    def extract_row(row, label):
        if ft(row) == label: return 0.0, [clean_float(v) for v in row[1:] if is_num(v)]
        try:
            idx = next(j for j, t in enumerate(row) if str(t).strip().upper() == label)
            return (clean_float(row[0]) if is_num(row[0]) else 0.0), [clean_float(v) for v in row[idx+1:] if is_num(v)]
        except StopIteration:
            nums = [clean_float(v) for v in row if is_num(v)]
            return (nums[0] if nums else 0.0), nums[1:]
    def extract_label(line):
        for tok in line:
            m = re.search(r'위치도\s*([A-Za-z0-9_]+)', str(tok))
            if m: return m.group(1)
        for tok in line:
            s = str(tok).strip()
            if re.fullmatch(r'[A-Za-z]{1,4}', s) and s.upper() not in ('X', 'Y'): return s.upper()
        return None

    i = 0
    pt_num = 1
    while i < len(lines) - 2:
        try:
            pos_line, mmc_line, next_line = lines[i], lines[i+1], lines[i+2]
            four_line = (i <= len(lines) - 4 and is_x_row(next_line) and is_y_row(lines[i+3]))
            three_line = (not four_line) and is_y_row(next_line)
            if not four_line and not three_line: i += 1; continue
            lbl = extract_label(pos_line) or f"P{pt_num}"
            pos_nums, mmc_nums = [clean_float(v) for v in pos_line if is_num(v)], [clean_float(v) for v in mmc_line if is_num(v)]
            if four_line:
                nom_x, ax_vals = extract_row(lines[i+2], 'X')
                nom_y, ay_vals = extract_row(lines[i+3], 'Y')
                step = 4
            else:
                nom_x, ax_vals = 0.0, [0.0] * len(extract_row(next_line, 'Y')[1])
                nom_y, ay_vals = extract_row(next_line, 'Y')
                step = 3
            pos_vals, mmc_vals = tail(pos_nums, sc), tail(mmc_nums, sc)
            ax_vals, ay_vals = tail(ax_vals, sc), tail(ay_vals, sc)
            n = min(sc, len(pos_vals), len(ay_vals))
            for s in range(n):
                pos_v = pos_vals[s] if s < len(pos_vals) else None
                raw_mmc = mmc_vals[s] if s < len(mmc_vals) else None
                mmc_v = raw_mmc if (raw_mmc is not None and raw_mmc > 0) else m_ref
                ax, ay = (ax_vals[s] if s < len(ax_vals) else nom_x), ay_vals[s]
                dx, dy = round(ax - nom_x, 4), round(ay - nom_y, 4)
                pos_res = round(pos_v, 4) if pos_v is not None else round(np.sqrt(dx**2 + dy**2) * 2, 4)
                bonus, limit = round(max(0.0, mmc_v - m_ref), 4), round(tol + round(max(0.0, mmc_v - m_ref), 4), 4)
                results.append({"ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y, "AX": ax, "AY": ay, "DIA": mmc_v, "POS": pos_res, "BONUS": bonus, "LIMIT": limit})
            pt_num += 1; i += step
        except Exception: i += 1
    return results

def draw_scatter_plot(df, tol):
    fig, ax = plt.subplots(figsize=(8, 8))
    dev_x, dev_y = df['DX'], df['DY']
    basic_r = tol / 2
    ax.add_patch(plt.Circle((0,0), basic_r, color='#3498db', fill=True, alpha=0.12, linestyle='--'))
    ax.add_patch(plt.Circle((0,0), basic_r, color='#3498db', fill=False, linestyle='--', linewidth=1.5, label=f'Basic Tol (O{tol:.3f})'))
    rep_limit = df['LIMIT'].median()
    mmc_r = rep_limit / 2
    if abs(mmc_r - basic_r) > 0.0001:
        ax.add_patch(plt.Circle((0,0), mmc_r, color='#e74c3c', fill=False, linewidth=2, label=f'Median MMC Tol (O{rep_limit:.3f})'))
    q99 = max(dev_x.abs().quantile(0.99), dev_y.abs().quantile(0.99)) if len(dev_x) > 0 else 0
    lim = max(max(basic_r, mmc_r), q99 if not np.isnan(q99) else 0) * 1.3
    outlier_mask = (dev_x.abs() > lim) | (dev_y.abs() > lim)
    normal_df, outlier_df = df[~outlier_mask], df[outlier_mask]
    ax.scatter(normal_df['DX'], normal_df['DY'], c=normal_df['RES'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c'), s=70, edgecolors='white', zorder=5, label='Measured Points')
    for _, row in outlier_df.iterrows():
        cx, cy = np.clip(row['DX'], -lim*0.85, lim*0.85), np.clip(row['DY'], -lim*0.85, lim*0.85)
        c = '#2ecc71' if 'OK' in row['RES'] else '#e74c3c'
        ax.annotate('', xy=(cx, cy), xytext=(cx * 0.6, cy * 0.6), arrowprops=dict(arrowstyle='->', color=c, lw=1.5))
        ax.text(cx, cy, row['ID'], fontsize=6, color=c, ha='center', va='bottom')
    if len(normal_df[normal_df['RES'].str.contains('NG')]) <= 20:
        for _, row in normal_df[normal_df['RES'].str.contains('NG')].iterrows():
            ax.annotate(row['ID'], (row['DX'], row['DY']), textcoords="offset points", xytext=(6, 6), fontsize=7, color='#c0392b', fontweight='bold')
    ax.axhline(0, color='black', linewidth=1.2); ax.axvline(0, color='black', linewidth=1.2)
    ax.set_xlabel("Deviation X (mm)"); ax.set_ylabel("Deviation Y (mm)")
    ax.set_title(f"Position Error Distribution", fontweight='bold'); ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_aspect('equal'); ax.legend(loc='upper right'); ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════
# 실행부 (메뉴 1, 2, 3)
# ══════════════════════════════════════════════════════════
def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")
    with st.sidebar:
        st.markdown("### 분석 설정")
        mode = st.radio("성적서 유형", ["유형 A (3줄: 포인트명/X/Y)", "유형 B (자동감지: 위치도/MMC/X?/Y)"])
        sc = st.number_input("시료 수 (Sample)", min_value=1, value=4)
        tol = st.number_input("기본 공차 (Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값 (지름)", value=0.350, format="%.3f")

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250, placeholder="헤더 줄 제외, 데이터 행만 붙여넣으세요.")
    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            if "A" in mode:
                res = parse_type_a(raw_input, sc)
                if not res: return st.error("데이터 파싱 실패")
                df = pd.DataFrame(res)
                df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
                df['POS'] = df.apply(lambda r: round(float(r['POS_RAW']), 4) if r['POS_RAW'] is not None else round(np.sqrt(r['DX']**2 + r['DY']**2) * 2, 4), axis=1)
                df['BONUS'], df['LIMIT'] = 0.0, tol
            else:
                res = parse_type_b(raw_input, sc, tol, m_ref)
                if not res: return st.error("데이터 파싱 실패")
                df = pd.DataFrame(res)
                df['DX'], df['DY'] = (df['AX'] - df['NX']).round(4), (df['AY'] - df['NY']).round(4)
            
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")
            st.pyplot(draw_scatter_plot(df, tol))
            
            c1, c2, c3 = st.columns(3)
            c1.metric("전체 샘플", f"{len(df)}개")
            c2.metric("합격률", f"{(df['RES'] == 'OK').sum() / len(df) * 100:.1f}%")
            c3.metric("평균 편차(X,Y)", f"{df['DX'].mean():.3f}, {df['DY'].mean():.3f}")

            st.dataframe(apply_style(df[['ID', 'DX', 'DY', 'POS', 'LIMIT', 'RES']].style, subset=['RES']), use_container_width=True)
        except Exception as e: st.error(f"오류: {e}")

def run_cavity_analysis():
    st.title("📈 핀 높이 멀티 캐비티 통합 분석")
    up = st.file_uploader("Excel / CSV 파일 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        for cav in cav_cols:
            df[f"{cav}_판정"] = df.apply(lambda r, c=cav: "OK" if r["SPEC_MIN"] <= r[c] <= r["SPEC_MAX"] else "NG", axis=1)
        st.subheader("통합 트렌드 분석")
        fig = go.Figure()
        for c in cav_cols: fig.add_trace(go.Scatter(x=df["Point"], y=df[c], mode='markers+lines', name=c))
        st.plotly_chart(fig, use_container_width=True)

def run_quality_calculator():
    st.title("🧮 품질 종합 계산기")
    tabs = st.tabs(["📏 MMC 공차 계산", "🔄 단위 변환"])
    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        base = c1.number_input("기본 공차", value=0.05)
        m_s = c2.number_input("MMC 규격", value=10.0)
        a_s = c3.number_input("실측 지름", value=10.02)
        st.metric("최종 허용 위치도", f"Ø{base + max(0.0, a_s - m_s):.4f}")

# ══════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════
def main():
    if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
    set_style()
    st.sidebar.title("QUALITY HUB v3.0")
    menu = st.sidebar.radio("분석 카테고리", ["🎯 위치도 정밀 분석", "📈 멀티 캐비티 분석", "🧮 품질 통합 계산기"], key=f"menu_{st.session_state.reset_key}")
    if st.sidebar.button("🗑️ 데이터 리셋"):
        st.session_state.reset_key += 1
        st.rerun()

    if menu == "🎯 위치도 정밀 분석": run_position_analysis()
    elif menu == "📈 멀티 캐비티 분석": run_cavity_analysis()
    elif menu == "🧮 품질 통합 계산기": run_quality_calculator()

if __name__ == "__main__":
    main()
