import streamlit as st
import streamlit_authenticator as stauth


def loginForm(names, usernames, passwords):
    authenticator = stauth.Authenticate(
        names, usernames, passwords, 'LaguzPricingCookie', 'LaguzPricingSignatureKey', cookie_expiry_days=0
    )
    name, authentication_status, username = authenticator.login('Login', 'main')
    return authenticator, name, authentication_status, username
