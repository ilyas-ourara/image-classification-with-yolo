#!/usr/bin/env python3
"""
Interface Streamlit pour classification avec modèle YOLO réel
Utilise exclusivement le modèle models/best.pt
"""

import streamlit as st
import numpy as np
import cv2
from PIL import Image
import plotly.graph_objects as go
import time
import os
import tempfile
import warnings

# Configuration de la page - DOIT être la première commande Streamlit
st.set_page_config(
    page_title="🤖 Classificateur d'Images Wang ",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

"""
Commande de lancement:
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python streamlit run 
Mini_Projet/app.py --server.port 8506
"""

# Supprimer les warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    st.error("❌ Ultralytics non installé. Installez avec: pip install ultralytics")
    st.stop()

# CSS pour l'interface
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .custom-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .prediction-card {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 5px;
    }
    
    .upload-zone {
        border: 2px dashed #4ECDC4;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background: rgba(255, 255, 255, 0.05);
    }
    
    .info-box {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration du modèle
@st.cache_resource
def load_yolo_model():
    """Charger le modèle YOLO et récupérer les noms des classes"""
    try:
        model_path = "models/best.pt"
        if not os.path.exists(model_path):
            st.error(f"❌ Modèle non trouvé: {model_path}")
            st.info("Assurez-vous que le modèle 'models/best.pt' existe")
            st.stop()
        
        model = YOLO(model_path)
        st.success(f"✅ Modèle YOLO chargé: {model_path}")
        
        # Récupérer les noms des classes du modèle
        class_names = model.names if hasattr(model, 'names') else {}
        
        return model, class_names
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du modèle: {str(e)}")
        st.stop()


def preprocess_image_for_yolo(image):
    """Préprocesser l'image pour YOLO"""
    try:
        # Convertir PIL en array numpy
        img_array = np.array(image)
        
        # Convertir RGB en BGR pour OpenCV si nécessaire
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        return img_array
    except Exception as e:
        st.error(f"Erreur lors du préprocessing: {str(e)}")
        return None

def predict_with_yolo(model, image):
    """Faire une prédiction avec YOLO"""
    try:
        # Préprocesser l'image
        processed_img = preprocess_image_for_yolo(image)
        if processed_img is None:
            return None, None
        
        # Faire la prédiction
        results = model(processed_img, verbose=False)
        
        # Extraire les probabilités
        if results and len(results) > 0:
            probs = results[0].probs

            if probs is not None:
                # Convertir en numpy array si nécessaire
                if hasattr(probs, 'data'):
                    probabilities = probs.data.cpu().numpy()
                else:
                    probabilities = np.array(probs)
                
                # Classe prédite
                predicted_class = np.argmax(probabilities)
                confidence = float(probabilities[predicted_class])
                
                return predicted_class, probabilities
        
        return None, None
        
    except Exception as e:
        st.error(f"Erreur lors de la prédiction: {str(e)}")
        return None, None

def create_confidence_chart(probabilities, class_names):
    """Créer un graphique de confiance"""
    if probabilities is None:
        return None
    
    try:
        # Trier par probabilité décroissante
        sorted_indices = np.argsort(probabilities)[::-1]
        sorted_probs = probabilities[sorted_indices]
        sorted_names = [class_names[i] for i in sorted_indices]
        
        # Créer le graphique Plotly
        fig = go.Figure(data=[
            go.Bar(
                x=sorted_names,
                y=sorted_probs * 100,  # Convertir en pourcentage
                marker=dict(
                    color=sorted_probs,
                    colorscale='Viridis',
                    colorbar=dict(title="Confiance (%)")
                ),
                text=[f'{p*100:.1f}%' for p in sorted_probs],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title="Distribution des Probabilités de Classification",
            xaxis_title="Classes",
            yaxis_title="Confiance (%)",
            height=500,
            showlegend=False,
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    except Exception as e:
        st.error(f"Erreur lors de la création du graphique: {str(e)}")
        return None

def main():
    """Fonction principale de l'application"""
    
    # Titre avec animation
    st.markdown("""
    <div class="custom-container">
        <h1 style="text-align: center; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            🤖 Classificateur d'Images Wang 
        </h1>
        <p style="text-align: center; color: white; font-size: 18px;">
            Classification d'images avec modèle YOLO entraîné sur le dataset Wang
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Charger le modèle et récupérer les noms des classes
    model, wang_classes = load_yolo_model()
    
    # Sidebar avec informations
    with st.sidebar:
        st.markdown("""
        <div class="info-box">
            <h3>📋 Informations du Modèle</h3>
            <p><strong>Type:</strong> YOLO Classification</p>
            <p><strong>Dataset:</strong> Wang </p>
            <p><strong>Classes:</strong> 10 catégories</p>
            <p><strong>Modèle:</strong> models/best.pt</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Classes disponibles:")
        if wang_classes:
            for idx, class_name in wang_classes.items():
                st.write(f"**{idx}**: {class_name}")
        else:
            st.warning("Classes non disponibles")
    
    # Zone d'upload
    st.markdown("""
    <div class="upload-zone">
        <h3 style="color: #4ECDC4;">📤 Téléchargez votre image</h3>
        <p>Formats supportés: JPG, JPEG, PNG</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choisissez une image...",
        type=['jpg', 'jpeg', 'png'],
        help="Téléchargez une image pour la classifier"
    )
    
    if uploaded_file is not None:
        try:
            # Charger et afficher l'image
            image = Image.open(uploaded_file)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### 🖼️ Image uploadée")
                st.image(image, caption=f"Fichier: {uploaded_file.name}", use_column_width=True)
                
                # Informations sur l'image
                st.markdown(f"""
                <div class="metric-card">
                    <strong>Dimensions:</strong> {image.size[0]} x {image.size[1]}<br>
                    <strong>Mode:</strong> {image.mode}<br>
                    <strong>Format:</strong> {image.format}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 🔮 Prédiction")
                
                # Faire la prédiction avec loading
                with st.spinner("🤖 Classification en cours..."):
                    time.sleep(0.5)  # Petit délai pour l'animation
                    predicted_class, probabilities = predict_with_yolo(model, image)
                
                if predicted_class is not None and probabilities is not None:
                    class_name = wang_classes.get(predicted_class, "Inconnu")
                    confidence = probabilities[predicted_class] * 100
                    
                    # Affichage de la prédiction
                    st.markdown(f"""
                    <div class="prediction-card">
                        <h2>🎯 {class_name}</h2>
                        <h3>{confidence:.1f}% de confiance</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Métriques détaillées
                    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
                    
                    with col_metrics1:
                        st.metric("🏆 Classe prédite", class_name)
                    
                    with col_metrics2:
                        st.metric("📊 Confiance", f"{confidence:.1f}%")
                    
                    with col_metrics3:
                        st.metric("🔢 Index classe", predicted_class)
                    
                    # Graphique de distribution
                    st.markdown("### 📈 Distribution des probabilités")
                    fig = create_confidence_chart(probabilities, wang_classes)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Top 3 des prédictions
                    st.markdown("### 🥇 Top 3 des prédictions")
                    top_indices = np.argsort(probabilities)[::-1][:3]
                    
                    for i, idx in enumerate(top_indices):
                        rank_emoji = ["🥇", "🥈", "🥉"][i]
                        class_name_top = wang_classes.get(idx, "Inconnu")
                        confidence_top = probabilities[idx] * 100
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            {rank_emoji} <strong>{class_name_top}</strong>: {confidence_top:.1f}%
                        </div>
                        """, unsafe_allow_html=True)
                
                else:
                    st.error("❌ Impossible de faire une prédiction pour cette image")
        
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement de l'image: {str(e)}")
            st.info("Veuillez vérifier que votre image est dans un format correct")
    
    else:
        # Informations d'aide
        st.markdown("""
        <div class="custom-container">
            <h3 style="color: white;">💡 Comment utiliser cette application:</h3>
            <ol style="color: white;">
                <li>📤 <strong>Téléchargez</strong> une image (JPG, JPEG, PNG)</li>
                <li>⏳ <strong>Attendez</strong> que le modèle YOLO traite l'image</li>
                <li>📊 <strong>Consultez</strong> les résultats et la distribution des probabilités</li>
                <li>🔍 <strong>Analysez</strong> le top 3 des prédictions</li>
            </ol>
            
            <h4 style="color: #4ECDC4;">🎯 Classes du dataset Wang:</h4>
            <p style="color: white;">Le modèle peut classifier des images dans 10 catégories: Jungle, Plage, Monuments, Bus, Dinosaures, Éléphants, Fleurs, Chevaux, Montagne, et Plats.</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()