from sqlalchemy import create_engine
import datetime as dt

import streamlit as st
import numpy as np
import pandas as pd

from utils.functions import *
from utils.constants import *

import plotly.graph_objects as go

entityId = 4655

cnn = createConnection()

entities = getEntities(cnn)
queueDf = getQueue(entityId, cnn)

queueDf.loc[queueDf['queueposition']<15, 'value']

entityMapDf = getEntityMap(entityId, cnn)
entityRegimeDf = getEntityRegime(entityId, cnn)
entityStatsDf = getEntityStats(entityId, cnn)
entityPlanDf = getEntityPlan(entityId, cnn)

pd.read_sql('SELECT * FROM deal', cnn)