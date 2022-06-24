from turtle import width
from sqlalchemy import create_engine
import datetime as dt

import streamlit as st
import numpy as np
import pandas as pd

from scipy import optimize
import scipy

from utils.functions import *
from utils.constants import *
from utils.computations import *

import plotly.graph_objects as go

startYear = '2022'
endYear = '2031'

entityId = 115

cnn = createConnection()

entities = getEntities(cnn)
queueDf = getQueue(entityId, cnn)

entityMapDf = getEntityMap(entityId, cnn)
entityRegimeDf = getEntityRegime(entityId, cnn)
entityStatsDf = getEntityStats(entityId, cnn)
entityPlanDf = getEntityPlan(entityId, cnn)
entityDealDf = getEntityDeal(entityId, cnn)

isinstance(entityDealDf['termosacordo'].iloc[0], type(None))

dateInterestDf = curvesIPCAEAndInterest(startYear, endYear)

paymentExpectation = (entityPlanDf['amt'] * entityPlanDf['amtperiodeq']).iloc[0]

dateAmortizationDf = amortizationSchedule(dateInterestDf, paymentExpectation)


entityPlanDf['exercicio'].iloc[0]

# entityDealDf['termosacordo'].iloc[0]['texto']

entityPlan = pd.read_sql('SELECT * FROM entityplan', cnn)
pd.read_sql('SELECT * FROM entitydealstatustype', cnn)


entityPlan.loc[entityPlan['amt'].isnull()]

pd.read_sql("SELECT * FROM entity WHERE id=1487", cnn)
pd.read_sql("SELECT * FROM entitydetails WHERE entity=1487", cnn)

durationBase = 0.52
sliderInterestRate = 8
sliderInflation = 5
inputPreMocPeriodYearsEq = 0
inputGracePeriodYearsEq = 0

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

durationBand = np.arange(0, 5, 0.25)
waterLine = np.full(len(durationBand), 35)

len(durationBand)

durationPlot = []
irrPlot = []

for dur in durationBand:
    try:
        irr = round(getInterpolIRRAndPx(dur)['interpolIRR']*100, 2)
        durationPlot.append(dur)
        irrPlot.append(irr)

    except:
        pass

import plotly.graph_objects as go

