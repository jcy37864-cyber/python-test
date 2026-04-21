def set_style():
    st.markdown("""
        <style>
        /* ───────── 사이드바 ───────── */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }

        /* ───────── 본문 텍스트 ───────── */
        div:not([data-testid="stSidebar"]) label {
            color: #111 !important;
            font-weight: 600;
        }

        div:not([data-testid="stSidebar"]) p,
        div:not([data-testid="stSidebar"]) span,
        div:not([data-testid="stSidebar"]) li {
            color: #222 !important;
        }

        /* 🔥 caption (설명글) */
        div:not([data-testid="stSidebar"]) .stCaption {
            color: #444 !important;
            font-size: 0.9rem;
        }

        /* 🔥 markdown 블록 (코드 설명 포함) */
        div:not([data-testid="stSidebar"]) .stMarkdown {
            color: #222 !important;
        }

        /* ───────── 입력창 ───────── */
        div:not([data-testid="stSidebar"]) input,
        div:not([data-testid="stSidebar"]) textarea {
            color: #111 !important;
            background-color: #ffffff !important;
        }

        .stNumberInput input {
            color: #111 !important;
            background-color: #ffffff !important;
        }

        /* ───────── 버튼 ───────── */
        .stButton > button {
            background-color: #ef4444 !important;
            color: white !important;
            font-weight: bold !important;
            width: 100%;
            border-radius: 8px;
            height: 3em;
        }

        /* ───────── NG 박스 ───────── */
        .ng-box {
            height: 200px;
            overflow-y: auto;
            border: 2px solid #ff0000;
            padding: 15px;
            border-radius: 8px;
            background-color: #fff5f5;
        }

        /* ───────── OK 박스 ───────── */
        .ok-box {
            padding: 12px;
            border-radius: 8px;
            background-color: #e8f5e9;
            color: #2e7d32;
            font-weight: bold;
            text-align: center;
            font-size: 1.1em;
        }

        /* ───────── 리포트 카드 ───────── */
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
