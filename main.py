import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import re
from io import BytesIO

st.set_page_config(page_title="Quality Hub Pro v2.10", layout="wide")

# ─────────────────────────────────────────────────
# 한글 폰트 설정 (그래프 한글 깨짐 방지)
# ─────────────────────────────────────────────────
def set_korean_font():
    try:
        # Noto Sans CJK KR 우선 사용
        font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        fm.fontManager.addfont(font_path)
        plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        try:
            plt.rcParams['font.family'] = 'Noto Sans CJK KR'
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass

set_korean_font()

def set_style():
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%; border-radius: 8px; font-weight: bold;
            height: 3.5em; background-color: #D32F2F; color: white;
        }
        .ng-box {
            height: 180px; overflow-y: auto; border: 2px solid #ff0000;
            padding: 15px; border-radius: 8px; background-color: #fff5f5;
        }
        .ok-box {
            padding: 10px; border-radius: 8px; background-color: #e8f5e9;
            color: #2e7d32; font-weight: bold; text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

def clean_float(val):
    """숫자만 추출 → float. 실패시 None"""
    try:
        v = re.sub(r'[^0-9.\-]', '', str(val))
        # 음수 부호가 맨 앞에 있는 경우만 허용
        if v.count('-') > 1:
            v = '-' + v.replace('-', '')
        return float(v) if v and v not in ('-', '.', '-.') else None
    except Exception:
        return None

def is_num(val):
    return clean_float(val) is not None

# ═══════════════════════════════════════════════════════
# A유형 파서
# ─────────────────────────────────────────────────────
# 3줄 세트 구조 (이미지 1 확인):
#   줄1: 포인트명(A,B,C..)  위치도_S1  위치도_S2  위치도_S3  위치도_S4
#   줄2: Nominal_X          X_S1       X_S2       X_S3       X_S4
#   줄3: Nominal_Y          Y_S1       Y_S2       Y_S3       Y_S4
# ═══════════════════════════════════════════════════════
def parse_type_a(raw_input, sc):
    results = []

    raw_lines = raw_input.strip().split('\n')
    lines = []
    for l in raw_lines:
        l = l.strip()
        if not l:
            continue
        # 탭 우선, 없으면 2칸 이상 공백
        if '\t' in l:
            parts = [p.strip() for p in l.split('\t') if p.strip()]
        else:
            parts = [p.strip() for p in re.split(r'\s{2,}', l) if p.strip()]
        if parts:
            lines.append(parts)

    i = 0
    pt_num = 1
    while i <= len(lines) - 3:
        try:
            pos_line = lines[i]    # 포인트명 + 위치도값
            x_line   = lines[i+1] # Nominal_X + 샘플X
            y_line   = lines[i+2] # Nominal_Y + 샘플Y

            # ── 포인트명 줄 검증: 첫 토큰이 문자(알파벳/한글) 포함해야 함
            first_tok = str(pos_line[0]) if pos_line else ''
            if not re.search(r'[A-Za-z가-힣]', first_tok):
                i += 1
                continue

            # ── X/Y 줄 검증: 첫 토큰이 숫자여야 함
            if not is_num(x_line[0]) or not is_num(y_line[0]):
                i += 1
                continue

            # 포인트명
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', first_tok) or f"P{pt_num}"

            # 위치도값 (pos_line 숫자 부분)
            pos_nums = [clean_float(v) for v in pos_line[1:] if is_num(v)]

            # X/Y Nominal + 실측값
            x_nums = [clean_float(v) for v in x_line if is_num(v)]
            y_nums = [clean_float(v) for v in y_line if is_num(v)]

            if len(x_nums) < 2 or len(y_nums) < 2:
                i += 3
                continue

            nom_x  = x_nums[0]
            nom_y  = y_nums[0]
            ax_vals = x_nums[1:]
            ay_vals = y_nums[1:]

            # 뒤에서 sc개 추출
            n = min(sc, len(ax_vals), len(ay_vals))
            if n == 0:
                i += 3
                continue

            for s in range(n):
                si  = len(ax_vals) - n + s
                ax  = ax_vals[si]
                ay  = ay_vals[si]

                # 위치도: pos_nums 뒤에서 n개 중 s번째
                if len(pos_nums) >= n:
                    pos_val = pos_nums[len(pos_nums) - n + s]
                elif pos_nums:
                    pos_val = pos_nums[min(s, len(pos_nums)-1)]
                else:
                    pos_val = None

                results.append({
                    "ID":      f"{lbl}_S{s+1}",
                    "NX":      nom_x,
                    "NY":      nom_y,
                    "AX":      ax,
                    "AY":      ay,
                    "POS_RAW": pos_val,
                })

            pt_num += 1
            i += 3

        except Exception:
            i += 1
            continue

    return results

# ═══════════════════════════════════════════════════════
# B유형 파서
# ─────────────────────────────────────────────────────
# 3줄 세트 구조 (이미지 2 확인):
#   줄1: Ø0.35ⓜ  0.00  0.35  Ref번호   위치도_S1  위치도_S2  위치도_S3  위치도_S4
#   줄2: Max0.41  0           MMC공차   MMC_S1     MMC_S2     MMC_S3     MMC_S4
#   줄3: Nominal  -100  100   Y         Y_S1       Y_S2       Y_S3       Y_S4
# ═══════════════════════════════════════════════════════
def parse_type_b(raw_input, sc, tol, m_ref):
    results = []

    raw_lines = raw_input.strip().split('\n')
    lines = []
    for l in raw_lines:
        l = l.strip()
        if not l:
            continue
        if '\t' in l:
            parts = [p.strip() for p in l.split('\t') if p.strip()]
        else:
            parts = [p.strip() for p in re.split(r'\s{2,}|\t', l) if p.strip()]
        if parts:
            lines.append(parts)

    i = 0
    pt_num = 1
    while i <= len(lines) - 3:
        try:
            pos_line = lines[i]    # 위치도값 줄 (Ø0.35ⓜ 포함)
            mmc_line = lines[i+1]  # MMC공차 줄
            y_line   = lines[i+2]  # Y좌표 줄

            # ── 줄1 검증: 'Ø' 또는 공차 관련 문자 포함하거나 첫 숫자가 0~1 범위
            # ── 줄3 검증: Nominal(숫자)이 첫 토큰
            if not is_num(y_line[0]):
                i += 1
                continue

            # Nominal Y
            nom_y = clean_float(y_line[0]) or 0.0
            # Nominal X = 0 (B유형은 Y방향 1D 측정)
            nom_x = 0.0

            # 포인트 Ref 번호 (pos_line에서 정수처럼 보이는 것)
            ref_candidates = [v for v in pos_line if re.fullmatch(r'\d+', str(v))]
            lbl = f"P{ref_candidates[0]}" if ref_candidates else f"P{pt_num}"

            # 위치도값: pos_line 뒤에서 sc개 숫자
            pos_nums = [clean_float(v) for v in pos_line if is_num(v)]
            # MMC 실측지름: mmc_line 뒤에서 sc개
            mmc_nums = [clean_float(v) for v in mmc_line if is_num(v) and clean_float(v) != 0.0]
            # Y 실측값: y_line 뒤에서 sc개
            y_nums_all = [clean_float(v) for v in y_line if is_num(v)]

            # 각 줄에서 뒤쪽 sc개 추출
            def tail(lst, n):
                lst = [v for v in lst if v is not None]
                if len(lst) >= n:
                    return lst[-n:]
                return lst

            pos_vals = tail(pos_nums, sc)
            mmc_vals = tail(mmc_nums, sc)
            y_vals   = tail(y_nums_all, sc)

            n = min(sc, len(pos_vals), len(y_vals))
            if n == 0:
                i += 3
                continue

            for s in range(n):
                pos_v = pos_vals[s] if s < len(pos_vals) else None
                mmc_v = mmc_vals[s] if s < len(mmc_vals) else m_ref
                ay    = y_vals[s]

                # 편차: Y방향만 있으므로 DX=0, DY=ay-nom_y
                dx = 0.0
                dy = round(ay - nom_y, 4)

                # 위치도: 성적서값 우선
                if pos_v is not None:
                    pos_result = round(pos_v, 4)
                else:
                    pos_result = round(abs(dy) * 2, 4)

                # MMC 보너스공차
                bonus = round(max(0.0, (mmc_v or m_ref) - m_ref), 4)
                limit = round(tol + bonus, 4)

                results.append({
                    "ID":    f"{lbl}_S{s+1}",
                    "NX":    nom_x,
                    "NY":    nom_y,
                    "AX":    nom_x,   # X는 없으므로 Nominal 그대로
                    "AY":    ay,
                    "DIA":   mmc_v or m_ref,
                    "POS":   pos_result,
                    "BONUS": bonus,
                    "LIMIT": limit,
                })

            pt_num += 1
            i += 3

        except Exception:
            i += 1
            continue

    return results

# ─────────────────────────────────────────────────
# 기본툴과 동일한 matplotlib 산포도
# ─────────────────────────────────────────────────
def draw_scatter_plot(df, tol):
    fig, ax = plt.subplots(figsize=(8, 8))

    dev_x = df['DX']
    dev_y = df['DY']

    # 🔵 Basic Tolerance 원
    basic_r = tol / 2
    ax.add_patch(plt.Circle((0, 0), basic_r,
                             color='#3498db', fill=True, alpha=0.12, linestyle='--'))
    ax.add_patch(plt.Circle((0, 0), basic_r,
                             color='#3498db', fill=False, linestyle='--', linewidth=1.5,
                             label=f'Basic Tol (O{tol:.3f})'))

    # 🔴 MMC 공차 원 (median)
    rep_limit = df['LIMIT'].median()
    mmc_r = rep_limit / 2
    ax.add_patch(plt.Circle((0, 0), mmc_r,
                             color='#e74c3c', fill=False, linewidth=2,
                             label=f'Median MMC Tol (O{rep_limit:.3f})'))

    # 측정 포인트
    colors = df['RES'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
    ax.scatter(dev_x, dev_y, c=colors, s=60, edgecolors='white', zorder=5,
               label='Measured Points')

    # NG 라벨
    for _, row in df[df['RES'] == "❌ NG"].iterrows():
        ax.annotate(row['ID'], (row['DX'], row['DY']),
                    textcoords="offset points", xytext=(6, 6),
                    fontsize=8, color='#c0392b', fontweight='bold')

    ax.axhline(0, color='black', linewidth=1.2)
    ax.axvline(0, color='black', linewidth=1.2)
    ax.set_xlabel("Deviation X", fontsize=12)
    ax.set_ylabel("Deviation Y", fontsize=12)

    # 제목 한글 제거 → 영문만 사용 (깨짐 방지)
    ax.set_title(f"Position Error Distribution\nBasic Tol O{tol:.3f} vs MMC Extension",
                 fontsize=13, fontweight='bold', pad=20)

    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_aspect('equal')
    ax.legend(loc='upper right', frameon=True, shadow=True)

    # 축 범위 자동
    tol_r  = max(basic_r, mmc_r)
    data_r = max(dev_x.abs().max(), dev_y.abs().max()) if len(dev_x) > 0 else tol_r
    lim    = max(tol_r, data_r) * 1.2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    return fig

# ─────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────
def run_analysis():
    set_style()
    st.title("🎯 품질 측정 위치도 분석 리포트")

    with st.sidebar:
        st.header("📋 보고서 설정")
        mode  = st.radio("성적서 유형", ["유형 B (3줄: 위치도/MMC/Y)", "유형 A (3줄: 포인트명/X/Y)"])
        sc    = st.number_input("시료 수(Sample)", min_value=1, value=4)
        tol   = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값(지름)", value=0.350, format="%.3f")

        st.markdown("---")
        if "A" in mode:
            st.caption("""
**A유형 — 3줄 세트**
```
줄1: 포인트명  위치도S1 위치도S2 ...
줄2: NomX  X_S1  X_S2 ...
줄3: NomY  Y_S1  Y_S2 ...
```
헤더(SPEC/측정구간 줄) 제외 후
포인트명 줄부터 끝까지 복사
            """)
        else:
            st.caption("""
**B유형 — 3줄 세트**
```
줄1: Ø0.35  ...  위치도S1 위치도S2 ...
줄2: Max0.41 ...  MMCS1  MMCS2 ...
줄3: NomY  ...  Y_S1  Y_S2 ...
```
헤더(Nominal/DIM±Tolerance 줄) 제외 후
데이터 행만 복사
            """)

    raw_input = st.text_area(
        "성적서 데이터를 붙여넣으세요",
        height=280,
        placeholder="헤더 줄 제외, 데이터 행만 붙여넣으세요."
    )

    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            # ── 파싱 ─────────────────────────────────────────
            if "A" in mode:
                results = parse_type_a(raw_input, sc)
                if not results:
                    st.error("❌ 데이터를 읽지 못했습니다. 유형/시료수를 확인하세요.")
                    return

                df = pd.DataFrame(results)
                df['DX']    = (df['AX'] - df['NX']).round(4)
                df['DY']    = (df['AY'] - df['NY']).round(4)
                # 위치도: 성적서값 우선, 없으면 직접 계산
                df['POS']   = df.apply(
                    lambda r: round(float(r['POS_RAW']), 4)
                              if r['POS_RAW'] is not None
                              else round(np.sqrt(r['DX']**2 + r['DY']**2) * 2, 4),
                    axis=1
                )
                df['BONUS'] = 0.0
                df['LIMIT'] = tol
                df['RES']   = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            else:  # B유형
                results = parse_type_b(raw_input, sc, tol, m_ref)
                if not results:
                    st.error("❌ 데이터를 읽지 못했습니다. 유형/시료수를 확인하세요.")
                    return

                df = pd.DataFrame(results)
                df['DX']  = 0.0
                df['DY']  = (df['AY'] - df['NY']).round(4)
                df['RES'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # ── 파싱 확인용 ───────────────────────────────────
            with st.expander("🔍 파싱 원본 확인 (이상할 때 클릭)"):
                st.dataframe(df, use_container_width=True)

            # ── 산포도 ────────────────────────────────────────
            st.divider()
            st.subheader("🎯 위치도 산포도")
            fig = draw_scatter_plot(df, tol)
            st.pyplot(fig)

            # ── 통계 요약 ─────────────────────────────────────
            st.divider()
            total = len(df)
            ok_n  = (df['RES'].str.contains('OK')).sum()
            ng_n  = total - ok_n
            ok_r  = ok_n / total * 100

            c1, c2, c3 = st.columns(3)
            c1.metric("전체 샘플 수", f"{total}개")
            c2.metric("합격률", f"{ok_r:.1f}%",
                      delta=f"-{ng_n} NG" if ng_n > 0 else "All Pass",
                      delta_color="inverse")
            avg_dx = df['DX'].mean()
            avg_dy = df['DY'].mean()
            c3.metric("평균 편차 (X, Y)", f"{avg_dx:.3f}, {avg_dy:.3f}")

            dir_x = "오른쪽(+)" if avg_dx > 0 else "왼쪽(-)"
            dir_y = "위쪽(+)"   if avg_dy > 0 else "아래쪽(-)"
            st.info(f"""
* **종합 판정:** 합격률 **{ok_r:.1f}%**
* **경향성:** **{dir_x}** `{abs(avg_dx):.3f}mm`, **{dir_y}** `{abs(avg_dy):.3f}mm` 편향
* **조치 권고:** 한 방향으로 몰리면 **원점 Offset 보정** 검토 / 특정 샘플만 튀면 **지그·이물질** 확인
            """)

            # ── 결과 테이블 ───────────────────────────────────
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                show_cols = ['ID', 'DX', 'DY', 'POS', 'LIMIT', 'RES']
                disp = df[[c for c in show_cols if c in df.columns]].copy()
                disp.columns = ['ID', 'X편차', 'Y편차', '위치도(Ø)', '규격(Ø)', '판정']

                def hi(v):
                    return ('background-color: #DFF2BF' if 'OK' in str(v)
                            else 'background-color: #FFBABA')
                try:
                    st.dataframe(disp.style.map(hi, subset=['판정']),
                                 use_container_width=True)
                except AttributeError:
                    st.dataframe(disp.style.applymap(hi, subset=['판정']),
                                 use_container_width=True)

            with col2:
                ng_df = df[df['RES'] == "❌ NG"]
                if not ng_df.empty:
                    st.markdown(
                        f"<div class='ng-box'>🚩 <b>NG {len(ng_df)}건</b><br>" +
                        "".join([f"• {r['ID']}: {r['POS']:.3f} (규격 {r['LIMIT']:.3f})<br>"
                                 for _, r in ng_df.iterrows()]) +
                        "</div>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<div class='ok-box'>✅ ALL PASS</div>",
                        unsafe_allow_html=True)

            # ── 다운로드 ──────────────────────────────────────
            st.divider()
            d1, d2 = st.columns(2)
            with d1:
                buf = BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as w:
                    df.to_excel(w, index=False, sheet_name='Analysis')
                st.download_button(
                    "📂 Excel 다운로드", buf.getvalue(),
                    "Position_Report.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            with d2:
                ibuf = BytesIO()
                fig.savefig(ibuf, format="png", bbox_inches='tight', dpi=300)
                st.download_button(
                    "🖼️ 그래프 저장", ibuf.getvalue(),
                    "Scatter_Plot.png", "image/png",
                    use_container_width=True)

            st.success(f"✅ 완료: {total}개 중 {ok_n}개 합격 / {ng_n}개 불합격")

        except Exception as e:
            st.error(f"오류 발생: {e}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    run_analysis()
