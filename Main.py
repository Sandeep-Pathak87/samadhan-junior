import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

# ==============================
# LOAD ENV & CONFIG
# ==============================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

APP_NAME = "Samadhan Junior"
VERSION = "v1.4"
MODEL_NAME = "gemini-2.5-flash-lite"
MAX_OUTPUT_TOKENS = 500 
TEMPERATURE = 0.7

if not api_key:
    st.error("API Key missing! Please check your .env file.")
    st.stop()

client = genai.Client(api_key=api_key)

# ==============================
# 1. CURRICULUM TEMPLATE
# ==============================
SAMADHAN_CURRICULUM = {
    "कक्षा 1": {
        "topics": {
            "स्थानिक समझ (Position)": "अंदर-बाहर, ऊपर-नीचे, आगे-पीछे, दाएँ-बाएँ",
            "संख्या ज्ञान (Numbers)": "1-9 तक गिनती",
        },
        "pedagogy": "Step 1: Scenario Setup -> Step 2: Observation Prompt -> Step 3: Comparison Cue -> Step 4: Choice Framing"
    },
    "कक्षा 2": {"topics": {"जोड़-घटाव": "General"}},
    "कक्षा 3": {"topics": {"PLACEHOLDER": ""}},
    "कक्षा 4": {"topics": {"PLACEHOLDER": ""}},
    "कक्षा 5": {"topics": {"PLACEHOLDER": ""}}
}

# ==============================
# 2. GLOBAL RULES
# ==============================
GLOBAL_RULES = """
भूमिका: आप "समाधान जूनियर" हैं, एक धैर्यवान और मित्रवत गणित साथी।

नियम:
1. **केवल देवनागरी लिपि** का प्रयोग करें। रोमन अक्षरों (जैसे: nahi, ok) का उपयोग सख्त वर्जित है।
2. "नमस्ते जूनियर!" केवल बातचीत की शुरुआत में एक बार बोलें।
3. परिदृश्य (Scenario) छोटा (6-8 वाक्य) और आकर्षक रखें।
4. हर रिस्पॉन्स के अंत में केवल एक सरल, मार्गदर्शक प्रश्न पूछें।
5. तकनीकी शब्द (Step 1, Scenario) न लिखें।
6. केवल ग्रामीण उदाहरणों (खेत, मटका, बरगद, कुआँ आदि) का प्रयोग करें।
"""

# ==============================
# 3. SIDEBAR UI
# ==============================
st.set_page_config(page_title="Samadhan Junior - 🎓", page_icon="🎓")

with st.sidebar:
    st.title("🎓 समाधान")
    sel_class = st.selectbox("कक्षा चुनें:", list(SAMADHAN_CURRICULUM.keys()))
    class_info = SAMADHAN_CURRICULUM[sel_class]
    sel_topic = st.selectbox("विषय चुनें:", list(class_info["topics"].keys()))
    
    st.divider()
    if st.button("Reset Conversation"):
        st.session_state.chat_history = []
        st.session_state.current_user_input = ""
        st.rerun()

# ==============================
# 4. SAFETY HANDLERS
# ==============================
EMERGENCY_KEYWORDS = ["सुसु", "पेशाब", "पोटी", "टट्टी", "दर्द", "डर", "susu", "potty", "dard","dar","darr","peshab",]
BASIC_ABUSE_WORDS = ["कमीना", "हरामी", "नालायक", "बेवकूफ", "साला", "kamina", "sala","nalayak","bebkoof","harami",]

def classify_input(text):
    text = text.lower()
    if any(word in text for word in EMERGENCY_KEYWORDS): return "emergency"
    return "learning"

def handle_emergency(text):
    if "दर्द" in text: return "अगर दर्द हो रहा है तो अभी आराम करो और किसी बड़े को बताओ।"
    if "डर" in text: return "डर लग रहा है तो तुरंत किसी बड़े को बताओ। मैं यहीं हूँ।"
    return "पहले आराम से जाकर आओ। फिर हम सीखना जारी रखेंगे।"

# ==============================
# 5. SESSION STATE & INPUT CLEAR LOGIC
# ==============================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_user_input" not in st.session_state:
    st.session_state.current_user_input = ""

# --- यह वह फंक्शन है जो बॉक्स को खाली करेगा ---
def submit_input():
    st.session_state.current_user_input = st.session_state.input_widget
    st.session_state.input_widget = ""

# ==============================
# MAIN UI
# ==============================
st.title("🎓 समाधान जूनियर")

if not st.session_state.chat_history:
    st.info(f"नमस्ते Junior : अभी हम सीख रहे हैं: {sel_topic} , क्या तुम तैयार हो ???")

# इनपुट विजेट (submit_input फंक्शन के साथ)
st.text_input("अपनी बात यहाँ लिखें:", key="input_widget", on_change=submit_input)

# प्रोसेसिंग के लिए इनपुट लें
user_input = st.session_state.current_user_input

if user_input:
    with st.spinner("समाधान सोच रहा है..."):
        input_type = classify_input(user_input)

        if input_type == "emergency":
            st.success(handle_emergency(user_input))
            st.session_state.current_user_input = "" # इनपुट रीसेट
        
        elif any(word in user_input.lower() for word in BASIC_ABUSE_WORDS):
            st.success("जूनियर, गंदी बात। ऐसे नहीं बोलते।")
            st.session_state.current_user_input = "" # इनपुट रीसेट
            
        else:
            try:
                history_text = ""
                if st.session_state.chat_history:
                    history_text = "पिछली बातचीत:\n" + "\n".join([f"बालक: {h['user']}\nसमाधान: {h['bot']}" for h in st.session_state.chat_history[-2:]])

                full_prompt = f"""
                {GLOBAL_RULES}
                संदर्भ: कक्षा {sel_class}, विषय {sel_topic}।
                {history_text}
                बच्चे का नया जवाब: {user_input}
                
                विशेष निर्देश:
                - यदि बच्चा 'हाँ' कहे, तो छोटा दृश्य सुनाकर पहला सवाल पूछें।
                - केवल देवनागरी हिंदी का प्रयोग करें।
                """
                
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=full_prompt,
                    config={"max_output_tokens": MAX_OUTPUT_TOKENS, "temperature": TEMPERATURE}
                )

                model_output = response.text.strip()
                st.session_state.chat_history.append({"user": user_input, "bot": model_output})
                
                st.write("---")
                st.success(model_output)
                
                # जवाब दिखाने के बाद करंट इनपुट खाली करें ताकि लूप न बने
                st.session_state.current_user_input = ""

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.current_user_input = ""
