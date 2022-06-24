import numpy as np
import pandas as pd
pd.options.display.float_format = '{:.3f}'.format

from scipy.interpolate import interp1d

import warnings
warnings.filterwarnings("ignore")


def createRangeEOYs(StartYear, EndYear):
    return pd.date_range(StartYear, EndYear, freq='Y')

# CurveIPCAEValuesStartPeriods = [0.050, 0.0460, 0.040]
def fillIPCAERange(StartYear, EndYear, CurveIPCAEValuesStartPeriods=[0.00]):
    RangeEOY = createRangeEOYs(StartYear, EndYear)
    dfData = pd.DataFrame({'RefDate': RangeEOY, 'IPCA-E': np.nan})
    for i in range(len(CurveIPCAEValuesStartPeriods)):
        dfData['IPCA-E'].iloc[i] = CurveIPCAEValuesStartPeriods[i]
    dfData['IPCA-E'] = dfData['IPCA-E'].fillna(method='ffill')
    dfData['CumFactorIPCA-E'] = np.cumprod(1 + dfData['IPCA-E'])
    return dfData


# CurveInterestValuesStartPeriods = [0.050, 0.060]
def fillIInterestRange(StartYear, EndYear, CurveInterestValuesStartPeriods=[0.07]):
    RangeEOY = createRangeEOYs(StartYear, EndYear)
    dfData = pd.DataFrame({'RefDate': RangeEOY, 'Juros': np.nan})
    for i in range(len(CurveInterestValuesStartPeriods)):
        dfData['Juros'].iloc[i] = CurveInterestValuesStartPeriods[i]
    dfData['Juros'] = dfData['Juros'].fillna(method='ffill')
    dfData['CumFactorJuros'] = np.cumprod(1 + dfData['Juros'])
    return dfData


def curvesIPCAEAndInterest(
    StartYear, EndYear, CurveIPCAEValuesStartPeriods=False, CurveInterestValuesStartPeriods=False
):
    if CurveIPCAEValuesStartPeriods is not False:
        dfDataIPCA = fillIPCAERange(StartYear, EndYear, CurveIPCAEValuesStartPeriods)
    else:
        dfDataIPCA = fillIPCAERange(StartYear, EndYear)
    if CurveInterestValuesStartPeriods is not False:
        dfDataInterest = fillIInterestRange(StartYear, EndYear, CurveInterestValuesStartPeriods)
    else:
        dfDataInterest = fillIInterestRange(StartYear, EndYear)
    dfDataCons = dfDataIPCA.merge(dfDataInterest, on='RefDate', how='left')
    return dfDataCons


def amortizationSchedule(dfDataCurvesIPCAEInterest, RCL, PercRCL, PercAcordo=False):
    dfAmortizationSchedule = dfDataCurvesIPCAEInterest
    if PercAcordo != False:
        dfAmortizationSchedule['AmortizationAmount'] = (
            RCL * PercRCL * PercAcordo * dfAmortizationSchedule['CumFactorIPCA-E']
        )
    else:
        dfAmortizationSchedule['AmortizationAmount'] = RCL * PercRCL * dfAmortizationSchedule['CumFactorIPCA-E']
    return dfAmortizationSchedule

def calculateDuration(lastDuration, amountPrecatoriosNetBalanceEoP, amortizationAmount):
    if amountPrecatoriosNetBalanceEoP > 0:
        duration = 1
        return duration
    else:
        if lastDuration > 0 and lastDuration <= 1:
            duration = (amountPrecatoriosNetBalanceEoP + amortizationAmount) / (amortizationAmount)
            return duration
        else:
            duration = 0
            return duration


def stockAmountAnalysis(
    RefDatePricing, dfAmortizationSchedule, TotalAmountPrecatoriosBoP, PercSplitPrincipalInterest=1.0
):
    dfStockAmountAnalysis = dfAmortizationSchedule
    dfStockAmountAnalysis['RefDateShift'] = np.nan
    dfStockAmountAnalysis['RefDateShift'].iloc[0] = pd.to_datetime(RefDatePricing, infer_datetime_format=True)
    dfStockAmountAnalysis['RefDateShift'].iloc[1:] = dfStockAmountAnalysis['RefDate'].iloc[1:].shift(-1)
    dfStockAmountAnalysis['RefDateShift'].iloc[-1:] = pd.date_range(
        dfStockAmountAnalysis['RefDateShift'].iloc[-2:].values[0], periods=2, freq='Y'
    )[1]
    dfStockAmountAnalysis['RefDateShift'] = pd.to_datetime(
        dfStockAmountAnalysis['RefDateShift'], infer_datetime_format=True
    )
    dfStockAmountAnalysis['PercSplitPrincipalInterest'] = PercSplitPrincipalInterest
    dfStockAmountAnalysis['CountingDays'] = abs(
        dfStockAmountAnalysis['RefDateShift'] - dfStockAmountAnalysis['RefDate']
    ).dt.days
    dfStockAmountAnalysis['CountingDaysYearEQ'] = round(dfStockAmountAnalysis['CountingDays'] / 365.0, 2)
    dfStockAmountAnalysis['AmountPrecatoriosOC'] = np.nan
    dfStockAmountAnalysis['InflationAdj'] = np.nan
    dfStockAmountAnalysis['InterestAdj'] = np.nan
    dfStockAmountAnalysis['TotalAmtAdj'] = np.nan
    dfStockAmountAnalysis['AmountPrecatoriosNetBalanceEoP'] = np.nan
    dfStockAmountAnalysis['Duration'] = np.nan
    for i in range(len(dfStockAmountAnalysis)):
        if i == 0:
            dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[0] = TotalAmountPrecatoriosBoP
            dfStockAmountAnalysis['InflationAdj'].iloc[i] = (
                dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i]
                * dfStockAmountAnalysis['IPCA-E'].iloc[i]
                * dfStockAmountAnalysis['CountingDaysYearEQ'].iloc[i]
            )
            dfStockAmountAnalysis['InterestAdj'].iloc[i] = (
                dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i]
                * dfStockAmountAnalysis['PercSplitPrincipalInterest'].iloc[i]
                * dfStockAmountAnalysis['Juros'].iloc[i]
                * dfStockAmountAnalysis['CountingDaysYearEQ'].iloc[i]
            )
            dfStockAmountAnalysis['TotalAmtAdj'].iloc[i] = (
                dfStockAmountAnalysis['InflationAdj'].iloc[i] + dfStockAmountAnalysis['InterestAdj'].iloc[i]
            )
            dfStockAmountAnalysis['AmountPrecatoriosNetBalanceEoP'].iloc[i] = (
                dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i]
                + dfStockAmountAnalysis['TotalAmtAdj'].iloc[i]
                - dfStockAmountAnalysis['AmortizationAmount'].iloc[i]
                * dfStockAmountAnalysis['CountingDaysYearEQ'].iloc[i]
            )
            dfStockAmountAnalysis['Duration'].iloc[i] = dfStockAmountAnalysis['CountingDaysYearEQ'].iloc[i]
        else:
            dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i] = dfStockAmountAnalysis[
                'AmountPrecatoriosNetBalanceEoP'
            ].iloc[i - 1]
            dfStockAmountAnalysis['InflationAdj'].iloc[i] = (
                dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i] * dfStockAmountAnalysis['IPCA-E'].iloc[i]
            )
            dfStockAmountAnalysis['InterestAdj'].iloc[i] = (
                dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i]
                * dfStockAmountAnalysis['PercSplitPrincipalInterest'].iloc[i]
                * dfStockAmountAnalysis['Juros'].iloc[i]
            )
            dfStockAmountAnalysis['TotalAmtAdj'].iloc[i] = (
                dfStockAmountAnalysis['InflationAdj'].iloc[i] + dfStockAmountAnalysis['InterestAdj'].iloc[i]
            )
            dfStockAmountAnalysis['AmountPrecatoriosNetBalanceEoP'].iloc[i] = (
                dfStockAmountAnalysis['AmountPrecatoriosOC'].iloc[i]
                + dfStockAmountAnalysis['TotalAmtAdj'].iloc[i]
                - dfStockAmountAnalysis['AmortizationAmount'].iloc[i]
            )
            amountPrecatoriosNetBalanceEoP = dfStockAmountAnalysis['AmountPrecatoriosNetBalanceEoP'].iloc[i]
            amortizationAmount = dfStockAmountAnalysis['AmortizationAmount'].iloc[i]
            lastDuration = dfStockAmountAnalysis['Duration'].iloc[i - 1]
            dfStockAmountAnalysis['Duration'].iloc[i] = calculateDuration(
                lastDuration, amountPrecatoriosNetBalanceEoP, amortizationAmount
            )

    dfStockAmountAnalysis['Duration'] = np.where(
        dfStockAmountAnalysis['Duration'] < 0, 0, dfStockAmountAnalysis['Duration']
    )
    return dfStockAmountAnalysis

# PercSplitPrincipalInterest = 0.5
def getDuration(RefDatePricing, dfAmortizationSchedule, TotalAmountPrecatoriosBoP, PercSplitPrincipalInterest=1.0):
    dfStockAmountAnalysis = stockAmountAnalysis(
        RefDatePricing, dfAmortizationSchedule, TotalAmountPrecatoriosBoP, PercSplitPrincipalInterest
    )
    return dfStockAmountAnalysis['Duration'].sum()

def getDurationAdj(duration):
    dfAdj = pd.DataFrame(
        {
            'definedRanges': [0, 1, 2, 3, 4],
            'pct': [0.6, 0.5, 0.4, 0.33, 0.30],
            'period': [0, 0, 0, 0, 0],
            'adj': [0, 0, 0, 0, 0],
        }
    )
    if duration <= 1:
        for i in range(0, len(dfAdj)):
            if i == 0:
                dfAdj['period'].iloc[i] = 1
            else:
                dfAdj['adj'] = dfAdj['pct'] * dfAdj['period']
                return duration + dfAdj['adj'].sum()
    if duration >= 4:
        for i in range(0, len(dfAdj)):
            if i < 4:
                dfAdj['period'].iloc[i] = 1
            else:
                dfAdj['period'].iloc[i] = duration - dfAdj['definedRanges'].iloc[i]
                dfAdj['adj'] = dfAdj['pct'] * dfAdj['period']
                return duration + dfAdj['adj'].sum()
    for i in range(0, len(dfAdj)):
        if duration >= dfAdj['definedRanges'].iloc[i]:
            dfAdj['period'].iloc[i] = 1
            i = i + 1
        else:
            dfAdj['period'].iloc[i - 1] = duration - dfAdj['definedRanges'].iloc[i - 1]
            break
    dfAdj['adj'] = dfAdj['pct'] * dfAdj['period']
    return duration + dfAdj['adj'].sum()

def getInterpolScennarios():
    scennarios = {
        'breakeven': {
            'duration': [0.5] + [i for i in range(1, 8)],
            'Px': [89.44, 80, 64, 51.2, 40.96, 32.77, 26.21, 20.97],
            'IRR': [0.35] * 8,
        },
        'default': {
            'duration': [0.5] + [i for i in range(1, 8)],
            'Px': [70, 60, 50, 40, 30, 25, 22, 20],
            'IRR': [1.2041, 0.8, 0.5274, 0.4658, 0.4593, 0.4251, 0.39, 0.3592],
        },
        'aggressive': {
            'duration': [0.5] + [i for i in range(1, 8)],
            'Px': [65, 50, 45, 35, 28, 25, 22, 20],
            'IRR': [1.5562, 1.16, 0.61, 0.5325, 0.4847, 0.4251, 0.39, 0.3592],
        },
    }
    return scennarios


def getInterpolIRRAndPx(duration, scennarioName='aggressive'):
    dataInterpolation = getInterpolScennarios()[scennarioName]
    fnIRR = interp1d(dataInterpolation['duration'], dataInterpolation['IRR'], 'cubic')
    fnPx = interp1d(dataInterpolation['duration'], dataInterpolation['Px'], 'cubic')
    return {
        'scennarioName': scennarioName,
        'duration': duration,
        'interpolIRR': dataInterpolation['IRR'][-1]
        if duration >= dataInterpolation['duration'][-1]
        else fnIRR(duration).tolist(),
        'interpolPx': dataInterpolation['Px'][-1]
        if duration >= dataInterpolation['duration'][-1]
        else fnPx(duration).tolist(),
    }


######################## CALCULATE ########################
def calculateTradePriceGivenIRR(
    expectedIRR,
    durationYearEq,
    priceType='compound',
    currentValue=100.0,
    interestRate=0.08,
    inflationRate=0.05,
    preMocPeriodYearEq=0.0,
    gracePeriodYearEq=0.0,
    hairCutAuction=0.0,
):
    futureValue = calculateFutureValue(
        durationYearEq, currentValue, interestRate, inflationRate, preMocPeriodYearEq, gracePeriodYearEq, hairCutAuction
    )
    return futureValue / (1 + expectedIRR) ** durationYearEq


def calculateFutureValue(
    durationYearEq,
    currentValue=100.0,
    interestRate=0.08,
    inflationRate=0.05,
    preMocPeriodYearEq=0.0,
    gracePeriodYearEq=0.0,
    hairCutAuction=0.0,
):
    if durationYearEq <= gracePeriodYearEq:
        return (currentValue * (1 + inflationRate) ** durationYearEq) * (1 - hairCutAuction)
    else:
        return (
            currentValue
            * (
                ((1 + interestRate) ** preMocPeriodYearEq)
                * ((1 + inflationRate) ** gracePeriodYearEq)
                * ((1 + interestRate) ** (durationYearEq - gracePeriodYearEq - preMocPeriodYearEq))
            )
            * (1 - hairCutAuction)
        )


def calculateIRR(futureValue, tradedValue, periodYearEq, IRRtype='compound', earnout=0):
    return (
        (futureValue / tradedValue - 1.0) / periodYearEq
        if IRRtype == 'linear'
        else ((futureValue - earnout * (futureValue - tradedValue)) / tradedValue) ** (1 / periodYearEq) - 1.0
    )

def calculatePriceByDuration(duration, sliderInterestRate, sliderInflation, inputPreMocPeriodYearsEq, inputGracePeriodYearsEq):
    pxCurve = getInterpolIRRAndPx(duration)
    irr = round(pxCurve['interpolIRR'] * 100, 2)
    price =  round(calculateTradePriceGivenIRR(
                    expectedIRR=(irr / 100),
                    durationYearEq=duration,
                    interestRate=sliderInterestRate / 100.0,
                    inflationRate=sliderInflation / 100.0,
                    preMocPeriodYearEq=inputPreMocPeriodYearsEq,
                    gracePeriodYearEq=inputGracePeriodYearsEq,
                    ), 2)

    return price

def generateEarnoutPricingScennario(
    earnout,
    tradedValue,
    startDate,
    periods,
    endDate=None,
    incremental='12M',
    currentValue=100.0,
    interestRate=0.08,
    inflationRate=0.05,
    preMocPeriodYearEq=0.0,
    gracePeriodYearEq=0.0,
    hairCutAuction=0.0,
):
    futureValueEarnoutScennarios = []
    irrEarnoutScennarios = []
    datesEarnout = createRangeOfPeriods(startDate=startDate, endDate=endDate, incremental=incremental, periods=periods)
    periodsEarnout = countYearsInRangeOfPeriods(
        startDate=startDate, endDate=endDate, incremental=incremental, periods=periods
    )
    earnoutProRataTemporis = createRangeEarnOutProRateTemporis(
        earnout=earnout, startDate=startDate, endDate=endDate, incremental=incremental, periods=periods
    )
    for i in range(len(periodsEarnout)):
        futureValueEarnoutScennarios.append(
            calculateFutureValueEarnout(
                durationYearEq=periodsEarnout[i],
                tradedValue=tradedValue,
                currentValue=currentValue,
                interestRate=interestRate,
                inflationRate=inflationRate,
                preMocPeriodYearEq=preMocPeriodYearEq,
                gracePeriodYearEq=gracePeriodYearEq,
                hairCutAuction=hairCutAuction,
                earnout=earnoutProRataTemporis[i],
            )
        )
        if periodsEarnout[i] != 0:
            irrEarnoutScennarios.append(
                calculateIRR(
                    futureValue=futureValueEarnoutScennarios[i],
                    tradedValue=tradedValue,
                    periodYearEq=periodsEarnout[i],
                    IRRtype='compound',
                )
            )
        else:
            irrEarnoutScennarios.append(np.nan)
    return {
        'earnout': earnout,
        'tradedValue': tradedValue,
        'startDate': startDate,
        'periods': periods,
        'earnoutDecay': earnoutProRataTemporis,
        'datesEarnout': datesEarnout,
        'periodsEarnout': periodsEarnout,
        'futureValueEarnoutScennarios': futureValueEarnoutScennarios,
        'irrEarnoutScennarios': irrEarnoutScennarios,
    }

def calculateFutureValueEarnout(
    durationYearEq,
    tradedValue,
    currentValue=100.0,
    interestRate=0.08,
    inflationRate=0.05,
    preMocPeriodYearEq=0.0,
    gracePeriodYearEq=0.0,
    hairCutAuction=0.0,
    earnout=0.0,
):
    futureValue = calculateFutureValue(
        durationYearEq, currentValue, interestRate, inflationRate, preMocPeriodYearEq, gracePeriodYearEq, hairCutAuction
    )
    return futureValue - earnout * (futureValue - tradedValue)

def calculateFutureValue(
    durationYearEq,
    currentValue=100.0,
    interestRate=0.08,
    inflationRate=0.05,
    preMocPeriodYearEq=0.0,
    gracePeriodYearEq=0.0,
    hairCutAuction=0.0,
):
    if durationYearEq <= gracePeriodYearEq:
        return (currentValue * (1 + inflationRate) ** durationYearEq) * (1 - hairCutAuction)
    else:
        return (
            currentValue
            * (
                ((1 + interestRate) ** preMocPeriodYearEq)
                * ((1 + inflationRate) ** gracePeriodYearEq)
                * ((1 + interestRate) ** (durationYearEq - gracePeriodYearEq - preMocPeriodYearEq))
            )
            * (1 - hairCutAuction)
        )

def calculateTradePriceGivenIRR(
    expectedIRR,
    durationYearEq,
    priceType='compound',
    currentValue=100.0,
    interestRate=0.08,
    inflationRate=0.05,
    preMocPeriodYearEq=0.0,
    gracePeriodYearEq=0.0,
    hairCutAuction=0.0,
):
    futureValue = calculateFutureValue(
        durationYearEq, currentValue, interestRate, inflationRate, preMocPeriodYearEq, gracePeriodYearEq, hairCutAuction
    )
    return futureValue / (1 + expectedIRR) ** durationYearEq

def calculateIRR(futureValue, tradedValue, periodYearEq, IRRtype='compound'):
    return (
        (futureValue / tradedValue - 1.0) / periodYearEq
        if IRRtype == 'linear'
        else (futureValue / tradedValue) ** (1 / periodYearEq) - 1.0
    )

def createRangeEarnOutProRateTemporis(earnout, startDate, endDate=None, incremental='12M', periods=None):
    countPeriods = countYearsInRangeOfPeriods(
        startDate=startDate, endDate=endDate, incremental=incremental, periods=periods
    )
    return [earnout * (1 - (p / countPeriods[-1])) for p in countPeriods]

def countDaysInRangeOfPeriods(startDate, endDate=None, incremental='12M', periods=None):
    periods = createRangeOfPeriods(startDate=startDate, endDate=endDate, incremental=incremental, periods=periods)
    return [(p - periods[0]).days for p in periods]

def countYearsInRangeOfPeriods(startDate, endDate=None, incremental='12M', periods=None):
    periods = createRangeOfPeriods(startDate=startDate, endDate=endDate, incremental=incremental, periods=periods)
    return [round((p - periods[0]).days / 365.0, 2) for p in periods]

def createRangeOfPeriods(startDate, endDate=None, incremental='12M', periods=None):
    return (
        (
            pd.date_range(
                start=pd.to_datetime(startDate, infer_datetime_format=True),
                end=pd.to_datetime(endDate, infer_datetime_format=True),
                freq=incremental,
            )
        )
        if periods is None
        else (
            pd.date_range(
                start=pd.to_datetime(startDate, infer_datetime_format=True), freq=incremental, periods=periods
            )
        )
    )
