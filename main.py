import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
from io import BytesIO

st.set_page_config(page_title="Quality Hub Pro v2.10", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #D32F2F; color: white; }
        .ng-box { height: 180px; overflow-y: auto; border: 2px solid #ff0000; padding: 15px; border-radius: 8px; background-color: #fff5f5; }
        .ok-box { padding: 10px; border-radius: 8px; background-color: #e8f5e9; color: #2e7d32; font-weight: bold; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

def clean_float(val):
    """문자열에서 숫자만 추출하여 float 반환. 실패시 None"""
    try:
        v = re.sub(r'[^0-9\.\-]', '', str(val))
        return float(v) if v and v != '-' and v != '.' else None
    except:
        return None

def is_numeric_token(val):
    return clean_float(val) is not None

# ─────────────────────────────────────────────────
# B유형 파서 (기존 그대로 유지)
# 4줄 세트: 포인트명 / 지름 / X좌표 / Y좌표
# ─────────────────────────────────────────────────
def parse_type_b(raw_input, sc):
    results = []
    lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]

    for i in range(0, len(lines) - 3, 4):
        try:
            pin_line = lines[i]
            dia_line = lines[i+1]
            x_line   = lines[i+2]
            y_line   = lines[i+3]

            nx  = clean_float(x_line[0]) or 0.0
            ny  = clean_float(y_line[0]) or 0.0
            lbl = next((str(x) for x in pin_line if "PIN" in str(x).upper()), f"P{i//4+1}")

            for s in range(sc):
                idx = -(sc - s)
                ax  = clean_float(x_line[idx])   or 0.0
                ay  = clean_float(y_line[idx])   or 0.0
                dia = clean_float(dia_line[idx]) if len(dia_line) > abs(idx) else 0.35
                if dia is None: dia = 0.35
                results.append({"ID": f"{lbl}_S{s+1}",
                                 "NX": nx, "NY": ny,
                                 "AX": ax, "AY": ay,
                                 "DIA": dia})
        except Exception:
            continue
    return results

# ─────────────────────────────────────────────────
# A유형 파서 (3D CMM 성적서)
# 4줄 세트:
#   줄1: Nominal_X  측정X_S1  측정X_S2 ...
#   줄2: Nominal_Y  측정Y_S1  측정Y_S2 ...
#   줄3: 포인트명   위치도_S1  위치도_S2 ...
#   줄4: Nominal_Z  측정Z_S1  측정Z_S2 ...
# ─────────────────────────────────────────────────
def parse_type_a(raw_input, sc):
    results = []

    # 탭 우선 분리, 안되면 2칸 이상 공백
    raw_lines = raw_input.strip().split('\n')
    lines = []
    for l in raw_lines:
        l = l.strip()
        if not l:
            continue
        if '\t' in l:
            parts = l.split('\t')
        else:
            parts = re.split(r'\s{2,}', l)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            lines.append(parts)

    pt_num = 1
    i = 0
    while i <= len(lines) - 4:
        try:
            x_line   = lines[i]     # X좌표 행
            y_line   = lines[i+1]   # Y좌표 행
            pos_line = lines[i+2]   # 포인트명 + 위치도값 행
            z_line   = lines[i+3]   # Z좌표 행

            # 각 행에서 숫자값 추출
            x_nums   = [clean_float(v) for v in x_line  if is_numeric_token(v)]
            y_nums   = [clean_float(v) for v in y_line  if is_numeric_token(v)]
            z_nums   = [clean_float(v) for v in z_line  if is_numeric_token(v)]
            pos_nums = [clean_float(v) for v in pos_line if is_numeric_token(v)]

            # 유효성 검사: X,Y 행에 최소 2개(Nominal + 샘플 1개) 필요
            if len(x_nums) < 2 or len(y_nums) < 2:
                i += 4
                continue

            nom_x = x_nums[0]
            nom_y = y_nums[0]
            nom_z = z_nums[0] if z_nums else 0.0

            # 포인트명: pos_line에서 문자 포함 토큰
            lbl = next(
                (str(v) for v in pos_line if re.search(r'[A-Za-z가-힣]', str(v))),
                f"P{pt_num}"
            )
            lbl = re.sub(r'[^A-Za-z0-9_가-힣]', '', lbl) or f"P{pt_num}"

            # Nominal 제외한 실측값
            ax_vals = x_nums[1:]
            ay_vals = y_nums[1:]
            az_vals = z_nums[1:] if len(z_nums) > 1 else [nom_z] * len(ax_vals)

            # 뒤에서 sc개 추출
            n = min(sc, len(ax_vals), len(ay_vals))
            if n == 0:
                i += 4
                continue

            for s in range(n):
                si  = len(ax_vals) - n + s   # 뒤에서부터 인덱스
                ax  = ax_vals[si]
                ay  = ay_vals[si]
                az  = az_vals[min(si, len(az_vals)-1)]

                # 위치도값: pos_nums에서 뒤에서 n개 중 s번째
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
                    "NZ":      nom_z,
                    "AX":      ax,
                    "AY":      ay,
                    "AZ":      az,
                    "POS_RAW": pos_val,
                })

            pt_num += 1
            i += 4

        except Exception:
            i += 4
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
                             label=f'Basic Tol (Ø{tol:.3f})'))

    # 🔴 MMC 확장 공차 원 (median 기준)
    rep_limit = df['LIMIT'].median()
    mmc_r = rep_limit / 2
    ax.add_patch(plt.Circle((0, 0), mmc_r,
                             color='#e74c3c', fill=False, linewidth=2,
                             label=f'Median MMC Tol (Ø{rep_limit:.3f})'))

    # 측정 포인트 (OK=초록, NG=빨강)
    colors = df['RES'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
    ax.scatter(dev_x, dev_y, c=colors, s=60, edgecolors='white', zorder=5,
               label='Measured Points')

    # NG 포인트 라벨만 표시
    for _, row in df[df['RES'] == "❌ NG"].iterrows():
        ax.annotate(row['ID'], (row['DX'], row['DY']),
                    textcoords="offset points", xytext=(6, 6),
                    fontsize=8, color='#c0392b', fontweight='bold')

    ax.axhline(0, color='black', linewidth=1.2)
    ax.axvline(0, color='black', linewidth=1.2)
    ax.set_xlabel("Deviation X", fontsize=12)
    ax.set_ylabel("Deviation Y", fontsize=12)
    ax.set_title(f"Position Error: Basic vs MMC Extension\n(기본공차 Ø{tol:.3f})",
                 fontsize=14, fontweight='bold', pad=20)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_aspect('equal')
    ax.legend(loc='upper right', frameon=True, shadow=True)

    # 축 범위 자동 (데이터 + 공차 중 큰 쪽의 1.2배)
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
        mode  = st.radio("성적서 유형", ["유형 B (가로형)", "유형 A (3D CMM)"])
        sc    = st.number_input("시료 수(Sample)", min_value=1, value=4)
        tol   = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값(지름)", value=0.350, format="%.3f")

        st.markdown("---")
        if mode == "유형 A (3D CMM)":
            st.caption("""
**A유형 4줄 세트 구조**
```
줄1: Nominal_X  X_S1  X_S2 ...
줄2: Nominal_Y  Y_S1  Y_S2 ...
줄3: 포인트명   POS_S1 POS_S2 ...
줄4: Nominal_Z  Z_S1  Z_S2 ...
```
※ A유형은 MMC 기준값 미적용
(성적서 위치도값 직접 사용)
            """)
        else:
            st.caption("""
**B유형 4줄 세트 구조**
```
줄1: PIN명줄
줄2: 지름값줄
줄3: X좌표줄
줄4: Y좌표줄
```
            """)

    raw_input = st.text_area(
        "성적서 데이터를 붙여넣으세요",
        height=280,
        placeholder="헤더(Nominal/DIM±Tolerance 등) 제외하고\n데이터 행만 붙여넣으세요."
    )

    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            # ── 파싱 & 계산 ──────────────────────────────────
            if mode == "유형 B (가로형)":
                results = parse_type_b(raw_input, sc)
                if not results:
                    st.error("❌ 데이터를 읽지 못했습니다. 유형/시료수를 확인하세요.")
                    return

                df = pd.DataFrame(results)
                df['DX']    = (df['AX'] - df['NX']).round(4)
                df['DY']    = (df['AY'] - df['NY']).round(4)
                df['POS']   = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
                df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
                df['LIMIT'] = (tol + df['BONUS']).round(4)
                df['RES']   = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            else:  # A유형
                results = parse_type_a(raw_input, sc)
                if not results:
                    st.error("❌ 데이터를 읽지 못했습니다. 유형/시료수를 확인하세요.")
                    return

                df = pd.DataFrame(results)
                # X/Y 편차
                df['DX'] = (df['AX'] - df['NX']).round(4)
                df['DY'] = (df['AY'] - df['NY']).round(4)
                # 위치도: 성적서값 우선, 없으면 직접 계산
                df['POS'] = df.apply(
                    lambda r: round(float(r['POS_RAW']), 4)
                              if r['POS_RAW'] is not None
                              else round(np.sqrt(r['DX']**2 + r['DY']**2) * 2, 4),
                    axis=1
                )
                # A유형: MMC 보너스 없이 기본공차 적용
                df['BONUS'] = 0.0
                df['LIMIT'] = tol
                df['RES']   = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # ── 파싱 결과 미리보기 (디버그용) ────────────────
            with st.expander("🔍 파싱 원본 데이터 확인 (문제 있을 때 확인)"):
                st.dataframe(df, use_container_width=True)

            # ── 산포도 ────────────────────────────────────────
            st.divider()
            st.subheader("🎯 위치도 산포도 (Basic vs MMC Zone)")
            fig = draw_scatter_plot(df, tol)
            st.pyplot(fig)

            # ── 통계 요약 ─────────────────────────────────────
            st.divider()
            st.subheader("💡 데이터 분석 가이드")

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
* **경향성:** 전체적으로 **{dir_x}** `{abs(avg_dx):.3f}mm`, **{dir_y}** `{abs(avg_dy):.3f}mm` 편향
* **조치 권고:** 점들이 한 방향으로 몰려 있으면 **원점(Offset) 보정** 검토, 특정 샘플만 튀면 **지그 고정력/이물질** 확인
            """)

            # ── 결과 테이블 ───────────────────────────────────
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                show_cols = ['ID', 'DX', 'DY', 'POS', 'LIMIT', 'RES']
                disp = df[[c for c in show_cols if c in df.columns]].copy()
                disp.columns = ['ID', 'X편차', 'Y편차', '위치도(Ø)', '규격(Ø)', '판정']

                def hi(v):
                    return 'background-color: #DFF2BF' if 'OK' in str(v) else 'background-color: #FFBABA'
                try:
                    st.dataframe(disp.style.map(hi, subset=['판정']), use_container_width=True)
                except AttributeError:
                    st.dataframe(disp.style.applymap(hi, subset=['판정']), use_container_width=True)

            with col2:
                ng_df = df[df['RES'] == "❌ NG"]
                if not ng_df.empty:
                    st.markdown(
                        f"<div class='ng-box'>🚩 <b>NG {len(ng_df)}건</b><br>" +
                        "".join([f"• {r['ID']}: {r['POS']:.3f} (규격 {r['LIMIT']:.3f})<br>"
                                 for _, r in ng_df.iterrows()]) + "</div>",
                        unsafe_allow_html=True)
                else:
                    st.markdown("<div class='ok-box'>✅ ALL PASS</div>", unsafe_allow_html=True)

            # ── 다운로드 ──────────────────────────────────────
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

            st.success(f"✅ 완료: {total}개 중 {ok_n}개 합격 / {ng_n}개 불합격")

        except Exception as e:
            st.error(f"오류 발생: {e}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    run_analysis()
