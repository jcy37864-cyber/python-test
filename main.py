# --- 3. 통합 과녁 그래프 (손그림 디자인 구현 및 문법 오류 수정) ---
st.markdown('<div class="stBox">', unsafe_allow_html=True)
st.subheader("🌐 전 캐비티 통합 위치 편차 분포 (v2.1)")

fig_target = go.Figure()

# 중심 십자선 (X, Y축)
fig_target.add_vline(x=0, line_width=1, line_color="black")
fig_target.add_hline(y=0, line_width=1, line_color="black")

# 1. 파란색 원 (기본 공차 ø0.3)
fig_target.add_shape(type="circle", x0=-0.15, y0=-0.15, x1=0.15, y1=0.15, 
                     line=dict(color="blue", width=2), name="Base Tol")

# 2. 보라색 영역 (MMC 보너스 포함 최종 한계선)
# 예시로 가장 큰 공차를 가진 포인트를 기준으로 시각화
max_final_tol = df_edit['Final_Tolerance'].max()
fig_target.add_shape(type="circle", x0=-max_final_tol/2, y0=-max_final_tol/2, x1=max_final_tol/2, y1=max_final_tol/2, 
                     line=dict(color="purple", width=2), fillcolor="rgba(148, 103, 189, 0.1)")

# 3. 빨간색 원 (경고선 - 공차의 1.2배 지점 등 시각적 기준)
danger_zone = max_final_tol * 0.6 
fig_target.add_shape(type="circle", x0=-danger_zone, y0=-danger_zone, x1=danger_zone, y1=danger_zone, 
                     line=dict(color="red", width=1, dash="dot"))

# --- 포인트 찍기 (오류 수정 지점) ---
for i, row in df_edit.iterrows():
    # NG인 경우 테두리를 빨간색으로, OK인 경우 초록색으로
    p_color = '#ef4444' if row['Status'] == "NG" else '#10b981'
    
    fig_target.add_trace(go.Scatter(
        x=[row['Dev_X']], 
        y=[row['Dev_Y']], 
        name=row['Point'],
        mode='markers+text',
        text=[row['Point']], 
        textposition="top center",
        marker=dict(
            size=12, 
            color=p_color, 
            symbol='circle',
            line=dict(width=2, color='white') # 점의 테두리
        ), # <--- 쉼표 확인
        hovertemplate=(
            f"<b>Point: {row['Point']}</b><br>" +
            f"X 편차: {row['Dev_X']:.3f}<br>" +
            f"Y 편차: {row['Dev_Y']:.3f}<br>" +
            f"위치도: {row['Actual_Position']:.3f}<br>" +
            f"상태: {row['Status']}<extra></extra>"
        )
    ))

fig_target.update_layout(
    xaxis=dict(title="X 편차 (mm)", range=[-0.3, 0.3], gridcolor='#f0f0f0'),
    yaxis=dict(title="Y 편차 (mm)", range=[-0.3, 0.3], gridcolor='#f0f0f0', scaleanchor="x", scaleratio=1),
    width=700, 
    height=700, 
    showlegend=True,
    plot_bgcolor='white'
)

st.plotly_chart(fig_target, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
