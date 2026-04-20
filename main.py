import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# --- 1. 페이지 설정 및 디자인 (사용자 선호 스타일 고정) ---
st.set_page_config(page_title="품질 통합 분석 시스템 v8.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] * { color: #f8fafc !important; }
    [data-testid="stSidebar"] div.stButton > button {
        background-color: #ef4444 !important; color: white !important; font-weight: bold !important;
        height: 3.5em !important; margin-top: 20px !important; border-radius: 8px; border: none;
    }
    .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 25px; }
    .report-text { font-size: 1.1em; line-height: 1.8; color: #1e293b; white-space: pre-wrap; font-family: 'Pretendard', 'Malgun Gothic', sans-serif; }
    .ok-text { color: #10b981; font-weight: bold; }
    .ng-text { color: #e11d48; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 초기화 로직
if 'reset_key' not in st.session_state: st.session_state.reset_key = 0

# --- 2. 사이드바 메뉴 (구조 고정) ---
st.sidebar.title("💎 품질 통합 플랫폼")
menu = st.sidebar.radio("📋 업무 선택", ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"], key=f"menu_{st.session_state.reset_key}")

if st.sidebar.button("🧹 모든 데이터 초기화", use_container_width=True):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.reset_key += 1
    st.rerun()

# --- [메뉴 1] 데이터 변환기 (다운로드 복구) ---
if menu == "🔄 데이터 변환기":
    st.title("🔄 좌표 데이터 변환기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.info("💡 엑셀에서 복사한 X, Y, Z 데이터를 아래 표에 붙여넣고 변환하세요.")
    df_input = st.data_editor(pd.DataFrame({"X": [""]*10, "Y": [""]*10, "Z": [""]*10}), num_rows="dynamic", use_container_width=True)
    
    if st.button("🚀 데이터 변환 및 결과 생성", use_container_width=True):
        res = []
        for _, r in df_input.iterrows():
            if str(r['X']).strip(): res.extend([r['Z'], r['X'], r['Y']])
        if res:
            df_res = pd.DataFrame(res, columns=["변환 데이터 (Z-X-Y 순서)"])
            st.success("✅ 변환 완료! 아래에서 데이터를 확인하고 다운로드하세요.")
            st.dataframe(df_res, use_container_width=True)
            st.download_button("📥 변환 데이터 CSV 저장", df_res.to_csv(index=False).encode('utf-8-sig'), "converted_coordinates.csv", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 2] 멀티 캐비티 분석 (템플릿 & 그래프 & 평균선 복구) ---
elif menu == "📈 멀티 캐비티 분석":
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    
    # 템플릿 제작 및 다운로드 (고정)
    def get_cav_template():
        df_t = pd.DataFrame({"Point": range(1,11), "SPEC_MIN": [30.1]*10, "SPEC_MAX": [30.5]*10, "Cavity_1": [30.2,30.3,30.2,30.6,30.2,30.1,30.3,30.4,30.2,30.3], "Cavity_2": [30.3,30.4,30.1,30.2,30.3,30.5,30.2,30.3,30.4,30.2]})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_t.to_excel(writer, index=False)
        return out.getvalue()
    
    st.download_button("📄 멀티캐비티 분석용 템플릿 다운로드", get_cav_template(), "Multi_Cavity_Template.xlsx", use_container_width=True)
    
    up = st.file_uploader("분석용 엑셀/CSV 파일 업로드", type=["xlsx", "csv"])
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_min, y_max = np.nanmin(all_vals) - 0.03, np.nanmax(all_vals) + 0.03
        
        # 개별 캐비티 분석 (바 그래프 스타일 고정)
        st.subheader("🔍 캐비티별 상세 분포")
        c_grid = st.columns(2)
        summary_list = []
        for i, cav in enumerate(cav_cols):
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            ng_count = len(df[df[f"{cav}_판정"]=="NG"])
            rate = ((len(df)-ng_count)/len(df))*100
            summary_list.append(f"• **{cav}**: 합격률 {rate:.1f}% (불량 {ng_count}건)")
            
            with c_grid[i % 2]:
                st.markdown(f'<div class="stBox"><b>{cav} 분석</b> (상태: {"✅ 양호" if ng_count==0 else "🚨 불량 발생"})', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                # [복구 고정] NG는 빨강, OK는 파랑
                b_colors = ['#ef4444' if p == "NG" else '#3b82f6' for p in df[f"{cav}_판정"]]
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=b_colors, name="실측치"))
                fig.update_layout(height=300, yaxis_range=[y_min, y_max], margin=dict(t=20, b=20), template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # [복구 고정] 통합 트렌드 분석
        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 및 평균 경향 분석")
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red", dash="dot")))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='markers', name=cav, marker=dict(opacity=0.4, size=8)))
        # [복구 고정] 전체 평균선 (검정 실선)
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="전체평균", line=dict(color="black", width=3)))
        fig_total.update_layout(height=450, yaxis_range=[y_min, y_max], template="plotly_white")
        st.plotly_chart(fig_total, use_container_width=True)
        
        st.subheader("📝 종합 분석 리포트")
        st.markdown(f'<div class="report-text">{"/n".join(summary_list)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 3] 위치도 분석 (템플릿 & 이미지 아이콘 & 파란선 복구) ---
elif menu == "🎯 위치도(MMC) 분석":
    st.title("🎯 위치도 정밀 분석 (MMC)")
    
    def get_pos_template():
        df_pt = pd.DataFrame({"측정포인트": [1, 2, 3], "기본공차": [0.3]*3, "도면치수_X": [10.0, 20.0, 30.0], "도면치수_Y": [10.0, 20.0, 30.0], "측정치_X": [10.02, 20.05, 30.15], "측정치_Y": [10.01, 20.03, 30.08], "실측지름_MMC용": [0.52, 0.55, 0.58]})
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer: df_pt.to_excel(writer, index=False)
        return out.getvalue()
    st.download_button("📄 위치도 분석 템플릿 다운로드", get_pos_template(), "Position_Template.xlsx", use_container_width=True)

    c1, c2 = st.columns([1, 2])
    with c1: mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
    with c2: file = st.file_uploader("데이터 파일 업로드", type=["xlsx"])

    if file:
        df_m = pd.read_excel(file)
        df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
        df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
        df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
        df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
        df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.info("💡 그래프 우측 상단 카메라 아이콘을 누르면 이미지(PNG)로 즉시 저장됩니다.")
        fig_m = go.Figure()
        # 정원 유지 설정
        fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinewidth=1, zerolinecolor='black')
        fig_m.update_xaxes(zeroline=True, zerolinewidth=1, zerolinecolor='black')
        
        # [복구 고정] 3단계 과녁 가이드
        max_t = df_m['최종공차'].max() / 2
        # 1. 파란색 중심선 (0.05 구간)
        fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", width=1, dash="dot"))
        # 2. 보라색 합격 공차선
        fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
        # 3. 빨간색 경고/한계선
        fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1, dash="dash"))
        
        for _, row in df_m.iterrows():
            p_c = '#10b981' if row['판정'] == "OK" else '#ef4444'
            fig_m.add_trace(go.Scatter(x=[row['X편차']], y=[row['Y편차']], mode='markers+text', text=[f"<b>{int(row['측정포인트'])}</b>"], textposition="top center", marker=dict(size=14, color=p_c, line=dict(width=1, color='white'))))
        
        fig_m.update_layout(width=700, height=700, template="plotly_white")
        st.plotly_chart(fig_m, use_container_width=False, config={'toImageButtonOptions': {'format': 'png', 'filename': 'Position_Target', 'scale': 2}})
        
        st.dataframe(df_m.style.map(lambda x: 'background-color: #d1fae5' if x == 'OK' else 'background-color: #fee2e2', subset=['판정']), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- [메뉴 4] 품질 계산기 (전체 로직 복구) ---
elif menu == "🧮 품질 계산기":
    st.title("🧮 품질 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스 공차", "🔧 단위 환산", "⚖️ 합격 판정기"])
    
    with tabs[0]:
        st.subheader("MMC 보너스 공차 계산")
        base_g = st.number_input("도면상 기하공차", value=0.05, format="%.3f")
        mmc_s = st.number_input("MMC 규격치", value=10.00, format="%.3f")
        actual_s = st.number_input("현재 실측치", value=10.02, format="%.3f")
        bonus_val = max(0, actual_s - mmc_s)
        st.metric("최종 허용 기하공차", f"{base_g + bonus_val:.4f}")
        
    with tabs[1]:
        st.subheader("주요 단위 환산")
        val_in = st.number_input("변환할 값 입력", value=1.0)
        conv_mode = st.selectbox("변환 종류 선택", ["mm ➔ inch", "inch ➔ mm", "kgf·m ➔ N·m", "N·m ➔ kgf·m"])
        if "mm ➔ inch" in conv_mode: res = val_in / 25.4
        elif "inch ➔ mm" in conv_mode: res = val_in * 25.4
        elif "kgf·m ➔ N·m" in conv_mode: res = val_in * 9.80665
        else: res = val_in * 0.10197
        st.success(f"변환 결과: {res:.4f}")
        
    with tabs[2]:
        st.subheader("규격 합격 판정")
        target_v = st.number_input("기준치(SPEC)", value=0.0)
        upper_v = st.number_input("상한공차(+)", value=0.1)
        lower_v = st.number_input("하한공차(-)", value=-0.1)
        measure_v = st.number_input("실제 측정값", value=0.0)
        if (target_v + lower_v) <= measure_v <= (target_v + upper_v): st.success("✅ 결과: 합격(OK)")
        else: st.error("🚨 결과: 불합격(NG)")
    st.markdown('</div>', unsafe_allow_html=True)
