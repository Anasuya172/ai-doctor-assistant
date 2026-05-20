from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from dotenv import load_dotenv
load_dotenv()

import os
import time
import streamlit as st
from streamlit_mic_recorder import mic_recorder

from brain_of_the_doctor import (
    encode_image,
    analyze_image_with_query
)

from voice_of_the_patient import transcribe_with_groq
from voice_of_the_doctor import text_to_speech_with_gtts


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Doctor Assistant",
    page_icon="🩺",
    layout="wide"
)

st.title("🩺 AI Doctor Assistant")


# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []

if "last_audio_text" not in st.session_state:
    st.session_state.last_audio_text = None

# PDF DATA
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = {
        "bmi": "",
        "diet": "",
        "yoga": "",
        "exercise": "",
        "recommendation": "",
        "advice": ""
    }


# ---------------- TOP BUTTONS ----------------
col1, col2 = st.columns(2)

with col1:

    if st.button("🗑 Clear Chat"):

        st.session_state.messages = []
        st.session_state.uploaded_images = []
        st.session_state.last_audio_text = None

        st.rerun()

with col2:

    if st.button("📄 Generate PDF"):

        pdf_file = "medical_report.pdf"

        doc = SimpleDocTemplate(pdf_file)

        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                "AI Doctor Medical Report",
                styles['Title']
            )
        )

        elements.append(Spacer(1, 20))

        elements.append(
            Paragraph(
                f"<b>BMI:</b> {st.session_state.pdf_data.get('bmi', ' ')}",
                styles['BodyText']
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"<b>Diet:</b> {st.session_state.pdf_data.get('diet', ' ')}",
                styles['BodyText']
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"<b>Yoga:</b> {st.session_state.pdf_data.get('yoga', ' ')}",
                styles['BodyText']
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"<b>Exercises:</b> {st.session_state.pdf_data.get('exercise', ' ')}",
                styles['BodyText']
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"<b>Recommendation:</b> {st.session_state.pdf_data.get('recommendation', ' ')}",
                styles['BodyText']
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"<b>Advice:</b> {st.session_state.pdf_data.get('advice', ' ')}",
                styles['BodyText']
            )
        )

        doc.build(elements)

        with open(pdf_file, "rb") as pdf:

            st.download_button(
                label="⬇ Download Medical Report",
                data=pdf,
                file_name="medical_report.pdf",
                mime="application/pdf"
            )


# ---------------- DIET FUNCTION ----------------
def get_diet_recommendation(response):

    response = response.lower()

    if "acne" in response:
        return "Avoid oily food, dairy products and junk food. Drink more water and eat fruits."

    elif "diabetes" in response:
        return "Eat low sugar foods and avoid processed snacks."

    elif "hair fall" in response:
        return "Eat protein rich foods, iron rich vegetables and drink water."

    elif "dandruff" in response:
        return "Avoid oily foods and consume zinc rich foods."

    else:
        return "Maintain a healthy balanced diet."


# ---------------- SIDEBAR ----------------
with st.sidebar:

    st.header("Patient Input")

    input_mode = st.radio(
        "Choose Input Method",
        ["Text", "Voice"]
    )

    # Multiple Image Upload
    image_files = st.file_uploader(
        "Upload Medical Images (Optional)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )

    if image_files:

        st.session_state.uploaded_images = []

        st.subheader("Uploaded Images")

        for image_file in image_files:

            image_bytes = image_file.getvalue()

            st.session_state.uploaded_images.append({
                "name": image_file.name,
                "bytes": image_bytes
            })

            st.image(
                image_bytes,
                caption=image_file.name,
                width=300
            )

    st.markdown("---")

    # Emergency backup
    st.subheader("🚨 Emergency Help")

    st.markdown(
        """
        <a href="tel:9115463503">
            <button style="
                width:100%;
                background-color:red;
                color:white;
                padding:12px;
                border:none;
                border-radius:10px;
                font-size:16px;
                cursor:pointer;
            ">
                📞 Emergency Call
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

    st.link_button(
        "🏥 Find Nearby Hospitals",
        "https://www.google.com/maps/search/hospitals+near+me/"
    )

    # ---------------- BMI CHECKER ----------------
    st.markdown("---")

    st.subheader("⚖ BMI Checker")

    weight = st.number_input(
        "Enter Weight (kg)",
        min_value=1.0,
        step=1.0
    )

    height = st.number_input(
        "Enter Height (cm)",
        min_value=1.0,
        step=1.0
    )

    if st.button("📊 Calculate BMI"):

        height_m = height / 100

        bmi = weight / (height_m ** 2)

        st.success(f"Your BMI is: {bmi:.2f}")

        st.session_state.pdf_data["bmi"] = f"{round(bmi,2)}"

        if bmi < 18.5:

            st.warning("Underweight")

        elif bmi < 25:

            st.success("Normal Weight")

        elif bmi < 30:

            st.warning("Overweight")

        else:

            st.error("Obese")


# ---------------- DISPLAY OLD CHAT ----------------
for i, msg in enumerate(st.session_state.messages):

    with st.chat_message(msg["role"]):

        st.write(msg["content"])

        if msg["role"] == "assistant" and "audio_file" in msg:
            st.audio(msg["audio_file"])

        # Generate audio in text mode
        if (
            msg["role"] == "assistant"
            and "audio_file" not in msg
            and input_mode == "Text"
        ):

            if st.button(
                "🔊 Generate Audio",
                key=f"audio_{i}"
            ):

                output_audio = f"doctor_reply_{i}.mp3"

                text_to_speech_with_gtts(
                    msg["content"],
                    output_audio
                )

                st.session_state.messages[i]["audio_file"] = output_audio

                st.rerun()

        # # Diet chart
        # if msg["role"] == "assistant" and "diet_tip" in msg:

        #     if st.button(
        #         "🥗 View Diet Chart",
        #         key=f"diet_{i}"
        #     ):

        #         st.session_state[f"show_diet_{i}"] = True

        #     if st.session_state.get(
        #         f"show_diet_{i}",
        #         False
        #     ):

        #         st.success(msg["diet_tip"])

        #         if st.button(
        #             "🔊 Generate Diet Audio",
        #             key=f"diet_audio_{i}"
        #         ):

        #             diet_audio = f"diet_audio_{i}.mp3"

        #             text_to_speech_with_gtts(
        #                 msg["diet_tip"],
        #                 diet_audio
        #             )

        #             st.session_state[
        #                 f"diet_audio_file_{i}"
        #             ] = diet_audio

        #             st.rerun()

        #         if st.session_state.get(
        #             f"diet_audio_file_{i}"
        #         ):

        #             st.audio(
        #                 st.session_state[
        #                     f"diet_audio_file_{i}"
        #                 ]
        #             )

        # Nearby hospital after old responses too
        if msg["role"] == "assistant":

            st.link_button(
                "🏥 Nearby Hospitals",
                "https://www.google.com/maps/search/hospitals+near+me/",
                key=f"old_hospital_{i}"
            )


# ---------------- MAIN RESPONSE ----------------
def generate_doctor_response(user_input):

    try:

        with st.chat_message("user"):
            st.write(user_input)

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        conversation_text = ""

        for msg in st.session_state.messages:

            conversation_text += (
                f"{msg['role']}: {msg['content']}\n"
            )

        system_prompt = """
You are a professional AI doctor.

If symptoms are severe or life-threatening,
clearly mention:

'This is a medical emergency'

Examples:
- breathing issues
- chest pain
- unconsciousness
- severe dizziness
- poison intake
- heavy bleeding
- accident
- stroke symptoms

For normal symptoms:
give short medical advice.

ALWAYS give output in this exact format:

Advice: your medical advice

Diet: recommended diet

Yoga: recommended yoga

Exercises: recommended exercises

Recommendation: additional recommendation

Keep responses concise.
"""

        final_query = system_prompt + conversation_text

        # Image analysis
        if st.session_state.uploaded_images:

            latest_image = st.session_state.uploaded_images[-1]

            ext = latest_image["name"].split(".")[-1]

            image_path = f"temp_image.{ext}"

            with open(image_path, "wb") as f:
                f.write(latest_image["bytes"])

            doctor_response = analyze_image_with_query(
                query=final_query,
                encoded_image=encode_image(image_path)
            )

        else:

            doctor_response = analyze_image_with_query(
                query=final_query
            )

        # ---------------- AI EMERGENCY DETECTION ----------------
        if (
            "medical emergency" in doctor_response.lower()
            or "call emergency" in doctor_response.lower()
            or "seek immediate medical attention" in doctor_response.lower()
            or "go to emergency room" in doctor_response.lower()
            or "call 911" in doctor_response.lower()
            or "urgent care" in doctor_response.lower()
        ):

            emergency_msg = """
🚨 Emergency detected by AI doctor.

Calling emergency contact now...
"""

            with st.chat_message("assistant"):

                st.error(emergency_msg)

                st.markdown(
                    """
                    <meta http-equiv="refresh" content="0; url=tel:9115463503">
                    """,
                    unsafe_allow_html=True
                )

                st.warning(
                    "If auto-call doesn't open automatically, use backup button."
                )

                st.link_button(
                    "🏥 Find Nearby Hospitals",
                    "https://www.google.com/maps/search/hospitals+near+me/"
                )

            if input_mode == "Voice":

                emergency_audio = "emergency_alert.mp3"

                text_to_speech_with_gtts(
                    emergency_msg,
                    emergency_audio
                )

                st.audio(emergency_audio)

            st.session_state.messages.append({
                "role": "assistant",
                "content": emergency_msg
            })

            st.rerun()
            return

        # Normal response
        diet_tip = get_diet_recommendation(
            doctor_response
        )

        final_response = doctor_response

        # ---------------- EXTRACT INFO ----------------
        diet = ""
        yoga = ""
        exercise = ""
        recommendation = ""

        lines = doctor_response.split("\n")

        for line in lines:

            line = line.strip()

            if line.startswith("Diet:"):

                diet = line.replace(
                    "Diet:",
                    ""
                ).strip()

            elif line.startswith("Yoga:"):

                yoga = line.replace(
                    "Yoga:",
                    ""
                ).strip()

            elif line.startswith("Exercises:"):

                exercise = line.replace(
                    "Exercises:",
                    ""
                ).strip()

            elif line.startswith("Recommendation:"):

                recommendation = line.replace(
                    "Recommendation:",
                    ""
                ).strip()

        # UPDATE PDF DATA
        st.session_state.pdf_data["diet"] = diet
        st.session_state.pdf_data["yoga"] = yoga
        st.session_state.pdf_data["exercise"] = exercise
        st.session_state.pdf_data["recommendation"] = recommendation
        st.session_state.pdf_data["advice"] = final_response

        # TEXT MODE
        if input_mode == "Text":

            with st.chat_message("assistant"):

                st.write(final_response)

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "🥗 Diet",
                        key=f"diet_btn_{len(st.session_state.messages)}"
                    ):

                        st.success(diet)

                    if st.button(
                        "🧘 Yoga",
                        key=f"yoga_btn_{len(st.session_state.messages)}"
                    ):

                        st.info(yoga)

                with col2:

                    if st.button(
                        "🏋 Exercises",
                        key=f"exercise_btn_{len(st.session_state.messages)}"
                    ):

                        st.warning(exercise)

                    if st.button(
                        "💡 Recommendation",
                        key=f"recommend_btn_{len(st.session_state.messages)}"
                    ):

                        st.write(recommendation)

                st.link_button(
                    "🏥 Find Nearby Hospitals",
                    "https://www.google.com/maps/search/hospitals+near+me/",
                    key=f"text_hospital_{len(st.session_state.messages)}"
                )

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_response,
                "diet_tip": diet_tip
            })

        # VOICE MODE
        else:

            output_audio = f"doctor_reply_{len(st.session_state.messages)}.mp3"

            with st.spinner("Doctor is responding..."):

                text_to_speech_with_gtts(
                    final_response,
                    output_audio
                )

            with st.chat_message("assistant"):

                placeholder = st.empty()

                shown_text = ""

                for word in final_response.split():

                    shown_text += word + " "

                    placeholder.write(shown_text)

                    time.sleep(0.05)

                st.audio(output_audio)

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "🥗 Diet",
                        key=f"voice_diet_btn_{len(st.session_state.messages)}"
                    ):

                        st.success(diet)

                    if st.button(
                        "🧘 Yoga",
                        key=f"voice_yoga_btn_{len(st.session_state.messages)}"
                    ):

                        st.info(yoga)

                with col2:

                    if st.button(
                        "🏋 Exercises",
                        key=f"voice_exercise_btn_{len(st.session_state.messages)}"
                    ):

                        st.warning(exercise)

                    if st.button(
                        "💡 Recommendation",
                        key=f"voice_recommend_btn_{len(st.session_state.messages)}"
                    ):

                        st.write(recommendation)

                st.link_button(
                    "🏥 Nearby Hospitals",
                    "https://www.google.com/maps/search/hospitals+near+me/",
                    key=f"voice_hospital_{len(st.session_state.messages)}"
                )

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_response,
                "audio_file": output_audio,
                "diet_tip": diet_tip
            })

        st.rerun()

    except Exception as e:

        st.error(f"Error: {str(e)}")


# ---------------- TEXT MODE ----------------
if input_mode == "Text":

    user_input = st.chat_input(
        "Describe your symptoms..."
    )

    if user_input:

        generate_doctor_response(user_input)


# ---------------- VOICE MODE ----------------
if input_mode == "Voice":

    audio_data = mic_recorder(
        start_prompt="🎙 Start Recording",
        stop_prompt="⏹ Stop Recording",
        just_once=False,
        use_container_width=True,
        key=f"recorder_{len(st.session_state.messages)}"
    )

    if audio_data:

        try:

            if "bytes" in audio_data:
                audio_bytes = audio_data["bytes"]

            else:
                audio_bytes = audio_data["audio_bytes"]

            with open(
                "temp_audio.wav",
                "wb"
            ) as f:

                f.write(audio_bytes)

            speech_text = transcribe_with_groq(
                GROQ_API_KEY=os.getenv("GROQ_API_KEY"),
                audio_filepath="temp_audio.wav",
                stt_model="whisper-large-v3"
            )

            if speech_text != st.session_state.last_audio_text:

                st.session_state.last_audio_text = speech_text

                st.info(f"📝 You said: {speech_text}")

                generate_doctor_response(
                    speech_text
                )

                st.rerun()

        except Exception as e:

            st.error(f"Voice Error: {str(e)}")




