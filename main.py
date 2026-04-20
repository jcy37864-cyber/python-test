import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="품질 측정 통합 프로그램 v2.0", layout="wide")

# 2. 그래프 폰트 및 스타일 설정
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

# 3. 사이드바 스타일 및 타이틀
st.markdown("""
<style>
[data-testid="stSidebar"] { background-color: #0E1117; }
[data-testid="stSidebar"] * { color: white; }
.main-title { font-size: 30px; font-weight: bold; color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

st.title("📊 품질 측정 통합 시스템 (Master)")

menu = st.sidebar.radio(
    "메뉴 선택",
    ["🔄 ZXY 대량 변환", "📈 전문 그래프 분석 (CPK)", "🧮 정밀 공차 계산기"]
)

# =========================
# 🔄 ZXY 대량 변환 (복사-붙여넣기 최적화)
# =========================
if menu == "🔄 ZXY 대량 변환":
    st.subheader("🔄 ZXY 데이터 대량 변환")
    st.info("엑셀에서 X, Y, Z 열을 복사하여 아래 입력창에 붙여넣으세요. (탭 구분 지원)")
    
    raw_data = st.text_area("여기에 데이터를 붙여넣으세요 (예: X [Tab] Y [Tab] Z)", height=200)
    
    if st.button("데이터 변환 시작"):
        try:
            # 텍스트 데이터를 데이터프레임으로 변환 (클립보드 데이터 형태 대응)
            from io import StringIO
            df_input = pd.read_csv(StringIO(raw_data), sep='\t', names=['X', 'Y', 'Z'])
            
            if df_input.empty:
                st.warning("데이터가 없습니다. 다시 확인해주세요.")
            else:
                results = []
                for _, row in df_input.iterrows():
                    x, y, z = str(row["X"]).strip(), str(row["Y"]).strip(), str(row["Z"]).strip()
                    results.extend([z, x, y])
                
                result_df = pd.DataFrame(results, columns=["변환 결과"])
                st.success(f"총 {len(df_input)}행 데이터 변환 완료!")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.dataframe(result_df, use_container_width=True)
                with col2:
                    csv = result_df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button("📂 변환 결과 CSV 다운로드", csv, "zxy_bulk_result.csv")
        except Exception as e:
            st.error(f"데이터 형식이 올바르지 않습니다: {e}")

# =========================
# 📈 전문 그래프 분석 (CPK 포함)
# =========================
elif menu == "📈 전문 그래프 분석 (CPK)":
    st.subheader("📈 품질 통계 분석 및 CPK 리포트")
    
    uploaded_file = st.file_uploader("분석할 파일을 업로드하세요 (XLSX, CSV)", type=["xlsx", "csv"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        
        # 기본 계산
        df["판정"] = df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
        df["편차"] = df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)
        
        # CPK 계산 로직
        usl, lsl = df["MAX"].iloc[0], df["MIN"].iloc[0]
        mean = df["VALUE"].mean()
        std = df["VALUE"].std()
        
        cp = (usl - lsl) / (6 * std) if std != 0 else 0
        cpu = (usl - mean) / (3 * std) if std != 0 else 0
        cpl = (mean - lsl) / (3 * std) if std != 0 else 0
        cpk = min(cpu, cpl)

        # 📊 그래프 시각화
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(df["VALUE"], marker='o', markersize=4, color='#1f77b4', label="측정값", alpha=0.7)
        ax.axhline(usl, color='red', linestyle='--', label=f"USL (MAX): {usl}")
        ax.axhline(lsl, color='orange', linestyle='--', label=f"LSL (MIN): {lsl}")
        ax.axhline(mean, color='green', linestyle='-', alpha=0.5, label=f"AVG: {mean:.4f}")
        
        # NG 포인트 강조
        ng_data = df[df["판정"] == "NG"]
        ax.scatter(ng_data.index, ng_data["VALUE"], color='red', s=50, zorder=5, label="NG 지점")
        
        ax.set_title(f"Quality Analysis (CPK: {cpk:.3f})", fontsize=15)
        ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        ax.grid(True, linestyle=':', alpha=0.5)
        st.pyplot(fig)
        
        # 핵심 요약 지표 (Metric)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("전체 샘플수", f"{len(df)}개")
        m2.metric("불량 개수(NG)", f"{len(ng_data)}개", delta=len(ng_data), delta_color="inverse")
        m3.metric("평균값 (AVG)", f"{mean:.4f}")
        m4.metric("공정능력 (CPK)", f"{cpk:.3f}")

        # 📄 엑셀 다운로드 (이미지 + 서식)
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png', bbox_inches='tight')
        
        excel_out = BytesIO()
        with pd.ExcelWriter(excel_out, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='분석결과')
            workbook = writer.book
            worksheet = writer.sheets['분석결과']
            
            # 서식 설정
            ng_format = workbook.add_format({'bg_color': '#FFCCCC', 'font_color': '#9C0006'})
            stat_format = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1})
            
            # NG 행 강조
            for row_num in range(1, len(df) + 1):
                if df.iloc[row_num-1]["판정"] == "NG":
                    worksheet.set_row(row_num, None, ng_format)
            
            # 통계 정보 추가
            worksheet.write('H2', '공정통계분석', stat_format)
            worksheet.write('H3', f'평균: {mean:.4f}')
            worksheet.write('H4', f'표준편차: {std:.4f}')
            worksheet.write('H5', f'CPK: {cpk:.3f}')
            
            # 이미지 삽입
            worksheet.insert_image('H7', 'graph.png', {'image_data': img_buffer, 'x_scale': 0.7, 'y_scale': 0.7})

        st.download_button("📂 전문 품질 리포트(Excel) 다운로드", excel_out.getvalue(), "Quality_Master_Report.xlsx")

# =========================
# 🧮 정밀 공차 계산기 (업그레이드)
# =========================
elif menu == "🧮 정밀 공차 계산기":
    st.subheader("🧮 상하한 분리형 정밀 판정기")
    
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        target = c1.number_input("기준값 (Target)", value=0.0, format="%.4f")
        u_tol = c2.number_input("상한공차 (+)", value=0.0, format="%.4f")
        l_tol = c3.number_input("하한공차 (-)", value=0.0, format="%.4f")
        val = c4.number_input("현재 측정값", value=0.0, format="%.4f")
        
        max_limit = target + abs(u_tol)
        min_limit = target - abs(l_tol)
        
        st.markdown("---")
        res_col1, res_col2 = st.columns([1, 1])
        
        if min_limit <= val <= max_limit:
            res_col1.success(f"## 판정: OK")
            res_col2.info(f"규격 범위: {min_limit:.4f} ~ {max_limit:.4f}")
        else:
            res_col1.error(f"## 판정: NG")
            diff = val - max_limit if val > max_limit else val - min_limit
            res_col2.warning(f"이탈 수치: {diff:.4f}\n\n규격 범위: {min_limit:.4f} ~ {max_limit:.4f}")
