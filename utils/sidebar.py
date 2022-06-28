import streamlit as st
from streamlit_option_menu import option_menu


def sidebar():
    with st.sidebar:
        sidebarSelection = option_menu(
            None,
            ['Pricing', 'Logout'],
            icons=['robot', 'power'],
            menu_icon='cast',
            default_index=0,
            orientation='vertical',
        )
    return sidebarSelection
