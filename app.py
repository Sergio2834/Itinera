import streamlit as st
import google.generativeai as genai
import json
import datetime
import geonamescache
import pandas as pd
from fpdf import FPDF

# --- CONFIGURAZIONE CHIAVE API ---
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cultural Travel Planner", page_icon="🏛️", layout="wide")

# --- STILE CSS PERSONALIZZATO ---
st.markdown("""
<style>
    /* Stile Card Attività */
    .activity-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #8B4513; /* Bronzo Storia */
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        margin-bottom: 10px;
        transition: transform 0.2s;
    }
    .activity-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }
    .card-title {
        color: #2c3e50;
        font-size: 1.1em;
        font-weight: bold;
        margin-bottom: 4px;
    }
    .card-desc {
        color: #555;
        font-size: 0.9em;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    .card-meta {
        font-size: 0.8em;
        color: #888;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .maps-link {
        color: #4285F4;
        text-decoration: none;
        font-weight: bold;
        border: 1px solid #4285F4;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .maps-link:hover { 
        background-color: #4285F4; 
        color: white;
    }
    
    /* Time Badge */
    .time-badge {
        background-color: #8B4513;
        color: white;
        padding: 4px 8px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.8em;
        text-align: center;
        width: fit-content;
        margin-bottom: 4px;
    }
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
    
    def clean_text(text):
        if not text: return ""
        return text.encode('latin-1', 'replace').decode('latin-1')

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'Itinerario Culturale: {clean_text(destination)}', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    title = clean_text(trip_data.get('trip_title', 'Titolo Viaggio'))
    summary = clean_text(trip_data.get('summary', ''))

    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(0, 10, f"Titolo: {title}")
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 10, f"Riassunto: {summary}")
    pdf.ln(5)

    for day in trip_data.get("days", []):
        date_str = str(day.get('date', 'Data'))
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 10, f"Giorno {day['day_number']} - {date_str}", 0, 1, fill=True)
        pdf.ln(2)
        
        for act in day.get("activities", []):
            time_str = clean_text(f"{act.get('time','')} ({act.get('duration','')})")
            place_name = clean_text(act.get('place_name',''))
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(45, 10, time_str)
            pdf.cell(0, 10, place_name, 0, 1)
            
            pdf.set_font("Arial", '', 10)
            desc = clean_text(act.get('description', ''))
            pdf.multi_cell(0, 6, f" - {desc}")

            q_place = place_name.replace(" ", "+")
            q_dest = destination.replace(" ", "+")
            maps_link = f"https://www.google.com/maps/search/?api=1&query={q_place}+{q_dest}"
            
            pdf.set_text_color(0, 0, 255)
            pdf.set_font("Arial", 'U', 9)
            pdf.cell(0, 8, "    --> Vedi su Google Maps (Clicca qui)", link=maps_link, ln=1)
            
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- FUNZIONE GENERAZIONE ITINERARIO ---
def get_itinerary(destination, start_date, arrival_time, end_date, departure_time):
    if not api_key:
        st.error("⚠️ Chiave API mancante.")
        return None

    genai.configure(api_key=api_key)
    
    # Configurazione generazione
    generation_config = {"temperature": 0.2, "top_p": 1, "top_k": 32, "max_output_tokens": 8192}
    model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)

    str_arr = arrival_time.strftime("%H:%M")
    str_dep = departure_time.strftime("%H:%M")

    # --- PROMPT ---
    prompt = f"""
    Agisci come una guida turistica esperta e logistica. Crea un itinerario culturale per {destination}.
    
    IMPORTANTE: LINGUA DI OUTPUT
    Devi scrivere TUTTO il contenuto ESCLUSIVAMENTE IN ITALIANO.
    Anche se la città è estera (es. Londra, Tokyo, New York), traduci le descrizioni, i consigli e i riassunti in italiano.
    Mantieni i nomi propri dei luoghi (es. "British Museum") in lingua originale se necessario, ma descrivili in ITALIANO.
    
    DATI INPUT:
    - ARRIVO: {start_date} ore {str_arr}.
    - RITORNO: {end_date}, partenza ore {str_dep}.
    
    OBIETTIVO:
    Itinerario focalizzato su **Musei, Storia, Arte**.
    
    REGOLE LOGISTICHE:
    1. **Arrivo/Partenza:** Calcola i tempi di transito aeroporto.
    2. **Coordinate:** Fornisci sempre lat/lon.
    3. **Ottimizzazione:** Raggruppa le attività per vicinanza geografica (quartieri).
    4. **Smart Skip:** Evita luoghi chiusi o troppo affollati.
    
    FORMATO OUTPUT (SOLO JSON):
    {{
      "trip_title": "Titolo evocativo in Italiano",
      "summary": "Riassunto del viaggio in Italiano",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome Luogo",
              "description": "Descrizione dettagliata in ITALIANO",
              "duration": "2h",
              "coordinates": {{ "lat": 0.0, "lon": 0.0 }},
              "tips": "Consiglio pratico in ITALIANO"
            }}
          ]
        }}
      ]
    }}
    """
    
    with st.spinner("Sto generando l'itinerario..."):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore generazione: {e}")
            return None

# --- UI PRINCIPALE ---
st.title("🏛️ AI Cultural Travel Planner")
st.markdown("Itinerari storici ottimizzati per **distanze** e **affollamento**.")
st.write("") 

# --- LAYOUT A RIGHE ---
h_col1, h_col2 = st.columns([2, 2])
with h_col1: st.subheader("📍 Destinazione")
with h_col2: st.subheader("✈️ Date e Orari")

# RIGA 1: Nazione | Data Arrivo | Ora Arrivo
r1_col1, r1_col2, r1_col3 = st.columns([2, 1, 1]) 
with r1_col1:
    default_ix = all_nations.index("Italy") if "Italy" in all_nations else 0
    selected_nation = st.selectbox("Seleziona Nazione", all_nations, index=default_ix)
    nation_code = map_name_code.get(selected_nation)
    available_cities = db_cities.get(nation_code, [])
    city_options = ["Scrivi manualmente..."] + available_cities
    
with r1_col2: start_date = st.date_input("Giorno di Arrivo", datetime.date.today())
with r1_col3: arrival_time = st.time_input("Orario di Atterraggio", datetime.time(10, 00))

# RIGA 2: Città | Data Partenza | Ora Partenza
r2_col1, r2_col2, r2_col3 = st.columns([2, 1, 1])
with r2_col1:
    selected_city_opt = st.selectbox(f"Città in {selected_nation}", city_options, index=1 if len(city_options) > 1 else 0)
    city_input = st.text_input("Inserisci città") if selected_city_opt == "Scrivi manualmente..." else selected_city_opt
    final_destination = f"{city_input}, {selected_nation}"

with r2_col2: end_date = st.date_input("Giorno di Partenza", datetime.date.today() + datetime.timedelta(days=3))
with r2_col3: departure_time = st.time_input("Orario di Decollo", datetime.time(18, 00))

st.markdown("---")

# --- PULSANTE CENTRATO ---
c_left, c_center, c_right = st.columns([1, 2, 1])
with c_center:
    generate_click = st.button("✨ Genera Itinerario", type="primary", use_container_width=True)

if generate_click:
    if not city_input:
        st.warning("Seleziona una città valida.")
    else:
        trip_data = get_itinerary(final_destination, start_date, arrival_time, end_date, departure_time)
        
        if trip_data:
            st.success(f"Itinerario creato per {final_destination}!")
            st.markdown("---")
            
            # Intestazione e PDF
            h_col1, h_col2 = st.columns([3, 1])
            with h_col1:
                st.header(trip_data.get("trip_title", ""))
                st.write(trip_data.get("summary", ""))
            with h_col2:
                pdf_bytes = create_pdf(trip_data, final_destination)
                st.download_button(
                    label="📄 Scarica PDF con Mappe",
                    data=pdf_bytes,
                    file_name=f"Itinerario_{city_input}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            # Loop Giorni
            for day in trip_data.get("days", []):
                with st.expander(f"📅 Giorno {day['day_number']} - {day.get('date', '')}", expanded=True):
                    
                    col_list, col_map = st.columns([2, 1])
                    
                    # Colonna Sinistra: Lista Attività
                    with col_list:
                        num_activities = len(day.get("activities", []))
                        for activity in day.get("activities", []):
                            q_place = activity['place_name'].replace(" ", "+")
                            q_city = city_input.replace(" ", "+")
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={q_place}+{q_city}"
                            
                            st.markdown(f"""
                            <div class="activity-card">
                                <div style="display:flex; justify-content:space-between; align-items:start;">
                                    <div class="card-title">{activity['place_name']}</div>
                                    <div class='time-badge'>{activity['time']}</div>
                                </div>
                                <div class="card-desc">{activity['description']}</div>
                                <div class="card-meta">
                                    <span>⏱️ {activity['duration']} | <i>{activity.get('tips', '')}</i></span>
                                    <a href="{maps_url}" target="_blank" class="maps-link">📍 Apri Mappa</a>
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
                            
                            # --- CALCOLO ALTEZZA DINAMICA (Calibrato) ---
                            # 100px per card
                            dynamic_height = max(350, num_activities * 100)
                            
                            st.map(df_map, size=20, color='#8B4513', use_container_width=True, height=dynamic_height)
                        else:
                            st.info("Nessuna coordinata disponibile.")

st.markdown("---")
st.caption("Powered by Google Gemini 2.0 Flash")