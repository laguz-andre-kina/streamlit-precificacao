from sqlalchemy import create_engine
import datetime as dt

import sqlalchemy
import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

from utils.functions import *

st.set_page_config(layout="wide")

# def applyStyling():
#     style = """
#     <style>
#     #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(3) > div {
#     border: 0.5px solid;
#     padding: 50px;
#     overflow: hidden;
#     }
#     </style>
#     """
#     st.markdown(style, unsafe_allow_html=True)

# applyStyling()


# Open connection to db
cnn = createConnection()

# Get entities and create form for queue
entitiesDf = getEntities(cnn)

###################### FILTERS ######################
with st.container():
    st.header('Filtros')

    filterCol1, filterCol2, filterCol3 = st.columns(3)
    with filterCol1:
        typeEnt = st.radio('Tipo do Ente', options=entitiesDf['entitytype'].drop_duplicates().sort_values(), index=0)
        
    with filterCol2:
        _ufOptions = ufOptions(entitiesDf, typeEnt)
        uf = st.selectbox('UF', options=_ufOptions, index=0)
        
    with filterCol3:
        _courtNameOptions = courtNameOptions(entitiesDf, typeEnt, uf)
        courtname = st.selectbox('Corte', options=_courtNameOptions, index=0)

    _entitiesOptions = entitiesOptions(entitiesDf, typeEnt, uf, courtname)
    entityname = st.selectbox('Entity', options=_entitiesOptions, index=0)


# Id to query and collect dataframes
entityId = getEntityId(entitiesDf, typeEnt, uf, courtname, entityname)

queueDf = getQueue(entityId, cnn)
entityMapDf = getEntityMap(entityId, cnn)
entityRegimeDf = getEntityRegime(entityId, cnn)
entityStatsDf = getEntityStats(entityId, cnn)
entityPlanDf = getEntityPlan(entityId, cnn)

# Show grid
with st.container():
    st.header('KPIs e Analytics')

    # KPIs
    metricCol1, metricCol2, metricCol3, metricCol4 = st.columns(4)
    with metricCol1:
        totalAmount = f"{np.sum(queueDf['value'])/B_TIMES:.2f} Bi"
        st.metric(label='Montante Total', value=totalAmount)

    with metricCol2:
        if not entityRegimeDf.empty:
            entityRegime = entityRegimeDf['regime'].iloc[0]
            st.metric(label='Regime do Ente', value=entityRegime)

    with metricCol3:
        if not entityStatsDf.empty:
            entityRCL = f"{entityStatsDf['valor'].iloc[0]/B_TIMES:.2f} Bi"
            st.metric(label='RCL do Ente', value=entityRCL)

    with metricCol4:
        if not entityPlanDf.empty:
            paymentExpectation = f"{(entityPlanDf['amt'] * entityPlanDf['amtperiodeq']).iloc[0]/B_TIMES:.2f} Bi"
            st.metric(label='Expectativa de Pagamento', value=paymentExpectation)

    # Charts
    queueChartCol1, queueChartCol2 = st.columns(2)
    with queueChartCol1:
        stackedConsBarChart = consolidatedAmountYearBarChart(queueDf)
        st.plotly_chart(stackedConsBarChart, use_container_width=True)

    with queueChartCol2:
        entityMapPaymentsBarChart = entityMapPaymentsBarChart(entityMapDf)
        st.plotly_chart(entityMapPaymentsBarChart, use_container_width=True)

    queueChartCol3, queueChartCol4 = st.columns(2)
    with queueChartCol3:
        scatterMapAmountChart = entityScatterPlot(queueDf)
        st.plotly_chart(scatterMapAmountChart, use_container_width=True)

    with queueChartCol4:
        countPieChart = entityCountPieChart(queueDf)
        st.plotly_chart(countPieChart, use_container_width=True)

with st.container():
    st.header('Fila de Precatórios')

    gb = GridOptionsBuilder.from_dataframe(queueDf)
    gb.configure_pagination()
    gb.configure_selection(
        selection_mode='single',
        use_checkbox=True,
    )
    gridOptions = gb.build()
    dataQueue = AgGrid(
        queueDf,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        allow_unsafe_jscode=True,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
    )

    selectedItem = dataQueue['selected_rows']

# Show item data
# TODO: Might change to return None if __name__
if bool(selectedItem):

    selectedItem = selectedItem[0]
    with st.container():
        st.header('KPIs do Precatório Selecionado')

        creditKPICol1, creditKPICol2, creditKPICol3, creditKPICol4, creditKPICol5 = st.columns(5)

        with creditKPICol1:
            position = selectedItem['queueposition']
            st.metric(label='Posição', value=position)

        with creditKPICol2:
            amountBeforeCredit = f"{queueDf.loc[queueDf['queueposition']<selectedItem['queueposition'], 'value'].sum()/M_TIMES:.2f}"
            st.metric(label='Montante à Frente (MM)', value=amountBeforeCredit)

        with creditKPICol3:
            budgetYear = selectedItem['budgetyear']
            st.metric(label='Ano de Orçamento', value=budgetYear)

        with creditKPICol4:
            creditType = selectedItem['type']
            st.metric(label='Tipo de Precatório', value=creditType)

        with creditKPICol5:
            creditAmount = selectedItem['value']
            st.metric(label='Montante do Crédito (MM)', value=f'{creditAmount/M_TIMES:.2f}')

