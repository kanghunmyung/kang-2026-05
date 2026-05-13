import os
import streamlit as st


def get_google_api_key():
    try:
        return (
            os.getenv("GOOGLE_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or st.secrets.get("GOOGLE_API_KEY")
            or st.secrets.get("GEMINI_API_KEY")
        )
    except Exception:
        return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


api_key = get_google_api_key()

if api_key:
    st.success("Google/Gemini API 키가 정상적으로 설정되었습니다.")
else:
    st.warning("GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다.")
