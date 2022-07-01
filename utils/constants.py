import datetime as dt
import streamlit as st

import os

TMP_FOLDER = 'tmp'
IMG_TMP_FOLDER = os.path.join('tmp', 'images')
DB_CONNECTION_PASS = st.secrets['passwords']['dbConnection']

# Generate doc variables
PDF_HEADER_IMG = './static/pdf_header.png'
FPDF_RIGHT_MARGIN = 20
LINE_BREAK = 8
TITLE_FONT_SIZE = 18
HEADER_EXTRA_LEFT_MARGIN = 27.5
HEADER_HEIGHT_MARGIN = 55
BASE_FONT_SIZE = 11
COMPOSE_TEXT_HEIGHT = 6
BREAK_LINE_HEIGHT = 6
CELL_HEIGHT = 2
KPI_HEADER_FONT_SIZE = 11
KPI_VALUE_FONT_SIZE = 16
BUCKET = 'laguz-tech-miscellaneous'

# Form variables
CONST_MAINTAIN_KEYS = ['password_correct', 'headers', 'authentication_status']
PRICING_ANALYSTS = [
    '',
    'JUAREZ VIQUEIRA MIGUEL',
    'JEFFERSON DANIEL TORRES DE SOUSA',
    'LIVIA PINHO DAMIATI'
]

CURRENT_DIR = os.path.dirname(os.getcwd())
TD_DATE = dt.date.today()
MIN_DATE = TD_DATE + dt.timedelta(days=-365*2)
MAX_DATE = TD_DATE + dt.timedelta(days=365*2)
START_YEAR = str(TD_DATE.year)
END_YEAR = '2031'

MEASURE_UNIT_DICT = {
    'T_TIMES': {
        'unit': 1000000000000,
        'suffix': 'Tri'
    },
    'B_TIMES': {
        'unit': 1000000000,
        'suffix': 'Bi'
    },
    'M_TIMES': {
        'unit': 1000000,
        'suffix': 'MM'
    },
    'K_TIMES': {
        'unit': 1000,
        'suffix': 'K'
    },
    'U_TIMES': {
        'unit': 1,
        'suffix': ''
    },
}

MONTH_DICT = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro',
}

FEDERATIVE_DOC_EARNOUT_PARAMS = {
    2022: {
        'ALIMENTAR': {
            'pricePercentage': 0.76,
            'earnoutText': '',
        },
        'COMUM': {
            'pricePercentage': 0.55,
            'earnoutText': "Fica ainda estabelecido 'earnout' pro-rata temporis de 25% (quarenta e cinco por cento) onde o valor base para incidência do percentual corresponde ao valor recebido excluindo-se o desembolso inicial. O prazo de vigente do 'earnout' será de 1 (um) ano e 6 (seis) meses a partir de 01/07/2022. Dessa forma, a partir de 01/01/2024 o 'earnout' deixa de existir.",
        }
    },
    2023: {
        'ALIMENTAR': {
            'pricePercentage': 0.35,
            'earnoutText': "Fica ainda estabelecido 'earnout' pro-rata temporis de 45% (quarenta e cinco por cento) onde o valor base para incidência do percentual corresponde ao valor recebido excluindo-se o desembolso inicial. O prazo de vigente do 'earnout' será de 2 (dois) anos a partir de 01/01/2023. Dessa forma, a partir de 01/01/2025 o 'earnout' deixa de existir.",
        },
        'COMUM': {
            'pricePercentage': 0.3,
            'earnoutText': "Fica ainda estabelecido 'earnout' pro-rata temporis de 45% (quarenta e cinco por cento) onde o valor base para incidência do percentual corresponde ao valor recebido excluindo-se o desembolso inicial. O prazo de vigente do 'earnout' será de 3 (três) anos a partir de 01/01/2023. Dessa forma, a partir de 01/01/2026 o 'earnout' deixa de existir",
        }
    },
    2024: {
        'ALIMENTAR': {
            'pricePercentage': 0.3,
            'earnoutText': "Fica ainda estabelecido 'earnout' pro-rata temporis de 45% (quarenta e cinco por cento) onde o valor base para incidência do percentual corresponde ao valor recebido excluindo-se o desembolso inicial. O prazo de vigente do 'earnout' será de 3 (três) anos a partir de 01/01/2024. Dessa forma, a partir de 01/01/2027 o 'earnout' deixa de existir.",
        },
        'COMUM': {
            'pricePercentage': 0.3,
            'earnoutText': "Fica ainda estabelecido 'earnout' pro-rata temporis de 45% (quarenta e cinco por cento) onde o valor base para incidência do percentual corresponde ao valor recebido excluindo-se o desembolso inicial. O prazo de vigente do 'earnout' será de 3 (três) anos a partir de 01/01/2024. Dessa forma, a partir de 01/01/2027 o 'earnout' deixa de existir.",
        }
    }
}

RCL_FIELD = 'PREVISÃO ATUALIZADA 2021'

TRANSLATE_BOOL_DICT = {
    True: 'SIM',
    False: 'NÃO',
    '-': '-'
}

YEAR_OPTIONS = [
    2022,
    2023,
    2024
]

COLORS_LIST = [
    '#081F2D',
    '#00A5B5',
    '#3E7E98',
    '#748188',
    '#00B9F1',
    '#3A4C57',
    '#006F92',
    '#BEE6EA',
]

BIG_COLOR_LIST = [
    '#E52B50',
    '#FFBF00',
    '#9966CC',
    '#FBCEB1',
    '#7FFFD4',
    '#007FFF',
    '#89CFF0',
    '#F5F5DC',
    '#CB4154',
    '#000000',
    '#0000FF',
    '#0095B6',
    '#8A2BE2',
    '#DE5D83',
    '#CD7F32',
    '#993300',
    '#800020',
    '#702963',
    '#960018',
    '#DE3163',
    '#007BA7',
    '#F7E7CE',
    '#7FFF00',
    '#7B3F00',
    '#0047AB',
    '#6F4E37',
    '#B87333',
    '#FF7F50',
    '#DC143C',
    '#00FFFF',
    '#EDC9Af',
    '#7DF9FF',
    '#50C878',
    '#00FF3F',
    '#FFD700',
    '#BEBEBE',
    '#008001',
    '#3FFF00',
    '#4B0082',
    '#FFFFF0',
    '#00A86B',
    '#29AB87',
    '#B57EDC',
    '#FFF700',
    '#C8A2C8',
    '#BFFF00',
    '#FF00FF',
    '#FF00AF',
    '#800000',
    '#E0B0FF',
    '#000080',
    '#CC7722',
    '#808000',
    '#FF6600',
    '#FF4500',
    '#DA70D6',
    '#FFE5B4',
    '#D1E231',
    '#CCCCFF',
    '#1C39BB',
    '#FFC0CB',
    '#8E4585',
    '#003153',
    '#CC8899',
    '#6A0DAD',
    '#E30B5C',
    '#FF0000',
    '#C71585',
    '#FF007F',
    '#E0115F',
    '#FA8072',
    '#92000A',
    '#0F52BA',
    '#FF2400',
    '#C0C0C0',
    '#708090',
    '#A7FC00',
    '#00FF7F',
    '#D2B48C',
    '#483C32',
    '#008080',
    '#40E0D0',
    '#3F00FF',
    '#7F00FF',
    '#40826D',
    '#FFFFFF',
    '#FFFF00',
]

