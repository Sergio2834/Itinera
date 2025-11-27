#set librerie opensource OSMnx=dati stradali,POI da opentreetmap, GeopPandas=gestione dati geospaziali, NetworkX=analisi grafi, Scikit-learn=raggruppamento luoghi in zone
pip install osmnx geopandas networkx scikit-learn
# import delle librerie necessarie
import osmnx as ox          # per scaricare e lavorare con i dati di OpenStreetMap
import networkx as nx         # Per i grafi e percorsi
import pandas as pd           # Per gestire i dati tabellari
from sklearn.cluster import KMeans  # Per i gruppi (zone)
from datetime import datetime # Per gestire gli orari