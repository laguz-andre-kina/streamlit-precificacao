import sys
sys.path.append('../')

from sqlalchemy import create_engine
import sqlalchemy
import streamlit as st
import pandas as pd
import numpy as np

import plotly.graph_objects as go

from .queries import *
from .constants import *

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

@st.cache(show_spinner=False, suppress_st_warning=True)
def ufOptions(entitiesDf, typeEnt):
    
    return entitiesDf.loc[entitiesDf['entitytype']==typeEnt, 'uf'].drop_duplicates().sort_values()

@st.cache(show_spinner=False, suppress_st_warning=True)
def courtNameOptions(entitiesDf, typeEnt, uf):
    
    # TODO: Create fix solution for ORGANIZACAO
    if typeEnt == 'ORGANIZACAO':
        return entitiesDf.loc[entitiesDf['entitytype']==typeEnt, 'courtname'].drop_duplicates().sort_values()
    
    return entitiesDf.loc[(entitiesDf['entitytype']==typeEnt) & (entitiesDf['uf']==uf), 'courtname'].drop_duplicates().sort_values()

@st.cache(show_spinner=False, suppress_st_warning=True)
def entitiesOptions(entitiesDf, typeEnt, uf, courtname):
    
    # TODO: Create fix solution for ORGANIZACAO
    if typeEnt == 'ORGANIZACAO':
        return entitiesDf.loc[entitiesDf['entitytype']==typeEnt, 'entityname'].drop_duplicates().sort_values()
    
    return entitiesDf.loc[(entitiesDf['entitytype']==typeEnt) & (entitiesDf['uf']==uf) & (entitiesDf['courtname'] == courtname), 'entityname'].drop_duplicates().sort_values()


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

    return fig

@st.cache(show_spinner=False, suppress_st_warning=True)
def entityMapPaymentsBarChart(entityMapDf):
    
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
            orientation='h',
            marker_color=COLORS_LIST[:4])
    ])

    fig.update_layout(title_text='Mapa de Pagamento',
        xaxis=dict(
            title='R$'
        ))

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

    fig.update_layout(title_text='Dispersão Montante Total por Ano',
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
    bins = [-np.inf, 100*K_TIMES, 500*K_TIMES, 1*M_TIMES, 5*M_TIMES, 20*M_TIMES, 50*M_TIMES, np.inf]
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