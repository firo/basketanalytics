import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Configura la pagina Streamlit con layout widescreen
st.set_page_config(layout="wide")
st.title('Basket Analytics - SG Arese')

# Definisci il percorso del file CSV salvato
csv_file = "players_data.csv"

# Funzione per caricare i dati salvati in precedenza
def load_saved_data():
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    return pd.DataFrame()  # Restituisce un DataFrame vuoto se il file non esiste

# Funzione per mostrare il grafico scatter di "Contribution" vs "Time"
def mostra_grafico(df, aggregato=False):
    if 'Time' not in df.columns:
        st.error("La colonna 'Time' non è presente nei dati.")
        return

    # Converte la colonna 'Time' in secondi
    try:
        df['Time'] = pd.to_timedelta(df['Time']).dt.total_seconds()
    except Exception as e:
        st.error(f"Errore nella conversione della colonna 'Time': {e}")
        return

    # Se aggregato è True, somma i dati per ogni giocatore
    if aggregato:
        df = df.groupby('Player Name').agg({
            'Points': 'sum',
            'Assists': 'sum',
            'Block': 'sum',
            'Deflection': 'sum',
            'Steal': 'sum',
            'Def Reb': 'sum',
            'Off Reb': 'sum',
            'Fouls': 'sum',
            'Travelling': 'sum',
            'T-over': 'sum',
            'Contribution': 'sum',
            'Time': 'sum'
        }).reset_index()

    # Filtra i dati per escludere righe con "Time" pari a 0
    df = df[df['Time'] != 0]

    # Calcola le mediane per le linee di riferimento
    median_time = df['Time'].median()
    median_contribution = df['Contribution'].median()

    # Crea il grafico scatter
    plt.figure(figsize=(10, 6))
    plt.scatter(df['Contribution'], df['Time'], alpha=0.7, edgecolors='w', s=100)
    plt.axhline(y=median_time, color='r', linestyle='--', linewidth=1)
    plt.axvline(x=median_contribution, color='r', linestyle='--', linewidth=1)

    # Etichette del grafico
    plt.title('Performance Chart: Contribution vs Time', fontsize=14)
    plt.xlabel('Contribution', fontsize=12)
    plt.ylabel('Time (MM:SS)', fontsize=12)
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x // 60)}:{int(x % 60):02d}"))

    # Aggiunge i nomi dei giocatori come annotazioni sul grafico
    for i in range(len(df)):
        plt.annotate(df['Player Name'].iloc[i], 
                     (df['Contribution'].iloc[i], df['Time'].iloc[i]), 
                     textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8)

    st.pyplot(plt)

# Uploader per il caricamento di file CSV dalla sidebar
uploaded_file_hoopstats = st.sidebar.file_uploader("Carica il file CSV delle partite da HoopStats", type=["csv"])

# Carica i dati salvati in precedenza
df = load_saved_data()

# Se è stato caricato un nuovo file CSV
if uploaded_file_hoopstats is not None:
    content = uploaded_file_hoopstats.read().decode('utf-8').splitlines()

    # Cerca le righe di inizio e fine dei dati relativi a SG Arese
    start = next((i for i, line in enumerate(content) if line.startswith("HOME:  SG Arese U15") or line.startswith("VISITORS:  SG Arese U15")), None)
    if start is not None:
        end = next(i for i in range(start, len(content)) if content[i].startswith("Team Events"))
        sg_arese_data = content[start:end]
        
        # Estrae le colonne e i dati dei giocatori
        columns = sg_arese_data[1].split(',')
        players_data = [line.split(',') for line in sg_arese_data[2:]]
        normalized_data = [row if len(row) == len(columns) else row[:len(columns)] for row in players_data]
        new_df = pd.DataFrame(normalized_data, columns=columns)

        # Aggiunge il nome della partita e la data ai nuovi dati
        new_df['Match'] = content[1]
        new_df['Date'] = content[2].split(',')[0]

        # Elimina colonne non necessarie e rinomina alcune colonne
        new_df = new_df.drop(columns=['Custom 2'])
        new_df = new_df.rename(columns={'Steps': 'Travelling'})
        
        # Converte colonne specifiche in numeri e calcola "Contribution"
        cols_to_sum = ['Points', 'Assists', 'Block', 'Deflection', 'Steal', 'Def Reb', 'Off Reb', 'Fouls', 'Travelling', 'T-over']
        new_df[cols_to_sum] = new_df[cols_to_sum].apply(pd.to_numeric, errors='coerce').fillna(0)
        new_df['Contribution'] = (new_df['Points'] + new_df['Assists'] + new_df['Block'] + new_df['Deflection'] +
                                  new_df['Steal'] + new_df['Def Reb'] + new_df['Off Reb'] - new_df['Fouls'] -
                                  new_df['Travelling'] - new_df['T-over'])

        # Aggiunge i nuovi dati al dataset esistente e li salva
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(csv_file, index=False)

# Mostra un messaggio se il dataset è vuoto
if df.empty:
    st.write("Non ci sono dati salvati. Carica un file per iniziare.")
else:
    # Filtri per partita e giocatore nella sidebar
    match_options = ["Tutte"] + df['Match'].unique().tolist()
    player_options = ["Tutti"] + df['Player Name'].unique().tolist()

    selected_matches = st.sidebar.multiselect("Seleziona partita", match_options, default="Tutte")
    selected_players = st.sidebar.multiselect("Seleziona giocatore", player_options, default="Tutti")

    # Filtro dei dati in base ai filtri selezionati
    df_filtered = df.copy()
    if "Tutte" not in selected_matches:
        df_filtered = df_filtered[df_filtered['Match'].isin(selected_matches)]
    if "Tutti" not in selected_players:
        df_filtered = df_filtered[df_filtered['Player Name'].isin(selected_players)]

    # Mostra il grafico e determina se aggregare i dati
    aggregato = ("Tutte" in selected_matches and "Tutti" in selected_players) or len(selected_matches) > 1
    mostra_grafico(df_filtered, aggregato=aggregato)

    # Mostra i dati filtrati come tabella
    df_view_only = df_filtered.drop(columns=['Date', 'Match', 'No.'])
    df_view_only['Time'] = pd.to_timedelta(df_view_only['Time'], errors='coerce').apply(lambda x: f"{int(x.total_seconds() // 60)}:{int(x.total_seconds() % 60):02d}" if pd.notnull(x) else "00:00")

    # Riordina le colonne e mostra i dati
    columns = list(df_view_only.columns)
    columns.insert(columns.index('+/-') + 1, columns.pop(columns.index('Eff')))
    df_view_only = df_view_only[columns]
    st.table(df_view_only)
