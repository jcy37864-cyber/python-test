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

# ── 글로벌 스타일 ───────────────────────────────────────────
def set_style():
    st.markdown("""
        <style>
        /* 사이드바 */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
        }

        /* 사이드바 기본 텍스트 */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stRadio > div,
        [data-testid="stSidebar"] .stNumberInput label {
            color: #f8fafc !important;
        }

        /* 🔥 입력창 (숫자, 텍스트) 글자색 강제 수정 */
        input, textarea {
            color: #111 !important;
            background-color: #ffffff !important;
        }

        /* 숫자 입력 내부 */
        .stNumberInput input {
            color: #111 !important;
            background-color: #ffffff !important;
        }

        /* 라벨 (시료 수, 공차 등) */
        label {
            color: #111 !important;
            font-weight: 600;
        }

        /* 버튼 */
        .stButton > button {
            background-color: #ef4444 !important;
            color: white !important;
            font-weight: bold !important;
            width: 100%;
            border-radius: 8px;
            height: 3em;
        }

        /* NG 박스 */
        .ng-box {
            height: 200px;
            overflow-y: auto;
            border: 2px solid #ff0000;
            padding: 15px;
            border-radius: 8px;
            background-color: #fff5f5;
        }

        /* OK 박스 */
        .ok-box {
            padding: 12px;
            border-radius: 8px;
            background-color: #e8f5e9;
            color: #2e7d32;
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
        }

        /* 리포트 카드 */
        .report-card {
            background-color: #f1f5f9;
            padding: 20px;
            border-left: 8px solid #3b82f6;
            border-radius: 8px;
            line-height: 2.0;
            font-size: 1.05em;
            color: #111;
        }
        </style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 공통 유틸
# ══════════════════════════════════════════════════════════
def clean_float(val):
    """숫자만 추출 -> float. 실패시 None 반환"""
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
# A유형 파서
# 3줄 세트:
#   줄1: 포인트명  위치도_S1 ... 위치도_SN
#   줄2: NomX     X_S1    ... X_SN
#   줄3: NomY     Y_S1    ... Y_SN
# ══════════════════════════════════════════════════════════
def parse_type_a(raw_input, sc):
    results = []
    lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l:
            continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l
                 else [p.strip() for p in re.split(r'\s{2,}', l) if p.strip()])
        if parts:
            lines.append(parts)

    i = 0
    pt_num = 1
    while i <= len(lines) - 3:
        try:
            pos_line, x_line, y_line = lines[i], lines[i+1], lines[i+2]
            first_tok = str(pos_line[0]) if pos_line else ''

            if not re.search(r'[A-Za-z가-힣]', first_tok):
                i += 1; continue
            if not is_num(x_line[0]) or not is_num(y_line[0]):
                i += 1; continue

            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', first_tok) or f"P{pt_num}"
            pos_nums = [clean_float(v) for v in pos_line[1:] if is_num(v)]
            x_nums   = [clean_float(v) for v in x_line if is_num(v)]
            y_nums   = [clean_float(v) for v in y_line if is_num(v)]

            if len(x_nums) < 2 or len(y_nums) < 2:
                i += 3; continue

            nom_x, nom_y = x_nums[0], y_nums[0]
            ax_vals, ay_vals = x_nums[1:], y_nums[1:]
            n = min(sc, len(ax_vals), len(ay_vals))
            if n == 0:
                i += 3; continue

            for s in range(n):
                si = len(ax_vals) - n + s
                ax, ay = ax_vals[si], ay_vals[si]
                if len(pos_nums) >= n:
                    pos_val = pos_nums[len(pos_nums) - n + s]
                elif pos_nums:
                    pos_val = pos_nums[min(s, len(pos_nums)-1)]
                else:
                    pos_val = None

                results.append({
                    "ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y,
                    "AX": ax, "AY": ay, "POS_RAW": pos_val,
                })
            pt_num += 1
            i += 3
        except Exception:
            i += 1
    return results

# ══════════════════════════════════════════════════════════
# B유형 파서 -- 3줄/4줄 자동 감지 (혼재 가능)
# [4줄] 줄1:위치도, 줄2:MMC, 줄3:X행, 줄4:Y행
# [3줄] 줄1:위치도, 줄2:MMC, 줄3:Y행(Nominal+Y혼합 or 'Y'시작)
# ══════════════════════════════════════════════════════════
def parse_type_b(raw_input, sc, tol, m_ref):
    results = []
    lines = []
    for l in raw_input.strip().split('\n'):
        l = l.strip()
        if not l:
            continue
        parts = ([p.strip() for p in l.split('\t') if p.strip()] if '\t' in l
                 else [p.strip() for p in re.split(r'\s{2,}|\t', l) if p.strip()])
        if parts:
            lines.append(parts)

    def tail(lst, n):
        lst = [v for v in lst if v is not None]
        return lst[-n:] if len(lst) >= n else lst

    def ft(row):
        return str(row[0]).strip().upper() if row else ''

    def is_y_row(row):
        if not row: return False
        if ft(row) == 'Y': return True
        return is_num(row[0]) and any(str(t).strip().upper() == 'Y' for t in row)

    def is_x_row(row):
        return ft(row) == 'X'

    def extract_row(row, label):
        if ft(row) == label:
            return 0.0, [clean_float(v) for v in row[1:] if is_num(v)]
        try:
            label_idx = next(j for j, t in enumerate(row)
                             if str(t).strip().upper() == label)
            nom = clean_float(row[0]) if is_num(row[0]) else 0.0
            return nom, [clean_float(v) for v in row[label_idx+1:] if is_num(v)]
        except StopIteration:
            nums = [clean_float(v) for v in row if is_num(v)]
            return (nums[0] if nums else 0.0), nums[1:]

    def extract_label(pos_line):
        for tok in pos_line:
            m = re.search(r'위치도\s*([A-Za-z0-9_]+)', str(tok))
            if m: return m.group(1)
        for tok in pos_line:
            s = str(tok).strip()
            if re.fullmatch(r'[A-Za-z]{1,4}', s) and s.upper() not in ('X', 'Y'):
                return s.upper()
        return None

    i = 0
    pt_num = 1
    while i < len(lines):
        if i > len(lines) - 3:
            break
        try:
            pos_line  = lines[i]
            mmc_line  = lines[i+1]
            next_line = lines[i+2]

            four_line  = (i <= len(lines) - 4
                          and is_x_row(next_line)
                          and is_y_row(lines[i+3]))
            three_line = (not four_line) and is_y_row(next_line)

            if not four_line and not three_line:
                i += 1; continue

            lbl      = extract_label(pos_line) or f"P{pt_num}"
            pos_nums = [clean_float(v) for v in pos_line if is_num(v)]
            mmc_nums = [clean_float(v) for v in mmc_line if is_num(v)]

            if four_line:
                nom_x, ax_vals = extract_row(lines[i+2], 'X')
                nom_y, ay_vals = extract_row(lines[i+3], 'Y')
                step = 4
            else:
                nom_x = 0.0
                nom_y, ay_vals = extract_row(next_line, 'Y')
                ax_vals = [0.0] * len(ay_vals)
                step = 3

            pos_vals = tail(pos_nums, sc)
            mmc_vals = tail(mmc_nums, sc)
            ax_vals  = tail(ax_vals,  sc)
            ay_vals  = tail(ay_vals,  sc)
            n = min(sc, len(pos_vals), len(ay_vals))
            if n == 0:
                i += step; continue

            for s in range(n):
                pos_v   = pos_vals[s] if s < len(pos_vals) else None
                raw_mmc = mmc_vals[s] if s < len(mmc_vals) else None
                mmc_v   = raw_mmc if (raw_mmc is not None and raw_mmc > 0) else m_ref
                ax      = ax_vals[s] if s < len(ax_vals) else nom_x
                ay      = ay_vals[s]
                dx      = round(ax - nom_x, 4)
                dy      = round(ay - nom_y, 4)
                pos_result = (round(pos_v, 4) if pos_v is not None
                              else round(np.sqrt(dx**2 + dy**2) * 2, 4))
                bonus  = round(max(0.0, mmc_v - m_ref), 4)
                limit  = round(tol + bonus, 4)
                results.append({
                    "ID": f"{lbl}_S{s+1}", "NX": nom_x, "NY": nom_y,
                    "AX": ax, "AY": ay, "DIA": mmc_v,
                    "POS": pos_result, "BONUS": bonus, "LIMIT": limit,
                })
            pt_num += 1
            i += step
        except Exception:
            i += 1
    return results

# ══════════════════════════════════════════════════════════
# 산포도 (A/B 공통 2D)
# - 이상치 튀는 점 때문에 원이 작아보이는 문제:
#   99퍼센타일 기준으로 축 범위 클리핑, 이상치는 화살표로 표시
# ══════════════════════════════════════════════════════════
def draw_scatter_plot(df, tol):
    fig, ax = plt.subplots(figsize=(8, 8))
    dev_x = df['DX']
    dev_y = df['DY']

    basic_r = tol / 2
    ax.add_patch(plt.Circle((0,0), basic_r, color='#3498db',
                             fill=True, alpha=0.12, linestyle='--'))
    ax.add_patch(plt.Circle((0,0), basic_r, color='#3498db',
                             fill=False, linestyle='--', linewidth=1.5,
                             label=f'Basic Tol (O{tol:.3f})'))

    rep_limit = df['LIMIT'].median()
    mmc_r = rep_limit / 2
    if abs(mmc_r - basic_r) > 0.0001:
        ax.add_patch(plt.Circle((0,0), mmc_r, color='#e74c3c',
                                 fill=False, linewidth=2,
                                 label=f'Median MMC Tol (O{rep_limit:.3f})'))

    # 축 범위: 99퍼센타일 기준 (이상치 튐 방지)
    if len(dev_x) > 0:
        q99 = max(dev_x.abs().quantile(0.99), dev_y.abs().quantile(0.99))
        data_r = q99 if not np.isnan(q99) else 0
    else:
        data_r = 0
    tol_r = max(basic_r, mmc_r)
    lim = max(tol_r, data_r) * 1.3

    # 이상치(범위 밖): 화살표로 방향만 표시
    outlier_mask = (dev_x.abs() > lim) | (dev_y.abs() > lim)
    normal_df    = df[~outlier_mask]
    outlier_df   = df[outlier_mask]

    colors_n = normal_df['RES'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
    ax.scatter(normal_df['DX'], normal_df['DY'],
               c=colors_n, s=70, edgecolors='white', zorder=5,
               label='Measured Points')

    for _, row in outlier_df.iterrows():
        cx = np.clip(row['DX'], -lim*0.85, lim*0.85)
        cy = np.clip(row['DY'], -lim*0.85, lim*0.85)
        c  = '#2ecc71' if 'OK' in row['RES'] else '#e74c3c'
        ax.annotate('', xy=(cx, cy),
                    xytext=(cx * 0.6, cy * 0.6),
                    arrowprops=dict(arrowstyle='->', color=c, lw=1.5))
        ax.text(cx, cy, row['ID'], fontsize=6, color=c, ha='center', va='bottom')

    # NG 라벨 (점 수 20개 이하만)
    ng_normal = normal_df[normal_df['RES'].str.contains('NG')]
    if len(ng_normal) <= 20:
        for _, row in ng_normal.iterrows():
            ax.annotate(row['ID'], (row['DX'], row['DY']),
                        textcoords="offset points", xytext=(6, 6),
                        fontsize=7, color='#c0392b', fontweight='bold')

    ax.axhline(0, color='black', linewidth=1.2)
    ax.axvline(0, color='black', linewidth=1.2)
    ax.set_xlabel("Deviation X (mm)", fontsize=12)
    ax.set_ylabel("Deviation Y (mm)", fontsize=12)
    ax.set_title(f"Position Error Distribution  Basic Tol O{tol:.3f} vs MMC",
                 fontsize=13, fontweight='bold', pad=20)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_aspect('equal')
    ax.legend(loc='upper right', frameon=True, shadow=True)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    if not outlier_df.empty:
        ax.text(0.02, 0.02,
                f"* 범위 밖 {len(outlier_df)}개 → 화살표로 표시",
                transform=ax.transAxes, fontsize=8, color='gray',
                va='bottom')

    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════
# 메뉴 1: 위치도 정밀 분석
# ══════════════════════════════════════════════════════════
def run_position_analysis():
    st.title("🎯 위치도 정밀 분석 시스템")
    st.caption("성적서 데이터를 붙여넣고 MMC 기반 위치도 합불 판정 및 산포도를 생성합니다.")

    with st.sidebar:
        st.markdown("### 분석 설정")
        mode  = st.radio("성적서 유형",
                         ["유형 A (3줄: 포인트명/X/Y)",
                          "유형 B (자동감지: 위치도/MMC/X?/Y)"])
        sc    = st.number_input("시료 수 (Sample)", min_value=1, value=4)
        tol   = st.number_input("기본 공차 (Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값 (지름)", value=0.350, format="%.3f")
        st.markdown("---")
        if "A" in mode:
            st.caption("""
**A유형 — 3줄 세트**
```
줄1: 포인트명  위치도S1 ...
줄2: NomX  X_S1  X_S2 ...
줄3: NomY  Y_S1  Y_S2 ...
```
헤더 제외 후 포인트명 줄부터 복사
            """)
        else:
            st.caption("""
**B유형 — 3줄/4줄 자동감지 (혼재 OK)**
```
[4줄: X+Y 둘 다]
줄1: Ø공차  위치도명  위치도S1...
줄2: Max  MMC허용공차  MMCS1...
줄3: X  X_S1 X_S2...
줄4: Y  Y_S1 Y_S2...

[3줄: Y만]
줄1: Ø공차  Ref  위치도S1...
줄2: Max  MMC허용공차  MMCS1...
줄3: NomY  Y  Y_S1 Y_S2...
```
헤더 제외 후 데이터 행만 복사
            """)

    raw_input = st.text_area(
        "성적서 데이터를 붙여넣으세요",
        height=280,
        placeholder="헤더 줄 제외, 데이터 행만 붙여넣으세요."
    )

    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            if "A" in mode:
                results = parse_type_a(raw_input, sc)
                if not results:
                    st.error("데이터를 읽지 못했습니다. 유형/시료수를 확인하세요.")
                    return
                df = pd.DataFrame(results)
                df['DX']    = (df['AX'] - df['NX']).round(4)
                df['DY']    = (df['AY'] - df['NY']).round(4)
                df['POS']   = df.apply(
                    lambda r: round(float(r['POS_RAW']), 4)
                              if r['POS_RAW'] is not None
                              else round(np.sqrt(r['DX']**2 + r['DY']**2) * 2, 4),
                    axis=1)
                df['BONUS'] = 0.0
                df['LIMIT'] = tol
                df['RES']   = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")

            else:
                results = parse_type_b(raw_input, sc, tol, m_ref)
                if not results:
                    st.error("데이터를 읽지 못했습니다. 유형/시료수를 확인하세요.")
                    return
                df = pd.DataFrame(results)
                df['DX']  = (df['AX'] - df['NX']).round(4)
                df['DY']  = (df['AY'] - df['NY']).round(4)
                df['RES'] = np.where(df['POS'] <= df['LIMIT'], "OK", "NG")

            with st.expander("🔍 파싱 원본 확인 (이상할 때 클릭)"):
                st.dataframe(df, use_container_width=True)

            # 산포도
            st.divider()
            st.subheader("🎯 위치도 산포도")
            fig = draw_scatter_plot(df, tol)
            st.pyplot(fig)

            # 통계
            st.divider()
            total  = len(df)
            ok_n   = (df['RES'] == 'OK').sum()
            ng_n   = total - ok_n
            ok_r   = ok_n / total * 100
            avg_dx = df['DX'].mean()
            avg_dy = df['DY'].mean()

            c1, c2, c3 = st.columns(3)
            c1.metric("전체 샘플 수", f"{total}개")
            c2.metric("합격률", f"{ok_r:.1f}%",
                      delta=f"-{ng_n} NG" if ng_n > 0 else "All Pass",
                      delta_color="inverse")
            c3.metric("평균 편차 (X, Y)", f"{avg_dx:.3f}, {avg_dy:.3f}")

            dir_x = "오른쪽(+)" if avg_dx > 0 else "왼쪽(-)"
            dir_y = "위쪽(+)"   if avg_dy > 0 else "아래쪽(-)"
            st.markdown(f"""<div class="report-card">
            <b>종합 판정:</b> 합격률 <b>{ok_r:.1f}%</b><br>
            <b>경향성:</b> <b>{dir_x}</b> {abs(avg_dx):.3f}mm &nbsp;
                          <b>{dir_y}</b> {abs(avg_dy):.3f}mm 편향<br>
            <b>조치 권고:</b>
            한 방향 편향 → 원점 Offset 보정 검토 /
            특정 샘플만 이탈 → 지그·이물질 확인
            </div>""", unsafe_allow_html=True)

            # 결과 테이블
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                show_cols = ['ID', 'DX', 'DY', 'POS', 'LIMIT', 'RES']
                disp = df[[c for c in show_cols if c in df.columns]].copy()
                disp.columns = ['ID', 'X편차', 'Y편차', '위치도(Ø)', '규격(Ø)', '판정']
                st.dataframe(apply_style(disp.style, subset=['판정']),
                             use_container_width=True)
            with col2:
                ng_df = df[df['RES'] == 'NG']
                if not ng_df.empty:
                    rows_html = "".join(
                        f"• {r['ID']}: {r['POS']:.3f} (규격 {r['LIMIT']:.3f})<br>"
                        for _, r in ng_df.iterrows())
                    st.markdown(
                        f"<div class='ng-box'>🚩 <b>NG {len(ng_df)}건</b><br>{rows_html}</div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>ALL PASS</div>",
                                unsafe_allow_html=True)

            # 다운로드
            st.divider()
            d1, d2 = st.columns(2)
            with d1:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df.to_excel(w, index=False, sheet_name='Analysis')
                st.download_button("📂 Excel 다운로드", buf.getvalue(),
                                   "Position_Report.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)
            with d2:
                ibuf = BytesIO()
                fig.savefig(ibuf, format="png", bbox_inches='tight', dpi=300)
                st.download_button("🖼️ 그래프 저장", ibuf.getvalue(),
                                   "Scatter_Plot.png", "image/png",
                                   use_container_width=True)

            st.success(f"완료: {total}개 중 {ok_n}개 합격 / {ng_n}개 불합격")

        except Exception as e:
            st.error(f"오류 발생: {e}")
            import traceback
            st.code(traceback.format_exc())

# ══════════════════════════════════════════════════════════
# 메뉴 2: 멀티 캐비티 분석
# ══════════════════════════════════════════════════════════
def run_cavity_analysis():
    st.title("📈 핀 높이 멀티 캐비티 통합 분석")
    st.caption("여러 캐비티의 측정 데이터를 업로드하여 트렌드와 합불을 분석합니다.")

    def get_template():
        df_t = pd.DataFrame({
            "Point":    range(1, 6),
            "SPEC_MIN": [30.1] * 5,
            "SPEC_MAX": [30.5] * 5,
            "Cavity_1": [30.2] * 5,
            "Cavity_2": [30.3] * 5,
            "Cavity_3": [30.2] * 5,
            "Cavity_4": [30.4] * 5,
        })
        out = BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            df_t.to_excel(w, index=False)
        return out.getvalue()

    st.download_button("📄 분석용 템플릿 다운로드", get_template(),
                       "Multi_Cavity_Template.xlsx")
    up = st.file_uploader("Excel / CSV 파일 업로드", type=["xlsx", "csv"])
    if not up:
        return

    df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
    cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
    if not cav_cols:
        st.error("'Cavity_N' 형식의 열이 없습니다.")
        return

    cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                  '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']

    for cav in cav_cols:
        df[f"{cav}_판정"] = df.apply(
            lambda r, c=cav: "OK" if r["SPEC_MIN"] <= r[c] <= r["SPEC_MAX"] else "NG", axis=1)

    st.subheader("캐비티별 측정값 분포")
    all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
    y_min = np.nanmin(all_vals) - 0.05
    y_max = np.nanmax(all_vals) + 0.05

    c_grid = st.columns(min(len(cav_cols), 2))
    summary_items = []
    for i, cav in enumerate(cav_cols):
        color = cav_colors[i % len(cav_colors)]
        ng_count = (df[f"{cav}_판정"] == "NG").sum()
        ok_rate  = (len(df) - ng_count) / len(df) * 100
        summary_items.append(f"<b>{cav}</b>: 합격률 <b>{ok_rate:.1f}%</b>  (NG {ng_count}건)")

        with c_grid[i % 2]:
            fig_c = go.Figure()
            fig_c.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"],
                                       line=dict(color="blue", dash="dash"), name="MIN"))
            fig_c.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"],
                                       line=dict(color="red", dash="dash"), name="MAX"))
            fig_c.add_trace(go.Bar(x=df["Point"], y=df[cav],
                                   marker_color=color, name="실측"))
            fig_c.update_layout(
                title=dict(text=cav, font=dict(color=color)),
                height=300, yaxis_range=[y_min, y_max],
                margin=dict(t=40, b=20))
            st.plotly_chart(fig_c, use_container_width=True)

    st.divider()
    st.subheader("통합 트렌드 분석")
    df['Avg'] = df[cav_cols].mean(axis=1)
    fig_all = go.Figure()
    fig_all.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"],
                                 name="MIN", line=dict(color="blue", dash="dot")))
    fig_all.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"],
                                 name="MAX", line=dict(color="red", dash="dot")))
    for i, cav in enumerate(cav_cols):
        fig_all.add_trace(go.Scatter(
            x=df["Point"], y=df[cav], mode='markers', name=cav,
            marker=dict(color=cav_colors[i % len(cav_colors)], size=10)))
    fig_all.add_trace(go.Scatter(x=df["Point"], y=df['Avg'],
                                 name="전체평균", line=dict(color="black", width=3)))
    fig_all.update_layout(height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig_all, use_container_width=True)
    st.caption("📸 그래프 우측 상단 카메라 아이콘 클릭 시 이미지 저장")

    st.markdown(
        '<div class="report-card">' + "<br>".join(summary_items) + "</div>",
        unsafe_allow_html=True)

    out_buf = BytesIO()
    with pd.ExcelWriter(out_buf, engine='openpyxl') as w:
        df.to_excel(w, index=False)
    st.download_button("📥 분석 결과 Excel 저장", out_buf.getvalue(), "Cavity_Result.xlsx")

# ══════════════════════════════════════════════════════════
# 메뉴 3: 품질 계산기
# ══════════════════════════════════════════════════════════
def run_quality_calculator():
    st.title("🧮 품질 종합 계산기")
    tabs = st.tabs(["📏 MMC 공차 계산", "🔄 단위 변환", "🔧 토크 변환", "합불 판정"])

    with tabs[0]:
        st.subheader("MMC 기하공차 계산")
        c1, c2, c3 = st.columns(3)
        base_g = c1.number_input("기본 기하공차", value=0.05, format="%.4f")
        mmc_s  = c2.number_input("MMC 규격 지름", value=10.000, format="%.3f")
        act_s  = c3.number_input("실측 지름",     value=10.020, format="%.3f")
        bonus  = max(0.0, act_s - mmc_s)
        final  = base_g + bonus
        r1, r2, r3 = st.columns(3)
        r1.metric("보너스 공차",   f"Ø{bonus:.4f}")
        r2.metric("최종 허용 공차", f"Ø{final:.4f}")
        r3.metric("판정 기준",     f"위치도 ≤ Ø{final:.4f}")

    with tabs[1]:
        st.subheader("mm / inch 변환")
        v = st.number_input("값 입력", value=1.0, format="%.4f")
        m = st.selectbox("변환 방향", ["mm → inch", "inch → mm"])
        result = v / 25.4 if "inch" in m else v * 25.4
        unit   = "inch" if "inch" in m else "mm"
        st.success(f"결과: **{result:.4f} {unit}**")

    with tabs[2]:
        st.subheader("토크 단위 변환")
        t_v = st.number_input("토크 값", value=1.0, format="%.3f")
        t_m = st.selectbox("변환 방향", ["N·m → kgf·cm", "kgf·cm → N·m"])
        t_r = t_v * 10.197 if "kgf" in t_m.split("→")[1] else t_v / 10.197
        t_u = "kgf·cm" if "kgf" in t_m.split("→")[1] else "N·m"
        st.success(f"결과: **{t_r:.3f} {t_u}**")

    with tabs[3]:
        st.subheader("합격/불합격 판정")
        c1, c2, c3, c4 = st.columns(4)
        spec = c1.number_input("기준값 (Spec)", value=0.0, format="%.3f")
        u    = c2.number_input("상한 공차 (+)", value=0.1,  format="%.3f")
        l    = c3.number_input("하한 공차 (-)", value=-0.1, format="%.3f")
        m_v  = c4.number_input("실제 측정값",  value=0.0,  format="%.3f")
        lo, hi = spec + l, spec + u
        if lo <= m_v <= hi:
            st.success(f"**{m_v:.3f}** → ✅ 합격  (허용 범위: {lo:.3f} ~ {hi:.3f})")
        else:
            st.error(f"**{m_v:.3f}** → ❌ 불합격  (허용 범위: {lo:.3f} ~ {hi:.3f})")

# ══════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════
def main():
    if 'reset_key' not in st.session_state:
        st.session_state.reset_key = 0

    set_style()

    st.sidebar.title("QUALITY HUB v3.0")
    menu = st.sidebar.radio(
        "분석 카테고리",
        ["🎯 위치도 정밀 분석", "📈 멀티 캐비티 분석", "🧮 품질 통합 계산기"],
        key=f"menu_{st.session_state.reset_key}"
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ 데이터 리셋"):
        st.session_state.reset_key += 1
        st.rerun()

    if menu == "🎯 위치도 정밀 분석":
        run_position_analysis()
    elif menu == "📈 멀티 캐비티 분석":
        run_cavity_analysis()
    elif menu == "🧮 품질 통합 계산기":
        run_quality_calculator()

if __name__ == "__main__":
    main()
