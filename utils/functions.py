import os, shutil
import sys
sys.path.append('../')

import boto3

from sqlalchemy import create_engine
import math
import sqlalchemy
import streamlit as st
import pandas as pd
import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .queries import *
from .constants import *
from .computations import *

############################ UTILS ############################
def deleteFilesFromFolder(dirPath: str) -> None: 
    for files in os.listdir(dirPath):
        path = os.path.join(dirPath, files)
        try:
            shutil.rmtree(path)
        except OSError:
            os.remove(path)

def numberToStrDict(value: float) -> dict:
    
    for key, unitDict in MEASURE_UNIT_DICT.items():
        if value >= unitDict['unit']: break

    return {
        'rawNumber': value,
        'rawNumberStr': f'{value:,.2f}',
        'reducedNumber': value/unitDict['unit'],
        'reducedNumberStr': f'{value/unitDict["unit"]:,.2f} {unitDict["suffix"]}',
        'suffix': unitDict['suffix']
    }

def deleteFilesFromS3(chartsDict: dict):
    s3 = boto3.client(
        's3',
        aws_access_key_id=st.secrets['AWS']['accessKey'],
        aws_secret_access_key=st.secrets['AWS']['secretKey'],
        region_name=st.secrets['AWS']['region']
        )

    for key in chartsDict.keys():
        response = s3.delete_object(Bucket=BUCKET, Key=f'{key}.png')

def saveChartsAsStaticImages(chartsDict: dict = {}) -> None:
    s3 = boto3.client(
        's3',
        aws_access_key_id=st.secrets['AWS']['accessKey'],
        aws_secret_access_key=st.secrets['AWS']['secretKey'],
        region_name=st.secrets['AWS']['region']
        )

    # Case empty dict
    if not bool(chartsDict): return None

    for key, chartInfo in chartsDict.items():
        
        fig = go.Figure(chartInfo['fig'])
        if key in ['chronologyCurve', 'earnoutChart']: 
            
            fig.update_layout(title=dict(font=dict(size=32)), width=chartInfo['size']['width'], height=chartInfo['size']['height'])

        img_bytes = fig.to_image(format='png')
        response = s3.put_object(Body=img_bytes, Bucket=BUCKET, Key=f'{key}.png')
        uploadFileUrl = s3.generate_presigned_url(
            ClientMethod='get_object', ExpiresIn=300, Params={'Bucket': BUCKET, 'Key': f'{key}.png'}
        )

        chartsDict[key]['pathToImage'] = uploadFileUrl

############################ CONNECTION TO DB ############################
@st.cache(allow_output_mutation=True, show_spinner=False, suppress_st_warning=True)
def createConnection():
    CNN_STRING = DB_CONNECTION_PASS
    cnn = create_engine(CNN_STRING)
    return cnn

############################ QUERIES/PANDAS ############################
@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getEntities(cnn):
    query = queryEntityDetails()
    
    return pd.read_sql(query, cnn)

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getQueue(idEntity, cnn):
    query = queryAdjusteQueue(idEntity)
    
    queue = pd.read_sql(query, cnn)
    
    return queue

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getEntityMap(idEntity, cnn):
    query = queryEntityMap(idEntity)

    entityMap = pd.read_sql(query, cnn)

    return entityMap

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getEntityRegime(idEntity, cnn):
    query = queryEntityRegime(idEntity)

    entityRegime = pd.read_sql(query, cnn)

    if len(entityRegime) > 1:
        st.error('Mais de um regime encontrado para o ente!!')

    return entityRegime

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getEntityStats(idEntity, cnn):
    query = queryEntityStats(idEntity)

    entityStats = pd.read_sql(query, cnn)

    if len(entityStats) > 1:
        st.error('Mais de uma metrica encontrada para o ente!!')

    return entityStats

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getEntityPlan(idEntity, cnn):
    query = queryEntityPlan(idEntity)

    entityPlan = pd.read_sql(query, cnn)

    if len(entityPlan) > 1:
        st.error('Mais de um plano encontrado para o ente!!')

    return entityPlan

@st.cache(hash_funcs={sqlalchemy.engine.base.Engine: id}, show_spinner=False, suppress_st_warning=True)
def getEntityDeal(idEntity, cnn):
    
    query = queryEntityDeal(idEntity)
    entityDeal = pd.read_sql(query, cnn)

    return entityDeal

@st.cache(show_spinner=False, suppress_st_warning=True)
def ufOptions(entitiesDf, typeEnt):
    
    return entitiesDf.loc[(entitiesDf['entitytype']==typeEnt)&~(entitiesDf['uf'].isnull()), 'uf'].dropna().drop_duplicates().sort_values()

@st.cache(show_spinner=False, suppress_st_warning=True)
def courtNameOptions(entitiesDf, typeEnt, uf):
    
    # TODO: Create fix solution for ORGANIZACAO
    if typeEnt == 'ORGANIZACAO':
        return entitiesDf.loc[entitiesDf['entitytype']==typeEnt, 'courtname'].dropna().drop_duplicates().sort_values()
    
    return entitiesDf.loc[(entitiesDf['entitytype']==typeEnt) & (entitiesDf['uf']==uf), 'courtname'].dropna().drop_duplicates().sort_values()

@st.cache(show_spinner=False, suppress_st_warning=True)
def entitiesOptions(entitiesDf, typeEnt, uf, courtname):
    
    # TODO: Create fix solution for ORGANIZACAO
    if typeEnt == 'ORGANIZACAO':
        return entitiesDf.loc[entitiesDf['entitytype']==typeEnt, 'entityname'].dropna().drop_duplicates().sort_values()
    
    return entitiesDf.loc[(entitiesDf['entitytype']==typeEnt) & (entitiesDf['uf']==uf) & (entitiesDf['courtname'] == courtname), 'entityname'].dropna().drop_duplicates().sort_values()


@st.cache(show_spinner=False, suppress_st_warning=True)
def getEntityId(entitiesDf, typeEnt, uf, courtname, entityname):
    dupEntitiesDf = entitiesDf.copy()
    
    # TODO: Create fix solution for ORGANIZACAO
    if typeEnt == 'ORGANIZACAO':
        dupEntitiesDf = dupEntitiesDf.loc[(dupEntitiesDf['entitytype']==typeEnt) & (dupEntitiesDf['courtname']==courtname) & (dupEntitiesDf['entityname']==entityname)]
        
    else:
        dupEntitiesDf = dupEntitiesDf.loc[(dupEntitiesDf['entitytype']==typeEnt) & (dupEntitiesDf['courtname']==courtname) & (dupEntitiesDf['uf']==uf) & (dupEntitiesDf['entityname']==entityname)]
        
        
    if len(dupEntitiesDf) > 1:
        st.error('Existe duplicidade para a entidade selecionada. Validar entidade selecionada!!')
        
    return dupEntitiesDf['entityid'].iloc[0]

@st.cache(show_spinner=False, suppress_st_warning=True)
def createCurveIrrXDuration(chronologyPricePrct, durationLowerLimit, hairCutAuction=0):
    step = 0.2
    minValue = durationLowerLimit if durationLowerLimit < 2 else durationLowerLimit - step * 2

    stopCalc = False
    baseCalcDur = minValue
    stepsAfterWaterLine = 5
    stopFlag = 0
    irr = 100

    durationPlot = []
    irrPlot = []

    while not bool(stopCalc) and stopFlag < stepsAfterWaterLine:
        try:
            vfut = calculateFutureValue(baseCalcDur, hairCutAuction=hairCutAuction)
            irr = round(calculateIRR(futureValue=vfut, tradedValue=chronologyPricePrct, periodYearEq=baseCalcDur), 2) * 100

            durationPlot.append(baseCalcDur)
            irrPlot.append(irr)

        except:
            pass

        if irr < 35:
            stopFlag += 1

        baseCalcDur += step

    return durationPlot, irrPlot

############################ PLOTS ############################

@st.cache(show_spinner=False, suppress_st_warning=True)
def consolidatedAmountYearBarChart(queueDf):
    baseDf = queueDf.copy()
    
    stackedBarTypeDf = baseDf.groupby(by=['budgetyear', 'type']).sum()[['value']].reset_index()

    fig = go.Figure(data=[
        go.Bar(name='ALIMENTAR', x=stackedBarTypeDf.loc[stackedBarTypeDf['type']=='ALIMENTAR', 'budgetyear'].values, y=stackedBarTypeDf.loc[stackedBarTypeDf['type']=='ALIMENTAR', 'value'].values, marker_color=COLORS_LIST[0]),
        go.Bar(name='COMUM', x=stackedBarTypeDf.loc[stackedBarTypeDf['type']=='COMUM', 'budgetyear'].values, y=stackedBarTypeDf.loc[stackedBarTypeDf['type']=='COMUM', 'value'].values, marker_color=COLORS_LIST[1])
    ])

    fig.update_layout(barmode='stack',
        title_text='Fila Consolidada por Tipo de Precatório',
        xaxis=dict(
            title='Ano'
        ),
        yaxis=dict(
            title='R$'
        ))

    fig.write_image('test.png', engine='kaleido')

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True)
def entityMapPaymentsBarPlot(entityMapDf):
    
    renameDict = {
        'finalamt': 'Valor Final', 
        'issuedamtcurrentyear': 'Montante Emitido', 
        'paidamtcurrentyear': 'Montante Pago', 
        'openamt': 'Montante em Aberto'
    }
    baseDf = entityMapDf.copy()

    # Possible check in case 'paidamtcurrentyear' not in cols
    try:
        baseDf['paidamtcurrentyear'] = baseDf['paidamtcurrentyear']*-1
    except:
        baseDf['paidamtcurrentyear'] = 0.0
    baseDf.rename(columns=renameDict, inplace=True)
    baseDf = baseDf[renameDict.values()].T

    fig = go.Figure(data=[
        go.Bar(x=list(baseDf.values.flatten()),
            y=list(baseDf.index),
            text=[numberToStrDict(vl)['reducedNumberStr'] for vl in list(baseDf.values.flatten())],
            orientation='h',
            marker_color=COLORS_LIST[:4])
    ])

    fig.update_layout(title_text='Mapa de Pagamento CNJ',
        xaxis=dict(
            title='R$'
        ))

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True)
def priceByDurationBarChart(durations, prices):

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=durations,
            y=prices,
            text=['Acordo', 'Base Case', 'C/ Ajuste', 'Pior'],
            marker=dict(
                color=COLORS_LIST
            )
        )
    )

    fig.update_layout(title_text='Preço por faixa de duration',
        xaxis=dict(
            title='Duration (Anos)'
            
        ),
        yaxis=dict(
            title='Preço (%)'
        )
    )
    # fig.update_traces(width=0.5)

    return fig


@st.cache(show_spinner=False, suppress_st_warning=True)
def entityScatterPlot(queueDf):
    renameDict = {'budgetyear': 'Ano', 'value': 'Montante Total', 'id': 'Número de Créditos'}

    baseDf = queueDf.copy()
    groupDf = baseDf.groupby(by=['budgetyear']).agg({'value': 'sum', 'id': 'count'}).reset_index()

    groupDf.rename(columns=renameDict, inplace=True)


    fig = go.Figure(data=go.Scatter(
        x=groupDf['Ano'].values,
        y=groupDf['Montante Total'].values,
        mode='markers',
        text=[f'#{count}' for count in groupDf['Número de Créditos'].values],
        marker=dict(
            size=groupDf['Número de Créditos'].values,
            sizemode='area',
            sizeref=2.*max(groupDf['Número de Créditos'].values)/(40.**2),
            color=BIG_COLOR_LIST,
        )
    ))

    fig.update_layout(title_text='Dispersão do Montante Total a Pagar Pela Qtde. de Créditos',
        xaxis=dict(
            title='Ano'
        ),
        yaxis=dict(
            title='R$'
        ))

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True)
def entityCountPieChart(queueDf):
    baseDf = queueDf.copy()

    # Create bins
    bins = [-np.inf, 100*MEASURE_UNIT_DICT['K_TIMES']['unit'], 500*MEASURE_UNIT_DICT['K_TIMES']['unit'], 1*MEASURE_UNIT_DICT['M_TIMES']['unit'], 5*MEASURE_UNIT_DICT['M_TIMES']['unit'], 20*MEASURE_UNIT_DICT['M_TIMES']['unit'], 50*MEASURE_UNIT_DICT['M_TIMES']['unit'], np.inf]
    labels = ['< 100K', '100K ~ 500K', '500K ~ 1MM', '1MM ~ 5MM', '5MM ~ 20MM', '20MM ~ 50MM', '> 50MM']

    baseDf['bandas'] = pd.cut(baseDf['value'], bins=bins, labels=labels, right=False, include_lowest=True)

    # Make sure order is correct
    groupDf = baseDf.groupby(by=['bandas']).count()[['id']]
    groupDf = groupDf.loc[labels, :]

    fig = go.Figure(
        data=[go.Pie(
            labels=list(groupDf.index),
            values=groupDf.values.flatten()
        )]
    )

    fig.update_traces(
        hoverinfo='label+percent',
        textinfo='value',
        marker=dict(
            colors=COLORS_LIST
        )
    )

    fig.update_layout(title_text='Composição da Fila de Precatórios por Banda de Valor')

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True)
def chronologyIRRDurPlot(chronologyPlotDur, chronologyPlotIrr, chronologyDuration, chronologyIrr, **kwargs):

    chronologyWaterLine = np.full(len(chronologyPlotDur), 35)

    # Chart with deal
    if 'dealPlotDur' in kwargs:
        dealWaterLine = np.full(len(kwargs['dealPlotDur']), 35)

        fig = make_subplots(rows=2, cols=1)

        ###################### CHRONOLOGY ######################

        fig.add_trace(go.Scatter(
            x=[chronologyDuration],
            y=[chronologyIrr],
            mode='markers',
            marker_symbol='cross',
            name='TIR Compra Cronologia',
            legendrank=1,
            marker=dict(
                color=COLORS_LIST[0],
                size=12
            )
        ), row=1, col=1)

        # Line Chart
        fig.add_trace(go.Scatter(
            x=chronologyPlotDur,
            y=chronologyPlotIrr,
            mode='lines+markers',
            name='Curva TIR Cronologia',
            legendrank=3,
            line=dict(
                color=COLORS_LIST[1]
            )
        ), row=1, col=1)

        # Waterline
        fig.add_trace(go.Scatter(
            x=chronologyPlotDur,
            y=chronologyWaterLine,
            mode='lines',
            name='35%',
            legendrank=5,
            line=dict(
                color='#B25068'
            )
        ), row=1, col=1)

        ###################### DEAL ######################

        fig.add_trace(go.Scatter(
            x=[kwargs['dealDuration']],
            y=[kwargs['dealIrr']],
            mode='markers',
            marker_symbol='cross',
            name='TIR Compra Acordo',
            legendrank=2,
            marker=dict(
                color=COLORS_LIST[2],
                size=12
            )
        ), row=2, col=1)

        # Line Chart
        fig.add_trace(go.Scatter(
            x=kwargs['dealPlotDur'],
            y=kwargs['dealPlotIrr'],
            mode='lines+markers',
            name='Curva TIR Acordo',
            legendrank=4,
            line=dict(
                color=COLORS_LIST[3]
            )
        ), row=2, col=1)

        # Waterline
        fig.add_trace(go.Scatter(
            x=kwargs['dealPlotDur'],
            y=dealWaterLine,
            name='35%',
            mode='lines',
            showlegend=False,
            line=dict(
                color='#B25068'
            )
        ), row=2, col=1)

        # Update axis
        fig.update_xaxes(title_text='Duration (Anos)', row=2, col=1)

        fig.update_yaxes(title_text='TIR Cronologia (%)', row=1, col=1)
        fig.update_yaxes(title_text='TIR Acordo (%)', row=2, col=1)

        fig.update_layout(
            title={
                'text': 'Análise de Sensibilidade da TIR',
            },
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            )
        )


    else: 
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[chronologyDuration],
            y=[chronologyIrr],
            mode='markers',
            marker_symbol='cross',
            name='TIR Compra Cronologia',
            marker=dict(
                color=COLORS_LIST[0],
                size=12
            )
        ))

        # Line Chart
        fig.add_trace(go.Scatter(
            x=chronologyPlotDur,
            y=chronologyPlotIrr,
            mode='lines+markers',
            name='Curva TIR Cronologia',
            line=dict(
                color=COLORS_LIST[1]
            )
        ))

        # Waterline
        fig.add_trace(go.Scatter(
            x=chronologyPlotDur,
            y=chronologyWaterLine,
            mode='lines',
            name='35%',
            line=dict(
                color='#B25068'
            )
        ))

        fig.update_layout(
            xaxis_title='Duration (Anos)',
            yaxis_title='TIR (%)',
            title={
                'text': 'Análise de Sensibilidade da TIR',
            },
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            )
        )

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True, allow_output_mutation=True )
def earnoutPlot(earnoutDict):

    # Adjust irrEarnout
    earnoutIrr  = [earnout if not math.isnan(earnout) else earnoutDict['irrEarnoutScennarios'][index+1]*2 for index, earnout in enumerate(earnoutDict['irrEarnoutScennarios'])]  * 100
    earnoutDates  = earnoutDict['datesEarnout'] 
    earnoutDecay = [earnoutDec * 100 for earnoutDec in earnoutDict['earnoutDecay']]

    baseDates = pd.date_range(start=earnoutDates[0], end=earnoutDates[-1], freq='6M')
    baseEarnoutIrr = [round(earnoutIrr[list(earnoutDates).index(date)] * 100, 2) if (date in earnoutDates) else None for date in baseDates]

    fig = make_subplots(specs=[[{"secondary_y": True}]])


    fig.add_trace(
        go.Bar(
            x=baseDates,
            y=baseEarnoutIrr,
            text=[f'{irr}%' if bool(irr) else '' for irr in baseEarnoutIrr],
            name='TIR Earnout (%)',
            marker_color=COLORS_LIST[0],
        ), secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=earnoutDates,
            y=earnoutDecay,
            name='Earnout (%)',
            mode='lines+markers',
            line=dict(
                color=COLORS_LIST[4]
            )
        ), secondary_y=True
    )

    fig.update_yaxes(title_text='TIR (%)', secondary_y=False)
    fig.update_yaxes(title_text='Earnout (%)', secondary_y=True)

    fig.update_layout(
        title_text='Cenário de Earnout',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            )
    )

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True, allow_output_mutation=True )
def calculateFutureValueEarnoutPlot(
    tradedValue,
    currentValue,
    interestRate,
    inflationRate,
    preMocPeriodYearEq,
    gracePeriodYearEq,
    hairCutAuction,
    earnout,
    pctInterestTradedValue,
):
    duration_X = np.arange(start=0.00, stop=8.00, step=0.5)
    calcValue_y = [
        calculateFutureValueEarnout(
        durationYearEq=dur,
        tradedValue=tradedValue,
        currentValue=currentValue,
        interestRate=interestRate,
        inflationRate=inflationRate,
        preMocPeriodYearEq=preMocPeriodYearEq,
        gracePeriodYearEq=gracePeriodYearEq,
        hairCutAuction=hairCutAuction,
        earnout=earnout,
        pctInterestTradedValue=pctInterestTradedValue)

        for dur in duration_X
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=duration_X,
            y=calcValue_y,
            text=[f'{calc:,.2f} %' for calc in calcValue_y],
            mode='lines+markers',
            line=dict(
                color=COLORS_LIST[1]
            ),
        )
    )

    fig.update_layout(
        title='Sensibilidade do Earnout',
        xaxis_title='Duration (Anos)',
        yaxis_title='Earnout (%)'
    )

    return fig


@st.cache(show_spinner=False, suppress_st_warning=True)
def typeDealIRRDurPlot(typeDeal, chronologyPlotDur, chronologyPlotIrr, chronologyDuration, chronologyIrr, **kwargs):

    chronologyWaterLine = np.full(len(chronologyPlotDur), 35)

    # Chart with deal
    if typeDeal == 'Acordo' and hasattr(kwargs['dealPlotDur'], '__len__'):

        dealWaterLine = np.full(len(kwargs['dealPlotDur']), 35)
        fig = go.Figure()

        ###################### DEAL ######################

        fig.add_trace(go.Scatter(
            x=[kwargs['dealDuration']],
            y=[kwargs['dealIrr']],
            mode='markers',
            marker_symbol='cross',
            name='TIR Compra Acordo',
            legendrank=2,
            marker=dict(
                color=COLORS_LIST[2],
                size=12
            )
        ))

        # Line Chart
        fig.add_trace(go.Scatter(
            x=kwargs['dealPlotDur'],
            y=kwargs['dealPlotIrr'],
            mode='lines+markers',
            name='Curva TIR Acordo',
            legendrank=4,
            line=dict(
                color=COLORS_LIST[3]
            )
        ))

        # Waterline
        fig.add_trace(go.Scatter(
            x=kwargs['dealPlotDur'],
            y=dealWaterLine,
            name='35%',
            mode='lines',
            showlegend=False,
            line=dict(
                color='#B25068'
            )
        ))

        # Update axis
        fig.update_xaxes(title_text='Duration (Anos)')
        fig.update_yaxes(title_text='TIR Acordo (%)')

        fig.update_layout(
            title={
                'text': 'Análise de Sensibilidade da TIR',
            },
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            )
        )

    elif typeDeal == 'Acordo' and not hasattr(kwargs['dealPlotDur'], '__len__'):
        fig = go.Figure()

    else: 
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[chronologyDuration],
            y=[chronologyIrr],
            mode='markers',
            marker_symbol='cross',
            name='TIR Compra Cronologia',
            marker=dict(
                color=COLORS_LIST[0],
                size=12
            )
        ))

        # Line Chart
        fig.add_trace(go.Scatter(
            x=chronologyPlotDur,
            y=chronologyPlotIrr,
            mode='lines+markers',
            name='Curva TIR Cronologia',
            line=dict(
                color=COLORS_LIST[1]
            )
        ))

        # Waterline
        fig.add_trace(go.Scatter(
            x=chronologyPlotDur,
            y=chronologyWaterLine,
            mode='lines',
            name='35%',
            line=dict(
                color='#B25068'
            )
        ))

        fig.update_layout(
            xaxis_title='Duration (Anos)',
            yaxis_title='TIR (%)',
            title={
                'text': 'Análise de Sensibilidade da TIR',
            },
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            )
        )

    return fig
