# Fase 1 — Comprensión del Negocio: Proyecto MVP de Predicción de Desnutrición Crónica

## 1. Determinación de Objetivos de Negocio (El "Por Qué")

- **Objetivo Principal:** Desarrollar un Producto Mínimo Viable (MVP) en formato de aplicación web (usando Streamlit) que prediga el riesgo de desnutrición crónica infantil (stunting) en menores de 5 años.
- **Audiencia:** Público general (no académico/científico).
- **Propósito:** Crear una herramienta funcional y educativa que demuestre el uso de Machine Learning para un problema de salud pública, priorizando la rapidez de desarrollo, funcionalidad e interpretabilidad.

### Árbol de Objetivos del MVP

Este diagrama conecta el "Por Qué" (la app) con el "Qué" (el modelo).

```mermaid
graph TD
    %% Nivel 1: Objetivo del Producto (El "Por Qué")
    A("1. Objetivo Producto:<br><b>MVP Web App (Streamlit)</b><br>para predecir riesgo de<br>desnutrición crónica")

    %% Nivel 2: Requisitos Clave
    B("2. Requisito Clave:<br><b>Tiempo Limitado</b> (Ciclo Académico)<br>Enfoque en velocidad y funcionalidad")
    C("2. Requisito Clave:<br><b>Público General</b><br>Enfoque en simplicidad e interpretabilidad")

    %% Nivel 3: Objetivos Técnicos (El "Qué")
    D("3. Objetivo ML:<br>Modelo predictivo <i>suficientemente bueno</i><br>para una demostración")
    E("3. Objetivo ML:<br>Usar un <b>conjunto reducido de variables</b><br>que sean fáciles de entender")
    F("3. Objetivo Despliegue:<br>Interfaz Streamlit simple<br>que muestre la predicción claramente")

    %% Conexiones
    A --> B
    A --> C
    B --> D
    B --> E
    C --> E
    C --> F
    D --> F
    E --> F

    %% Estilos (Colores)
    classDef objetivoProducto fill:#cceeff,stroke:#0066cc,stroke-width:2px;
    classDef requisito fill:#ffcccc,stroke:#cc0000,stroke-width:2px;
    classDef objetivoTecnico fill:#ccffcc,stroke:#008000,stroke-width:2px;

    class A objetivoProducto;
    class B,C requisito;
    class D,E,F objetivoTecnico;
```

## 2. Determinación de Objetivos de Minería de Datos (El "Qué" Técnico)

Este es el "plano" técnico del modelo, basado en el informe de Scopus AI.

### Variable Objetivo (Target)

- **Nombre:** Desnutricion_Cronica (variable que crearemos).
- **Definición:** Será una variable binaria (0 o 1).
- **Cálculo:** Desnutricion_Cronica = 1 si el puntaje Z de Talla para la Edad (HAZ) es < -2.
- **Cálculo:** Desnutricion_Cronica = 0 si el puntaje Z de Talla para la Edad (HAZ) es >= -2.
- **Fuente de HAZ:** Módulo de Antropometría de niños (probablemente REC41.csv).

### Variables Predictoras (Features)

Se seleccionará un conjunto reducido (aprox. 5–10) de predictores fuertes e interpretables, basados en el informe de Scopus AI.

- **Candidatos prioritarios:**
  - Maternos: Nivel educativo, Estatura de la madre.
  - Niño: Edad del niño, Peso al nacer.
  - Hogar: Nivel de riqueza, Saneamiento (tipo de baño), Acceso al agua.
  - Contextual: Zona (Urbano/Rural).

### Modelos a Evaluar (Enfoque MVP)

- **Prioridad 1 (Interpretable):** Regresión Logística o Árbol de Decisión (rápidos de entrenar y fáciles de explicar en Streamlit).
- **Prioridad 2 (Si el tiempo permite):** Random Forest (buen rendimiento y permite ver "Importancia de Características").

```mermaid
flowchart TD
    A["<b>1. Comprensión</b><br>Definir MVP<br><i>(¡Hecho!)</i>"] --> B("<b>2. Datos Rápida</b><br>Cargar CSVs clave<br>Localizar ~10 vars")
    B --> C("<b>3. Preparación Enfocada</b><br>Join tablas<br>Limpieza básica<br>Crear Target (HAZ < -2)<br>Codificar Features")
    C --> D("<b>4. Modelado Eficiente</b><br>Split Datos<br>Entrenar LogReg<br>Evaluar<br><i>(Opc: RF)</i>")
    D --> E("<b>5. Evaluación Funcional</b><br>¿Modelo 'OK' para MVP?")
    E -- Sí --> F("<b>6. Despliegue Streamlit</b><br>Guardar modelo (pickle/joblib)<br>Crear UI básica<br>Mostrar Predicción<br>Desplegar App")
    E -- No --> C_Mod{"Revisar Preparación<br>o Modelado"}
    C_Mod --> C
    C_Mod --> D

    %% Estilos (Colores por Fase)
    classDef fase1 fill:#D1E7DD,stroke:#198754,stroke-width:2px;
    classDef fase2 fill:#CFE2FF,stroke:#0D6EFD,stroke-width:2px;
    classDef fase3 fill:#FFF3CD,stroke:#FFC107,stroke-width:2px;
    classDef fase4 fill:#F8D7DA,stroke:#DC3545,stroke-width:2px;
    classDef fase5 fill:#E2D9F3,stroke:#6F42C1,stroke-width:2px;
    classDef fase6 fill:#D1ECF1,stroke:#0DCAF0,stroke-width:2px;
    classDef revision fill:#FEE7D5,stroke:#FD7E14,stroke-width:2px;

    class A fase1;
    class B fase2;
    class C fase3;
    class D fase4;
    class E fase5;
    class F fase6;
    class C_Mod revision;
```
