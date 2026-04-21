import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import re
from io import BytesIO

# 1. 초기 설정 및 테마 적용
st.set_page_config(page_title="Quality Hub Pro v2.10", layout="wide")

def set_style():
    st.markdown("""
        <style>
        .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.5em; background-color: #D32F2F; color: white; }
        .ng-box { height: 180px; overflow-y: auto; border: 2px solid #ff0000; padding: 15px; border-radius: 8px; background-color: #fff5f5; }
        .ok-box { padding: 10px; border-radius: 8px; background-color: #e8f5e9; color: #2e7d32; font-weight: bold; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

def run_analysis():
    set_style()
    st.title("🎯 품질 측정 위치도 분석 리포트")

    with st.sidebar:
        st.header("📋 보고서 설정")
        mode = st.radio("성적서 유형", ["유형 B (가로형)", "유형 A (3줄 세트)"])
        sc = st.number_input("시료 수(Sample)", min_value=1, value=4)
        tol = st.number_input("기본 공차(Ø)", value=0.350, format="%.3f")
        m_ref = st.number_input("MMC 기준값", value=0.060 if mode == "유형 A (3줄 세트)" else 0.350, format="%.3f")

    raw_input = st.text_area("성적서 데이터를 붙여넣으세요", height=250)

    if st.button("📊 분석 보고서 생성") and raw_input:
        try:
            results = []

            if mode == "유형 B (가로형)":
                lines = [re.split(r'\s+', l.strip()) for l in raw_input.strip().split('\n') if l.strip()]
                for i in range(0, len(lines), 4):
                    if i + 3 >= len(lines): break

                    def clean_v(lst, idx):
                        v = re.sub(r'[^0-9\.\-]', '', lst[idx])
                        return float(v) if v and v != '-' else 0.0

                    try:
                        nx, ny = clean_v(lines[i+2], 0), clean_v(lines[i+3], 0)
                        lbl = lines[i][0] if "PIN" in str(lines[i]) else f"P{i//4 + 1}"
                        for s in range(sc):
                            idx = -(sc - s)
                            ax, ay = clean_v(lines[i+2], idx), clean_v(lines[i+3], idx)
                            dv = clean_v(lines[i+1], idx) if len(lines[i+1]) > abs(idx) else 0.35
                            results.append({"ID": f"{lbl}_S{s+1}", "NX": nx, "NY": ny, "AX": ax, "AY": ay, "DIA": dv})
                    except Exception:
                        continue

            else:  # 유형 A (3줄 세트)
                lines = [l.strip() for l in raw_input.split('\n') if l.strip()]
                rows = []
                for l in lines:
                    nums = [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', l)]
                    rows.append([v if abs(v) < 150 else v % 100 for v in nums])
                rows = [r for r in rows if r]
                for i in range(0, len(rows) // 3 * 3, 3):
                    for s in range(1, len(rows[i+1])):
                        results.append({
                            "ID": f"P{(i//3)+1}_S{s}",
                            "NX": rows[i+1][0],
                            "NY": rows[i+2][0],
                            "AX": rows[i+1][s],
                            "AY": rows[i+2][s],
                            "DIA": rows[i][s-1] if (s-1) < len(rows[i]) else rows[i][-1]
                        })

            df = pd.DataFrame(results)
            if df.empty:
                st.error("데이터를 분석할 수 없습니다.")
                return

            # 데이터 가공 및 판정
            df['DX'] = (df['AX'] - df['NX']).round(4)
            df['DY'] = (df['AY'] - df['NY']).round(4)
            df['POS'] = (np.sqrt(df['DX']**2 + df['DY']**2) * 2).round(4)
            df['BONUS'] = (df['DIA'] - m_ref).clip(lower=0).round(4)
            df['LIMIT'] = (tol + df['BONUS']).round(4)
            df['RES'] = np.where(df['POS'] <= df['LIMIT'], "✅ OK", "❌ NG")

            # ===================================================
            # 📊 기본툴과 동일한 matplotlib 위치도 산포도
            # ===================================================
            st.divider()
            st.subheader("🎯 위치도 산포도 분석 (Basic vs MMC Zone)")

            fig, ax = plt.subplots(figsize=(8, 8))

            dev_x = df['DX']
            dev_y = df['DY']

            # 🔵 기본 공차 영역 (Basic Tolerance)
            basic_radius = tol / 2
            ax.add_patch(plt.Circle((0, 0), basic_radius,
                                    color='#3498db', fill=True, alpha=0.15, linestyle='--'))
            ax.add_patch(plt.Circle((0, 0), basic_radius,
                                    color='#3498db', fill=False, linestyle='--', linewidth=1.5,
                                    label=f'Basic Tol (Ø{tol:.3f})'))

            # 🔴 MMC 확장 공차 영역 (Median 기준)
            representative_final_tol = df['LIMIT'].median()
            mmc_radius = representative_final_tol / 2
            ax.add_patch(plt.Circle((0, 0), mmc_radius,
                                    color='#e74c3c', fill=False, linewidth=2,
                                    label=f'Median MMC Tol (Ø{representative_final_tol:.3f})'))

            # 🟢/🔴 측정 데이터 포인트 (OK=초록, NG=빨강)
            colors = df['RES'].apply(lambda x: '#2ecc71' if 'OK' in x else '#e74c3c')
            ax.scatter(dev_x, dev_y, c=colors, s=60, edgecolors='white', zorder=5,
                       label='Measured Points')

            # NG 포인트에만 ID 라벨 표시
            ng_df = df[df['RES'] == "❌ NG"]
            for _, row in ng_df.iterrows():
                ax.annotate(row['ID'], (row['DX'], row['DY']),
                            textcoords="offset points", xytext=(6, 6),
                            fontsize=8, color='#c0392b', fontweight='bold')

            # 축 및 레이아웃
            ax.axhline(0, color='black', linewidth=1.2)
            ax.axvline(0, color='black', linewidth=1.2)
            ax.set_xlabel("Deviation X", fontsize=12)
            ax.set_ylabel("Deviation Y", fontsize=12)
            ax.set_title(f"Position Error: Basic vs MMC Extension\n(기본공차 Ø{tol:.3f})",
                         fontsize=14, fontweight='bold', pad=20)
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.set_aspect('equal')
            ax.legend(loc='upper right', frameon=True, shadow=True)

            # 축 범위 자동 설정 (기본툴과 동일 로직)
            tol_radius = max(basic_radius, mmc_radius)
            data_radius = pd.concat([dev_x.abs(), dev_y.abs()]).max()
            limit = max(tol_radius, data_radius) * 1.2
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)

            st.pyplot(fig)

            # ===================================================
            # 📋 결과 요약 및 통계
            # ===================================================
            st.divider()
            st.subheader("💡 데이터 분석 가이드")

            total_count = len(df)
            ok_count = (df['RES'].str.contains('OK')).sum()
            ng_count = total_count - ok_count
            ok_rate = (ok_count / total_count) * 100
            avg_dev_x = dev_x.mean()
            avg_dev_y = dev_y.mean()

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("전체 샘플 수", f"{total_count}개")
            col_m2.metric("합격률", f"{ok_rate:.1f}%",
                          delta=f"-{ng_count} NG" if ng_count > 0 else "All Pass",
                          delta_color="inverse")
            col_m3.metric("평균 편차(X, Y)", f"{avg_dev_x:.3f}, {avg_dev_y:.3f}")

            dir_x = "오른쪽(+)" if avg_dev_x > 0 else "왼쪽(-)"
            dir_y = "위쪽(+)" if avg_dev_y > 0 else "아래쪽(-)"
            advice = f"""
* **종합 판정:** 현재 전체 합격률은 **{ok_rate:.1f}%**입니다.
* **경향성 분석:** 데이터가 전체적으로 **{dir_x}**으로 `{abs(avg_dev_x):.3f}mm`, **{dir_y}**으로 `{abs(avg_dev_y):.3f}mm` 밀려 있습니다.
* **조치 권고:** 1. 점들이 한 방향으로 줄지어 있다면 **장비 원점(Offset) 보정**을 검토하세요.
    2. 특정 샘플만 튀는 경우 **지그(Jig) 고정력 및 이물질** 확인이 필요합니다.
"""
            st.info(advice)

            # 결과 테이블
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                display_df = df[['ID', 'POS', 'BONUS', 'LIMIT', 'RES']].copy()
                display_df.columns = ['ID', '위치도(Ø)', '보너스(+Ø)', '규격(Ø)', '판정']

                def highlight_res(val):
                    color = '#DFF2BF' if 'OK' in str(val) else '#FFBABA'
                    return f'background-color: {color}'

                try:
                    st.dataframe(display_df.style.map(highlight_res, subset=['판정']),
                                 use_container_width=True)
                except AttributeError:
                    st.dataframe(display_df.style.applymap(highlight_res, subset=['판정']),
                                 use_container_width=True)

            with col2:
                if not ng_df.empty:
                    st.markdown(
                        f"<div class='ng-box'>🚩 <b>불합격(NG) {len(ng_df)}건 발생</b><br>" +
                        "".join([f"• {r['ID']}: {r['POS']:.3f} (규격 {r['LIMIT']:.3f})<br>"
                                 for _, r in ng_df.iterrows()]) + "</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown("<div class='ok-box'>✅ 모든 시료 합격 (ALL PASS)</div>",
                                unsafe_allow_html=True)

            # 다운로드 버튼
            st.divider()
            st.subheader("💾 분석 결과 저장")
            col_dl1, col_dl2 = st.columns(2)

            with col_dl1:
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Position_Analysis')
                st.download_button(
                    label="📂 Excel 결과 다운로드",
                    data=excel_buffer.getvalue(),
                    file_name="Position_Analysis_Report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with col_dl2:
                img_buffer = BytesIO()
                fig.savefig(img_buffer, format="png", bbox_inches='tight', dpi=300)
                st.download_button(
                    label="🖼️ 그래프 이미지 저장",
                    data=img_buffer.getvalue(),
                    file_name="Position_Scatter_Plot.png",
                    mime="image/png",
                    use_container_width=True
                )

            st.success(f"✅ 분석 완료: {total_count}개 중 {ok_count}개 합격 (불합격 {ng_count}개)")

        except Exception as e:
            st.error(f"오류: {e}")


if __name__ == "__main__":
    run_analysis()
