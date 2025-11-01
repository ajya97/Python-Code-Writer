import streamlit as st
import google.generativeai as genai
import json
import re
from openai import OpenAI

st.set_page_config(
    page_title="🐍 Python Code Writer",
    page_icon="✨",
    layout="wide"
)

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=st.secrets["OPENAI_API_KEY"],
)

def openai_model(promt):
    completion = client.chat.completions.create(
      extra_headers={
        "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
        "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
      },
      model="openai/gpt-4o",
      messages=[
        {
          "role": "user",
          "content": f"{promt}"
        }
      ]
    )
    return completion.choices[0].message.content

def configure_gemini():
    api_key = st.secrets["GEMINI_API_KEY"]
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"⚠️ Error configuring A.I.: {str(e)}")
        return None

def create_json_prompt(user_prompt):
    return json.dumps({
        "request": "generate_python_code",
        "prompt": user_prompt,
        "requirements": {
            "language": "python",
            "code_style": "minimal",
            "include_comments": False,
            "include_docs": False,
            "include_examples": False
        }
    }, indent=2)

def extract_code_from_response(response_text):
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', response_text, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    code_blocks = re.findall(r'"""(.*?)"""', response_text, re.DOTALL)
    if code_blocks:
        return code_blocks[0]
    return response_text

def extract_modules_from_code(code):
    return sorted(set(re.findall(r'^(?:import|from)\s+(\w+)', code, re.MULTILINE)))

def clean_code(code):
    code = re.sub(r'#.*', '', code)
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
    return "\n".join([line for line in code.split("\n") if line.strip()])

def generate_code(json_prompt):
    model = configure_gemini()
    if not model:
        return "⚠️ API not configured. Please check your API key."
    prompt = f"""As an expert Python developer, analyze this JSON request and generate clean, minimal Python code: 
            {json_prompt}
            
            Requirements:
            1. Essential code only (no comments/docs)
            2. Concise and functional
            3. Efficient, modern Python
            4. Wrap response inside ```python"""
    try:
        response = model.generate_content(
            f"{prompt}"
        )
        return response.text
    except Exception as e:
        try:
            return openai_model(prompt)
        except Exception as o:
            return f"⚠️ Error generating code by gemini: {str(e)}\n⚠️ Error generating code by openai: {str(o)}"

def explain_code_hinglish(code, user_level="beginner"):
    model = configure_gemini()
    if not model:
        return "⚠️ API not configured. Please check your API key."
    try:
        prompt = f"""
        Explain this Python code in Hinglish (Hindi + English) (Not in Hindi) for a {user_level} level programmer:
        {code}
        
        Guidelines:
        - Easy to understand with simple analogies
        - Use mix of Hindi and English words
        - Explain main sections
        - Conversational and friendly
        - Length depend upon code
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        try:
            return openai_model(prompt)
        except:
            return f"⚠️ Error generating explanation: {str(e)}"

for key in ["json_prompt", "generated_output", "modules", "explanation"]:
    if key not in st.session_state:
        st.session_state[key] = ""

st.title("✨ Python Code Writer & Explainer")
st.caption("Generate clean, minimal Python code using AI")

# Input Section
st.markdown("### 📝 Describe Your Task")
user_prompt = st.text_area(
    "Enter your coding task below 👇",
    placeholder="Example: Create a neural network for image classification using TensorFlow",
    height=100
)

generate_btn = st.button("⚡ Generate Code", use_container_width=True, type="primary")

if generate_btn and user_prompt:
    with st.spinner("🔮 Generating clean, minimal code..."):
        st.session_state.json_prompt = create_json_prompt(user_prompt)
        raw_output = generate_code(st.session_state.json_prompt)
        extracted_code = extract_code_from_response(raw_output)
        st.session_state.generated_output = clean_code(extracted_code)
        st.session_state.modules = extract_modules_from_code(st.session_state.generated_output)
        st.session_state.explanation = ""  # reset explanation when generating new code

if st.session_state.generated_output:
    st.markdown("## 🎯 Results")

    # with st.expander("📜 JSON Prompt Sent to AI"):
    #     st.code(st.session_state.json_prompt, language="json")

    if st.session_state.modules:
        st.markdown("### 📦 Required Modules")
        st.info("You'll need to install the following packages:")
        st.code(f"pip install {' '.join(st.session_state.modules)}", language="bash")

    st.markdown("### 🧩 Generated Code")
    st.code(st.session_state.generated_output, language="python")

    if st.button("💡 Explain Code in Hinglish", use_container_width=True):
        with st.spinner("🗣️ Generating explanation in Hinglish..."):
            st.session_state.explanation = explain_code_hinglish(st.session_state.generated_output)

if st.session_state.explanation:
    st.success("✅ Explanation Ready!")
    st.markdown("### 🔍 Code Explanation (Hinglish)")
    st.write(st.session_state.explanation)

st.markdown("---")
st.markdown(
    "<center>⚡ Built with Streamlit & A.I. API | @ 2025 ⚡</center>",
    unsafe_allow_html=True
)

