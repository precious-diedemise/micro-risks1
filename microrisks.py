import streamlit as st
import google.generativeai as genai
import json

#Debugging: Print available models to the app screen
#st.write("Available Models:")
#for m in genai.list_models():
#    if 'generateContent' in m.supported_generation_methods:
 #       st.write(m.name)

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Micro-Actuary", page_icon="⚖️", layout="centered")

# --- SIDEBAR: API KEY INPUT ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.caption("Get a free key at aistudio.google.com")
    
    # Configure the API if key is present
    if api_key:
        genai.configure(api_key=api_key)

# --- HELPER FUNCTION: THE LLM CALL ---
def get_actuarial_data_from_llm(product_name):
    """
    Sends a prompt to the LLM asking for failure rates.
    Returns a dictionary: {'probability': int, 'source': str, 'reason': str}
    """
    if not api_key:
        return None  # Handle missing key case
    
    try:
        # 1. Select the Model
        model = genai.GenerativeModel('gemini-flash-latest')

        # 2. The "Actuary" Prompt (Prompt Engineering)
        # We force the AI to return JSON so our code can read it easily.
        prompt = f"""
        You are an actuarial database. 
        Task: Estimate the probability of failure or need for repair for a '{product_name}' within 3 years.
        Based on consumer reliability reports (Consumer Reports, Wirecutter, etc).
        
        Return ONLY a JSON string with no markdown formatting. Use this exact format:
        {{
            "probability": <integer between 0 and 100>,
            "reason": "<short 10-word explanation of common failure points>",
            "source": "<name of a likely data source>"
        }}
        """

        # 3. The Call
        response = model.generate_content(prompt)
        
        # 4. Clean and Parse the JSON
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data

    except Exception as e:
        st.error(f"AI Error: {e}")
        return {"probability": 5, "reason": "AI Failed, using average", "source": "Estimation"}

# --- MAIN APP UI ---

st.title("⚖️ Micro-Actuary")
st.subheader("The Mathematics of Everyday Decision")

# --- STEP 1: INPUTS ---
st.markdown("### 🛒 Product Details")
col1, col2 = st.columns(2)
with col1:
    item_name = st.text_input("Product Name", placeholder="e.g. MacBook Air M2", value="Sony WH-1000XM5 Headphones")
    item_cost = st.number_input("Item Cost ($)", value=350)
with col2:
    warranty_cost = st.number_input("Warranty Cost ($)", value=60)
    warranty_years = st.number_input("Warranty Length (Years)", value=2)

st.divider()

# --- STEP 2: QUANTIFY IT (THE AI PART) ---
st.markdown("### 🎲 Risk Assessment")

# Initialize session state for probability if it doesn't exist
if 'prob_fail' not in st.session_state:
    st.session_state['prob_fail'] = 0
if 'reason' not in st.session_state:
    st.session_state['reason'] = "Waiting for analysis..."

# The AI Button
if st.button("✨ Assess Risk with AI", type="primary"):
    with st.spinner(f"Consulting actuarial models for {item_name}..."):
        if api_key:
            # CALL THE FUNCTION WE WROTE ABOVE
            ai_data = get_actuarial_data_from_llm(item_name)
            
            if ai_data:
                st.session_state['prob_fail'] = ai_data['probability']
                st.session_state['reason'] = f"{ai_data['reason']} (Source: {ai_data['source']})"
        else:
            st.warning("⚠️ No API Key found. Using simulated data.")
            st.session_state['prob_fail'] = 12
            st.session_state['reason'] = "Simulated Estimate (Add API Key for real data)"

# Display the results from the AI
st.info(f"**AI Analysis:** {st.session_state['reason']}")
prob_fail = st.slider("Adjust Probability of Failure (%)", 0, 100, st.session_state['prob_fail'])


# --- STEP 3: COMPARE IT (THE MATH) ---
st.divider()
st.markdown("### 📊 The Verdict")

# The Math: Expected Value
expected_loss = item_cost * (prob_fail / 100)
net_cost = warranty_cost - expected_loss

c1, c2, c3 = st.columns(3)
c1.metric("Cost of Warranty", f"${warranty_cost}")
c2.metric("Expected Loss (Risk)", f"${expected_loss:.2f}")
c3.metric("Net Premium", f"${net_cost:.2f}", 
          delta_color="inverse", 
          delta=f"-${net_cost:.2f}" if net_cost > 0 else f"+${abs(net_cost):.2f}")

# The Decision Logic
if expected_loss > warranty_cost:
    st.success(f"**VERDICT: BUY THE WARRANTY.** The risk (${expected_loss:.0f}) is higher than the price (${warranty_cost}).")
elif net_cost < (item_cost * 0.05):
    st.warning("**VERDICT: TOSS UP.** It's slightly overpriced, but maybe worth it for peace of mind.")
else:
    st.error(f"**VERDICT: SKIP IT.** You are mathematically overpaying by ${net_cost:.0f}.")

# --- STEP 4: HABIT BUILDER ---
if expected_loss < warranty_cost:
    st.markdown("---")
    st.caption(f"📝 **New Habit Rule:** 'I do not buy warranties for {item_name}s unless the warranty price is under ${expected_loss:.0f}.'")
