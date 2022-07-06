import sys
import numbers
import datetime as dt

from utils.functions import numberToStrDict

sys.path.append('../')

from utils.constants import *

from num2words import num2words
from fpdf import FPDF

def adjustNum2Words(value, monetary = False):
    # Make sure its rounded
    baseValue = round(value, 2)
    # If has decimal part break in 2 parts else simple num2words
    if not float(baseValue).is_integer():
        baseValueExtended = num2words(baseValue, lang='pt-br')
        decimalPartValueExtended = num2words(round((baseValue % 1) * 100, 2) , lang='pt-br')

        baseValueExtendedSplited = baseValueExtended.split('vírgula')
        baseValueExtendedSplited[1] = decimalPartValueExtended

        returnTxt = 'vírgula '.join(baseValueExtendedSplited)

    else:
        returnTxt = num2words(baseValue, lang='pt-br')

    if not bool(monetary): return returnTxt

    if 'vírgula' in returnTxt: 
        return f'{returnTxt.replace("vírgula", "reais e")} centavos'
    else:
        return f'{returnTxt} reais'


def numToStr(value):

    if isinstance(value, numbers.Number):
        return f'{value:,.2f}'.replace('.', '#').replace(',', '.').replace('#', ',')
    else:
        return value

###################### BASE TEXTS ######################
def creditHeader(processNumber, entityType, entityUf, entityName, creditType):
    entityNameStr = f'{entityType}: {entityName}' if entityType == 'ESTADO' else f'{entityType}: {entityName}/{entityUf}'
    
    return f"""Precatório: {creditType}\nProcesso: {processNumber}\n{entityNameStr}""".encode('latin-1', 'replace').decode('latin-1')

def baseText(creditType, creditId, processNumber, entityType, entityRegime, entityBudgetYear, purchaseAmount, entityName, entityUf):
    purchaseValueExtended = adjustNum2Words(round(purchaseAmount, 2), monetary=True)
    entityNameStr = f'{entityType}: {processNumber}' if entityType == 'ESTADO' else f'{entityType}: {entityName}/{entityUf}'
    baseText = f"""Precatório {creditType}, número {creditId}, expedido junto ao processo {processNumber}, em face do(a) {entityName if entityType == 'ESTADO' else f'{entityName}/{entityUf}'}, ente inscrito no Regime {entityRegime} de Pagamentos, ordem orçamentária {entityBudgetYear}, passível de aquisição pelo valor máximo de R$ {numToStr(purchaseAmount)} ({purchaseValueExtended})."""

    return baseText.encode('latin-1', 'replace').decode('latin-1')

def federativeBaseText(creditType, creditId, creditProcessId, purchaseAmount, pricePercentage):

    purchaseAmountExtended = adjustNum2Words(round(purchaseAmount, 2), monetary=True)
    adjPricePercentage = round(pricePercentage*100, 2)
    adjPricePercentageExtended = adjustNum2Words(adjPricePercentage)

    baseText = f"""Precatório {creditType}, número {creditId}, expedido junto ao processo {creditProcessId}, em face da União, passível de aquisição pelo valor máximo de R$ {numToStr(purchaseAmount)} ({purchaseAmountExtended}), equivalente à {adjPricePercentage}% ({adjPricePercentageExtended} por cento) do montante liquido atualizado."""
    return baseText

def chronologyText(creditQueuePosition, percentageToPayCreditPosition, chronologyDuration, entityPaymentExpectation):
    entityPaymentExpectationMonthly = round(entityPaymentExpectation / 12, 2)
    entityPaymentExpectationMonthlyExtended = adjustNum2Words(entityPaymentExpectationMonthly, monetary=True)
    percentageToPayCreditPositionExtended = adjustNum2Words(percentageToPayCreditPosition)
    creditQueuePositionAdj = numToStr(creditQueuePosition)[:-3]

    chronologyText = f"""O preço apresentado considera a expectativa de recebimento via ordem cronológica em sua elaboração. Assim, dado que o precatório ocupa a posição {creditQueuePositionAdj}° na fila de pagamento, e que, para a sua efetiva liquidação, o ente deverá quitar {numToStr(percentageToPayCreditPosition)}% ({percentageToPayCreditPositionExtended}) do montante do estoque, a expectativa de pagamento é de {numToStr(chronologyDuration)} anos, ante o desembolso mensal previsto de R$ {numToStr(entityPaymentExpectationMonthly)} ({entityPaymentExpectationMonthlyExtended}) pelo ente junto ao Plano de Pagamentos."""

    return chronologyText.encode('latin-1', 'replace').decode('latin-1')

def dealText(dealNoticeType, dealNoticeNumber, dealPrice, dealDuration, dealDisbursementMonthly):

    dealPriceExtended = adjustNum2Words(dealPrice)
    dealDurationExtended = adjustNum2Words(dealDuration)
    dealDisbursementMonthlyExtended = adjustNum2Words(dealDisbursementMonthly, monetary=True)

    dealText = f"""O preço apresentado considera a política de acordos do ente em sua elaboração. Tal política, conforme {dealNoticeType} {dealNoticeNumber}, estabelece proposta de deságio em {numToStr(dealPrice)}% ({dealPriceExtended} por cento), com perspectiva de recebimento em {numToStr(dealDuration)} ({dealDurationExtended}) anos, ante o desembolso mensal previsto de R$ {numToStr(dealDisbursementMonthly)} ({dealDisbursementMonthlyExtended}) pelo ente junto ao Plano de Pagamentos."""

    return dealText.encode('latin-1', 'replace').decode('latin-1')

def earnoutText(earnout, periods, startDate):

    earnoutPrct = round(earnout * 100, 2)
    dateAdj = f'{startDate[8:10]}/{startDate[5:7]}/{startDate[0:4]}'
    earnoutExtended = adjustNum2Words(earnoutPrct)
    periodsExtended = adjustNum2Words(periods)

    earnoutText = f"""Fica ainda estabelecido 'earn-out' pro-rata temporis de {numToStr(earnoutPrct)}% ({earnoutExtended} por cento) onde o valor base para incidência do percentual corresponde ao valor recebido excluindo-se o desembolso inicial. O prazo de vigente do 'earn-out' será de {numToStr(periods)} anos a partir da data de liquidação."""

    return earnoutText.encode('latin-1', 'replace').decode('latin-1')

def conclusionText(creditorName, contractualFees):

    contractualFeesExtended = adjustNum2Words(contractualFees)
    contractualFeesText = 'sem reserva de honorários contratuais' if not bool(contractualFees) else f'ressalvados honorários contratuais de {numToStr(contractualFees)}% ({contractualFeesExtended} por cento)'

    conclusionText = f"""Fica ressalvado que o presente valor considera a cessão da totalidade liquida do crédito do(a) credor(a) {creditorName.upper()}, (excluindo-se assim contribuições homologadas em conta de execução e Imposto de Renda na forma da legislação vigente), {contractualFeesText}, e que o precatório, e seu respectivo processo, serão alvo de diligência onde, encontradas ocorrências que diminuam este valor (prioridade paga, bloqueio, sequestro, penhora, compensação, acordo, etc.), o dispendido em liquidação poderá ser alterado na proporção do incidente ocorrido.\n\nPor fim, registre-se que toda a precificação se baseia em fontes públicas de informação junto aos Tribunais Regionais e Federais. Estas informações não necessariamente apresentam valores atualizados de requisição, estoque ou até mesmo de previsão de pagamento, levando o presente valor de aquisição a considerar estas incertezas em sua elaboração."""

    return conclusionText.encode('latin-1', 'replace').decode('latin-1')

def entityAnalyticsAndKPIsText(queueRefdate, queueTotalAmount, entityRegime, entityRCL, entityRCLYear, entityPaymentExpectation, entityPaymentExpectationYear):

    analyticsText = f"""Data Atualização da Fila: {queueRefdate}\tMontante Total da Fila: {numToStr(queueTotalAmount)}\tRegime do Ente: {entityRegime}\tRCL do Ente: {numToStr(entityRCL)} (Ano {entityRCLYear})\tExpectativa de Pgto. do Ente: {numToStr(entityPaymentExpectation)} (Ano {entityPaymentExpectationYear})\t"""

    return analyticsText.encode('latin-1', 'replace').decode('latin-1')

def federativeContractualText(creditorName, contractualFees) -> str:

    contractualFeesExtended = adjustNum2Words(contractualFees)
    contractualFeeText = f'ressalvados honorários contratuais de {numToStr(contractualFees)}% ({contractualFeesExtended} por cento)' if bool(contractualFees) else 'sem reserva de honorários contratuais'

    text = f"""Fica ressalvado que o presente valor considera a cessão da totalidade liquida do crédito do(a) credor(a) {creditorName.upper()}, (excluindo-se assim contribuições homologadas em conta de execução e Imposto de Renda na forma da legislação vigente), {contractualFeeText}, e que o precatório, e seu respectivo processo, serão alvo de diligência onde, encontradas ocorrências que diminuam este valor (prioridade paga, bloqueio, sequestro, penhora, compensação, acordo, etc.), o dispendido em liquidação poderá ser alterado na proporção do incidente ocorrido."""

    return text.encode('latin-1', 'replace').decode('latin-1')

def federativeConclusionText() -> str:

    text = f"""Por fim, registre-se que toda a precificação se baseia em fontes públicas de informação junto aos Tribunais Regionais e Federais. Estas informações não necessariamente apresentam valores atualizados de requisição, estoque ou até mesmo de previsão de pagamento, levando o presente valor de aquisição a considerar estas incertezas em sua elaboração."""

    return text.encode('latin-1', 'replace').decode('latin-1')

###################### CLASS ######################
class CreditDoc(FPDF):

    def __init__(self, orientation: str, unit: str, format: tuple, creditInfoDict : dict = {}) -> None:
        super().__init__(orientation, unit, format)
        self.creditInfoDict = creditInfoDict
        self.options()

    def options(self) -> None:
        self.alias_nb_pages()
        self.add_page()

    def header(self) -> None:
        self.image(PDF_HEADER_IMG, w=71, h=24, type='PNG')
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.ln(BREAK_LINE_HEIGHT)

    def footer(self) -> None:
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.set_y(-15)
        # Page number
        self.cell(0, 10, 'Av. Brigadeiro Luiz Antonio, 2503 | CJ. 112 | Jardim Paulista | São Paulo | SP | 01401 001 | laguz.com.br', 0, 0, 'C')

    # Write pdf
    def writeTitle(self, title: str, cellHeight: int = CELL_HEIGHT) -> None:
        self.set_font('Arial', style='B', size=TITLE_FONT_SIZE)
        self.cell(0, cellHeight, title, 0, 1, 'C')
        self.ln(BREAK_LINE_HEIGHT)

    def writeCreditHeader(self) -> None:
        headerText = creditHeader(
            self.creditInfoDict['processNumber'],
            self.creditInfoDict['entityType'],
            self.creditInfoDict['entityUf'],
            self.creditInfoDict['entityName'],
            self.creditInfoDict['creditType'],
            )
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, headerText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeFederativeCreditHeader(self) -> None:
        headerText = f"""Precatório: {self.creditInfoDict['creditType']}\nProcesso: {self.creditInfoDict['creditProcessId']}\nUnião"""
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, headerText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeFederativeBaseText(self) -> None:
        baseText = federativeBaseText(
            self.creditInfoDict['creditType'],
            self.creditInfoDict['creditId'],
            self.creditInfoDict['creditProcessId'],
            self.creditInfoDict['purchaseAmount'],
            self.creditInfoDict['pricePercentage']
        )
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, baseText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeFederativeEarnoutText(self) -> None:
        if not bool(self.creditInfoDict['earnoutText']): return None

        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, self.creditInfoDict['earnoutText'], 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeFederativeContractualText(self) -> None:
        
        baseText = federativeContractualText(
            self.creditInfoDict['creditorName'],
            self.creditInfoDict['contractualFees']
            )
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, baseText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeFederativeConclusionText(self) -> None:
        baseText = federativeConclusionText()

        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, baseText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeText(self, text) -> None:
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, text, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeBaseText(self) -> None:
        bodyText = baseText(
            self.creditInfoDict['creditType'],
            self.creditInfoDict['creditId'],
            self.creditInfoDict['processNumber'],
            self.creditInfoDict['entityType'],
            self.creditInfoDict['entityRegime'],
            self.creditInfoDict['entityBudgetYear'],
            self.creditInfoDict['purchaseAmount'],
            self.creditInfoDict['entityName'],
            self.creditInfoDict['entityUf'])

        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, bodyText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeDealText(self, typeDeal: str) -> None:
        if typeDeal == 'Cronologia':
            bodyText = chronologyText(
                self.creditInfoDict['creditQueuePosition'],
                self.creditInfoDict['percentageToPayCreditPosition'],
                self.creditInfoDict['chronologyDuration'],
                self.creditInfoDict['entityPaymentExpectation']
                )
        elif typeDeal=='Acordo':
            bodyText = dealText(
                self.creditInfoDict['dealNoticeType'], 
                self.creditInfoDict['dealNoticeNumber'], 
                self.creditInfoDict['dealPrice'], 
                self.creditInfoDict['dealDuration'], 
                self.creditInfoDict['dealDisbursementMonthly']
                )

        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, bodyText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeEarnoutText(self) -> None:
        bodyText = earnoutText(
            self.creditInfoDict['earnout'],
            self.creditInfoDict['periods'],
            self.creditInfoDict['startDate']
            )
        
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, bodyText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeConclusionText(self) -> None:
        bodyText = conclusionText(
            self.creditInfoDict['creditorName'], 
            self.creditInfoDict['contractualFees']
            )
        
        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, bodyText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def insertKPI(self, kpiHeader, kpiValue, x, y):
        # Write header
        self.set_font('Arial', style='B', size=KPI_HEADER_FONT_SIZE)
        self.text(x=x, y=y, txt=kpiHeader)

        # Write value
        self.set_font('Arial', style='', size=KPI_VALUE_FONT_SIZE)
        self.text(x=x, y=y+7.5, txt=kpiValue)

    def writeEntityAnalyticsText(self) -> None:
        bodyText = entityAnalyticsAndKPIsText(
            self.creditInfoDict['queueRefdate'],
            self.creditInfoDict['queueTotalAmount'],
            self.creditInfoDict['entityRegime'],
            self.creditInfoDict['entityRCL'],
            self.creditInfoDict['entityRCLYear'],
            self.creditInfoDict['entityPaymentExpectation'],
            self.creditInfoDict['entityPaymentExpectationYear']
            )

        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, bodyText, 0, align='J')
        self.ln(BREAK_LINE_HEIGHT)

    def writeSignature(self) -> None:
        tdDate = dt.date.today()

        self.set_font('Arial', size=BASE_FONT_SIZE)
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, 'Validade da Proposta: 7 (sete) dias.', 0, align='L')
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, f'Laguz, {str(tdDate.day)} de {MONTH_DICT[tdDate.month]} de {tdDate.year}', 0, align='R')

        self.ln(BREAK_LINE_HEIGHT)
        self.ln(BREAK_LINE_HEIGHT)
        self.ln(BREAK_LINE_HEIGHT)

        capitalizeName = ' '.join([name.capitalize() for name in self.creditInfoDict['pricingAnalyst'].split()])
        self.multi_cell(0, COMPOSE_TEXT_HEIGHT, f'{capitalizeName}\nRODRIGO BAER SVIRSKY', 0, align='C')

    def insertBreakLine(self) -> None:
        self.ln(BREAK_LINE_HEIGHT)

    def addNewPage(self, orientation='P') -> None:
        self.add_page(orientation=orientation)

    def returnPdfAsBytes(self) -> str:
        return self.output(dest='S').encode('latin-1')

    def closePdf(self) -> None:
        self.close()