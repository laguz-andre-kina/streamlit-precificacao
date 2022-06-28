import numbers
import streamlit as st
import numpy as np

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

from fpdf import FPDF
import base64

from utils.functions import *
from utils.constants import *
from utils.computations import *
from utils.sidebar import *
from utils.login import *
from utils.user import *

st.set_page_config(layout="wide")


def applyStyling():
    style = """
    <style>
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div.css-ocx5ag.epcbefy1 > div:nth-child(1) > div > div:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div > div > div > div {
    flex-direction: row;
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)


applyStyling()


def create_download_link(val, filename):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'


names, usernames, passwords = getUsers()
authenticator, name, authentication_status, username = loginForm(names, usernames, passwords)

if authentication_status:
    sidebarSelection = sidebar()
    if sidebarSelection == 'Pricing':
        with st.container():
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
                    typeEnt = st.radio(
                        'Tipo do Ente', options=entitiesDf['entitytype'].drop_duplicates().sort_values(), index=0
                    )

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
            entityHasDealRecord = (
                entityHasDeal
            ) = (
                entityAuctionPrct
            ) = (
                entityNoticesCount
            ) = entityDealPaymentWaitYears = entityDealAvgAmount = entityDealTerms = entityDealFrequency = False
            # If entity has deal add a column
            if not entityDealDf.empty:
                entityHasDealRecord = True
                entityHasDeal = (
                    entityDealDf['acordo'].iloc[0]
                    if not isinstance(entityDealDf['acordo'].iloc[0], type(None))
                    else '-'
                )
                entityAuctionPrct = (
                    entityDealDf['pctdesagiomax'].iloc[0]
                    if not isinstance(entityDealDf['pctdesagiomax'].iloc[0], type(None))
                    else '-'
                )
                entityNoticesCount = (
                    entityDealDf['contagemeditais'].iloc[0]
                    if not isinstance(entityDealDf['contagemeditais'].iloc[0], type(None))
                    else 0
                )
                entityDealPaymentWaitYears = (
                    float(entityDealDf['prazoesperadoparapagamento'].iloc[0])
                    if not isinstance(entityDealDf['prazoesperadoparapagamento'].iloc[0], type(None))
                    else 0.0
                )
                entityDealAvgAmount = (
                    entityDealDf['montantemedioderecursosporedital'].iloc[0]
                    if not isinstance(entityDealDf['montantemedioderecursosporedital'].iloc[0], type(None))
                    else 0
                )
                entityDealTerms = (
                    entityDealDf['termosacordo'].iloc[0]['texto']
                    if not isinstance(entityDealDf['termosacordo'].iloc[0], type(None))
                    else '-'
                )

                entityDealFrequency = (
                    entityDealDf['dealfrequencia'].iloc[0]
                    if not isinstance(entityDealDf['dealfrequencia'].iloc[0], type(None))
                    else '-'
                )

            with st.expander(label='', expanded=True):
                st.header('Entidade Devedora')

                # KPIs
                entityKPIListCols = st.columns(6)
                with entityKPIListCols[0]:
                    queueRefdate = queueDf['refdate'].iloc[0].strftime('%d/%m/%Y')
                    st.metric(label='Data Atualização Fila', value=queueRefdate)

                with entityKPIListCols[1]:
                    totalAmount = f"{totalQueueAmount/M_TIMES:.2f} MM"
                    st.metric(label='Estoque Total de Precatórios', value=totalAmount)

                with entityKPIListCols[2]:
                    if not entityRegimeDf.empty:
                        st.metric(
                            label='Valores do Estoque de Precatórios', value='HISTÓRICO' if uf != 'SP' else 'ATUALIZADO'
                        )

                with entityKPIListCols[3]:
                    if not entityRegimeDf.empty:
                        entityRegime = entityRegimeDf['regime'].iloc[0]
                        st.metric(label='Regime do Ente', value=entityRegime)

                with entityKPIListCols[4]:
                    exercEntityRCL = entityStatsDf['exercicio'].iloc[0] if not entityStatsDf.empty else '-'
                    entityRCL = f"{entityStatsDf['valor'].iloc[0]/M_TIMES:.2f} MM" if not entityStatsDf.empty else '-'
                    st.metric(label=f'RCL do Ente (Ano: {exercEntityRCL})', value=entityRCL)

                with entityKPIListCols[5]:
                    exercPaymentExpectation = entityPlanDf['exercicio'].iloc[0] if not entityPlanDf.empty else '-'
                    paymentExpectation = (
                        (entityPlanDf['amt'] * entityPlanDf['amtperiodeq']).iloc[0] if not entityPlanDf.empty else '-'
                    )
                    paymentExpectationStr = f"{paymentExpectation/M_TIMES:.2f} MM" if not entityPlanDf.empty else '-'
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

            # Show grid
            with st.expander(label='', expanded=True):
                # entityNoticesCount > 0
                if bool(entityHasDealRecord):
                    st.header('Acordo')
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

                    st.write(entityDealTerms)

            with st.container():
                st.header('Ordem Cronológica')

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
                amountToPayCreditPosition = queueDf.loc[
                    queueDf['queueposition'] <= selectedItem['queueposition'], 'value'
                ].sum()

                with st.expander(label='', expanded=True):
                    st.header('Precatório Selecionado')

                    creditKPICols = st.columns(6)

                    with creditKPICols[0]:
                        position = selectedItem['queueposition']
                        st.metric(label='Posição', value=position)

                    with creditKPICols[1]:
                        amountToPayCreditPositionStr = f"{amountToPayCreditPosition/M_TIMES:.2f}"
                        st.metric(label='Montante p/ Pagar Crédito (MM)', value=amountToPayCreditPositionStr)

                    with creditKPICols[2]:
                        st.metric(
                            label='Prct. Fila p/ Pagar Crédito (%)',
                            value=f'{amountToPayCreditPosition/totalQueueAmount*100:.2f}',
                        )

                    with creditKPICols[3]:
                        budgetYear = selectedItem['budgetyear']
                        st.metric(label='Ano de Orçamento', value=budgetYear)

                    with creditKPICols[4]:
                        creditType = selectedItem['type']
                        st.metric(label='Tipo de Precatório', value=creditType)

                    with creditKPICols[5]:
                        creditAmount = selectedItem['value']
                        st.metric(label='Montante do Crédito (K)', value=f'{creditAmount/K_TIMES:.2f}')

            if paymentExpectation != '-' and bool(selectedItem):
                # Pricing inputs
                with st.form('selectedCreditForm'):
                    ######################## PRICING ########################
                    st.header('Parametrização - Precificação')

                    pricingOptionsCols = st.columns([4, 2, 2, 2, 2])

                    with pricingOptionsCols[0]:
                        dtPricing = st.date_input(
                            label='Data de Precificação', value=TD_DATE, min_value=MIN_DATE, max_value=MAX_DATE
                        )

                        adjQueueAmount = st.number_input(
                            label='Montante Depositado - Ajustar Fila',
                            min_value=0.00,
                            max_value=None,
                            value=0.00,
                            step=1.00,
                        )

                    with pricingOptionsCols[1]:
                        inputPrctSplit = st.number_input(
                            label='Orçamento para Cronologia (%)',
                            value=50.0 if entityRegime == 'ESPECIAL' else 0.0,
                            step=1.0,
                        )
                        inputPrctAuction = st.number_input(
                            label='Deságio - Acordo (%)',
                            value=float(entityAuctionPrct * 100)
                            if isinstance(entityAuctionPrct, numbers.Number)
                            else 40.0,
                            step=1.0,
                        )

                    with pricingOptionsCols[2]:
                        dealIrr = st.slider(
                            label='TIR - Acordo (%)', min_value=0.0, max_value=100.0, value=35.0, step=1.0
                        )
                        dealDuration = st.slider(
                            label='Duration Esperada - Acordo (Anos)',
                            min_value=0.0,
                            max_value=10.0,
                            value=entityDealPaymentWaitYears if bool(entityDealPaymentWaitYears) != False else 2.0,
                            step=0.5,
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
                            'Período da Graça (Anos)',
                            min_value=0.0,
                            max_value=2.0,
                            value=0.0,
                            step=0.1,
                            key='inputGracePeriodYearsEq',
                        )

                        inputPreMocPeriodYearsEq = st.slider(
                            'Período pré-MOC (Anos)',
                            min_value=0.0,
                            max_value=2.0,
                            value=0.0,
                            step=0.1,
                            key='inputPreMocPeriodYearsEq',
                        )

                    secondaryOptions = st.columns([2, 4, 4, 4])

                    with secondaryOptions[0]:
                        dealScenario = st.checkbox(
                            label='Incluir Cenário de Acordo',
                            value=entityHasDeal if entityHasDeal != '-' else False,
                        )

                    with secondaryOptions[1]:
                        basePriceScenario = st.radio(
                            label='Cenário de Precificação', options=['Otimista', 'Base', 'Pessimista'], index=1
                        )

                    st.markdown('---')

                    ######################## EARNOUT ########################
                    st.header('Parametrização - Earnout')

                    baseEarnoutOptions = st.columns([2, 2, 8])
                    with baseEarnoutOptions[0]:
                        calcEarnout = st.checkbox(label='Incluir Cenário de Earnout', value=True)

                    with baseEarnoutOptions[1]:
                        useCalcDuration = st.checkbox(label='Assumir Duration Pré-Definida', value=True)

                    earnoutOptionsCols = st.columns([2, 4, 4])

                    with earnoutOptionsCols[0]:
                        earnoutStrat = st.radio(
                            label='Estratégia de Aquisição', options=['Cronologia', 'Acordo'], index=0
                        )

                    with earnoutOptionsCols[1]:
                        earnoutTradeVl = st.number_input(
                            label='Desembolso Inical (%)', min_value=0.00, max_value=100.00, value=40.00
                        )

                    with earnoutOptionsCols[2]:
                        earnoutPrct = st.slider(
                            label='Earnout (%)', min_value=0.00, max_value=100.00, value=40.00, step=0.50
                        )
                        earnoutPeriods = (
                            st.slider(label='Periodos (Anos)', min_value=0.00, max_value=10.00, value=3.00, step=1.00)
                            + 1
                        )

                    submitPricingButton = st.form_submit_button(label='Precificar')

            # On click run calculations
            if paymentExpectation != '-' and bool(selectedItem) and submitPricingButton:
                with st.expander(label='', expanded=True):
                    st.header('Precificação')

                    rangeEOY = createRangeEOYs(START_YEAR, END_YEAR)
                    dfDataCurvesIPCAEInterest = curvesIPCAEAndInterest(START_YEAR, END_YEAR)

                    dfAmortizationSchedule = amortizationSchedule(
                        dfDataCurvesIPCAEInterest, paymentExpectation, 1.0, inputPrctSplit / 100
                    )

                    ########################### PRICING ###########################
                    pricingDict = {}

                    # Pricing for deal
                    priceDeal = calculateTradePriceGivenIRR(
                        expectedIRR=dealIrr / 100,
                        durationYearEq=dealDuration,
                        currentValue=100.0,
                        interestRate=sliderInterestRate / 100.0,
                        inflationRate=sliderInflation / 100.0,
                        preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                        gracePeriodYearEq=inputGracePeriodYearsEq,
                        hairCutAuction=inputPrctAuction / 100.0,
                    )

                    pricingDict['Acordo'] = {
                        'duration': dealDuration,
                        'pricePrct': round(priceDeal, 2),
                        'irr': round(dealIrr, 2),
                    }

                    durationBaseAdj = 1.2

                    # Pricing for hold
                    durationBase = (
                        round(
                            getDuration(
                                dtPricing.strftime('%Y-%m-%d'),
                                dfAmortizationSchedule,
                                amountToPayCreditPosition - adjQueueAmount,
                            ),
                            2,
                        )
                        * durationBaseAdj
                    )

                    pxCurveBase = getInterpolIRRAndPx(durationBase)
                    pxBase = round(pxCurveBase['interpolPx'], 2)
                    irrBase = round(pxCurveBase['interpolIRR'] * 100, 2)
                    priceBase = round(
                        calculateTradePriceGivenIRR(
                            expectedIRR=(irrBase / 100),
                            durationYearEq=durationBase,
                            interestRate=sliderInterestRate / 100.0,
                            inflationRate=sliderInflation / 100.0,
                            preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                            gracePeriodYearEq=inputGracePeriodYearsEq,
                        ),
                        2,
                    )

                    # Adjusted Duration
                    durationAdj = round(getDurationAdj(durationBase), 2)
                    pxCurveAdj = getInterpolIRRAndPx(durationAdj)
                    pxAdj = round(pxCurveAdj['interpolPx'], 2)
                    irrAdj = round(pxCurveAdj['interpolIRR'] * 100, 2)
                    priceAdj = round(
                        calculateTradePriceGivenIRR(
                            expectedIRR=(irrAdj / 100),
                            durationYearEq=durationAdj,
                            interestRate=sliderInterestRate / 100.0,
                            inflationRate=sliderInflation / 100.0,
                            preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                            gracePeriodYearEq=inputGracePeriodYearsEq,
                        ),
                        2,
                    )

                    # Worst Duration
                    durationWorstCase = round(getDurationAdj(durationAdj), 2)
                    pxCurveWorstCase = getInterpolIRRAndPx(durationWorstCase)
                    pxWorstCase = round(pxCurveWorstCase['interpolPx'], 2)
                    irrWorstCase = round(pxCurveWorstCase['interpolIRR'] * 100, 2)
                    priceWorstCase = round(
                        calculateTradePriceGivenIRR(
                            expectedIRR=(irrWorstCase / 100),
                            durationYearEq=durationWorstCase,
                            interestRate=sliderInterestRate / 100.0,
                            inflationRate=sliderInflation / 100.0,
                            preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                            gracePeriodYearEq=inputGracePeriodYearsEq,
                        ),
                        2,
                    )

                    pricingDict['Otimista'] = {
                        'duration': round(durationBase, 2),
                        'pricePrct': round(priceBase, 2),
                        'irr': round(irrBase, 2),
                        'label': 'Cenário Otimista',
                    }

                    pricingDict['Base'] = {
                        'duration': round(durationAdj, 2),
                        'pricePrct': round(priceAdj, 2),
                        'irr': round(irrAdj, 2),
                        'label': 'Cenário Base',
                    }

                    pricingDict['Pessimista'] = {
                        'duration': round(durationWorstCase, 2),
                        'pricePrct': round(priceWorstCase, 2),
                        'irr': round(irrWorstCase, 2),
                        'label': 'Pior Cenário',
                    }

                    # Cronologia
                    chronologyLabel = pricingDict[basePriceScenario]["label"]
                    chronologyPricePrct = pricingDict[basePriceScenario]['pricePrct']
                    chronologyDuration = pricingDict[basePriceScenario]['duration']
                    chronologyIrr = pricingDict[basePriceScenario]['irr']

                    pricingScenarios = st.columns(3)
                    with pricingScenarios[0]:
                        st.metric(label=f'Preço {chronologyLabel} (%)', value=chronologyPricePrct)

                    with pricingScenarios[1]:
                        st.metric(label=f'Duration {chronologyLabel} (Anos)', value=chronologyDuration)

                    with pricingScenarios[2]:
                        st.metric(label=f'TIR {chronologyLabel} (%)', value=chronologyIrr)

                    chronologyPlotDur, chronologyPlotIrr = createCurveIrrXDuration(chronologyPricePrct, durationBase)

                    # Acordo
                    if dealScenario:
                        dealCols = st.columns(3)
                        with dealCols[0]:
                            st.metric(label='Preço Acordo (%)', value=pricingDict['Acordo']['pricePrct'])

                        with dealCols[1]:
                            st.metric(label='Duration Acordo (Anos)', value=pricingDict['Acordo']['duration'])

                        with dealCols[2]:
                            st.metric(label='TIR Acordo (%)', value=pricingDict['Acordo']['irr'])

                        dealPlotDur, dealPlotIrr = createCurveIrrXDuration(
                            priceDeal, dealDuration, hairCutAuction=(inputPrctAuction / 100.0)
                        )

                    # TODO: improve logic
                    if dealScenario:
                        chronologyCurve = chronologyIRRDurPlot(
                            chronologyPlotDur,
                            chronologyPlotIrr,
                            chronologyDuration,
                            chronologyIrr,
                            dealPlotDur=dealPlotDur,
                            dealPlotIrr=dealPlotIrr,
                            dealDuration=dealDuration,
                            dealIrr=dealIrr,
                        )
                    else:
                        chronologyCurve = chronologyIRRDurPlot(
                            chronologyPlotDur, chronologyPlotIrr, chronologyDuration, chronologyIrr
                        )

                    st.plotly_chart(chronologyCurve, use_container_width=True)

                    ########################### EARNOUT ###########################
                    earnoutDurCalc = (
                        earnoutPeriods
                        if not bool(useCalcDuration)
                        else math.floor(pricingDict['Otimista']['duration']) + 1
                    )

                    if bool(calcEarnout) and earnoutDurCalc > 1:
                        earnoutDict = generateEarnoutPricingScennario(
                            earnout=earnoutPrct / 100,
                            tradedValue=earnoutTradeVl,
                            startDate=dtPricing.strftime('%Y-%m-%d'),
                            periods=earnoutPeriods
                            if not bool(useCalcDuration)
                            else math.floor(pricingDict['Otimista']['duration']) + 1,
                            currentValue=100.0,
                            interestRate=sliderInterestRate / 100.0,
                            inflationRate=sliderInflation / 100.0,
                            preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                            gracePeriodYearEq=inputGracePeriodYearsEq,
                            hairCutAuction=inputPrctAuction / 100.0 if earnoutStrat == 'Acordo' else 0,
                        )
                        st.header('Earnout')
                        earnoutCols = st.columns(3)
                        with earnoutCols[0]:
                            st.metric(label='Desembolso Inicial / Preço de Aquisição (%)', value=earnoutTradeVl)

                        with earnoutCols[1]:
                            st.metric(
                                label='Vigência do Earnout (Anos)',
                                value=(
                                    earnoutPeriods - 1
                                    if not bool(useCalcDuration)
                                    else math.floor(pricingDict['Otimista']['duration'])
                                ),
                            )

                        with earnoutCols[2]:
                            st.metric(label='Earnout (%)', value=earnoutPrct)

                        earnoutChart = earnoutPlot(earnoutDict)
                        st.plotly_chart(earnoutChart, use_container_width=True)
    if sidebarSelection == 'Logout':
        authenticator.cookie_manager.delete(authenticator.cookie_name)
        st.session_state['logout'] = True
        st.session_state['name'] = None
        st.session_state['username'] = None
        st.session_state['authentication_status'] = None
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
