import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import load_img, img_to_array
from django.conf import settings

# Chemin vers ton modèle .h5 stocké à la racine dans ai_model
MODEL_PATH = os.path.join(settings.BASE_DIR, 'ai_model', 'best_model.h5')

# Charger le modèle une seule fois au démarrage pour optimiser les performances
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = load_model(MODEL_PATH)
        print("✅ Modèle IA chargé avec succès !")
    except Exception as e:
        print(f"⚠️ Impossible de charger le modèle IA : {e}")
        model = None

def predict_pneumonia(img_path):
    """
    Prend le chemin d'une image de radiographie, la prétraite, 
    et retourne la classe prédite ainsi que le pourcentage de confiance.
    """
    if model is None:
        return "Erreur", 0.0

    # 1. Charger et redimensionner l'image à la norme attendue par le CNN (224x224)
    img = load_img(img_path, target_size=(224, 224))
    
    # 2. Convertir en tableau numpy
    x = img_to_array(img)
    
    # 3. Ajouter une dimension pour correspondre au batch (1, 224, 224, 3)
    x = np.expand_dims(x, axis=0)
    
    # Note : Ton EfficientNet intègre déjà sa propre normalisation/rescaling interne 
    # définie lors de l'entraînement, on passe donc l'image directement.

    # 4. Inférence (Prédiction)
    prediction = model(x, training=False)
    score = float(prediction[0][0])  # Valeur entre 0 et 1 (sigmoïde)

    # 5. Interprétation du résultat (selon ton entraînement binaire)
    # Si score > 0.5 -> Pneumonie, sinon -> Normal (ou inversement selon ton encodage)
    if score > 0.5:
        classe = "Pneumonie"
        confiance = score * 100
    else:
        classe = "Normal"
        confiance = (1 - score) * 100

    return classe, round(confiance, 2)