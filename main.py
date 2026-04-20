import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# 1. 페이지 설정
st.set_page_config(page_title="정밀측정실 품질 분석 시스템", layout="wide")

# 2. 그래프 폰트 설정 (영문 사용으로 깨짐 방지)
plt.rcParams['axes.unicode_minus'] = False
plt.rc('font', family='sans-serif') 

st.title("📊 품질 측정 통합 프로그램 (전치수/개발품 대응)")

menu = st.sidebar.radio("메뉴 선택", ["🔄 ZXY 변환", "📈 그래프 분석", "🧮 계산기"])

# =========================
# 🔄 ZXY 변환 (세로 쌓기 로직 유지)
# =========================
if menu == "🔄 ZXY 변환":
    st.subheader("🔄 ZXY 데이터 변환")
    st.info("X, Y, Z 데이터를 [Z -> X -> Y] 순서의 세로형 리스트로 변환합니다.")

    if "df_zxy" not in st.session_state:
        st.session_state.df_zxy = pd.DataFrame({"X": [""] * 10, "Y": [""] * 10, "Z": [""] * 10})
    
    edited_df = st.data_editor(st.session_state.df_zxy, use_container_width=True, num_rows="dynamic")
    
    if st.button("ZXY 결과 생성"):
        results = []
        for _, row in edited_df.iterrows():
            if str(row["X"]).strip() and str(row["Y"]).strip() and str(row["Z"]).strip():
                results.extend([row["Z"], row["X"], row["Y"]])
        
        if results:
            res_df = pd.DataFrame(results, columns=["변환 결과"])
            st.dataframe(res_df, use_container_width=True)
            csv = res_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📂 CSV 다운로드", csv, "zxy_result.csv")

# =========================
# 📈 그래프 분석 (그룹화 및 Worst 시인성 개선)
# =========================
elif menu == "📈 그래프 분석":
    st.subheader("📈 품질 그래프 분석")
    uploaded_file = st.file_uploader("데이터 파일 업로드 (TYPE 열 포함 권장)", type=["xlsx", "csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        
        # [기능 추가] TYPE 열을 이용한 그룹화 필터
        filtered_df = df.copy()
        if "TYPE" in df.columns:
            st.sidebar.markdown("---")
            st.sidebar.subheader("🔍 항목 필터")
            all_types = df["TYPE"].unique().tolist()
            selected_types = st.sidebar.multiselect("분석할 항목 선택", options=all_types, default=all_types)
            filtered_df = df[df["TYPE"].isin(selected_types)].reset_index(drop=True)
        
        if filtered_df.empty:
            st.warning("선택된 데이터가 없습니다.")
        else:
            # 판정 및 편차 계산
            filtered_df["판정"] = filtered_df.apply(lambda x: "OK" if x["MIN"] <= x["VALUE"] <= x["MAX"] else "NG", axis=1)
            filtered_df["편차"] = filtered_df.apply(lambda x: max(x["VALUE"] - x["MAX"], x["MIN"] - x["VALUE"], 0), axis=1)

            # NG 데이터 강조 테이블
            st.dataframe(filtered_df.style.apply(lambda r: ['background-color: #ffcccc' if r["판정"] == "NG" else ''] * len(r), axis=1), use_container_width=True)

            # 📊 그래프 생성
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(filtered_df["VALUE"], marker='o', markersize=4, label="VALUE", zorder=3, alpha=0.8)
            ax.plot(filtered_df["MAX"], color='green', linestyle='--', label="MAX", alpha=0.5)
            ax.plot(filtered_df["MIN"], color='orange', linestyle='--', label="MIN", alpha=0.5)

            # Worst 강조 (이중 원 시각화)
            worst_idx = filtered_df["편차"].idxmax()
            worst_row = filtered_df.loc[worst_idx]
            
            if worst_row["편차"] > 0:
                ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', s=450, linewidths=2.5, zorder=5)
                ax.scatter(worst_idx, worst_row["VALUE"], facecolors='none', edgecolors='red', s=200, linewidths=1.5, zorder=5, alpha=0.5)

            ax.set_title("Quality Trend Analysis")
            ax.set_xlabel("Sample Index")
            ax.set_ylabel("Value")
            ax.legend(loc='lower left')
            ax.grid(True, linestyle=':', alpha=0.4)
            st.pyplot(fig)

            # 하단 정보 섹션 (Worst 텍스트는 여기서 확인)
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📋 분석 요약")
                total, ng = len(filtered_df), len(filtered_df[filtered_df["판정"] == "NG"])
                st.write(f"• 선택 항목 샘플: {total}개 / **불량(NG): {ng}개**")
                if ng == 0: st.success("✅ 선택된 모든 치수가 규격 내에 있습니다.")
                else: st.error(f"🚨 {ng}건의 규격 이탈이 확인되었습니다.")

            with col2:
                st.markdown("### 📍 Worst Point 정보")
                if worst_row["편차"] > 0:
                    st.error(f"**최대 편차 값: {worst_row['VALUE']:.4f}**")
                    if "TYPE" in filtered_df.columns: st.write(f"• 해당 항목: {worst_row['TYPE']}")
                    st.write(f"• 규격 대비 편차량: {worst_row['편차']:.4f}")
                else:
                    st.info("Worst 포인트가 없습니다 (전체 양호).")

            # 결과 파일 다운로드
            excel_out = BytesIO()
            with pd.ExcelWriter(excel_out, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False)
            st.download_button("📄 분석 결과 엑셀 저장", excel_out.getvalue(), "quality_analysis.xlsx")

# =========================
# 🧮 계산기 (기능 유지)
# =========================
elif menu == "🧮 계산기":
    st.subheader("🧮 보조 계산기")
    calc = st.selectbox("기능 선택", ["토크 변환", "평균 계산", "공차 판정"])
    
    if calc == "토크 변환":
        v = st.number_input("수치", 0.0)
        m = st.selectbox("단위", ["N·m → kgf·m", "kgf·m → N·m"])
        st.success(f"결과: {v * 0.101972:.4f}" if "kgf" in m else f"결과: {v * 9.80665:.4f}")
    
    elif calc == "평균 계산":
        txt = st.text_input("값 입력 (쉼표 구분)", "10.1, 10.2, 10.5")
        try:
            vals = [float(x.strip()) for x in txt.split(",") if x.strip()]
            if vals: st.info(f"평균값: {sum(vals)/len(vals):.4f}")
        except: st.error("숫자 형식을 확인해주세요.")

    elif calc == "공차 판정":
        c1, c2, c3 = st.columns(3)
        t, tol, v = c1.number_input("기준값"), c2.number_input("공차±"), c3.number_input("측정값")
        if t-tol <= v <= t+tol: st.success("판정: OK")
        else: st.error("판정: NG")
