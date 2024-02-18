import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import io
import os
import plotly.express as px
from my_functons import italian_date_to_datetime, extract_text_segments, extract_numbers_after_zero, extract_intermediario_names, extract_intermediario_section, create_df_from_pdf
import re
import pdfplumber
from collections import namedtuple
import matplotlib 
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import locale

# Welcome to Streamlit!


st.set_page_config(page_title="ANALISI CENTRALE RISCHI", page_icon=":bar_chart:",layout="wide")

st.title(" :bar_chart: Analisi CR")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

# Streamlit file uploader
pdf_file = st.file_uploader(":file_folder: Upload a file", type=(["pdf"]))

if pdf_file:
        # Leggi il contenuto del file PDF
        #process_pdf_file(pdf_file)

    # Carica un DataFrame di esempio (puoi sostituire questo passo con il caricamento dei tuoi dati)
        df = create_df_from_pdf(pdf_file)

# Create a mask based on the specified conditions
mask = (
    (df['Accordato'] == df['Accordato Operativo']) |
    (df['Accordato'] == df['Utilizzato']) |
    (df['Accordato Operativo'] == df['Utilizzato'])
)

# Apply the mask to filter the DataFrame
df = df[mask]
st.write(df)

col1, col2 = st.columns((2))
df['Periodo_dt'] = df['Periodo'].apply(italian_date_to_datetime)

startDate = pd.to_datetime(df["Periodo_dt"]).min()
endDate = pd.to_datetime(df["Periodo_dt"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

df = df[(df["Periodo_dt"] >= date1) & (df["Periodo_dt"] <= date2)].copy()

# Filter the DataFrame to include only "RISCHI AUTOLIQUIDANTI" and "RISCHI A SCADENZA"
filtered_df = df[df['Categoria'].isin(['RISCHI AUTOLIQUIDANTI', 'RISCHI A REVOCA'])]
# Create a new DataFrame with the desired calculation
ratio_df = filtered_df.groupby('Periodo_dt').apply(lambda group: group['Utilizzato'].sum() / group['Accordato Operativo'].sum()).reset_index(name='Utilizzato_to_Accordato_Operativo_Ratio')
ratio_df = ratio_df.sort_values('Periodo_dt')
ratio_df['Utilizzato_to_Accordato_Operativo_Ratio_Percentage'] = ratio_df['Utilizzato_to_Accordato_Operativo_Ratio'] * 100

with col1:
        st.subheader("Utilizzato to Accordato Operativo Ratio over Time")
        fig = px.bar(ratio_df, x = "Periodo_dt", y = "Utilizzato_to_Accordato_Operativo_Ratio_Percentage", template = "seaborn")
        st.plotly_chart(fig, height = 200)

with col2:
        st.subheader("Utilizzato per Intermediario")
        fig = px.pie(filtered_df, values = "Utilizzato", names = "Intermediario", hole = 0.5)
        fig.update_traces(text = filtered_df["Intermediario"], textposition = "outside")
        st.plotly_chart(fig,use_container_width=True)
