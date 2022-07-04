import numbers
import streamlit as st
import numpy as np

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

from fpdf import FPDF
import base64

from classes.CreditDoc import CreditDoc

from utils.functions import *
from utils.constants import *
from utils.computations import *
from utils.sidebar import *
from utils.login import *
from utils.user import *

st.set_page_config(layout="wide")

######################### STATE MANAGEMENT #########################
def resetApp():
    for key in st.session_state.keys():
        if key not in CONST_MAINTAIN_KEYS:
            del st.session_state[key]

def resetPricingSate():
    for key in ['pricingState', 'requestDocState']:
        if key in st.session_state.keys():
            del st.session_state[key]

def pricingState():
    st.session_state['pricingState'] = True

    # Reset doc state
    if 'requestDocState' in st.session_state:
        del st.session_state['requestDocState']

def requestDocState():
    st.session_state['requestDocState'] = True

def resetDownloadState():
    if 'requestDocState' in st.session_state:
        del st.session_state['requestDocState']

def selectedItemState(selectedItem):

    # Not selected credit:
    # First time rendering or filter parameters => reset session_state
    if not bool(selectedItem):
        for key in st.session_state.keys():
            if key in ['pricingState', 'requestDocState', 'selectedItem']:
                del st.session_state[key]

    # First time selecting an item
    elif bool(selectedItem) and 'selectedItem' not in st.session_state.keys():
        st.session_state['selectedItem'] = selectedItem
        resetPricingSate()
    
    # Picked a different item or maintained item
    elif bool(selectedItem) and 'selectedItem' in st.session_state.keys():
        if selectedItem == st.session_state['selectedItem']:
            return None

        else:
            st.session_state['selectedItem'] = selectedItem
            resetPricingSate()

def federativeCreditWorkflow():
    with st.expander(label='', expanded=True):
        with st.form('federativeForm', clear_on_submit=False):
            st.header('Gerar Parecer')
            federativeDocCols = st.columns(4)
            with federativeDocCols[0]:
                creditType = st.radio(label='Tipo de Crédito', options=['ALIMENTAR', 'COMUM'], index=0)
                creditorName = st.text_input(label='Nome do Credor')

            with federativeDocCols[1]:
                creditId = st.text_input(label='Número do Precatório')
                creditProcessId = st.text_input(label='Processo')

            with federativeDocCols[2]:
                budgetYear = st.selectbox(label='Ano de Orçamento', options=YEAR_OPTIONS, index=0)
                purchaseAmount = st.number_input(label='Valor Máximo de Aquisição', format='%.2f', value=1000.00)

            with federativeDocCols[3]:
                contractualFees = st.number_input(label='Honorários Contratuais (%)', format='%.2f', value=0.00, min_value=0.00, max_value=100.00, step=1.00)

            analystCols = st.columns([2, 4])
            with analystCols[0]:
                pricingAnalyst = st.selectbox(label='Responsável pelo parecer', options=PRICING_ANALYSTS, index=0)

            submitForm = st.form_submit_button(label='Gerar Parecer')

    if submitForm:
        creditInfoDict = {
            'creditType': creditType,
            'creditorName': creditorName,
            'creditId': creditId,
            'creditProcessId': creditProcessId,
            'purchaseAmount': purchaseAmount,
            'budgetYear': budgetYear,
            'contractualFees': contractualFees,
            'pricingAnalyst': pricingAnalyst,
        }

        earnoutDict = FEDERATIVE_DOC_EARNOUT_PARAMS[creditInfoDict['budgetYear']][creditInfoDict['creditType']]
        creditInfoDict = {**creditInfoDict, **earnoutDict}

        generateDocFederative(creditInfoDict)


def generateDocFederative(entityDict: dict):

    pdf = CreditDoc('P', 'mm', (210, 297), entityDict)
    pdf.writeTitle(title='Parecer de Crédito')

    ###### Write doc ######
    ###### First page ######
    pdf.writeFederativeCreditHeader()
    pdf.writeFederativeBaseText()
    pdf.writeFederativeEarnoutText()
    pdf.writeFederativeContractualText()
    pdf.writeFederativeConclusionText()
    pdf.writeSignature()

    PDFbyte = pdf.returnPdfAsBytes()
    pdf.close()

    file_name = f'UNIAO_{"".join(e for e in entityDict["creditId"] if e.isalnum())}.pdf'

    # Download
    st.download_button(
        label='Download Pdf',
        file_name=file_name,
        data=PDFbyte,
        mime='application/octet-stream'
    )

    pass

def generateDoc(entityDict: dict, typeDeal: str, withEarnout: bool, chartsDict: dict):

    pdf = CreditDoc('P', 'mm', (210, 297), entityDict)
    pdf.writeTitle(title='Parecer de Crédito')

    ###### Write doc ######
    ###### First page ######
    pdf.writeCreditHeader()
    pdf.writeBaseText()
    pdf.writeDealText(typeDeal=typeDeal)
    if bool(withEarnout): pdf.writeEarnoutText()
    pdf.writeConclusionText()
    pdf.writeSignature()

    ###### Second page ######
    pdf.addNewPage()
    pdf.writeTitle(title='Indicadores e Análise Técnica do Ente')

    # Print kpis
    kpisShow = [
        'kpiEntityTotalAmount',
        'kpiEntityRegime',
        'kpiEntityRCL',
        'kpiEntityPaymentExpection',
        ]

    kpisUnitXSpace = 10
    for kpi in kpisShow:
        pdf.insertKPI(
            kpiHeader=entityDict[f'{kpi}Header'],
            kpiValue=str(entityDict[f'{kpi}Value']),
            x=kpisUnitXSpace,
            y=HEADER_HEIGHT_MARGIN
            )

        pdf.set_font('Arial', style='B', size=KPI_HEADER_FONT_SIZE)
        kpiStrHeaderWidth = pdf.get_string_width(s=entityDict[f'{kpi}Header'])

        kpisUnitXSpace += kpiStrHeaderWidth + 6
    
    # Print charts
    chartsStartY = 70
    
    pdf.image(name=chartsDict['stackedConsBarChart']['pathToImage'], x=10, y=chartsStartY, w=100, h=70, type='png')
    pdf.image(name=chartsDict['entityMapPaymentsBarChart']['pathToImage'], x=105, y=chartsStartY, w=100, h=70, type='png')
    pdf.image(name=chartsDict['scatterMapAmountChart']['pathToImage'], x=10, y=chartsStartY + 70, w=100, h=70, type='png')
    pdf.image(name=chartsDict['countPieChart']['pathToImage'], x=105, y=chartsStartY + 70, w=100, h=70, type='png')

    # Credit
    pdf.set_font('Arial', style='B', size=TITLE_FONT_SIZE)
    pdf.text(x=61, y=220, txt='Indicadores do Crédito')

    # Kpis
    creditKpisShow = [
        'kpiCreditPosition',
        'kpiCreditType',
        'kpiCreditBudgetYear',
    ]

    kpisUnitXSpace = 10
    for kpi, dist in zip(creditKpisShow, [53, 40, 0]):
        pdf.insertKPI(
            kpiHeader=entityDict[f'{kpi}Header'],
            kpiValue=str(entityDict[f'{kpi}Value']),
            x=kpisUnitXSpace,
            y=230
            )

        pdf.set_font('Arial', style='B', size=KPI_HEADER_FONT_SIZE)
        kpiStrHeaderWidth = pdf.get_string_width(s=entityDict[f'{kpi}Header'])

        kpisUnitXSpace += kpiStrHeaderWidth + dist

    creditKpisShow = [
        'kpiCreditToPayPosition',
        'kpiCreditPercentagePay',
        'kpiCreditAmount',
    ]

    kpisUnitXSpace = 10
    for kpi in creditKpisShow:
        pdf.insertKPI(
            kpiHeader=entityDict[f'{kpi}Header'],
            kpiValue=str(entityDict[f'{kpi}Value']),
            x=kpisUnitXSpace,
            y=248
            )

        pdf.set_font('Arial', style='B', size=KPI_HEADER_FONT_SIZE)
        kpiStrHeaderWidth = pdf.get_string_width(s=entityDict[f'{kpi}Header'])

        kpisUnitXSpace += kpiStrHeaderWidth + 20


    ###### Third page ######
    pdf.addNewPage(orientation='P')
    pdf.writeTitle(title='Precificação')

    if typeDeal=='Acordo':
        creditKpisShow = [
        'kpiDealPercentage',
        'kpiDealDuration',
        'kpiDealTir',
        ]
        dist = 35
    elif typeDeal=='Cronologia':
        creditKpisShow = [
            'kpiChronologyPercentage',
            'kpiChronologyDuration',
            'kpiChronologyTir',
        ]
        dist = 25

    kpisUnitXSpace = 10
    for kpi in creditKpisShow:
        pdf.insertKPI(
            kpiHeader=entityDict[f'{kpi}Header'],
            kpiValue=str(entityDict[f'{kpi}Value']),
            x=kpisUnitXSpace,
            y=HEADER_HEIGHT_MARGIN
            )

        pdf.set_font('Arial', style='B', size=KPI_HEADER_FONT_SIZE)
        kpiStrHeaderWidth = pdf.get_string_width(s=entityDict[f'{kpi}Header'])

        kpisUnitXSpace += kpiStrHeaderWidth + dist

    pdf.image(name=chartsDict['chronologyCurve']['pathToImage'], x=10, y=67, w=200, h=120, type='png')

    if 'earnoutChart' in chartsDict:
        pdf.image(name=chartsDict['earnoutChart']['pathToImage'], x=10, y=187, w=200, h=100, type='png')

    PDFbyte = pdf.returnPdfAsBytes()
    pdf.close()

    file_name = f'{entityDict["entityType"]}_{entityDict["entityName"]}{"_" + entityDict["entityUf"] if entityDict["entityType"]=="MUNICIPIO" else ""}_{"".join(e for e in entityDict["creditId"] if e.isalnum())}.pdf'

    # Download
    st.download_button(
        label='Download Pdf',
        file_name=file_name,
        data=PDFbyte,
        mime='application/octet-stream',
        on_click=resetDownloadState
    )

    deleteFilesFromS3(chartsDict)

###################### STYLING ######################
def applyStyling():
    style = """
    <style>
    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div.css-ocx5ag.epcbefy1 > div:nth-child(1) > div > div:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div > div > div > div {
    flex-direction: row;
    }

    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(12) > ul > li > div.streamlit-expanderContent.st-ae.st-af.st-ag.st-ah.st-ai.st-aj.st-bt.st-br.st-cf.st-cg.st-bw.st-bx.st-as.st-at.st-by.st-bz.st-c0.st-c1.st-c2.st-ch.st-am.st-ci.st-cj.st-b1.st-ck.st-b3.st-c7.st-c8.st-c9 > div:nth-child(1) > div > div.css-ocx5ag.epcbefy1 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v4 > div.css-j5r0tf.e1tzin5v2 > div:nth-child(1) > div > div > div > div {
    flex-direction: row;
    }

    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(12) > ul > li > div.streamlit-expanderContent.st-ae.st-af.st-ag.st-ah.st-ai.st-aj.st-bt.st-br.st-cf.st-cg.st-bw.st-bx.st-as.st-at.st-by.st-bz.st-c0.st-c1.st-c2.st-ch.st-am.st-ci.st-cj.st-b1.st-ck.st-b3.st-c7.st-c8.st-c9 > div:nth-child(1) > div > div.css-ocx5ag.epcbefy1 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v4 > div:nth-child(4) > div:nth-child(1) > div > div:nth-child(1) > div > div {
    flex-direction: row;
    }

    #root > div:nth-child(1) > div.withScreencast > div > div > div > section > div > div:nth-child(1) > div > div:nth-child(12) > ul > li > div.streamlit-expanderContent.st-ae.st-af.st-ag.st-ah.st-ai.st-aj.st-bt.st-br.st-cf.st-cg.st-bw.st-bx.st-as.st-at.st-by.st-bz.st-c0.st-c1.st-c2.st-ch.st-am.st-ci.st-cj.st-b1.st-ck.st-b3.st-c7.st-c8.st-c9 > div:nth-child(1) > div > div.css-ocx5ag.epcbefy1 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v4 > div:nth-child(1) > div:nth-child(1) > div > div:nth-child(1) > div > div {
    flex-direction: row; 
    }

    #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-1v3fvcr.egzxvld3 > div > div:nth-child(1) > div > div:nth-child(2) > div > div.css-ocx5ag.epcbefy1 > div:nth-child(1) > div > div:nth-child(3) > div:nth-child(2) > div:nth-child(1) > div > div > div {
    flex-direction: row; 
    }

    </style>
    """
    st.markdown(style, unsafe_allow_html=True)
    
def header():
    st.image('static/header.png', use_column_width=True)
    st.title('Mapa de Precificação')


def pricingMap() -> None:
    names, usernames, passwords = getUsers()
    authenticator, name, authentication_status, username = loginForm(names, usernames, passwords)

    if st.session_state['authentication_status']:
        sidebarSelection = sidebar()
        if sidebarSelection == 'Pricing':
            with st.container():
                ###################### CLEAR STATIC FOLDER ######################
                

                ###################### DATABASE ######################
                # Open connection to db
                cnn = createConnection()

                # Get entities and create form for queue
                entitiesDf = getEntities(cnn)

                ###################### HEADER ######################
                applyStyling()
                header()

                ###################### FILTERS ######################
                with st.expander(label='', expanded=True):
                    st.header('Filtros')

                    filterCol1, filterCol2, filterCol3 = st.columns(3)
                    with filterCol1:
                        typeEnt = st.radio('Tipo do Ente', options=entitiesDf['entitytype'].drop_duplicates().sort_values(), index=0, on_change=resetApp)
                        
                    with filterCol2:
                        _ufOptions = ufOptions(entitiesDf, typeEnt)
                        uf = st.selectbox('UF', options=_ufOptions, index=0, on_change=resetApp)
                        
                    with filterCol3:
                        _courtNameOptions = courtNameOptions(entitiesDf, typeEnt, uf)
                        courtname = st.selectbox('Corte', options=_courtNameOptions, index=0, on_change=resetApp)

                    _entitiesOptions = entitiesOptions(entitiesDf, typeEnt, uf, courtname)
                    entityname = st.selectbox('Entity', options=_entitiesOptions, index=0, on_change=resetApp)

                if typeEnt == 'FEDERAL':
                    federativeCreditWorkflow()
                    return None

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
                dealPlotDur = dealPlotIrr = dealDuration = dealIrr = False
                # If entity has deal add a column
                if not entityDealDf.empty:
                    entityHasDealRecord = True
                    entityHasDeal = entityDealDf['acordo'].iloc[0] if not isinstance(entityDealDf['acordo'].iloc[0], type(None)) else '-'
                    entityAuctionPrct = entityDealDf['pctdesagiomax'].iloc[0] if not isinstance(entityDealDf['pctdesagiomax'].iloc[0], type(None)) else '-'
                    entityNoticesCount = entityDealDf['contagemeditais'].iloc[0] if not isinstance(entityDealDf['contagemeditais'].iloc[0], type(None)) else 0
                    entityDealPaymentWaitYears = float(entityDealDf['prazoesperadoparapagamento'].iloc[0]) if not isinstance(entityDealDf['prazoesperadoparapagamento'].iloc[0], type(None)) else 0.0
                    entityDealAvgAmount = entityDealDf['montantemedioderecursosporedital'].iloc[0] if not isinstance(entityDealDf['montantemedioderecursosporedital'].iloc[0], type(None)) else 0
                    entityDealTerms = entityDealDf['termosacordo'].iloc[0]['texto'] if not isinstance(entityDealDf['termosacordo'].iloc[0], type(None)) else '-'

                    entityDealFrequency = entityDealDf['dealfrequencia'].iloc[0] if not isinstance(entityDealDf['dealfrequencia'].iloc[0], type(None)) else '-'

                # Show grid
                with st.expander(label='', expanded=True):
                    # entityNoticesCount > 0
                    if bool(entityHasDealRecord):
                        st.header('Indicadores do Acordo')
                        dealKPIsCols = st.columns(5)

                        with dealKPIsCols[0]:
                            translateBoolDeal = TRANSLATE_BOOL_DICT[entityHasDeal]
                            kpiDealHeader = 'Faz acordo ?'
                            st.metric(label=kpiDealHeader, value=translateBoolDeal)

                        with dealKPIsCols[1]:
                            kpiNoticesCountHeader = 'N° Editais'
                            st.metric(label=kpiNoticesCountHeader, value=entityNoticesCount)

                        with dealKPIsCols[2]:
                            kpiEntityDealPaymentHeader = 'Prazo Est. Pgto. (Anos)'
                            st.metric(label=kpiEntityDealPaymentHeader, value=entityDealPaymentWaitYears)

                        with dealKPIsCols[3]:
                            entityDealAvgAmountToStrDict = numberToStrDict(entityDealAvgAmount)
                            entityDealAvgAmountHeader = 'Montante Prev. Edital'
                            st.metric(label=entityDealAvgAmountHeader, value=f'{entityDealAvgAmountToStrDict["reducedNumberStr"]}')

                        with dealKPIsCols[4]:
                            entityDealFrequencyHeader = 'Frequência Editais'
                            st.metric(label=entityDealFrequencyHeader, value=entityDealFrequency)

                        st.write(entityDealTerms)

                with st.expander(label='', expanded=True):
                    st.header('Indicadores e Análise Técnica do Ente')

                    # KPIs
                    entityKPIListCols = st.columns(5)
                    with entityKPIListCols[0]:
                        queueRefdate = queueDf['refdate'].iloc[0].strftime('%d/%m/%Y')
                        kpiEntityQueueDateHeader = 'Data Atualização Fila'
                        st.metric(label=kpiEntityQueueDateHeader, value=queueRefdate)

                    with entityKPIListCols[1]:
                        totalAmountNumToStrDict = numberToStrDict(totalQueueAmount)
                        kpiEntityTotalAmountHeader = 'Montante Total'
                        totalAmount = f"{totalAmountNumToStrDict['reducedNumberStr']}"
                        st.metric(label=kpiEntityTotalAmountHeader, value=totalAmount)

                    with entityKPIListCols[2]:
                        kpiEntityRegimeHeader = 'Regime do Ente'
                        entityRegime = entityRegimeDf['regime'].iloc[0] if not entityRegimeDf.empty else '-'
                        st.metric(label=kpiEntityRegimeHeader, value=entityRegime)

                    with entityKPIListCols[3]:
                        exercEntityRCL = entityStatsDf['exercicio'].iloc[0] if not entityStatsDf.empty else '-'
                        entityRCL = f"{numberToStrDict(entityStatsDf['valor'].iloc[0])['reducedNumberStr']}" if not entityStatsDf.empty else '-'
                        kpiEntityRCLHeader = f'RCL do Ente (Ano: {exercEntityRCL})'

                        st.metric(label=kpiEntityRCLHeader, value=entityRCL)

                    with entityKPIListCols[4]:
                        exercPaymentExpectation = entityPlanDf['exercicio'].iloc[0] if not entityPlanDf.empty else '-'
                        paymentExpectation = (entityPlanDf['amt'] * entityPlanDf['amtperiodeq']).iloc[0] if not entityPlanDf.empty else '-'
                        kpiEntityPaymentExpectionHeader = f'Expect. de Pagto. (Ano: {exercPaymentExpectation})'

                        paymentExpectationStr = f"{numberToStrDict(paymentExpectation)['reducedNumberStr']}" if not entityPlanDf.empty else '-'
                        st.metric(label=kpiEntityPaymentExpectionHeader, value=paymentExpectationStr)

                    # Charts
                    queueChartCol1, queueChartCol2 = st.columns(2)
                    with queueChartCol1:
                        stackedConsBarChart = consolidatedAmountYearBarChart(queueDf)
                        st.plotly_chart(stackedConsBarChart, use_container_width=True)

                    with queueChartCol2:
                        entityMapPaymentsBarChart = entityMapPaymentsBarPlot(entityMapDf)
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

                    pickedItem = dataQueue['selected_rows']
                    if bool(pickedItem): selectedItemState(pickedItem[0])

                # Show item data
                # TODO: Might change to return None if __name__

                if 'selectedItem' in st.session_state and bool(st.session_state['selectedItem']):

                    selectedItem = st.session_state['selectedItem']
                    amountToPayCreditPosition = queueDf.loc[queueDf['queueposition']<=selectedItem['queueposition'], 'value'].sum()

                    with st.expander(label='', expanded=True):
                        st.header('Indicadores do Precatório Selecionado')

                        creditKPICols = st.columns(6)

                        with creditKPICols[0]:
                            position = selectedItem['queueposition']
                            kpiCreditPositionHeader = 'Posição'
                            st.metric(label=kpiCreditPositionHeader, value=position)

                        with creditKPICols[1]:
                            amountToPayCreditPositionStr = f"{numberToStrDict(amountToPayCreditPosition)['reducedNumberStr']}"
                            kpiCreditToPayPositionHeader = 'Montante p/ Pagar Crédito'
                            st.metric(label=kpiCreditToPayPositionHeader, value=amountToPayCreditPositionStr)

                        with creditKPICols[2]:
                            kpiCreditPercentagePayHeader = 'Prct. Fila p/ Pagar Crédito (%)'
                            kpiCreditPercentagePayValue = f'{amountToPayCreditPosition/totalQueueAmount*100:.2f}'
                            st.metric(label=kpiCreditPercentagePayHeader, value=kpiCreditPercentagePayValue)

                        with creditKPICols[3]:
                            budgetYear = selectedItem['budgetyear']
                            kpiCreditBudgetYearHeader = 'Ano de Orçamento'
                            st.metric(label=kpiCreditBudgetYearHeader, value=budgetYear)

                        with creditKPICols[4]:
                            creditType = selectedItem['type']
                            kpiCreditTypeHeader = 'Tipo de Precatório'
                            st.metric(label=kpiCreditTypeHeader, value=creditType)

                        with creditKPICols[5]:
                            creditAmount = selectedItem['value']
                            kpiCreditAmountHeader = 'Valor do Crédito'
                            kpiCreditAmountValue = f'{numberToStrDict(creditAmount)["reducedNumberStr"]}'
                            st.metric(label=kpiCreditAmountHeader, value=kpiCreditAmountValue)

                if paymentExpectation != '-' and 'selectedItem' in st.session_state:
                    # Pricing inputs
                    with st.form('selectedCreditForm'):
                        ######################## PRICING ########################
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
                                value=entityDealPaymentWaitYears if bool(entityDealPaymentWaitYears) != False else 2.0,
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

                        secondaryOptions = st.columns([2, 4, 4, 4])

                        with secondaryOptions[0]:
                            dealScenario = st.checkbox(label='Cálculo para Acordo', value=entityHasDeal if entityHasDeal != '-' else False)

                        with secondaryOptions[1]:
                            basePriceScenario = st.radio(label='Cenário p/ Cronologia', options=['Otimista', 'Ajuste', 'Pior'], index=1)

                        st.markdown('---')

                        ######################## EARNOUT ########################
                        st.header('Parâmetros p/ Earnout')

                        baseEarnoutOptions = st.columns([2, 2, 4])
                        with baseEarnoutOptions[0]:
                            calcEarnout = st.checkbox(label='Cálculo para Earnout', value=True)

                        with baseEarnoutOptions[1]:
                            useCalcDuration = st.checkbox(label='Duration Pré Definido p/ Earnout', value=True)

                        earnoutOptionsCols = st.columns([2, 4, 4])

                        with earnoutOptionsCols[0]:
                            earnoutStrat = st.radio(label='Estratégia de aquisição', options=['Cronologia', 'Acordo'], index = 0)

                        with earnoutOptionsCols[1]:
                            earnoutTradeVl = st.number_input(label='Desembolso Inical (%)', min_value=0.00, max_value=100.00, value=40.00)

                        with earnoutOptionsCols[2]:
                            earnoutPrct = st.slider(label='Earnout (%)', min_value=0.00, max_value=100.00, value=40.00, step=0.50)
                            earnoutPeriods = st.slider(label='Periodos (Anos)', min_value=0.00, max_value=10.00, value=3.00, step=1.00)


                        submitPricingButton = st.form_submit_button(label='Precificar', on_click=pricingState)

                # On click run calculations
                if paymentExpectation != '-' and 'pricingState' in st.session_state and bool(st.session_state['pricingState']):
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
                            hairCutAuction=inputPrctAuction / 100.0
                        )

                        pricingDict['Acordo'] = {
                            'duration': dealDuration,
                            'pricePrct': round(priceDeal, 2),
                            'irr': round(dealIrr, 2)
                        }

                        durationBaseAdj = 1.2

                        # Pricing for hold
                        durationBase = round(getDuration(
                            dtPricing.strftime('%Y-%m-%d'),
                            dfAmortizationSchedule,
                            amountToPayCreditPosition - adjQueueAmount,
                        ), 2) * durationBaseAdj

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

                        pricingDict['Otimista'] = {
                            'duration': round(durationBase, 2),
                            'pricePrct': round(priceBase, 2),
                            'irr':round(irrBase, 2),
                            'label': 'Cenário Otimista'
                        }

                        pricingDict['Ajuste'] = {
                            'duration': round(durationAdj, 2),
                            'pricePrct': round(priceAdj, 2),
                            'irr':round(irrAdj, 2),
                            'label': 'Cenário Base'
                        }

                        pricingDict['Pior'] = {
                            'duration': round(durationWorstCase, 2),
                            'pricePrct': round(priceWorstCase, 2),
                            'irr':round(irrWorstCase, 2),
                            'label': 'Pior Cenário'
                        }

                        # Acordo
                        kpiDealPercentageHeader = 'Preço Acordo (%)'
                        kpiDealDurationHeader = 'Duration Acordo (Anos)'
                        kpiDealTirHeader = 'TIR Acordo (%)'
                        if dealScenario:
                            dealCols = st.columns(3)
                            with dealCols[0]:
                                st.metric(label=kpiDealPercentageHeader, value=pricingDict['Acordo']['pricePrct'])

                            with dealCols[1]:
                                st.metric(label=kpiDealDurationHeader, value=pricingDict['Acordo']['duration'])

                            with dealCols[2]:
                                st.metric(label=kpiDealTirHeader, value=pricingDict['Acordo']['irr'])

                            dealPlotDur, dealPlotIrr = createCurveIrrXDuration(priceDeal, dealDuration, hairCutAuction=(inputPrctAuction / 100.0))

                        # Cronologia
                        chronologyLabel = pricingDict[basePriceScenario]["label"]
                        chronologyPricePrct = pricingDict[basePriceScenario]['pricePrct']
                        chronologyDuration = pricingDict[basePriceScenario]['duration']
                        chronologyIrr = pricingDict[basePriceScenario]['irr']

                        pricingScenarios = st.columns(3)
                        with pricingScenarios[0]:
                            kpiChronologyPercentageHeader = f'Preço {chronologyLabel} (%)'
                            st.metric(label=kpiChronologyPercentageHeader, value=chronologyPricePrct)

                        with pricingScenarios[1]:
                            kpiChronologyDurationHeader = f'Duration {chronologyLabel} (Anos)'
                            st.metric(label=kpiChronologyDurationHeader, value=chronologyDuration)

                        with pricingScenarios[2]:
                            kpiChronologyTirHeader = f'TIR {chronologyLabel} (%)'
                            st.metric(label=kpiChronologyTirHeader, value=chronologyIrr)

                        chronologyPlotDur, chronologyPlotIrr = createCurveIrrXDuration(chronologyPricePrct, durationBase)
                        
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
                                dealIrr=dealIrr)

                        else:
                            chronologyCurve = chronologyIRRDurPlot(
                                chronologyPlotDur,
                                chronologyPlotIrr, 
                                chronologyDuration, 
                                chronologyIrr)

                        st.plotly_chart(chronologyCurve, use_container_width=True)

                        ########################### EARNOUT ###########################
                        earnoutDurCalc = earnoutPeriods if not bool(useCalcDuration) else math.floor(pricingDict['Otimista']['duration'])
                        earnoutDict = {}

                        if bool(calcEarnout) and earnoutDurCalc > 1:
                            earnoutDict = generateEarnoutPricingScennario(
                                earnout = earnoutPrct / 100,
                                tradedValue = earnoutTradeVl,
                                startDate = dtPricing.strftime('%Y-%m-%d'),
                                periods = earnoutPeriods if not bool(useCalcDuration) else math.floor(pricingDict['Otimista']['duration']),
                                currentValue=100.0,
                                interestRate=sliderInterestRate / 100.0,
                                inflationRate=sliderInflation / 100.0,
                                preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                                gracePeriodYearEq=inputGracePeriodYearsEq,
                                hairCutAuction=inputPrctAuction / 100.0 if earnoutStrat == 'Acordo' else 0,
                            )

                            earnoutChart = earnoutPlot(earnoutDict)
                            st.plotly_chart(earnoutChart, use_container_width=True)

                if paymentExpectation != '-' and 'pricingState' in st.session_state and bool(st.session_state['pricingState']):
                    with st.expander(label='', expanded=True):
                        st.header('Gerar Parecer')

                        # Doc form
                        with st.form('docForm'):
                            docOptionsCols = st.columns([4, 4, 4, 4])
                            with docOptionsCols[0]:
                                typeDeal = st.radio(label='Parecer para: ', options=['Cronologia', 'Acordo'], index=0)
                                withEarnout = st.checkbox(label='Considerar Earnout', value=bool(earnoutDict))
                                pricingAnalyst = st.selectbox(label='Responsável pelo parecer', options=PRICING_ANALYSTS, index=0)

                            with docOptionsCols[1]:
                                creditorName = st.text_input(label='Nome do Credor')
                                purchaseAmount = st.number_input(label='Valor a Ser Pago', format='%.2f', value=1000.00)
                            
                            with docOptionsCols[2]:
                                processNumber = st.text_input(label='Número do Processo')
                                contractualFees = st.number_input(label='Honorários Contratuais (%)', format='%.2f', value=0.00, min_value=0.00, max_value=100.00, step=1.00)

                            with docOptionsCols[3]:
                                dealNoticeType = st.radio(label='Instrumento em Caso de Acordo', options=['Edital', 'Decreto'], index=0)
                                dealNoticeNumber = st.text_input(label='Número do Edital/Decreto')
                                dealDisbursementMonthly = st.number_input(label='Desembolso Mensal do Ente em Caso de Acordo', format='%.2f', value=1000.00)

                            formBtn = st.form_submit_button(label='Gerar Pdf', on_click=requestDocState)

                # Download button
                if paymentExpectation != '-' and 'requestDocState' in st.session_state and bool(st.session_state['requestDocState']):
                    creditInfoDict = {
                        'entityType': typeEnt,
                        'entityUf': uf,
                        'entityCourtname': courtname,
                        'entityName': entityname,
                        'entityDealPaymentWaitYears': entityDealPaymentWaitYears,
                        'entityDealAvgAmount': entityDealAvgAmount,
                        'entityBudgetYear': budgetYear,
                        'entityRCL': exercEntityRCL,
                        'entityRCLYear': exercEntityRCL,
                        'queueRefdate': queueRefdate,
                        'queueTotalAmount': totalAmount,
                        'entityRegime': entityRegime,
                        'entityPaymentExpectation': paymentExpectation,
                        'entityPaymentExpectationYear': exercPaymentExpectation,
                        'amountToPayCreditPosition': amountToPayCreditPosition,
                        'percentageToPayCreditPosition': amountToPayCreditPosition/totalQueueAmount*100,
                        'creditId': st.session_state['selectedItem']['id'],
                        'creditQueuePosition': position,
                        'creditType': creditType,
                        'creditAmount': creditAmount,
                        'pricingDate': dtPricing,
                        'dealPrice': pricingDict['Acordo']['pricePrct'],
                        'dealDuration': pricingDict['Acordo']['duration'],
                        'chronologyPrice': chronologyPricePrct,
                        'chronologyDuration': chronologyDuration,
                        'processNumber': processNumber,
                        'purchaseAmount': purchaseAmount,
                        'dealNoticeType': dealNoticeType,
                        'dealNoticeNumber': dealNoticeNumber,
                        'dealScenario': dealScenario,
                        'dealDisbursementMonthly': dealDisbursementMonthly,
                        'creditorName': creditorName,
                        'contractualFees': contractualFees,
                        'kpiEntityQueueDateHeader': kpiEntityQueueDateHeader,
                        'kpiEntityQueueDateValue': queueRefdate,
                        'kpiEntityTotalAmountHeader': kpiEntityTotalAmountHeader,
                        'kpiEntityTotalAmountValue': totalAmount,
                        'kpiEntityRegimeHeader': kpiEntityRegimeHeader,
                        'kpiEntityRegimeValue': entityRegime,
                        'kpiEntityRCLHeader': kpiEntityRCLHeader,
                        'kpiEntityRCLValue': entityRCL,
                        'kpiEntityPaymentExpectionHeader': kpiEntityPaymentExpectionHeader,
                        'kpiEntityPaymentExpectionValue': paymentExpectationStr,
                        # 'kpiDealHeader': kpiDealHeader,
                        # 'kpiDealValue': translateBoolDeal,
                        # 'kpiNoticesCountHeader': kpiNoticesCountHeader,
                        # 'kpiNoticesCountValue': entityNoticesCount,
                        # 'kpiEntityDealPaymentHeader': kpiEntityDealPaymentHeader,
                        # 'kpiEntityDealPaymentValue': entityDealPaymentWaitYears,
                        # 'entityDealAvgAmountHeader': entityDealAvgAmountHeader,
                        # 'entityDealAvgAmountValue': f'{entityDealAvgAmountToStrDict["reducedNumberStr"]}',
                        # 'entityDealFrequencyHeader': entityDealFrequencyHeader,
                        # 'entityDealFrequencyValue': entityDealFrequency,
                        'kpiCreditPositionHeader': kpiCreditPositionHeader,
                        'kpiCreditPositionValue': str(position),
                        'kpiCreditToPayPositionHeader': kpiCreditToPayPositionHeader,
                        'kpiCreditToPayPositionValue': amountToPayCreditPositionStr,
                        'kpiCreditPercentagePayHeader': kpiCreditPercentagePayHeader,
                        'kpiCreditPercentagePayValue': kpiCreditPercentagePayValue,
                        'kpiCreditBudgetYearHeader': kpiCreditBudgetYearHeader,
                        'kpiCreditBudgetYearValue': str(budgetYear),
                        'kpiCreditTypeHeader': kpiCreditTypeHeader,
                        'kpiCreditTypeValue': creditType,
                        'kpiCreditAmountHeader': kpiCreditAmountHeader,
                        'kpiCreditAmountValue': kpiCreditAmountValue,
                        'kpiChronologyPercentageHeader': kpiChronologyPercentageHeader,
                        'kpiChronologyPercentageValue': chronologyPricePrct,
                        'kpiChronologyDurationHeader': kpiChronologyDurationHeader,
                        'kpiChronologyDurationValue': chronologyDuration,
                        'kpiChronologyTirHeader': kpiChronologyTirHeader,
                        'kpiChronologyTirValue': chronologyIrr,
                        'kpiDealPercentageHeader': kpiDealPercentageHeader,
                        'kpiDealPercentageValue': pricingDict['Acordo']['pricePrct'],
                        'kpiDealDurationHeader': kpiDealDurationHeader,
                        'kpiDealDurationValue': pricingDict['Acordo']['duration'],
                        'kpiDealTirHeader': kpiDealTirHeader,
                        'kpiDealTirValue': pricingDict['Acordo']['irr'],
                        'pricingAnalyst': pricingAnalyst,
                        'typeDeal': typeDeal
                    }

                    creditInfoDict = {**creditInfoDict, **earnoutDict}

                    earnoutOnDoc = withEarnout
                    # Check if earnout was checked but earnoutDict is empty
                    if bool(withEarnout) and not bool(earnoutDict): earnoutOnDoc = False                    

                    typeDealCurve = typeDealIRRDurPlot(
                            typeDeal,
                            chronologyPlotDur,
                            chronologyPlotIrr, 
                            chronologyDuration, 
                            chronologyIrr, 
                            dealPlotDur=dealPlotDur, 
                            dealPlotIrr=dealPlotIrr, 
                            dealDuration=dealDuration,
                            dealIrr=dealIrr)

                    # Save charts to static images files
                    chartsDict = {
                        'stackedConsBarChart': {
                            'fig': stackedConsBarChart,
                            'size': {
                                'width': 378*2,
                                'height': 265*2
                            }
                        },
                        'entityMapPaymentsBarChart': {
                            'fig': entityMapPaymentsBarChart,
                            'size': {
                                'width': 378*2,
                                'height': 265*2
                            }
                        },
                        'scatterMapAmountChart': {
                            'fig': scatterMapAmountChart,
                            'size': {
                                'width': 378*2,
                                'height': 265*2
                            }
                        },
                        'countPieChart': {
                            'fig': countPieChart,
                            'size': {
                                'width': 378*2,
                                'height': 265*2
                            }
                        },
                        'chronologyCurve': {
                            'fig': typeDealCurve,
                            'size': {
                                'width': 756*2.5,
                                'height': 453*2.5
                            }
                        },
                    }
                    if bool(earnoutOnDoc) and bool(earnoutDict): 
                        chartsDict['earnoutChart'] = {'fig': earnoutChart, 'size': {'width': 756*2.5, 'height': 378*2.5}}
                    
                    saveChartsAsStaticImages(chartsDict)
                    generateDoc(creditInfoDict, typeDeal, earnoutOnDoc, chartsDict)


if __name__ == '__main__':
    pricingMap()