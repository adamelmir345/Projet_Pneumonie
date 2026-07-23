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


# ─────────────────────────────────────────────────────────────────────────────
# Grad-CAM : Explicabilité de l'IA (Carte de Chaleur)
# ─────────────────────────────────────────────────────────────────────────────
import tensorflow as tf
from PIL import Image

def _find_last_conv_layer(model):
    """
    Parcourt le modèle en sens inverse pour trouver automatiquement
    la dernière couche convolutionnelle (Conv2D). 
    C'est cette couche qui contient les « feature maps » les plus riches.
    """
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
        # Support pour les modèles imbriqués (ex: EfficientNet encapsulé dans un Functional model)
        if hasattr(layer, 'layers'):
            for sub_layer in reversed(layer.layers):
                if isinstance(sub_layer, tf.keras.layers.Conv2D):
                    return sub_layer.name
    return None


def generate_gradcam(img_path, output_path):
    """
    Génère une carte de chaleur Grad-CAM et la superpose sur la radiographie d'origine.
    
    Args:
        img_path (str): Chemin absolu vers l'image de la radiographie.
        output_path (str): Chemin absolu où sauvegarder l'image Grad-CAM résultante.
    
    Returns:
        bool: True si la génération a réussi, False sinon.
    """
    if model is None:
        return False

    try:
        # 1. Charger et prétraiter l'image (identique à predict_pneumonia)
        img = load_img(img_path, target_size=(224, 224))
        x = img_to_array(img)
        x = np.expand_dims(x, axis=0)

        # 2. Identifier la dernière couche convolutionnelle
        #    Pour EfficientNet, on cherche dans le sous-modèle imbriqué
        last_conv_layer_name = None
        grad_model_base = model

        # Chercher si EfficientNet est un sous-modèle (cas fréquent avec transfer learning)
        for layer in model.layers:
            if hasattr(layer, 'layers') and len(layer.layers) > 10:
                # C'est le backbone EfficientNet
                for sub_layer in reversed(layer.layers):
                    if isinstance(sub_layer, tf.keras.layers.Conv2D):
                        last_conv_layer_name = sub_layer.name
                        grad_model_base = layer
                        break
                if last_conv_layer_name:
                    break

        # Fallback : chercher directement dans le modèle principal
        if not last_conv_layer_name:
            last_conv_layer_name = _find_last_conv_layer(model)
            grad_model_base = model

        if not last_conv_layer_name:
            print("⚠️ Grad-CAM : Aucune couche Conv2D trouvée dans le modèle.")
            return False

        # 3. Construire le sous-modèle Grad-CAM
        #    Il a deux sorties : les feature maps de la dernière conv + la prédiction finale
        grad_model = tf.keras.Model(
            inputs=model.input,
            outputs=[
                grad_model_base.get_layer(last_conv_layer_name).output,
                model.output
            ]
        )

        # 4. Calculer les gradients avec GradientTape
        x_tensor = tf.cast(x, tf.float32)
        with tf.GradientTape() as tape:
            conv_outputs, predictions = grad_model(x_tensor, training=False)
            # On prend la sortie correspondant à la classe « positive » (Pneumonie)
            loss = predictions[:, 0]

        # 5. Extraire les gradients de la dernière couche convolutionnelle
        grads = tape.gradient(loss, conv_outputs)

        # 6. Global Average Pooling des gradients (importance de chaque filtre)
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        # 7. Pondérer les feature maps par l'importance de chaque filtre
        conv_outputs = conv_outputs[0]
        heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)

        # 8. Normaliser la heatmap entre 0 et 1
        heatmap = tf.maximum(heatmap, 0) / (tf.math.reduce_max(heatmap) + 1e-8)
        heatmap = heatmap.numpy()

        # 9. Redimensionner la heatmap à la taille de l'image originale
        heatmap_resized = np.uint8(255 * heatmap)
        heatmap_pil = Image.fromarray(heatmap_resized).resize(
            (224, 224), Image.LANCZOS
        )

        # 10. Appliquer une colormap (rouge = zones chaudes, bleu = zones froides)
        import matplotlib
        matplotlib.use('Agg')  # Mode non-interactif (serveur sans écran)

        colormap = matplotlib.colormaps['jet']
        heatmap_colored = colormap(np.array(heatmap_pil) / 255.0)
        heatmap_colored = np.uint8(heatmap_colored[:, :, :3] * 255)
        heatmap_rgba = Image.fromarray(heatmap_colored).convert('RGBA')

        # 11. Superposer la heatmap sur l'image originale (transparence 40%)
        original = Image.open(img_path).resize((224, 224)).convert('RGBA')
        heatmap_rgba.putalpha(102)  # 40% d'opacité (255 * 0.4 ≈ 102)
        
        composite = Image.alpha_composite(original, heatmap_rgba)
        composite = composite.convert('RGB')

        # 12. Sauvegarder l'image finale
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        composite.save(output_path, quality=95)
        print(f"✅ Grad-CAM généré avec succès : {output_path}")
        return True

    except Exception as e:
        print(f"⚠️ Erreur lors de la génération Grad-CAM : {e}")
        import traceback
        traceback.print_exc()
        return False