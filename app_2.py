from click import option
import streamlit as st

from utils.computations import *
from utils.functions import *
from utils.constants import *

st.set_page_config(layout="wide")

st.title('Calculadora Earn-out')

optionsCols = st.columns(4)

with optionsCols[0]:
    durationYearEq = st.number_input(label='Duration (Anos)', min_value=0.00, max_value=8.00, step=0.10, value=2.00)
    tradedValue = st.number_input(label='Valor Negociado (%)', min_value=0.00, max_value=100.00, step=0.50, value=40.00)

with optionsCols[1]:
    currentValue = st.number_input(label='Valor Atual (%)', min_value=0.00, max_value=100.00, step=0.50, value=100.00)
    interestRate = st.number_input(label='Selic (%)', min_value=0.00, max_value=20.00, step=0.10, value=8.00)
    inflationRate = st.number_input(label='IPCA-E (%)', min_value=0.00, max_value=20.00, step=0.10, value=5.00)

with optionsCols[2]:
    preMocPeriodYearEq = st.number_input(label='Período Pré-MOC (Anos)', min_value=0.00, max_value=12.00, step=0.10, value=0.00)
    gracePeriodYearEq = st.number_input(label='Período da Graça (Anos)', min_value=0.00, max_value=12.00, step=0.10, value=0.00)

with optionsCols[3]:
    hairCutAuction = st.number_input(label='Haircut (%)', min_value=0.00, max_value=100.00, step=0.50, value=0.00)
    earnout = st.number_input(label='Earn-out (%)', min_value=0.00, max_value=100.00, step=0.50, value=0.00)
    pctInterestTradedValue = st.number_input(label='Valor Negociado de Juros (%)', min_value=0.00, max_value=100.00, step=0.50, value=0.00)

calcValue = calculateFutureValueEarnout(
    durationYearEq=durationYearEq,
    tradedValue=tradedValue/100,
    currentValue=currentValue,
    interestRate=interestRate/100,
    inflationRate=inflationRate/100,
    preMocPeriodYearEq=preMocPeriodYearEq,
    gracePeriodYearEq=gracePeriodYearEq,
    hairCutAuction=hairCutAuction/100,
    earnout=earnout/100,
    pctInterestTradedValue=pctInterestTradedValue,
)

responseCols = st.columns([2, 4, 2])
with responseCols[1]:
    st.subheader(body=f'Valor de Earn-out: {calcValue:,.2f}%')

plotlyChart = calculateFutureValueEarnoutPlot(
    tradedValue=tradedValue/100,
    currentValue=currentValue,
    interestRate=interestRate/100,
    inflationRate=inflationRate/100,
    preMocPeriodYearEq=preMocPeriodYearEq,
    gracePeriodYearEq=gracePeriodYearEq,
    hairCutAuction=hairCutAuction/100,
    earnout=earnout/100,
    pctInterestTradedValue=pctInterestTradedValue,
)

st.plotly_chart(plotlyChart, use_container_width=True)