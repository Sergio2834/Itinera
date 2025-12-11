import streamlit as st
import google.generativeai as genai
import json
import datetime
import geonamescache
import pandas as pd
from fpdf import FPDF
import base64
import os

# --- CONFIGURAZIONE CHIAVE API ---
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"  # Inserisci la tua chiave reale qui

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cultural Travel Planner", page_icon="🏛️", layout="wide")

# --- FUNZIONI DI UTILITÀ ---
def get_base64_of_bin_file(bin_file):
    """Legge un file binario e restituisce la stringa base64."""
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# --- CARICAMENTO SFONDO E STILE DARK MODE ---
img_base64 = get_base64_of_bin_file("david.jpg")

# CSS Dinamico per sfondo
if img_base64:
    bg_image_css = f"""
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(20, 20, 20, 0.9)), url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
    }}
    """
else:
    # Fallback se non c'è l'immagine: sfondo grigio scuro
    bg_image_css = """
    .stApp {
        background-color: #121212;
    }
    """

# CSS Globale per adattare tutto al tema scuro
st.markdown(f"""
<style>
    /* 1. Applica sfondo */
    {bg_image_css}

    /* 2. Forza testo bianco globale per titoli e label */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, div {{
        color: #E0E0E0 !important;
    }}

    /* 3. Stile Card Attività (Versione Dark) */
    .activity-card {{
        background-color: #262730; /* Grigio scuro Streamlit */
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FFD700; /* Oro per contrasto su scuro */
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 10px;
        transition: transform 0.2s;
        color: white; /* Testo interno card */
    }}
    .activity-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.5);
        background-color: #2e2f38;
    }}
    .card-title {{
        color: #FFD700; /* Oro */
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 4px;
    }}
    .card-desc {{
        color: #d1d1d1; /* Grigio chiaro */
        font-size: 0.95em;
        line-height: 1.4;
        margin-bottom: 8px;
    }}
    .card-meta {{
        font-size: 0.8em;
        color: #999;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #444;
        padding-top: 5px;
        margin-top: 5px;
    }}
    .maps-link {{
        color: #4285F4;
        text-decoration: none;
        font-weight: bold;
    }}
    .maps-link:hover {{ text-decoration: underline; color: #7aa9ff; }}
    
    /* Time Badge */
    .time-badge {{
        background-color: #444;
        color: #FFF;
        padding: 4px 8px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.8em;
        border: 1px solid #666;
    }}

    /* 4. Personalizzazione Widget Input per renderli leggibili su scuro */
    .stTextInput > div > div > input {{
        background-color: rgba(255, 255, 255, 0.1); 
        color: white;
        border-color: #555;
    }}
    .stSelectbox > div > div > div {{
        background-color: rgba(255, 255, 255, 0.1);
        color: white;
    }}
    /* Colore testo dentro i box input */
    .stDateInput input, .stTimeInput input {{
        color: white !important;
    }}

</style>
""", unsafe_allow_html=True)

# --- DATABASE LOCALE ---
@st.cache_data
def load_location_data():
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    country_names = sorted([data['name'] for code, data in countries.items()])
    map_name_code = {data['name']: code for code, data in countries.items()}
    
    cities = gc.get_cities()
    cities_by_country_code = {}
    for city_id, data in cities.items():
        cc = data['countrycode']
        if cc not in cities_by_country_code: cities_by_country_code[cc] = []
        cities_by_country_code[cc].append(data['name'])
    
    for cc in cities_by_country_code: cities_by_country_code[cc].sort()
    return country_names, map_name_code, cities_by_country_code

all_nations, map_name_code, db_cities = load_location_data()

# --- FUNZIONE PDF EXPORT ---
def create_pdf(trip_data, destination):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'Itinerario Culturale: {destination}', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Titolo e Riassunto
    pdf.set_font("Arial", 'B', 12)
    # Gestione encoding base per FPDF (latin-1)
    safe_title = trip_data.get('trip_title', '').encode('latin-1', 'replace').decode('latin-1')
    safe_summary = trip_data.get('summary', '').encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 10, f"Titolo: {safe_title}")
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 10, f"Riassunto: {safe_summary}")
    pdf.ln(5)

    for day in trip_data.get("days", []):
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Giorno {day['day_number']} - {day['date']}", 0, 1)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 11)
        for act in day.get("activities", []):
            time_str = f"{act['time']} ({act['duration']})"
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(40, 10, time_str)
            
            safe_place = act['place_name'].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, safe_place, 0, 1)
            
            pdf.set_font("Arial", '', 10)
            desc = act['description'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f" - {desc}")
            pdf.ln(2)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- FUNZIONE GENERAZIONE ITINERARIO ---
def get_itinerary(destination, start_date, arrival_time, end_date, departure_time):
    if not api_key:
        st.error("⚠️ Chiave API mancante.")
        return None

    genai.configure(api_key=api_key)
    
    generation_config = {"temperature": 0.2, "top_p": 1, "top_k": 32, "max_output_tokens": 8192}
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config) # Aggiornato a 1.5 flash che è stabile

    str_arr = arrival_time.strftime("%H:%M")
    str_dep = departure_time.strftime("%H:%M")

    prompt = f"""
    Agisci come una guida turistica esperta. Crea un itinerario culturale per {destination}.
    
    DATI INPUT:
    - ARRIVO: {start_date} ore {str_arr}.
    - RITORNO: {end_date}, partenza ore {str_dep}.
    
    OBIETTIVO:
    Itinerario su Musei, Storia, Arte.
    
    REGOLE:
    1. Attività vicine tra loro nella stessa giornata.
    2. Coordinate lat/lon precise.
    3. Evita luoghi chiusi all'orario indicato.

    FORMATO OUTPUT (SOLO JSON):
    {{
      "trip_title": "Titolo",
      "summary": "Breve riassunto",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome Luogo",
              "description": "Descrizione sintetica",
              "duration": "2h",
              "coordinates": {{ "lat": 41.9028, "lon": 12.4964 }},
              "tips": "Consiglio utile"
            }}
          ]
        }}
      ]
    }}
    """

    with st.spinner(f'Analisi mappe e storia per {destination}...'):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore nella generazione: {e}")
            return None

# --- UI PRINCIPALE ---
st.title("🏛️ AI Cultural Travel Planner")
st.markdown("Itinerari storici generati dall'AI, ottimizzati per la logistica.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Destinazione")
    default_ix = all_nations.index("Italy") if "Italy" in all_nations else 0
    selected_nation = st.selectbox("Seleziona Nazione", all_nations, index=default_ix)
    nation_code = map_name_code.get(selected_nation)
    available_cities = db_cities.get(nation_code, [])
    
    city_options = ["Scrivi manualmente..."] + available_cities
    selected_city_opt = st.selectbox(f"Città in {selected_nation}", city_options, index=1 if len(city_options) > 1 else 0)
    city_input = st.text_input("Inserisci città") if selected_city_opt == "Scrivi manualmente..." else selected_city_opt
    final_destination = f"{city_input}, {selected_nation}"

with col2:
    st.subheader("✈️ Date e Orari")
    c_date_in, c_time_in = st.columns(2)
    with c_date_in: start_date = st.date_input("Giorno Arrivo", datetime.date.today())
    with c_time_in: arrival_time = st.time_input("Ora Atterraggio", datetime.time(10, 00))
    
    st.write("")
    c_date_out, c_time_out = st.columns(2)
    with c_date_out: end_date = st.date_input("Giorno Partenza", datetime.date.today() + datetime.timedelta(days=3))
    with c_time_out: departure_time = st.time_input("Ora Decollo", datetime.time(18, 00))

st.markdown("---")

if st.button("✨ Genera Itinerario Ottimizzato", type="primary", use_container_width=True):
    if not city_input:
        st.warning("Seleziona una città valida.")
    else:
        trip_data = get_itinerary(final_destination, start_date, arrival_time, end_date, departure_time)
        
        if trip_data:
            st.success(f"Itinerario creato per {final_destination}!")
            st.markdown("---")
            
            # Intestazione e Download PDF
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.header(trip_data.get("trip_title", ""))
                st.write(trip_data.get("summary", ""))
            with h_col2:
                pdf_bytes = create_pdf(trip_data, final_destination)
                st.download_button(
                    label="📄 Scarica PDF",
                    data=pdf_bytes,
                    file_name=f"Itinerario_{city_input}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            # Loop Giorni
            for day in trip_data.get("days", []):
                with st.expander(f"📅 Giorno {day['day_number']} - {day['date']}", expanded=True):
                    
                    col_list, col_map = st.columns([2, 1])
                    
                    # Colonna Sinistra: Lista Attività
                    with col_list:
                        for activity in day.get("activities", []):
                            clean_place = activity['place_name'].replace(" ", "+")
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={clean_place}+{city_input}"
                            
                            st.markdown(f"""
                            <div class="activity-card">
                                <div style="display:flex; justify-content:space-between; align-items:start;">
                                    <div class="card-title">{activity['place_name']}</div>
                                    <div class='time-badge'>{activity['time']}</div>
                                </div>
                                <div class="card-desc">{activity['description']}</div>
                                <div class="card-meta">
                                    <span>⏱️ {activity['duration']} | <i>{activity['tips']}</i></span>
                                    <a href="{maps_url}" target="_blank" class="maps-link">📍 Maps</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Colonna Destra: Mappa
                    with col_map:
                        st.markdown("###### 🗺️ Mappa del Giorno")
                        map_points = []
                        for act in day.get("activities", []):
                            if "coordinates" in act:
                                map_points.append(act["coordinates"])
                        
                        if map_points:
                            df_map = pd.DataFrame(map_points)
                            st.map(df_map, size=20, color='#FFD700', use_container_width=True)
                        else:
                            st.info("Nessuna coordinata disponibile.")

st.markdown("---")
st.caption("Powered by Google Gemini 1.5 Flash & Streamlit")