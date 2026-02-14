# **Générateur d'Images Hexagonales Géographiques**

Ce projet Python génère automatiquement des images composites basées sur des frontières géographiques réelles (Départements, Régions, DOM-TOM, France).

## **🎨 Le Concept**

Le script crée une image finale composée de 3 couches :

1. **Fond Base :** Une image carrée en arrière-plan (fond\_exterieur.png).  
2. **Fond Milieu (Hexagone) :** Une image découpée en forme d'hexagone (fond.png), centrée sur la base.  
3. **Intérieur (Carte) :** Une image découpée selon la frontière géographique (ex: Bretagne), centrée dans l'hexagone.

## **🛠️ Prérequis**

* Python 3.8 ou supérieur.  
* Les bibliothèques listées dans requirements.txt.

### **Installation**

1. Clonez ce dépôt ou téléchargez les fichiers.  
2. Installez les dépendances :  
   pip install \-r requirements.txt

   *(Note : Si vous n'avez pas de fichier requirements.txt, installez : osmnx, matplotlib, Pillow, geopandas)*

## **📂 Structure des Dossiers**

Il est important de respecter cette structure pour que le script trouve vos images.  
mon-projet/  
│  
├── main.py                  \# Le script principal  
├── output/                  \# (Créé automatiquement) Contient les images générées  
│  
└── inputs/                  \# VOS IMAGES SOURCES  
    ├── fond\_exterieur.png   \# Image de fond tout en bas (Base)  
    ├── fond.png             \# Image qui sera découpée en Hexagone (Milieu)  
    ├── interieur.png        \# Image par défaut pour la carte géographique  
    │  
    ├── Bretagne.png         \# (Optionnel) Image spécifique pour la Bretagne  
    ├── Paris.png            \# (Optionnel) Image spécifique pour Paris  
    └── ...

## **🚀 Utilisation**

1. Placez vos images de base dans le dossier inputs/.  
2. Lancez le script :  
   python main.py

3. Attendez que le script télécharge les données OpenStreetMap et traite les images.  
4. Retrouvez les résultats dans le dossier output/.

## **⚙️ Fonctionnalités**

* **Gestion intelligente des images :** Le script cherche d'abord une image spécifique (ex: Bretagne.png). Si elle n'existe pas, il utilise interieur.png.  
* **France Spéciale :** Génère automatiquement deux versions de la France : "Avec Corse" et "Sans Corse" (en reconstruisant proprement la carte à partir des régions pour éviter les trous).  
* **Outre-mer :** Gère les DOM-TOM et COM avec des requêtes spécifiques pour obtenir les contours des îles physiques (et non les immenses zones maritimes administratives).  
* **Anti-débordement :** La carte géographique est redimensionnée pour tenir parfaitement dans l'hexagone avec une marge de sécurité.  
* **Projection automatique :** Les cartes sont projetées (Web Mercator) pour éviter d'être "écrasées" ou déformées.

## **⚠️ Notes**

* **Connexion Internet :** Requise pour télécharger les frontières via OpenStreetMap (OSMnx).  
* **Performance :** Le premier lancement peut être un peu lent le temps de télécharger les géométries.  
* **Erreurs :** Si un lieu n'est pas trouvé, le script l'indique dans la console et passe au suivant sans s'arrêter.