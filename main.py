import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from io import BytesIO

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="품질 통합 분석 시스템", layout="wide")

# 스타일 설정 (시각적 피드백 강화)
st.markdown("""
    <style>
    .stBox { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .summary-card { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; border-top: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); margin-bottom: 10px; text-align: center;
    }
    .ng-text { color: #e11d48; font-weight: bold; font-size: 1.1em; }
    .ok-text { color: #10b981; font-weight: bold; }
    .cav-label { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; display: block; }
    </style>
""", unsafe_allow_html=True)

# 나중에 통합을 위해 사이드바가 아닌 본문에 배치 (원하시는 대로 수정 가능)
st.title("📊 핀 높이 멀티 캐비티 품질 분석")

# --- [구조화] 데이터 입력 섹션 (나중에 이 부분만 메뉴별로 분기 가능) ---
with st.expander("📂 데이터 업로드 및 템플릿", expanded=True):
    col_file, col_temp = st.columns([3, 1])
    with col_file:
        uploaded_file = st.file_uploader("분석 파일을 선택하세요 (XLSX, CSV)", type=["xlsx", "csv"])
    with col_temp:
        # 가상의 템플릿 생성 로직 (생략 가능)
        st.write("") 

if uploaded_file:
    # 데이터 로드
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    cav_cols = [c for c in df.columns if 'Cavity' in c]
    
    # 캐비티별 고유 색상 정의 (시각적으로 확연히 구분되는 고대비 색상)
    # Cav 1: Blue, Cav 2: Orange, Cav 3: Green, Cav 4: Purple
    cav_colors = {
        'Cavity_1': '#1f77b4', # 강한 블루
        'Cavity_2': '#ff7f0e', # 강한 오렌지
        'Cavity_3': '#2ca02c', # 강한 그린
        'Cavity_4': '#9467bd', # 강한 퍼플
        'Default': '#7f7f7f'
    }

    # --- 2. 전 캐비티 통합 분석 (Scatter 전용) ---
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    st.subheader("🌐 전 캐비티 통합 산포도 (경향성 비교)")
    
    fig_total = go.Figure()
    
    # SPEC 라인 (점선)
    fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], name="SPEC MIN", line=dict(color="#2563eb", width=1.5, dash="dash")))
    fig_total.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], name="SPEC MAX", line=dict(color="#dc2626", width=1.5, dash="dash")))
    
    for cav in cav_cols:
        # 판정 로직 적용
        df[f"{cav}_판정"] = df.apply(lambda x: "OK" if x["SPEC_MIN"] <= x[cav] <= x["SPEC_MAX"] else "NG", axis=1)
        color = cav_colors.get(cav, cav_colors['Default'])
        
        # 전체 점 (선 없이 점만)
        fig_total.add_trace(go.Scatter(
            x=df["Point"], y=df[cav], name=cav,
            mode='markers', marker=dict(size=9, color=color, opacity=0.7),
            hovertemplate=f"<b>{cav}</b><br>Point: %{{x}}<br>Value: %{{y}}<extra></extra>"
        ))
        
        # NG 지점 강조 (빨간 테두리 추가)
        ng_df = df[df[f"{cav}_판정"] == "NG"]
        if not ng_df.empty:
            fig_total.add_trace(go.Scatter(
                x=ng_df["Point"], y=ng_df[cav], name=f"{cav} NG",
                mode='markers', marker=dict(size=12, color='rgba(0,0,0,0)', line=dict(width=2, color='red'), symbol='circle'),
                showlegend=False, hoverinfo='skip'
            ))

    all_vals = df[cav_cols + ["SPEC_MIN", "SPEC_MAX"]].values.flatten()
    fig_total.update_layout(
        yaxis_range=[all_vals.min() - 0.05, all_vals.max() + 0.05],
        height=550, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(240,240,240,0.5)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_total, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. 캐비티별 상세 그래프 복구 (2열 배치) ---
    st.subheader("🔍 캐비티별 상세 분석 (개별 확인)")
    cav_grids = st.columns(2)
    
    summary_data = [] # 요약용 데이터 수집

    for i, cav in enumerate(cav_cols):
        with cav_grids[i % 2]:
            st.markdown('<div class="stBox">', unsafe_allow_html=True)
            color = cav_colors.get(cav, cav_colors['Default'])
            
            # 개별 그래프 생성 (막대 + SPEC 라인)
            fig_ind = go.Figure()
            fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MIN"], line=dict(color="blue", width=1), showlegend=False))
            fig_ind.add_trace(go.Scatter(x=df["Point"], y=df["SPEC_MAX"], line=dict(color="red", width=1), showlegend=False))
            
            # 측정값 (NG는 빨간색, OK는 해당 캐비티 고유색)
            bar_colors = ['#ef4444' if p == "NG" else color for p in df[f"{cav}_판정"]]
            fig_ind.add_trace(go.Bar(x=df["Point"], y=df[cav], name=cav, marker_color=bar_colors))
            
            fig_ind.update_layout(title=f"<b>{cav} 상세 데이터</b>", yaxis_range=[all_vals.min()-0.05, all_vals.max()+0.05], height=350, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_ind, use_container_width=True)
            
            # 통계 데이터 계산
            total_cnt = len(df)
            ng_cnt = len(df[df[f"{cav}_판정"] == "NG"])
            summary_data.append({"cav": cav, "total": total_cnt, "ng": ng_cnt, "rate": ((total_cnt-ng_cnt)/total_cnt)*100})
            st.markdown('</div>', unsafe_allow_html=True)

    # --- 4. 하단 요약 브리핑 ---
    st.markdown("### 📋 품질 분석 최종 요약")
    s_cols = st.columns(len(summary_data))
    for i, s in enumerate(summary_data):
        with s_cols[i]:
            st.markdown(f"""
                <div class="summary-card">
                    <span class="cav-label">{s['cav']}</span>
                    <hr style='margin:10px 0;'>
                    <p style='margin:5px 0;'>합격률: <span class="{'ok-text' if s['rate']==100 else 'ng-text'}">{s['rate']:.1f}%</span></p>
                    <p style='margin:0;'>불량: <span class="ng-text">{s['ng']}</span> / {s['total']} EA</p>
                </div>
            """, unsafe_allow_html=True)

    # 텍스트 리포트
    st.markdown('<div class="stBox">', unsafe_allow_html=True)
    ng_total = sum(d['ng'] for d in summary_data)
    if ng_total > 0:
        st.error(f"🚨 **전체 캐비티에서 총 {ng_total}개의 규격 이탈이 발견되었습니다.**")
        for s in summary_data:
            if s['ng'] > 0:
                ng_list = df[df[f"{s['cav']}_판정"] == "NG"]["Point"].tolist()
                st.write(f"👉 **{s['cav']}**: 포인트 {ng_list}번 확인 요망")
    else:
        st.success("✅ **모든 캐비티가 합격권입니다.**")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("📊 위 섹션에서 데이터를 업로드하면 분석이 시작됩니다.")
