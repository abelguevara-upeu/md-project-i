import streamlit as st
import joblib
import json
import pandas as pd
import os


MODEL_PATH = os.path.join("models", "desnutricion_model_v1.joblib")
METADATA_PATH = os.path.join("models", "desnutricion_model_v1_metadata.json")


@st.cache_resource
def load_model_and_metadata(model_path=MODEL_PATH, metadata_path=METADATA_PATH):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No se encontró el modelo en: {model_path}")
    model = joblib.load(model_path)

    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

    # Intentar obtener el best_estimator_ si el objeto es un SearchCV
    best = getattr(model, 'best_estimator_', model)
    return model, best, metadata


def get_ohe_categories(best_estimator):
    try:
        preprocessor = best_estimator.named_steps['preprocessor']
        cat_transformer = preprocessor.named_transformers_['cat']
        ohe = cat_transformer.named_steps['onehot']
        categories = list(ohe.categories_)
        return categories
    except Exception:
        return None


def main():
    st.set_page_config(page_title="Desnutricion - Predictor", layout="centered")
    st.title("Predicción de Desnutrición Crónica")

    st.markdown("Ingrese las características del niño/a y la madre.\nEl modelo usará el umbral óptimo guardado para decidir la clase.")

    # Cargar modelo y metadatos
    try:
        model_obj, best_estimator, metadata = load_model_and_metadata()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Asegúrate de ejecutar el notebook de modelado y de tener el archivo .joblib en la carpeta `models/`.")
        return

    optimal_threshold = metadata.get('optimal_threshold', 0.5)

    # Definir columnas (mismas que en el notebook)
    numeric_features = ['edad_meses', 'peso_nacer_kg', 'talla_madre_cm']
    categorical_features = ['zona', 'agua', 'saneamiento', 'riqueza', 'educacion_madre']
    PREDICTORS = numeric_features + categorical_features

    # Obtener categorías desde el OneHotEncoder si es posible
    categories = get_ohe_categories(best_estimator)

    with st.form('input_form'):
        st.subheader('Características numéricas')
        edad_meses = st.number_input('Edad (meses)', min_value=0, max_value=200, value=24)
        peso_nacer_kg = st.number_input('Peso al nacer (kg)', min_value=0.0, max_value=6.0, value=3.0, format="%.2f")
        talla_madre_cm = st.number_input('Talla de la madre (cm)', min_value=100.0, max_value=200.0, value=150.0, format="%.1f")

        st.subheader('Características categóricas')

        # Si tenemos categorías desde el encoder, usamos esas opciones; si no, usamos campos de texto
        cat_values = {}
        if categories is not None and len(categories) == len(categorical_features):
            for feat, opts in zip(categorical_features, categories):
                # convertir a strings para selectbox
                opts_list = [str(x) for x in opts]
                cat_values[feat] = st.selectbox(feat.capitalize(), opts_list)
        else:
            for feat in categorical_features:
                cat_values[feat] = st.text_input(feat.capitalize(), value="")

        submitted = st.form_submit_button('Predecir')

    if submitted:
        # Construir DataFrame de una fila con el mismo orden de columnas
        row = {
            'edad_meses': edad_meses,
            'peso_nacer_kg': peso_nacer_kg,
            'talla_madre_cm': talla_madre_cm,
        }
        for feat in categorical_features:
            row[feat] = cat_values.get(feat, '')

        X = pd.DataFrame([row], columns=PREDICTORS)

        # Predecir
        try:
            proba = model_obj.predict_proba(X)[:, 1][0]
            pred_label = int(proba >= optimal_threshold)

            st.metric(label="Probabilidad (clase 1 - Sí desnutrido)", value=f"{proba:.3f}")
            st.write(f"Umbral óptimo usado: {optimal_threshold:.3f}")
            if pred_label == 1:
                st.error("Predicción: SÍ Desnutrido (Clase 1)")
            else:
                st.success("Predicción: No Desnutrido (Clase 0)")

            # Mostrar datos y resultado
            with st.expander('Ver entrada y resultado'):
                st.write(X.T)
                st.write({'probabilidad_clase_1': float(proba), 'prediccion_label': int(pred_label)})

        except Exception as e:
            st.error(f"Error al predecir: {e}")
            st.info('Asegúrate de que el pipeline en el modelo acepte DataFrame con las columnas esperadas.')


if __name__ == '__main__':
    main()
