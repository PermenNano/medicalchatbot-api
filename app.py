from flask import Flask, render_template, request, jsonify
import os
import logging
import google.generativeai as genai

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure API key for Google Generative AI
API_KEY = os.getenv("GOOGLE_API_KEY")  # Ensure this matches the environment variable name

if not API_KEY:
    raise ValueError("API key is not set. Please set the GOOGLE_API_KEY environment variable.")

genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",  # Use the correct model name
    generation_config=generation_config,
    system_instruction=(
        "You are a medical assistant chatbot designed to provide helpful and informative responses. "
        "Your primary role is to offer light remedies and general advice for common symptoms such as headaches, colds, and allergies. "
        "Always remind users to consult a healthcare professional if their symptoms persist, worsen, or if they have any serious health concerns. "
        "Avoid providing any specific diagnoses or treatment instructions, as you are not a substitute for professional medical advice. "
        "Use a friendly and empathetic tone, ensuring that users feel supported and understood. "
        "Encourage users to describe their symptoms in detail to provide more tailored advice. "
        "If a user asks about a specific medication or treatment, provide general information but emphasize the importance of consulting a doctor. "
        "Be cautious with sensitive topics and ensure that your responses are respectful and non-judgmental. "
        "If you do not have enough information to provide a helpful response, suggest that the user seek professional medical advice."
    ),
)

# List to store the conversation history
messages = []

@app.route("/")
def index():
    # Add a greeting message to the conversation history
    greeting_message = "Hello! I'm your Medical Assistant Chatbot. How can I assist you today?"
    messages.append({"author": "bot", "content": greeting_message})

    # Add an introduction message to the conversation history
    introduction_message = (
        "Welcome to the Medical Assistant Chatbot! "
        "I am here to help you with common medical symptoms and provide light remedies. "
        "Please describe your symptoms or ask me any questions you may have."
    )
    messages.append({"author": "bot", "content": introduction_message})

    return render_template("index.html", messages=messages)

@app.route("/send_message", methods=["POST"])
def send_message():
    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Check for greetings
    if is_greeting(user_message):
        assistant_message = "Hello! How can I assist you today?"
        messages.append({"author": "bot", "content": assistant_message})
        return jsonify({"response": assistant_message})

    # Validate user input for medical queries
    if not is_medical_query(user_message):
        return jsonify({"error": "Please ask a question related to medical symptoms."}), 400

    try:
        # Start a new chat session
        chat_session = model.start_chat(
            history=[
                {"role": "user", "parts": [user_message]},
            ]
        )

        # Send the user message and get the response
        response = chat_session.send_message(user_message)

        # Extract the assistant's response
        assistant_message = response.text if response else "I'm sorry, I couldn't generate a response at this time."

        # Add light medicine suggestions based on the user's symptoms
        light_medicine = get_light_medicine(user_message)
        if light_medicine:
            assistant_message += "\n\nLight Medicines:\n" + light_medicine

        # Add the assistant's response to the conversation history
        messages.append({"author": "bot", "content": assistant_message})

        # Return the response without the disclaimer
        return jsonify({"response": assistant_message})
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

def is_greeting(message):
    """Check if the message is a greeting."""
    greetings = ["hello", "hi", "hey", "greetings", "what's up", "howdy"]
    return any(greeting in message.lower() for greeting in greetings)

def is_medical_query(message):
    """Enhanced validation to check if the user query is related to medical symptoms."""
    keywords = [
        "headache", "fever", "cough", "cold", "pain", "sore", "symptom",
        "diagnose", "medical", "doctor", "illness", "health", "infection",
        "nausea", "vomiting", "fatigue", "dizziness", "chills", "allergy",
        "rash", "stomach", "throat", "muscle", "joint", "treatment", "remedy"
    ]
    return any(keyword in message.lower() for keyword in keywords)

def get_light_medicine(user_message):
    """Provide light medicine suggestions based on user symptoms."""
    remedies = {
        "headache": "Consider taking Tylenol (acetaminophen) or Advil (ibuprofen) for relief.",
        "fever": "You might try taking Tylenol (acetaminophen) to help reduce your fever.",
        "cough": "Robitussin or Delsym can help soothe your cough.",
        "cold": "Over-the-counter medications like Sudafed or NyQuil can alleviate cold symptoms.",
        "sore throat": "Throat lozenges like Halls or cough syrups like Cepacol can provide relief.",
        "nausea": "Ginger ale or Dramamine can help settle your stomach.",
        "fatigue": "Consider taking a multivitamin or energy supplements like B12.",
        "dizziness": "Meclizine (Antivert) can help with dizziness and motion sickness.",
        "allergy": "Antihistamines like Claritin or Zyrtec can help relieve allergy symptoms."
    }

    for symptom in remedies:
        if symptom in user_message.lower():
            return remedies[symptom]
    
    return None

if __name__ == "__main__":
    app.run(debug=True)
