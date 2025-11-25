import streamlit as st
import joblib
import json
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go


MODEL_PATH = os.path.join("models", "desnutricion_model_v1.joblib")
METADATA_PATH = os.path.join("models", "desnutricion_model_v1_metadata.json")
DATA_PATH = os.path.join("data", "processed", "mvp_dataset_fase3_limpio.csv")


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


@st.cache_data
def load_data():
    """Cargar dataset para visualizaciones"""
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    return None


def predictor_page(model_obj, best_estimator, metadata, categories):
    """Página de predicción individual"""
    st.title("🔮 Predicción de Desnutrición Crónica")

    # Header mejorado con diseño
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h4 style='color: #0e1117; margin: 0;'>📋 Instrucciones</h4>
        <p style='color: #31333F; margin: 10px 0 0 0;'>
            Complete los datos del niño/a, madre y hogar. El modelo calculará la probabilidad
            de desnutrición crónica usando un umbral optimizado.
        </p>
    </div>
    """, unsafe_allow_html=True)

    optimal_threshold = metadata.get('optimal_threshold', 0.5)

    # Definir columnas
    numeric_features = ['edad_meses', 'peso_nacer_kg', 'talla_madre_cm']
    categorical_features = ['zona', 'agua', 'saneamiento', 'riqueza', 'educacion_madre']
    PREDICTORS = numeric_features + categorical_features

    # Diseño con columnas para inputs
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 👶 Características del Niño/a")
        edad_meses = st.slider('Edad (meses)', min_value=0, max_value=59, value=24,
                               help='Edad en meses del niño/a (0-59 meses)', key='edad_slider')

        # Calcular años y meses
        años = edad_meses // 12
        meses_restantes = edad_meses % 12
        if edad_meses == 0:
            edad_ref = "Recién nacido"
        elif años == 0:
            edad_ref = f"{meses_restantes} {'mes' if meses_restantes == 1 else 'meses'}"
        elif meses_restantes == 0:
            edad_ref = f"{años} {'año' if años == 1 else 'años'}"
        else:
            edad_ref = f"{años} {'año' if años == 1 else 'años'} y {meses_restantes} {'mes' if meses_restantes == 1 else 'meses'}"
        st.info(f"📅 Equivalente: **{edad_ref}**")

        peso_nacer_kg = st.slider('Peso al nacer (kg)', min_value=0.5, max_value=6.0, value=3.0,
                                  step=0.1, format="%.1f",
                                  help='Peso del niño/a cuando nació (dato histórico)', key='peso_slider')

        # Indicador de riesgo por peso
        if peso_nacer_kg < 2.5:
            st.warning("⚠️ Bajo peso al nacer (<2.5 kg)")
        elif peso_nacer_kg >= 3.0:
            st.success("✅ Peso adecuado")

    with col_right:
        st.markdown("### 👩 Características de la Madre")
        talla_madre_cm = st.slider('Talla (cm)', min_value=100.0, max_value=200.0, value=150.0,
                                   step=0.5, format="%.1f",
                                   help='Estatura de la madre en centímetros', key='talla_slider')

        # Indicador de riesgo por talla
        if talla_madre_cm < 145:
            st.warning("⚠️ Talla baja (<145 cm)")
        elif talla_madre_cm >= 150:
            st.success("✅ Talla adecuada")

    # Separador visual antes de características del hogar
    st.markdown("---")
    st.markdown("### 🏠 Características del Hogar")

    # Características categóricas
    cat_values = {}
    if categories is not None and len(categories) == len(categorical_features):
        labels = {
            'zona': 'Ubicación geográfica',
            'agua': 'Fuente principal de agua del hogar',
            'saneamiento': 'Tipo de servicio sanitario (baño/letrina)',
            'riqueza': 'Nivel socioeconómico del hogar',
            'educacion_madre': 'Nivel educativo alcanzado por la madre'
        }

        col1, col2 = st.columns(2)
        for i, (feat, opts) in enumerate(zip(categorical_features, categories)):
            opts_list = [str(x) for x in opts]
            label = labels.get(feat, feat.capitalize())
            with col1 if i % 2 == 0 else col2:
                cat_values[feat] = st.selectbox(label, opts_list, key=f'{feat}_select')
    else:
        for feat in categorical_features:
            cat_values[feat] = st.text_input(feat.capitalize(), value="", key=f'{feat}_input')

    # Botón de predicción centrado y destacado
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        submitted = st.button('🔍 Realizar Predicción', type='primary', width='stretch')

    if submitted:
        row = {
            'edad_meses': edad_meses,
            'peso_nacer_kg': peso_nacer_kg,
            'talla_madre_cm': talla_madre_cm,
        }
        for feat in categorical_features:
            row[feat] = cat_values.get(feat, '')

        X = pd.DataFrame([row], columns=PREDICTORS)

        try:
            proba = model_obj.predict_proba(X)[:, 1][0]
            pred_label = int(proba >= optimal_threshold)

            # Resultados con diseño mejorado
            st.markdown("---")
            st.markdown("## 📊 Resultados de la Predicción")

            # Gauge chart para probabilidad
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=proba * 100,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Probabilidad de Desnutrición (%)", 'font': {'size': 20}},
                delta={'reference': optimal_threshold * 100, 'increasing': {'color': "red"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "darkred" if proba >= optimal_threshold else "green"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, optimal_threshold * 100], 'color': 'lightgreen'},
                        {'range': [optimal_threshold * 100, 100], 'color': 'lightcoral'}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': optimal_threshold * 100
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, width='stretch')

            # Resultado final con estilo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Probabilidad", f"{proba:.1%}")
            with col2:
                st.metric("Umbral", f"{optimal_threshold:.1%}")
            with col3:
                if pred_label == 1:
                    st.error("🚨 **SÍ Desnutrido**")
                else:
                    st.success("✅ **No Desnutrido**")

            # Interpretación
            st.markdown("### 💡 Interpretación")
            if proba >= optimal_threshold:
                st.error(f"""
                ⚠️ **Alto Riesgo**: La probabilidad ({proba:.1%}) supera el umbral óptimo ({optimal_threshold:.1%}).

                **Recomendaciones:**
                - Evaluación nutricional inmediata
                - Seguimiento médico especializado
                - Suplementación nutricional
                - Educación a los padres sobre alimentación adecuada
                """)
            elif proba >= 0.4:
                st.warning(f"""
                ⚡ **Riesgo Moderado**: La probabilidad ({proba:.1%}) está cerca del umbral ({optimal_threshold:.1%}).

                **Recomendaciones:**
                - Monitoreo nutricional periódico
                - Educación nutricional a la familia
                - Evaluar condiciones del hogar
                - Seguimiento preventivo
                """)
            else:
                st.success(f"""
                ✅ **Bajo Riesgo**: La probabilidad ({proba:.1%}) está por debajo del umbral ({optimal_threshold:.1%}).

                **Recomendaciones:**
                - Mantener controles de crecimiento regulares
                - Continuar con prácticas nutricionales adecuadas
                - Vigilancia preventiva
                """)

            # Detalles técnicos
            with st.expander('🔬 Ver detalles técnicos'):
                st.write("**Datos de entrada:**")
                st.dataframe(X.T, width='stretch')
                st.write("**Resultado del modelo:**")
                st.json({
                    'probabilidad_clase_1': float(proba),
                    'prediccion_label': int(pred_label),
                    'umbral_usado': optimal_threshold
                })

        except Exception as e:
            st.error(f"❌ Error al predecir: {e}")
            st.info('Asegúrate de que el pipeline del modelo esté correctamente configurado.')


def analytics_page():
    """Página de análisis y gráficos interactivos"""
    st.title("📈 Análisis y Visualizaciones del Modelo")

    # Cargar datos
    df = load_data()

    if df is None:
        st.error("No se pudo cargar el dataset. Asegúrate de que exista el archivo en `data/processed/mvp_dataset_fase3_limpio.csv`")
        return

    # Tabs para organizar visualizaciones
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Distribuciones", "🔗 Correlaciones", "🎯 Variables Clave", "📉 Análisis por Grupos"])

    with tab1:
        st.markdown("### Distribución de Variables")

        col1, col2 = st.columns(2)

        with col1:
            # Distribución de HAZ Score
            fig_haz = px.histogram(df, x='haz_score', nbins=50,
                                   title='Distribución del HAZ Score (Talla/Edad)',
                                   labels={'haz_score': 'HAZ Score'},
                                   color_discrete_sequence=['#636EFA'])
            fig_haz.add_vline(x=-2, line_dash="dash", line_color="red",
                            annotation_text="Umbral Desnutrición (-2 SD)")
            st.plotly_chart(fig_haz, width='stretch')

            # Estadísticas
            st.metric("Media HAZ Score", f"{df['haz_score'].mean():.2f}")
            st.metric("% con Desnutrición (<-2 SD)",
                     f"{(df['haz_score'] < -2).sum() / len(df) * 100:.1f}%")

        with col2:
            # Distribución de edad
            fig_edad = px.histogram(df, x='edad_meses', nbins=60,
                                   title='Distribución de Edad (meses)',
                                   labels={'edad_meses': 'Edad (meses)'},
                                   color_discrete_sequence=['#EF553B'])
            st.plotly_chart(fig_edad, width='stretch')

            st.metric("Edad Media", f"{df['edad_meses'].mean():.1f} meses")
            st.metric("Rango", f"{df['edad_meses'].min():.0f} - {df['edad_meses'].max():.0f} meses")

    with tab2:
        st.markdown("### Matriz de Correlación")

        # Cargar correlación
        if os.path.exists('notebooks/tabla_2_correlacion.csv'):
            corr_df = pd.read_csv('notebooks/tabla_2_correlacion.csv', index_col=0)

            # Renombrar columnas e índices para mayor claridad
            labels_mapping = {
                'V106': 'V106 (Educación Madre)',
                'HV270': 'HV270 (Riqueza)',
                'HV025': 'HV025 (Zona)'
            }
            corr_df = corr_df.rename(columns=labels_mapping, index=labels_mapping)

            # Heatmap
            fig_corr = px.imshow(corr_df,
                                text_auto='.2f',
                                aspect="auto",
                                color_continuous_scale='RdBu_r',
                                title='Correlación entre Variables')
            st.plotly_chart(fig_corr, width='stretch')

            # Insights
            st.markdown("#### 🔍 Insights Clave:")
            st.markdown("""
            - **Talla Madre** (0.39): Mayor correlación positiva con HAZ score
            - **Peso al Nacer** (0.34): Segunda variable más importante
            - **Riqueza** (0.30): Factor socioeconómico relevante
            - **Zona Urbana** (-0.24): Zona rural presenta mayor riesgo
            """)

    with tab3:
        st.markdown("### Impacto de Variables Clave")

        # Crear target binario
        df['desnutrido'] = (df['haz_score'] < -2).astype(int)

        col1, col2 = st.columns(2)

        with col1:
            # Por zona
            zona_stats = df.groupby('zona')['desnutrido'].agg(['sum', 'count', 'mean']).reset_index()
            zona_stats['porcentaje'] = zona_stats['mean'] * 100

            fig_zona = px.bar(zona_stats, x='zona', y='porcentaje',
                            title='% Desnutrición por Zona',
                            labels={'porcentaje': '% Desnutridos', 'zona': 'Zona'},
                            color='porcentaje',
                            color_continuous_scale='Reds')
            st.plotly_chart(fig_zona, width='stretch')

        with col2:
            # Por nivel educativo madre
            if 'educacion_madre' in df.columns:
                edu_stats = df.groupby('educacion_madre')['desnutrido'].agg(['sum', 'count', 'mean']).reset_index()
                edu_stats['porcentaje'] = edu_stats['mean'] * 100

                fig_edu = px.bar(edu_stats, x='educacion_madre', y='porcentaje',
                               title='% Desnutrición por Educación Materna',
                               labels={'porcentaje': '% Desnutridos', 'educacion_madre': 'Nivel Educativo'},
                               color='porcentaje',
                               color_continuous_scale='Oranges')
                st.plotly_chart(fig_edu, width='stretch')

        # Por riqueza
        if 'riqueza' in df.columns:
            riq_stats = df.groupby('riqueza')['desnutrido'].agg(['sum', 'count', 'mean']).reset_index()
            riq_stats['porcentaje'] = riq_stats['mean'] * 100

            fig_riq = px.bar(riq_stats, x='riqueza', y='porcentaje',
                           title='% Desnutrición por Nivel de Riqueza',
                           labels={'porcentaje': '% Desnutridos', 'riqueza': 'Nivel de Riqueza'},
                           color='porcentaje',
                           color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig_riq, width='stretch')

    with tab4:
        st.markdown("### Análisis Comparativo")

        # Boxplot por zona
        fig_box_zona = px.box(df, x='zona', y='haz_score',
                             title='Distribución HAZ Score por Zona',
                             color='zona')
        fig_box_zona.add_hline(y=-2, line_dash="dash", line_color="red")
        st.plotly_chart(fig_box_zona, width='stretch')

        # Scatter: Peso vs HAZ
        col1, col2 = st.columns(2)

        with col1:
            fig_scatter1 = px.scatter(df.sample(min(1000, len(df))),
                                     x='peso_nacer_kg', y='haz_score',
                                     title='Peso al Nacer vs HAZ Score',
                                     opacity=0.6,
                                     trendline="ols")
            fig_scatter1.add_hline(y=-2, line_dash="dash", line_color="red")
            st.plotly_chart(fig_scatter1, width='stretch')

        with col2:
            fig_scatter2 = px.scatter(df.sample(min(1000, len(df))),
                                     x='talla_madre_cm', y='haz_score',
                                     title='Talla Madre vs HAZ Score',
                                     opacity=0.6,
                                     trendline="ols")
            fig_scatter2.add_hline(y=-2, line_dash="dash", line_color="red")
            st.plotly_chart(fig_scatter2, width='stretch')


def main():
    st.set_page_config(
        page_title="Predictor Desnutrición Infantil",
        layout="wide",
        page_icon="👶",
        initial_sidebar_state="expanded"
    )

    # Sidebar con navegación
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/baby.png", width=80)
        st.title("Navegación")
        page = st.radio(
            "Seleccione una página:",
            ["🔮 Predicción Individual", "📈 Análisis del Modelo"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### ℹ️ Acerca del Modelo")
        st.info("""
        **Modelo:** CatBoost Classifier

        **Variables:**
        - Edad del niño
        - Peso al nacer
        - Talla materna
        - Zona (rural/urbana)
        - Agua y saneamiento
        - Nivel socioeconómico
        - Educación materna
        """)

        st.markdown("---")
        st.caption("© 2025 - Predictor de Desnutrición Infantil")

    # Cargar modelo y metadatos
    try:
        model_obj, best_estimator, metadata = load_model_and_metadata()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Asegúrate de ejecutar el notebook de modelado y de tener el archivo .joblib en la carpeta `models/`.")
        return

    categories = get_ohe_categories(best_estimator)

    # Renderizar página seleccionada
    if page == "🔮 Predicción Individual":
        predictor_page(model_obj, best_estimator, metadata, categories)
    else:
        analytics_page()


if __name__ == '__main__':
    main()
