import datetime as dt
import streamlit as st

TD_DATE = dt.date.today()
MIN_DATE = TD_DATE + dt.timedelta(days=-365 * 2)
MAX_DATE = TD_DATE + dt.timedelta(days=365 * 2)
START_YEAR = str(TD_DATE.year)
END_YEAR = '2031'

K_TIMES = 1000
M_TIMES = 1000000
B_TIMES = 1000000000

DB_CONNECTION_PASS = st.secrets['passwords']['dbConnection']

RCL_FIELD = 'PREVISÃO ATUALIZADA 2021'

TRANSLATE_BOOL_DICT = {True: 'SIM', False: 'NÃO', '-': '-'}

COLORS_LIST = [
    '#081F2D',
    '#00A5B5',
    '#3E7E98',
    '#081F2D',  #'#748188',
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
