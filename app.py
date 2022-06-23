import numbers
from operator import sub
from tokenize import Number
import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

from utils.functions import *
from utils.constants import *
from utils.computations import *

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

###################### HEADER ######################
header()

###################### FILTERS ######################
with st.expander(label='', expanded=True):
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
entityDealDf = getEntityDeal(entityId, cnn)
entityMapDf = getEntityMap(entityId, cnn)
entityRegimeDf = getEntityRegime(entityId, cnn)
entityStatsDf = getEntityStats(entityId, cnn)
entityPlanDf = getEntityPlan(entityId, cnn)

totalQueueAmount = np.sum(queueDf['value'])

# TODO: Possibily think of better logic for creating KPIs cols (encapsulate into a dict maybe)
entityHasDealRecord = entityHasDeal = entityAuctionPrct = entityNoticesCount = entityDealPaymentWaitYears = entityDealAvgAmount = entityDealTerms = entityDealFrequency = False
# If entity has deal add a column
if not entityDealDf.empty:
    entityHasDealRecord = True
    entityHasDeal = entityDealDf['acordo'].iloc[0] if not isinstance(entityDealDf['acordo'].iloc[0], type(None)) else ''
    entityAuctionPrct = entityDealDf['pctdesagiomax'].iloc[0] if not isinstance(entityDealDf['pctdesagiomax'].iloc[0], type(None)) else ''
    entityNoticesCount = entityDealDf['contagemeditais'].iloc[0] if not isinstance(entityDealDf['contagemeditais'].iloc[0], type(None)) else 0
    entityDealPaymentWaitYears = float(entityDealDf['prazoesperadoparapagamento'].iloc[0]) if not isinstance(entityDealDf['prazoesperadoparapagamento'].iloc[0], type(None)) else 2.0
    entityDealAvgAmount = entityDealDf['montantemedioderecursosporedital'].iloc[0] if not isinstance(entityDealDf['montantemedioderecursosporedital'].iloc[0], type(None)) else 0
    entityDealTerms = entityDealDf['termosacordo'].iloc[0] if not isinstance(entityDealDf['termosacordo'].iloc[0], type(None)) else False

    entityDealFrequency = entityDealDf['dealfrequencia'].iloc[0] if not isinstance(entityDealDf['dealfrequencia'].iloc[0], type(None)) else ''

# Show grid
with st.expander(label='', expanded=True):
    # entityNoticesCount > 0
    if bool(entityDealTerms):
        st.header('KPIs do Acordo')
        dealKPIsCols = st.columns(5)

        with dealKPIsCols[0]:
            translateBoolDeal = TRANSLATE_BOOL_DICT[entityHasDeal]
            st.metric(label='Faz acordo ?', value=translateBoolDeal)

        with dealKPIsCols[1]:
            st.metric(label='N° Editais', value=entityNoticesCount)

        with dealKPIsCols[2]:
            st.metric(label='Prazo Est. Pgto. (Anos)', value=entityDealPaymentWaitYears)

        with dealKPIsCols[3]:
            st.metric(label='Montante Prev. Edital (MM)', value=f'{entityDealAvgAmount/M_TIMES:.2f}')

        with dealKPIsCols[4]:
            st.metric(label='Frequência Editais', value=entityDealFrequency)

        st.write(entityDealDf['termosacordo'].iloc[0]['texto'])

with st.expander(label='', expanded=True):
    st.header('KPIs e Analytics')

    # KPIs
    entityKPIListCols = st.columns(5)
    with entityKPIListCols[0]:
        queueRefdate = queueDf['refdate'].iloc[0].strftime('%d/%m/%Y')
        st.metric(label='Data Atualização Fila', value=queueRefdate)

    with entityKPIListCols[1]:
        totalAmount = f"{totalQueueAmount/B_TIMES:.2f} Bi"
        st.metric(label='Montante Total', value=totalAmount)

    with entityKPIListCols[2]:
        if not entityRegimeDf.empty:
            entityRegime = entityRegimeDf['regime'].iloc[0]
            st.metric(label='Regime do Ente', value=entityRegime)

    with entityKPIListCols[3]:
        exercEntityRCL = entityStatsDf['exercicio'].iloc[0] if not entityStatsDf.empty else '-'
        entityRCL = f"{entityStatsDf['valor'].iloc[0]/B_TIMES:.2f} Bi" if not entityStatsDf.empty else '-'
        st.metric(label=f'RCL do Ente (Ano: {exercEntityRCL})', value=entityRCL)

    with entityKPIListCols[4]:
        exercPaymentExpectation = entityPlanDf['exercicio'].iloc[0] if not entityPlanDf.empty else '-'
        paymentExpectation = (entityPlanDf['amt'] * entityPlanDf['amtperiodeq']).iloc[0] if not entityPlanDf.empty else '-'
        paymentExpectationStr = f"{paymentExpectation/B_TIMES:.2f} Bi" if not entityPlanDf.empty else '-'
        st.metric(label=f'Expect. de Pagto. (Ano: {exercPaymentExpectation})', value=paymentExpectationStr)

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
    amountToPayCreditPosition = queueDf.loc[queueDf['queueposition']<=selectedItem['queueposition'], 'value'].sum()

    with st.expander(label='', expanded=True):
        st.header('KPIs do Precatório Selecionado')

        creditKPICols = st.columns(6)

        with creditKPICols[0]:
            position = selectedItem['queueposition']
            st.metric(label='Posição', value=position)

        with creditKPICols[1]:
            amountToPayCreditPositionStr = f"{amountToPayCreditPosition/M_TIMES:.2f}"
            st.metric(label='Montante p/ Pagar Crédito (MM)', value=amountToPayCreditPositionStr)

        with creditKPICols[2]:
            st.metric(label='Prct. Fila p/ Pagar Crédito (%)', value=f'{amountToPayCreditPosition/totalQueueAmount*100:.2f}')

        with creditKPICols[3]:
            budgetYear = selectedItem['budgetyear']
            st.metric(label='Ano de Orçamento', value=budgetYear)

        with creditKPICols[4]:
            creditType = selectedItem['type']
            st.metric(label='Tipo de Precatório', value=creditType)

        with creditKPICols[5]:
            creditAmount = selectedItem['value']
            st.metric(label='Montante do Crédito (MM)', value=f'{creditAmount/M_TIMES:.2f}')

    # Pricing inputs
    with st.form('selectedCreditForm'):
        st.header('Parâmetros p/ Precificação')

        pricingOptionsCols = st.columns([4, 2, 2, 2, 2])

        with pricingOptionsCols[0]:
            dtPricing = st.date_input(label='Data de Precificação',
                value=TD_DATE,
                min_value=MIN_DATE,
                max_value=MAX_DATE)

            adjQueueAmount = st.number_input(
                label='Montante p/ Ajustar Fila (MM)',
                min_value=0.00,
                max_value=None,
                value=0.00,
                step=1.00
            )

        with pricingOptionsCols[1]:
            inputPrctSplit = st.number_input(label='Dividir Fila p/ Edital (%)', value=50.0 if entityRegime=='ESPECIAL' else 0.0, step=1.0)
            inputPrctAuction = st.number_input(label='Deságio em Acordo (%)', value=float(entityAuctionPrct*100) if isinstance(entityAuctionPrct, numbers.Number) else 40.0, step=1.0)

        with pricingOptionsCols[2]:
            dealIrr = st.slider(
                label='TIR p/ Acordo (%)',
                min_value=0.0,
                max_value=100.0,
                value=35.0,
                step=1.0
            )
            dealDuration = st.slider(
                label='Duration p/ Acordo (Anos)',
                min_value=0.0,
                max_value=10.0,
                value=entityDealPaymentWaitYears if entityDealPaymentWaitYears != False else 2.0,
                step=0.5
            )

        with pricingOptionsCols[3]:
            sliderInterestRate = st.slider(
                'Selic (%)',
                min_value=2.0,
                max_value=20.0,
                value=8.0,
                step=0.1,
                key='sliderInterestRate',
            )
            sliderInflation = st.slider(
                'IPCA-E (%)',
                min_value=2.0,
                max_value=20.0,
                value=5.0,
                step=0.1,
                key='sliderInflation',
            )

        with pricingOptionsCols[4]:
            inputGracePeriodYearsEq = st.slider(
                'Período da Graça (Years)',
                min_value=0.0,
                max_value=2.0,
                value=0.0,
                step=0.1,
                key='inputGracePeriodYearsEq',
            )
            inputPreMocPeriodYearsEq = st.slider(
                'Período pré-MOC (Years)',
                min_value=0.0,
                max_value=2.0,
                value=0.0,
                step=0.1,
                key='inputPreMocPeriodYearsEq',
            )

        submitPricingButton = st.form_submit_button(label='Precificar')

# On click run calculations
if bool(selectedItem) and submitPricingButton:
    with st.expander(label='', expanded=True):
        rangeEOY = createRangeEOYs(START_YEAR, END_YEAR)
        dfDataCurvesIPCAEInterest = curvesIPCAEAndInterest(START_YEAR, END_YEAR)

        dfAmortizationSchedule = amortizationSchedule(
            dfDataCurvesIPCAEInterest, paymentExpectation, 1.0, inputPrctSplit / 100
        )

        ########################### PRICING ###########################
        # Pricing for deal
        # st.write(dealIrr, dealDuration, 100.0, )

        priceDeal = calculateTradePriceGivenIRR(
            expectedIRR=dealIrr / 100,
            durationYearEq=dealDuration,
            currentValue=100.0,
            interestRate=sliderInterestRate / 100.0,
            inflationRate=sliderInflation / 100.0,
            preMocPeriodYearEq=inputPreMocPeriodYearsEq,
            gracePeriodYearEq=inputGracePeriodYearsEq,
            hairCutAuction=inputPrctAuction / 100.0
        )

        # Pricing for hold
        durationBase = round(getDuration(
            dtPricing.strftime('%Y-%m-%d'),
            dfAmortizationSchedule,
            amountToPayCreditPosition - adjQueueAmount,
        ), 2)

        pxCurveBase = getInterpolIRRAndPx(durationBase)
        pxBase = round(pxCurveBase['interpolPx'], 2)
        irrBase = round(pxCurveBase['interpolIRR'] * 100, 2)
        priceBase = round(calculateTradePriceGivenIRR(
                        expectedIRR=(irrBase / 100),
                        durationYearEq=durationBase,
                        interestRate=sliderInterestRate / 100.0,
                        inflationRate=sliderInflation / 100.0,
                        preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                        gracePeriodYearEq=inputGracePeriodYearsEq,
                        ), 2)

        # Adjusted Duration
        durationAdj = round(getDurationAdj(durationBase), 2)
        pxCurveAdj = getInterpolIRRAndPx(durationAdj)
        pxAdj = round(pxCurveAdj['interpolPx'], 2)
        irrAdj = round(pxCurveAdj['interpolIRR'] * 100, 2)
        priceAdj = round(calculateTradePriceGivenIRR(
                        expectedIRR=(irrAdj / 100),
                        durationYearEq=durationAdj,
                        interestRate=sliderInterestRate / 100.0,
                        inflationRate=sliderInflation / 100.0,
                        preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                        gracePeriodYearEq=inputGracePeriodYearsEq,
                        ), 2)

        # Worst Duration
        durationWorstCase = round(getDurationAdj(durationAdj), 2)
        pxCurveWorstCase = getInterpolIRRAndPx(durationWorstCase)
        pxWorstCase = round(pxCurveWorstCase['interpolPx'], 2)
        irrWorstCase = round(pxCurveWorstCase['interpolIRR'] * 100, 2)
        priceWorstCase =  round(calculateTradePriceGivenIRR(
                                expectedIRR=(irrWorstCase / 100),
                                durationYearEq=durationWorstCase,
                                interestRate=sliderInterestRate / 100.0,
                                inflationRate=sliderInflation / 100.0,
                                preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                                gracePeriodYearEq=inputGracePeriodYearsEq,
                                ), 2)

        pricingCols = st.columns(4)

        with pricingCols[0]:
            st.metric(label='Duration Acordo (Anos)', value=dealDuration)
            st.metric(label='Preço Acordo (%)', value=round(priceDeal, 2))
            st.metric(label='TIR Acordo (%)', value=dealIrr)

        with pricingCols[1]:
            st.metric(label='Duration Best Case (Anos)', value=durationBase)
            st.metric(label='Preço Best Case (%)', value=priceBase)
            st.metric(label='TIR Best Case (%)', value=irrBase)

        with pricingCols[2]:
            st.metric(label='Duration c/ Ajuste (Anos)', value=durationAdj)
            st.metric(label='Preço c/ Ajuste (%)', value=priceAdj)
            st.metric(label='TIR c/ Ajuste (%)', value=irrAdj)

        with pricingCols[3]:
                st.metric(label='Duration Pior Cenário (Anos)', value=durationWorstCase)
                st.metric(label='Preço Pior Cenário (%)', value=priceWorstCase)
                st.metric(label='TIR Pior Cenário (%)', value=irrWorstCase)

        dursToPlot = [dealDuration, durationBase, durationAdj, durationWorstCase]
        pricesToPlot = [priceDeal, priceBase, priceAdj, priceWorstCase]

        pricesByDurPlot = priceByDurationBarChart(dursToPlot, pricesToPlot)
        st.plotly_chart(pricesByDurPlot, use_container_width=True)