import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO

# ==========================================
# 1. 전역 설정 및 스타일 (공통)
# ==========================================
def set_global_style():
    st.set_page_config(page_title="품질 통합 분석 시스템 v9.5", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        [data-testid="stSidebar"] { background-color: #0f172a !important; }
        [data-testid="stSidebar"] * { color: #f8fafc !important; }
        .stButton > button {
            background-color: #ef4444 !important; color: white !important;
            font-weight: bold !important; width: 100%; border-radius: 8px;
        }
        .capture-info {
            background-color: #e0f2fe; padding: 10px; border-radius: 5px; 
            border: 1px solid #7dd3fc; color: #0369a1; font-size: 0.9em;
            margin-bottom: 20px; text-align: center;
        }
        .stBox { background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); margin-bottom: 25px; }
        .report-card { background-color: #f1f5f9; padding: 20px; border-left: 10px solid #3b82f6; border-radius: 8px; line-height: 2.0; font-size: 1.1em; }
        .guide-box { padding: 15px; background-color: #f8fafc; border-radius: 10px; border: 1px dashed #cbd5e1; margin-bottom: 15px; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 메뉴별 독립 기능 (함수화)
# ==========================================

import re

def clean_float(value):
    """문자열에서 숫자만 추출하여 실수로 변환하는 안전한 함수"""
    try:
        # 숫자, 마이너스(-), 소수점(.)만 남기고 나머지 제거 (예: '0.35mm' -> '0.35')
        cleaned = re.sub(r'[^0-9\.\-]', '', str(value))
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

# ... (기존 코드 생략) ...

# 4줄씩 한 세트 처리 부분 수정
for i in range(0, len(lines), 4):
    try:
        pin_line = lines[i]
        mmc_line = lines[i+1]
        x_line = lines[i+2]
        y_line = lines[i+3]
        
        pin_name = pin_line[0].strip()
        sample_count = len(pin_line) - 1
        
        for s in range(sample_count):
            # clean_float 함수를 사용하여 안전하게 숫자 변환
            act_x = clean_float(x_line[s+1])
            act_y = clean_float(y_line[s+1])
            
            processed_results.append({
                "측정포인트": f"{pin_name}_S{s+1}",
                "기본공차": 0.35,
                "도면치수_X": 0.0, 
                "도면치수_Y": 0.0,
                "측정치_X": act_x,
                "측정치_Y": act_y,
                "실측지름_MMC용": 0.35
            })
    except Exception as e:
        continue
def run_cavity_analysis():
    """메뉴 2: 멀티 캐비티 분석"""
    st.title("📊 핀 높이 멀티 캐비티 통합 분석")
    def get_cav_template():
        df_t = pd.DataFrame({"Point": range(1,6), "SPEC_MIN": [30.1]*5, "SPEC_MAX": [30.5]*5, "Cavity_1": [30.2]*5, "Cavity_2": [30.3]*5, "Cavity_3": [30.2]*5, "Cavity_4": [30.4]*5})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_t.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    
    st.download_button("📄 분석용 템플릿 다운로드", get_cav_template(), "Multi_Cavity_Template.xlsx")
    up = st.file_uploader("파일 업로드", type=["xlsx", "csv"])
    
    if up:
        df = pd.read_excel(up) if up.name.endswith('.xlsx') else pd.read_csv(up)
        cav_cols = [c for c in df.columns if 'Cavity' in c or 'Cav' in c]
        cav_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
        y_min, y_max = np.nanmin(all_vals) - 0.03, np.nanmax(all_vals) + 0.03
        
        c_grid = st.columns(2)
        summary_items = []
        for i, cav in enumerate(cav_cols):
            color = cav_colors[i % len(cav_colors)]
            df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
            summary_items.append(f"✅ **{cav}**: 합격률 **{((len(df)-len(df[df[f'{cav}_판정']=='NG']))/len(df))*100:.1f}%**")
            with c_grid[i % 2]:
                st.markdown(f'<div class="stBox"><b style="color:{color}; font-size:1.1em;">{cav}</b>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", dash="dash"), name="MIN"))
                fig.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", dash="dash"), name="MAX"))
                fig.add_trace(go.Bar(x=df["Point"], y=df[cav], marker_color=color, name="실측"))
                fig.update_layout(height=280, yaxis_range=[y_min, y_max], margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.subheader("🌐 통합 트렌드 분석")
        df['Avg'] = df[cav_cols].mean(axis=1)
        fig_total = go.Figure()
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="MIN", line=dict(color="blue", dash="dot")))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="MAX", line=dict(color="red", dash="dot")))
        for i, cav in enumerate(cav_cols):
            fig_total.add_trace(go.Scatter(x=df["Point"], y=df[cav], mode='markers', name=cav, marker=dict(color=cav_colors[i%len(cav_colors)], size=10)))
        fig_total.add_trace(go.Scatter(x=df["Point"], y=df['Avg'], name="전체평균", line=dict(color="black", width=3)))
        st.plotly_chart(fig_total, use_container_width=True)
        st.markdown('<div class="capture-info">📸 그래프 우측 상단 <b>카메라 아이콘</b>을 누르면 이미지가 즉시 저장됩니다.</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-card">{"<br>".join(summary_items)}</div>', unsafe_allow_html=True)
        out_cav = BytesIO(); writer = pd.ExcelWriter(out_cav, engine='xlsxwriter'); df.to_excel(writer, index=False); writer.close()
        st.download_button("📥 분석 결과 엑셀 저장", out_cav.getvalue(), "Cavity_Result.xlsx")
        st.markdown('</div>', unsafe_allow_html=True)

def run_position_analysis():
    """메뉴 3: 위치도 분석"""
    st.title("🎯 위치도 정밀 분석 (MMC)")
    def get_pos_template():
        df_pt = pd.DataFrame({"측정포인트": [1], "기본공차": [0.3], "도면치수_X": [10.0], "도면치수_Y": [10.0], "측정치_X": [10.02], "측정치_Y": [10.01], "실측지름_MMC용": [0.52]})
        out = BytesIO(); writer = pd.ExcelWriter(out, engine='xlsxwriter'); df_pt.to_excel(writer, index=False); writer.close()
        return out.getvalue()
    
    st.download_button("📄 위치도 템플릿 다운로드", get_pos_template(), "Position_Template.xlsx")
    up_pos = st.file_uploader("파일 업로드", type=["xlsx"])
    
    if up_pos:
        df_m = pd.read_excel(up_pos)
        mmc_val = st.number_input("MMC 기준값", value=0.500, format="%.3f")
        df_m['X편차'] = df_m['측정치_X'] - df_m['도면치수_X']
        df_m['Y편차'] = df_m['측정치_Y'] - df_m['도면치수_Y']
        df_m['위치도결과'] = 2 * np.sqrt(df_m['X편차']**2 + df_m['Y편차']**2)
        df_m['최종공차'] = df_m['기본공차'] + (df_m['실측지름_MMC용'] - mmc_val).clip(lower=0)
        df_m['판정'] = np.where(df_m['위치도결과'] <= df_m['최종공차'], "OK", "NG")

        st.markdown('<div class="stBox">', unsafe_allow_html=True)
        st.markdown('<div class="guide-box">🔵 <span style="color:blue">파란 점선</span>: 중심 정밀 관리 (±0.05) | 🟣 <span style="color:purple">보라 실선</span>: <b>최종 합격 공차</b> | 🔴 <span style="color:red">빨간 점선</span>: 공차 한계선</div>', unsafe_allow_html=True)
        
        fig_m = go.Figure()
        fig_m.update_yaxes(scaleanchor="x", scaleratio=1, zeroline=True, zerolinecolor='black')
        fig_m.update_xaxes(zeroline=True, zerolinecolor='black')
        max_t = df_m['최종공차'].max() / 2
        fig_m.add_shape(type="circle", x0=-0.05, y0=-0.05, x1=0.05, y1=0.05, line=dict(color="Blue", width=1, dash="dot"))
        fig_m.add_shape(type="circle", x0=-max_t, y0=-max_t, x1=max_t, y1=max_t, line=dict(color="Purple", width=3), fillcolor="rgba(147, 112, 219, 0.1)")
        fig_m.add_shape(type="circle", x0=-(max_t+0.05), y0=-(max_t+0.05), x1=(max_t+0.05), y1=(max_t+0.05), line=dict(color="Red", width=1, dash="dash"))
        for _, r in df_m.iterrows():
            p_c = '#10b981' if r['판정']=="OK" else '#ef4444'
            fig_m.add_trace(go.Scatter(x=[r['X편차']], y=[r['Y편차']], mode='markers+text', text=[f"<b>{int(r['측정포인트'])}</b>"], textposition="top center", marker=dict(size=12, color=p_c, line=dict(width=1, color='white'))))
        
        st.plotly_chart(fig_m, use_container_width=True, config={'toImageButtonOptions': {'format': 'png', 'filename': 'Position_Target', 'scale': 2}})
        st.markdown('<div class="capture-info">📸 그래프 우측 상단 <b>카메라 아이콘</b>을 누르면 고화질 PNG 이미지가 저장됩니다.</div>', unsafe_allow_html=True)
        st.subheader("📋 실측 데이터 확인")
        st.dataframe(df_m.style.map(lambda x: 'background-color: #d1fae5' if x == 'OK' else 'background-color: #fee2e2', subset=['판정']), use_container_width=True)
        
        out_pos = BytesIO(); writer = pd.ExcelWriter(out_pos, engine='xlsxwriter'); df_m.to_excel(writer, index=False); writer.close()
        st.download_button("📥 위치도 분석 결과 저장 (Excel)", out_pos.getvalue(), "Position_Analysis.xlsx")
        st.markdown('</div>', unsafe_allow_html=True)

def run_quality_calculator():
    """메뉴 4: 품질 계산기"""
    st.title("🧮 품질 종합 계산기")
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    tabs = st.tabs(["🎯 MMC 보너스", "🔧 일반 단위환산", "⚙️ 토크 변환", "⚖️ 합격 판정"])
    
    with tabs[0]:
        base_g = st.number_input("기본 기하공차", value=0.05)
        mmc_s = st.number_input("MMC 규격", value=10.00)
        act_s = st.number_input("현재 실측", value=10.02)
        st.metric("최종 공차", f"{base_g + max(0, act_s - mmc_s):.4f}")
    with tabs[1]:
        v = st.number_input("값", value=1.0)
        m = st.selectbox("종류", ["mm ➔ inch", "inch ➔ mm"])
        st.success(f"결과: {v/25.4:.4f}" if "inch" in m[:4] else f"결과: {v*25.4:.4f}")
    with tabs[2]:
        t_v = st.number_input("토크 값 입력", value=1.0)
        t_m = st.selectbox("단위", ["N·m ➔ kgf·m", "kgf·m ➔ N·m", "N·m ➔ kgf·cm", "kgf·cm ➔ N·m"])
        res = t_v * 0.10197 if "kgf·m" in t_m else (t_v * 9.80665 if "N·m" in t_m and "kgf·m" in t_m[:5] else (t_v * 10.197 if "kgf·cm" in t_m else t_v * 0.09806))
        st.info(f"변환 결과: {res:.4f}")
    with tabs[3]:
        spec = st.number_input("기준")
        u, l = st.number_input("상한"), st.number_input("하한")
        m_v = st.number_input("측정")
        if (spec+l) <= m_v <= (spec+u): st.success("✅ 합격")
        else: st.error("🚨 불합격")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 3. 메인 프로그램 제어 (Main Loop)
# ==========================================
def main():
    set_global_style()
    
    if 'reset_key' not in st.session_state: st.session_state.reset_key = 0
    
    st.sidebar.title("💎 품질 플랫폼 v9.5")
    menu = st.sidebar.radio("📋 업무 선택", 
                            ["🔄 데이터 변환기", "📈 멀티 캐비티 분석", "🎯 위치도(MMC) 분석", "🧮 품질 계산기"], 
                            key=f"m_{st.session_state.reset_key}")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🧹 모든 데이터 초기화"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.session_state.reset_key += 1
        st.rerun()

    # 메뉴 선택에 따른 함수 실행
    if menu == "🔄 데이터 변환기":
        run_data_converter()
    elif menu == "📈 멀티 캐비티 분석":
        run_cavity_analysis()
    elif menu == "🎯 위치도(MMC) 분석":
        run_position_analysis()
    elif menu == "🧮 품질 계산기":
        run_quality_calculator()

if __name__ == "__main__":
    main()
