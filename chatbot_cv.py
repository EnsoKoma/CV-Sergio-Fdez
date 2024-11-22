import streamlit as st
from fpdf import FPDF
import pyttsx3  # Para Text-to-Speech
import openai  # API de OpenAI
import matplotlib.pyplot as plt
import tempfile
import os
import subprocess

# Configurar clave como variable de entorno usando Bash
os.environ["OPENAI_API_KEY"] = "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"

# Configuración de la página
st.set_page_config(
    page_title="Interactive CV Chatbot",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Inicializar TTS
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('voice', 'english')  # Cambiar a español si es necesario

# Función Text-to-Speech con manejo de errores
def speak_text(text):
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        st.warning("TTS no está disponible en este entorno. Error: " + str(e))

# Configura tu clave API de OpenAI de forma segura
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    st.error("No se encontró la clave de API de OpenAI. Configúrala como variable de entorno.")

# Función para obtener respuesta desde OpenAI API
def get_openai_response(question, user_data):
    prompt = f"""
    Actúa como un asistente virtual que representa a {user_data['name']}. 
    Responde preguntas sobre su experiencia, habilidades y trayectoria laboral basada en los datos proporcionados.
    Datos del usuario:
    - Nombre: {user_data['name']}
    - Secciones:
    """
    for section, items in user_data["sections"].items():
        prompt += f"\n  {section}:\n"
        for item in items:
            prompt += f"    - {item}\n"

    prompt += f"\nPregunta: {question}\n"
    prompt += "Respuesta:"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# Datos predeterminados
default_data = {
    "name": "Your Name",
    "sections": {
        "Experience": ["Document Controller in major engineering firms.", "Junior UX/UI with projects like [Project]."],
        "Skills": ["Figma", "Adobe XD", "Python", "HTML/CSS"],
        "Education": ["Bachelor's in Computer Science, University of XYZ"],
    }
}

# Editor en la barra lateral
st.sidebar.title("CV Editor")
st.sidebar.write("Use este menú para modificar o agregar secciones:")
name = st.sidebar.text_input("Name / Nombre", default_data["name"], key="name_input")

# Carga de imágenes
uploaded_image = st.sidebar.file_uploader("Upload an Image (e.g., Profile Picture or Logo)", type=["png", "jpg", "jpeg"])

# Configuración de gráficos
st.sidebar.subheader("Skill Chart Settings")
skills = st.sidebar.text_area("Skills (comma-separated)", "Python,Figma,UX Design,HTML/CSS", key="skills_input").split(",")
try:
    levels = list(map(int, st.sidebar.text_area("Levels (comma-separated)", "8,7,9,6", key="levels_input").split(",")))
except ValueError:
    st.sidebar.error("Please ensure skill levels are integers.")
    levels = []

# Mostrar gráfico de habilidades
fig, ax = plt.subplots()
ax.barh(skills, levels, color='purple')
ax.set_xlabel("Skill Level (1-10)")
ax.set_title("Skill Chart")
st.pyplot(fig)

# Mostrar y editar secciones
updated_sections = {}
for section_name, items in default_data["sections"].items():
    st.sidebar.subheader(section_name)
    section_data = st.sidebar.text_area(f"{section_name} Items", "\n".join(items), key=f"{section_name}_input")
    updated_sections[section_name] = section_data.split("\n")

# Agregar nuevas secciones dinámicamente
new_section_name = st.sidebar.text_input("New Section Name (optional)", "", key="new_section_name")
new_section_data = st.sidebar.text_area("New Section Content (optional)", "", key="new_section_data")
if new_section_name and new_section_data:
    updated_sections[new_section_name] = new_section_data.split("\n")

# Datos finales actualizados
updated_data = {"name": name, "sections": updated_sections}

# Mostrar datos dinámicos en pantalla
st.title(f"Hello, I'm {updated_data['name']}!")
if uploaded_image:
    st.image(uploaded_image, caption="Uploaded Image", use_column_width=True)

for section, items in updated_data["sections"].items():
    st.subheader(section)
    for item in items:
        st.write(f"- {item}")

# Responder preguntas usando OpenAI API
st.subheader("Ask a Question")
user_question = st.text_input("Enter your question here:", key="user_question_input")
if user_question:
    response = get_openai_response(user_question, updated_data)
    st.write(response)
    speak_text(response)

# Función para generar PDF dinámico
def create_pdf(data, image_file=None, chart_image=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Curriculum Vitae", ln=True, align="C")
    pdf.ln(10)

    if image_file:
        pdf.image(image_file, x=10, y=8, w=30)

    if chart_image:
        pdf.image(chart_image, x=50, y=40, w=100)

    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Name / Nombre: {data['name']}", ln=True)
    pdf.ln(5)

    for section, items in data["sections"].items():
        pdf.cell(200, 10, txt=f"{section}:", ln=True)
        for item in items:
            pdf.multi_cell(0, 10, txt=f"- {item}")
        pdf.ln(5)

    file_name = "CV_with_image_chart.pdf"
    pdf.output(file_name)
    return file_name

# Crear PDF con imagen y gráfico
if uploaded_image:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_image.read())
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as chart_file:
            fig.savefig(chart_file.name)
            pdf_file_name = create_pdf(updated_data, tmp_file.name, chart_file.name)
else:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as chart_file:
        fig.savefig(chart_file.name)
        pdf_file_name = create_pdf(updated_data, chart_image=chart_file.name)

# Descargar CV en PDF
st.subheader("Download CV / Descargar CV")
with open(pdf_file_name, "rb") as pdf_file:
    st.download_button(
        label="Download CV",
        data=pdf_file,
        file_name="CV_with_image_chart.pdf",
        mime="application/pdf",
    )

