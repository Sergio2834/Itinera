import streamlit as st # Libreria principale per creare il sito web
import google.generativeai as genai # Libreria per usare l'intelligenza artificiale di Google (Gemini)
import json # Per gestire i dati strutturati (l'itinerario)
import datetime # Per gestire le date (calendario)
import geonamescache # Database locale di nazioni e città
import pandas as pd # Per creare le tabelle di dati per le mappe
from fpdf import FPDF # Per creare il file PDF da scaricare
import base64 # Per convertire immagini e font in codice leggibile dal browser
import os # Per interagire con il sistema operativo (controllare se i file esistono)

# --- 1. CONFIGURAZIONE INIZIALE DELLA PAGINA ---
# Impostiamo il titolo della scheda del browser e il layout "wide" (largo)
st.set_page_config(page_title="Cultural Travel Planner", layout="wide")

# --- 2. CONFIGURAZIONE CHIAVE API ---
# Qui devi inserire la tua chiave segreta per far funzionare l'IA
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"

# --- 3. FUNZIONE DI UTILITÀ PER FILE LOCALI ---
# Questa funzione serve a leggere file (come immagini o font) dal tuo computer
# e trasformarli in una stringa di testo (base64) che l'HTML può capire.
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# --- 4. FUNZIONE CHE DEFINISCE IL DESIGN (CSS) ---
# Qui avviene tutta la magia grafica. Scriviamo codice CSS dentro Python.
def set_custom_design():
    # A. Caricamento del Font "Foremost"
    # Controlliamo se il file del font esiste nella cartella e lo carichiamo
    font_b64 = get_base64_of_bin_file("Foremost Regular.ttf")
    if font_b64:
        # Se il font c'è, creiamo la regola CSS per usarlo
        font_face_css = f"""
        @font-face {{
            font-family: 'Foremost';
            src: url('data:font/ttf;base64,{font_b64}') format('truetype');
        }}
        """
        main_font = "'Foremost', serif"
    else:
        # Se non c'è, usiamo un font standard elegante come piano B
        font_face_css = ""
        main_font = "serif"

    # B. Caricamento Sfondo David
    # Cerchiamo l'immagine david.jpg nella cartella
    bg_b64 = get_base64_of_bin_file("david.jpg")
    
    if bg_b64:
        # Se c'è il file locale, lo usiamo
        bg_image_css = f'url("data:image/jpg;base64,{bg_b64}")'
    else:
        # Se manca, usiamo un link di internet come riserva
        bg_image_css = 'url("https://upload.wikimedia.org/wikipedia/commons/8/80/Michelangelo%27s_David_-_3.jpg")'

    # Definiamo il colore "Oro Antico" usato per titoli e pulsanti
    accent_color = "#D4AF37" 

    # C. Iniezione del CSS nella pagina
    # st.markdown con unsafe_allow_html=True permette di scrivere vero codice HTML/CSS
    st.markdown(f"""
    <style>
        {font_face_css}
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');

        /* Applichiamo il font personalizzato a tutti i testi principali */
        html, body, [class*="css"], div, p, h1, h2, h3, h4, span, button, input, label {{
            font-family: {main_font} !important;
        }}

        /* IMPOSTAZIONE SFONDO */
        .stApp {{
            /* Mettiamo un velo nero (0.85 opacity) sopra l'immagine per scurirla */
            background-image: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), {bg_image_css};
            background-attachment: fixed; /* L'immagine sta ferma quando scorri */
            background-size: cover; /* Copre tutto lo schermo */
            background-position: center 20%; /* Centra l'immagine in alto */
        }}

        /* STILE DEI TITOLI PRINCIPALI (H1) */
        h1 {{
            color: {accent_color} !important; /* Colore Oro */
            font-size: 3.5rem !important; /* Grandezza testo */
            text-align: center; /* Centrato */
            text-shadow: 2px 2px 5px #000; /* Ombra nera per leggere meglio */
            margin-bottom: 30px !important;
        }}
        
        /* STILE DEI SOTTOTITOLI (H3) */
        h3 {{
            color: #FFFFFF !important;
            font-size: 1.8rem !important;
            border-bottom: 2px solid {accent_color}; /* Linea dorata sotto il titolo */
            padding-bottom: 10px;
            margin-bottom: 20px;
            margin-top: 0 !important;
        }}

        /* --- IL CONTENITORE CENTRALE --- */
        /* Questo è il box nero dove ci sono i pulsanti e le scritte */
        .main .block-container {{
            background-color: rgba(10, 10, 10, 0.90); /* Nero al 90% di opacità */
            padding: 3rem; /* Spazio interno */
            border-radius: 4px;
            border-top: 5px solid {accent_color}; /* Bordo dorato in alto */
            box-shadow: 0 0 60px rgba(0,0,0,1); /* Ombra esterna luminosa */
            max-width: 850px; /* Larghezza fissata a 850px per non disperdere gli elementi */
            margin-left: auto; /* Centra orizzontalmente */
            margin-right: auto;
        }}

        /* TESTI NORMALI (Paragrafi) */
        p, li, .stMarkdown, div, span {{
            color: #E0E0E0 !important; /* Bianco leggermente grigio */
            font-size: 1.1rem !important;
            line-height: 1.6;
        }}

        /* ETICHETTE SOPRA GLI INPUT (es. "Seleziona Nazione") */
        .stSelectbox label, .stTextInput label, .stDateInput label, .stTimeInput label {{
            color: {accent_color} !important;
            font-size: 1.2rem !important;
            margin-bottom: 5px;
        }}

        /* CAMPI DOVE SCRIVI (Input) */
        .stTextInput > div > div > input, 
        .stDateInput > div > div > input, 
        .stTimeInput > div > div > input, 
        .stSelectbox > div > div > div {{
            background-color: #222 !important; /* Sfondo grigio scuro */
            color: #FFF !important; /* Scritta bianca */
            border: 1px solid #555;
            border-radius: 4px;
            min-height: 45px; /* Altezza fissa per allinearli tutti */
        }}

        /* --- IL PULSANTE GENERA --- */
        div.stButton > button {{
            background-color: {accent_color} !important; /* Sfondo Oro */
            color: #000000 !important; /* Scritta Nera */
            border: 1px solid #fff;
            padding: 15px 25px;
            font-size: 1.4rem !important;
            font-family: 'Roboto', sans-serif !important; /* Font speciale per il grassetto */
            text-transform: uppercase; /* Tutto maiuscolo */
            font-weight: 900 !important; /* Molto spesso (Bold) */
            letter-spacing: 1px;
            width: 100%;
            border-radius: 4px;
            margin-top: 10px;
        }}
        
        /* Quando passi il mouse sopra il pulsante */
        div.stButton > button:hover {{
            background-color: #FFF !important; /* Diventa bianco */
            box-shadow: 0 0 20px rgba(212, 175, 55, 0.6); /* Emana luce dorata */
        }}
        
        /* STILE DELLE CARD DELL'ITINERARIO (Risultati) */
        .activity-card {{
            background-color: #1a1a1a; 
            padding: 20px;
            border: 1px solid #444;
            margin-bottom: 25px;
            border-left: 5px solid {accent_color}; /* Linea colorata a sinistra */
            border-radius: 6px;
        }}

        /* LINEA TEMPORALE VERTICALE */
        .timeline-container {{
            border-left: 1px solid {accent_color};
            margin-left: 15px;
            padding-left: 30px;
            position: relative;
        }}
        .timeline-dot {{
            position: absolute;
            left: -37px; /* Posizione del pallino sulla linea */
            top: 25px;
            width: 15px;
            height: 15px;
            background-color: {accent_color};
            border-radius: 50%; /* Lo rende rotondo */
            border: 2px solid #000;
        }}

        /* LINK A GOOGLE MAPS */
        .maps-link {{
            display: inline-block;
            margin-top: 15px;
            color: {accent_color} !important;
            text-decoration: none;
            font-size: 1rem !important;
            border-bottom: 1px dotted {accent_color};
        }}
        .maps-link:hover {{ color: #FFF !important; border-bottom: 1px solid #FFF; }}

    </style>
    """, unsafe_allow_html=True)

# Avviamo la funzione di design subito
set_custom_design()

# --- 5. CARICAMENTO DATI GEOGRAFICI ---
# Questa funzione scarica la lista di Paesi e Città e la salva in memoria (cache)
# per non doverla ricaricare ogni volta che clicchi un tasto.
@st.cache_data
def load_location_data():
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    country_names = sorted([data['name'] for code, data in countries.items()])
    map_name_code = {data['name']: code for code, data in countries.items()}
    
    cities = gc.get_cities()
    cities_by_country_code = {}
    
    # Organizziamo le città per codice nazione
    for city_id, data in cities.items():
        cc = data['countrycode']
        if cc not in cities_by_country_code: cities_by_country_code[cc] = []
        cities_by_country_code[cc].append(data['name'])
    
    # Ordiniamo alfabeticamente
    for cc in cities_by_country_code: cities_by_country_code[cc].sort()
    return country_names, map_name_code, cities_by_country_code

# Carichiamo i dati nelle variabili
all_nations, map_name_code, db_cities = load_location_data()

# --- 6. FUNZIONE PER CREARE IL PDF ---
# Prende i dati dell'itinerario (trip_data) e crea un file PDF scaricabile
def create_pdf(trip_data, destination):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'Itinerario Culturale: {destination}', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Scrittura Titolo e Riassunto
    pdf.set_font("Arial", 'B', 14)
    pdf.multi_cell(0, 10, f"{trip_data.get('trip_title', 'Itinerario')}")
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 10, f"{trip_data.get('summary', '')}")
    pdf.ln(10)

    # Ciclo attraverso i giorni e le attività
    for day in trip_data.get("days", []):
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Giorno {day['day_number']} - {day['date']}", 0, 1)
        pdf.ln(5)
        
        for act in day.get("activities", []):
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(30, 10, f"{act['time']}")
            pdf.cell(0, 10, f"{act['place_name']} ({act['duration']})", 0, 1)
            
            pdf.set_font("Arial", '', 10)
            # Pulizia caratteri speciali per evitare errori nel PDF
            desc = act['description'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f"{desc}")
            pdf.ln(2)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(0, 10, f"Tip: {act['tips']}", 0, 1)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- 7. FUNZIONE CHE CHIAMA L'INTELLIGENZA ARTIFICIALE ---
def get_itinerary(destination, start_date, arrival_time, end_date, departure_time):
    # Controllo di sicurezza: hai messo la chiave?
    if not api_key or "INSERISCI" in api_key:
        st.error("⚠️ Chiave API mancante.")
        return None

    # Colleghiamo la chiave a Gemini
    genai.configure(api_key=api_key)
    generation_config = {"temperature": 0.3, "top_p": 1, "top_k": 32, "max_output_tokens": 8192}
    model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)

    # Formattiamo gli orari come stringhe
    str_arr = arrival_time.strftime("%H:%M")
    str_dep = departure_time.strftime("%H:%M")

    # Questo è il "Prompt", ovvero le istruzioni che diamo all'IA
    prompt = f"""
    Agisci come una guida turistica esperta. Crea un itinerario culturale per {destination}.
    DATI INPUT: ARRIVO: {start_date} ore {str_arr}. RITORNO: {end_date}, partenza ore {str_dep}.
    OBIETTIVO: Itinerario focalizzato su Musei, Storia, Arte classica e rinascimentale.
    FORMATO OUTPUT (SOLO JSON):
    {{
      "trip_title": "Titolo Evocativo",
      "summary": "Breve descrizione dell'esperienza",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome Luogo",
              "description": "Descrizione culturale dettagliata.",
              "duration": "2h",
              "coordinates": {{ "lat": 0.0, "lon": 0.0 }},
              "tips": "Consiglio pratico per la visita"
            }}
          ]
        }}
      ]
    }}
    """

    # Mostriamo una rotellina di caricamento mentre l'IA pensa
    with st.spinner(f'Elaborazione itinerario per {destination}...'):
        try:
            response = model.generate_content(prompt)
            # Puliamo la risposta dell'IA per ottenere solo il JSON puro
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore nella generazione: {e}")
            return None

# --- 8. INTERFACCIA UTENTE (LAYOUT) ---
st.title("AI Cultural Travel Planner")
st.markdown("### Pianifica il tuo viaggio nell'arte.")
st.markdown("<br>", unsafe_allow_html=True)

# Creiamo due colonne per l'input: Destinazione e Date
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 🏛️ Destinazione")
    
    # Selezione Nazione
    default_ix = all_nations.index("Italy") if "Italy" in all_nations else 0
    selected_nation = st.selectbox("Seleziona Nazione", all_nations, index=default_ix)
    
    # Caricamento dinamico delle città in base alla nazione scelta
    nation_code = map_name_code.get(selected_nation)
    available_cities = db_cities.get(nation_code, [])
    
    city_options = ["Scrivi manualmente..."] + available_cities
    selected_city_opt = st.selectbox(f"Città in {selected_nation}", city_options, index=1 if len(city_options) > 1 else 0)
    
    # Se l'utente sceglie "manuale", usa il campo testo, altrimenti usa la selezione
    city_input = st.text_input("Inserisci città") if selected_city_opt == "Scrivi manualmente..." else selected_city_opt
    final_destination = f"{city_input}, {selected_nation}"

with col2:
    st.markdown("### ✈️ Date e Voli")
    
    # Sottocolonne per allineare Data e Ora sulla stessa riga
    r1_c1, r1_c2 = st.columns(2)
    with r1_c1: start_date = st.date_input("Giorno Arrivo", datetime.date.today())
    with r1_c2: arrival_time = st.time_input("Ora Arrivo", datetime.time(10, 00))
    
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1: end_date = st.date_input("Giorno Partenza", datetime.date.today() + datetime.timedelta(days=3))
    with r2_c2: departure_time = st.time_input("Ora Partenza", datetime.time(18, 00))

st.markdown("<br>", unsafe_allow_html=True)

# --- 9. PULSANTE DI GENERAZIONE ---
# Usiamo 3 colonne invisibili per centrare il pulsante e farlo largo il 50%
b_col1, b_col2, b_col3 = st.columns([1, 2, 1])

with b_col2:
    generate_btn = st.button("GENERA ITINERARIO", type="primary", use_container_width=True)

# --- 10. GESTIONE DEL CLICK ---
if generate_btn:
    if not city_input:
        st.warning("Inserisci una città valida.")
    else:
        # Chiamata alla funzione principale
        trip_data = get_itinerary(final_destination, start_date, arrival_time, end_date, departure_time)
        
        # Se abbiamo dati, mostriamo i risultati
        if trip_data:
            st.markdown("<br>", unsafe_allow_html=True)
            # Titolo generato dall'IA
            st.markdown(f'<h1 style="text-align:center;">{trip_data.get("trip_title", "")}</h1>', unsafe_allow_html=True)
            st.markdown(f'<p style="text-align:center; font-style:italic; font-size:1.2rem; color:#fff;">{trip_data.get("summary", "")}</p>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Bottone PDF
            col_pdf, col_map_pad = st.columns([1,3])
            with col_pdf:
                pdf_bytes = create_pdf(trip_data, final_destination)
                st.download_button("📄 SCARICA PDF", data=pdf_bytes, file_name=f"Itinerario_{city_input}.pdf", mime="application/pdf", use_container_width=True)
            
            st.markdown("---")
            
            # Ciclo per mostrare ogni giorno del viaggio
            for day in trip_data.get("days", []):
                st.markdown(f"## Giorno {day['day_number']} - {day['date']}")
                
                # Mappa con puntini
                map_points = [act["coordinates"] for act in day.get("activities", []) if "coordinates" in act]
                if map_points:
                    st.map(pd.DataFrame(map_points), size=20, color='#D4AF37')
                
                # Visualizzazione Timeline (Cards)
                st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
                for activity in day.get("activities", []):
                    # Creazione link Google Maps dinamico
                    clean_place = activity['place_name'].replace(" ", "+")
                    maps_url = f"https://www.google.com/maps/search/?api=1&query={clean_place}+{city_input}"
                    
                    # HTML della card singola
                    st.markdown(f"""
                    <div class="timeline-dot"></div>
                    <div class="activity-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #333; padding-bottom:10px; margin-bottom:10px;">
                            <strong style="color:#D4AF37; font-size:1.3rem;">{activity['time']}</strong>
                            <span style="font-size:1rem; color:#999;">{activity['duration']}</span>
                        </div>
                        <h3 class="card-title" style="margin-top:5px; margin-bottom:10px; font-size:1.5rem;">{activity['place_name']}</h3>
                        <p style="margin-bottom:15px; color:#ddd;">{activity['description']}</p>
                        <div class="tip-box">
                            <strong style="color:#D4AF37;">💡 TIP:</strong> {activity['tips']}
                        </div>
                        <a href="{maps_url}" target="_blank" class="maps-link">Vedi su Maps</a>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div><br><br>', unsafe_allow_html=True)

# Footer
st.markdown("<br><br><center><small style='color:#666;'>Design by AI</small></center>", unsafe_allow_html=True)