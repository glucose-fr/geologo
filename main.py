import os
import logging
import io
import math
import matplotlib
import matplotlib.pyplot as plt
import osmnx as ox
import geopandas as gpd
from PIL import Image, ImageOps, ImageDraw, ImageChops

# Configuration du backend matplotlib
matplotlib.use('Agg')

# --- CONFIGURATION ---
INPUT_DIR = "inputs"
OUTPUT_DIR = "output"

# Nouvelle organisation des images
DEFAULT_BASE_IMG = "fond_exterieur.png"    # La nouvelle image de fond tout en bas
DEFAULT_MIDDLE_IMG = "fond.png"            # L'ancienne image de fond (devient le milieu hexagone)
DEFAULT_INTERNAL_IMG = "interieur.png"     # L'ancienne image centrale (la carte géographique)

# --- LISTES GÉOGRAPHIQUES ---

# Liste complète des départements métropolitains (96)
DEPARTEMENTS = [
    "Ain", "Aisne", "Allier", "Alpes-de-Haute-Provence", "Hautes-Alpes",
    "Alpes-Maritimes", "Ardèche", "Ardennes", "Ariège", "Aube", "Aude",
    "Aveyron", "Bouches-du-Rhône", "Calvados", "Cantal", "Charente",
    "Charente-Maritime", "Cher", "Corrèze", "Corse-du-Sud", "Haute-Corse",
    "Côte-d'Or", "Côtes-d'Armor", "Creuse", "Dordogne", "Doubs", "Drôme",
    "Eure", "Eure-et-Loir", "Finistère", "Gard", "Haute-Garonne", "Gers",
    "Gironde", "Hérault", "Ille-et-Vilaine", "Indre", "Indre-et-Loire",
    "Isère", "Jura", "Landes", "Loir-et-Cher", "Loire", "Haute-Loire",
    "Loire-Atlantique", "Loiret", "Lot", "Lot-et-Garonne", "Lozère",
    "Maine-et-Loire", "Manche", "Marne", "Haute-Marne", "Mayenne",
    "Meurthe-et-Moselle", "Meuse", "Morbihan", "Moselle", "Nièvre", "Nord",
    "Oise", "Orne", "Pas-de-Calais", "Puy-de-Dôme", "Pyrénées-Atlantiques",
    "Hautes-Pyrénées", "Pyrénées-Orientales", "Bas-Rhin", "Haut-Rhin",
    "Rhône", "Haute-Saône", "Saône-et-Loire", "Sarthe", "Savoie",
    "Haute-Savoie", "Paris", "Seine-Maritime", "Seine-et-Marne",
    "Yvelines", "Deux-Sèvres", "Somme", "Tarn", "Tarn-et-Garonne", "Var",
    "Vaucluse", "Vendée", "Vienne", "Haute-Vienne", "Vosges", "Yonne",
    "Territoire de Belfort", "Essonne", "Hauts-de-Seine", "Seine-Saint-Denis",
    "Val-de-Marne", "Val-d'Oise"
]

# Liste complète des 13 régions métropolitaines
REGIONS = [
    "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne, France",
    "Centre-Val de Loire", "Corse", "Grand Est", "Hauts-de-France",
    "Île-de-France", "Normandie", "Nouvelle-Aquitaine", "Occitanie",
    "Pays de la Loire", "Provence-Alpes-Côte d'Azur"
]

# DOM-TOM & COM
DOM_TOM = [
    "Guadeloupe", "Martinique", "Guyane", "La Réunion", "Mayotte",
    "Saint-Pierre-et-Miquelon", "Saint-Barthélemy", "Saint-Martin",
    "Wallis-et-Futuna", "Polynésie française", "Nouvelle-Calédonie"
]

# --- REQUÊTES SPÉCIALES OSM ---
CUSTOM_OSM_QUERIES = {
    "La Réunion": "Île de La Réunion",
    "Martinique": "Île de la Martinique",
    "Guadeloupe": "Guadeloupe, France", 
    "Guyane": "Guyane française",
    "Mayotte": "Mayotte, France", 
    "Saint-Pierre-et-Miquelon": "Saint-Pierre-et-Miquelon",
    "Saint-Barthélemy": "Saint-Barthélemy, France",
    "Saint-Martin": "Saint-Martin (partie française)", 
    "Wallis-et-Futuna": "Wallis-et-Futuna",
    "Polynésie française": "Polynésie française",
    "Nouvelle-Calédonie": "Nouvelle-Calédonie",
    "Terres australes et antarctiques françaises": "Terres australes et antarctiques françaises",
    "Clipperton": "Île de Clipperton"
}

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def get_internal_image(place_name):
    """
    Cherche l'image 'Intérieure' (celle qui prendra la forme du département/pays).
    """
    search_name = place_name.split('_')[0] 
    
    specific_path = os.path.join(INPUT_DIR, f"{search_name}.png")
    default_path = os.path.join(INPUT_DIR, DEFAULT_INTERNAL_IMG)

    if os.path.exists(specific_path):
        return Image.open(specific_path).convert("RGBA")
    elif os.path.exists(default_path):
        logger.warning(f"Image spécifique absente pour {search_name}. Utilisation du défaut.")
        return Image.open(default_path).convert("RGBA")
    else:
        raise FileNotFoundError(f"Aucune image trouvée pour {place_name} (ni spécifique, ni défaut).")


def generate_mask_from_gdf(gdf):
    """Génère le masque géographique (Région/Département)."""
    # Projection en Web Mercator (EPSG:3857) pour éviter l'écrasement
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.set_aspect('equal')
    ax.axis('off')
    
    gdf.plot(ax=ax, color='black')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=300, transparent=True)
    plt.close(fig)
    buf.seek(0)
    
    mask_img = Image.open(buf).convert("RGBA")
    r, g, b, alpha = mask_img.split()
    return alpha


def generate_hexagon_mask(size):
    """
    Génère un masque en forme d'hexagone régulier.
    size: tuple (width, height)
    """
    width, height = size
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    
    # Calcul des points de l'hexagone
    # On prend le rayon comme la moitié de la plus petite dimension pour que ça rentre
    radius = min(width, height) / 2
    cx, cy = width / 2, height / 2
    
    points = []
    for i in range(6):
        # Angle en radians (commence à -90° pour avoir une pointe en haut)
        angle_deg = 60 * i - 30 
        angle_rad = math.radians(angle_deg)
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)
        points.append((x, y))
    
    draw.polygon(points, fill=255)
    return mask


def process_place(place_name, base_img_path, custom_gdf=None, output_suffix=""):
    """
    Pipeline de génération : Base -> Hexagone (Middle) -> Forme Géo (Internal)
    """
    try:
        display_name = place_name + output_suffix
        logger.info(f"--- Traitement : {display_name} ---")

        # 1. Chargement de la BASE (Tout au fond)
        if not os.path.exists(base_img_path):
             raise FileNotFoundError(f"Image de base introuvable : {base_img_path}")
        
        base_img = Image.open(base_img_path).convert("RGBA")
        
        # --- MODIFICATION: Forcer le format CARRÉ ---
        # On recadre l'image de base pour qu'elle soit carrée (sur la plus petite dimension)
        min_dim = min(base_img.size)
        base_img = ImageOps.fit(base_img, (min_dim, min_dim), method=Image.Resampling.LANCZOS)
        base_w, base_h = base_img.size # Maintenant base_w == base_h

        # 2. Chargement du MILIEU (Celui qui sera hexagone)
        middle_path = os.path.join(INPUT_DIR, DEFAULT_MIDDLE_IMG)
        if not os.path.exists(middle_path):
             raise FileNotFoundError(f"Image milieu introuvable : {middle_path}")
        middle_source = Image.open(middle_path).convert("RGBA")

        # 3. Chargement de l'INTERIEUR (Celui qui sera la carte)
        internal_source = get_internal_image(place_name)

        # 4. Génération du Masque GÉOGRAPHIQUE
        if custom_gdf is not None:
            geo_mask = generate_mask_from_gdf(custom_gdf)
        else:
            if place_name in CUSTOM_OSM_QUERIES:
                query = CUSTOM_OSM_QUERIES[place_name]
                logger.info(f"Requête OSM optimisée : '{query}'")
            elif place_name not in ["France", "France métropolitaine"]:
                query = f"{place_name}, France"
            else:
                query = place_name
            
            gdf = ox.geocode_to_gdf(query)
            geo_mask = generate_mask_from_gdf(gdf)

        # --- CALCULS DE TAILLES ---
        
        # Taille cible de l'Hexagone (90% de la base -> Marge de 5% de chaque côté)
        hex_w = int(base_w * 0.9)
        hex_h = int(base_h * 0.9)
        
        # Taille cible de la Forme Géo (70% de l'Hexagone)
        # On réduit à 70% (contre 80% avant) pour que la carte rentre totalement dans l'hexagone
        # y compris les coins (comme la Corse qui dépasse en bas à droite sinon)
        geo_target_w_max = int(hex_w * 0.7)
        geo_target_h_max = int(hex_h * 0.7)
        
        # --- ÉTAPE A : CRÉATION DU LAYER CARTE (Interieur + Masque Géo) ---
        
        # Redimensionner le masque géo pour qu'il rentre dans l'hexagone
        scale_geo = min(geo_target_w_max / geo_mask.width, geo_target_h_max / geo_mask.height)
        geo_w = int(geo_mask.width * scale_geo)
        geo_h = int(geo_mask.height * scale_geo)
        
        geo_mask_resized = geo_mask.resize((geo_w, geo_h), Image.Resampling.LANCZOS)
        
        # Adapter l'image 'Interieur' à la taille du masque géo
        internal_fitted = ImageOps.fit(internal_source, (geo_w, geo_h), method=Image.Resampling.LANCZOS)
        
        # Création de l'objet Carte découpée
        layer_map = Image.new("RGBA", (geo_w, geo_h), (0, 0, 0, 0))
        layer_map.paste(internal_fitted, (0, 0), mask=geo_mask_resized)

        # --- ÉTAPE B : CRÉATION DU LAYER HEXAGONE (Milieu + Masque Hex + Layer Carte) ---
        
        # Création du masque Hexagone
        hex_mask = generate_hexagon_mask((hex_w, hex_h))
        
        # Adapter l'image 'Milieu' à la taille de l'hexagone
        middle_fitted = ImageOps.fit(middle_source, (hex_w, hex_h), method=Image.Resampling.LANCZOS)
        
        # Création de l'objet Hexagone découpé
        layer_hex = Image.new("RGBA", (hex_w, hex_h), (0, 0, 0, 0))
        layer_hex.paste(middle_fitted, (0, 0), mask=hex_mask)
        
        # On colle la Carte (layer_map) au centre de l'Hexagone (layer_hex)
        offset_map_x = (hex_w - geo_w) // 2
        offset_map_y = (hex_h - geo_h) // 2
        layer_hex.paste(layer_map, (offset_map_x, offset_map_y), layer_map)

        # --- SECURITE ANTI-DEBORDEMENT ---
        # On ré-applique le masque hexagone sur le tout pour couper ce qui dépasserait (les coins de la carte)
        # Cela garantit que rien ne sort de l'hexagone
        r, g, b, a = layer_hex.split()
        a = ImageChops.multiply(a, hex_mask) # Intersection des alphas
        layer_hex.putalpha(a)

        # --- ÉTAPE C : ASSEMBLAGE FINAL SUR LA BASE ---
        
        offset_hex_x = (base_w - hex_w) // 2
        offset_hex_y = (base_h - hex_h) // 2
        
        final_composition = base_img.copy()
        final_composition.paste(layer_hex, (offset_hex_x, offset_hex_y), layer_hex)

        # 7. Sauvegarde
        filename = f"{place_name}{output_suffix}.png"
        save_path = os.path.join(OUTPUT_DIR, filename)
        final_composition.save(save_path)
        logger.info(f"OK : {filename}")

    except Exception as e:
        logger.error(f"ERREUR sur {place_name} : {str(e)}")


def process_france_special(base_img_path):
    """Logique spéciale pour la France (Reconstruction par Régions)"""
    try:
        logger.info("--- Spécial : Reconstruction France par Régions ---")
        
        gdf_regions = ox.geocode_to_gdf(REGIONS)
        
        # Cas 1 : Avec Corse
        gdf_avec_corse = gdf_regions.union_all()
        gdf_avec_corse_wrapper = gpd.GeoDataFrame(geometry=[gdf_avec_corse], crs=gdf_regions.crs)
        process_place("France", base_img_path, custom_gdf=gdf_avec_corse_wrapper, output_suffix="_avec_corse")
        
        # Cas 2 : Sans Corse
        regions_sans_corse = [r for r in REGIONS if r != "Corse"]
        gdf_regions_mainland = ox.geocode_to_gdf(regions_sans_corse)
        gdf_sans_corse = gdf_regions_mainland.union_all()
        gdf_sans_corse_wrapper = gpd.GeoDataFrame(geometry=[gdf_sans_corse], crs=gdf_regions_mainland.crs)

        process_place("France", base_img_path, custom_gdf=gdf_sans_corse_wrapper, output_suffix="_sans_corse")

    except Exception as e:
        logger.error(f"ERREUR SPÉCIALE FRANCE : {str(e)}")


def main():
    setup_directories()
    
    # On vérifie maintenant l'image de BASE (fond_exterieur.png)
    base_path = os.path.join(INPUT_DIR, DEFAULT_BASE_IMG)
    
    if not os.path.exists(base_path):
        logger.error(f"Image de base manquante : {base_path} ! Ajoutez-la dans {INPUT_DIR}")
        return

    # 1. Traitement Spécial France
    process_france_special(base_path)

    # 2. Traitement des Départements et DOM-TOM
    all_places = DEPARTEMENTS + DOM_TOM
    
    for place in all_places:
        process_place(place, base_path)

if __name__ == "__main__":
    main()