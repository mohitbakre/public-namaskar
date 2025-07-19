import streamlit as st
import datetime
from supabase import create_client, Client
import base64

# --- GLOBAL DATE DEFINITIONS ---
today = datetime.date.today() # This correctly initializes 'today' as a datetime.date object
min_allowed_dob = today.replace(year=today.year - 100) # 'today' is already a date object, so no .date() needed
# --- END GLOBAL DATE DEFINITIONS ---

# --- Supabase Client Initialization (kept for potential future use) ---
#supabase_url = st.secrets.get("SUPABASE_URL")
#supabase_key = st.secrets.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    # This warning won't stop the app now, as we're not relying on auth initially
    st.sidebar.warning("Supabase URL or Key not found in Streamlit secrets. Supabase features will be disabled.")
    supabase = None # Set supabase to None if keys are missing
else:
    supabase: Client = create_client(supabase_url, supabase_key)

# --- Session State Management (kept for potential future use) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {'name': '', 'dob': None}
if 'display_error_message' not in st.session_state:
    st.session_state['display_error_message'] = None

# --- Helper functions (kept for potential future use) ---
def set_error_message(message):
    st.session_state['display_error_message'] = message

def clear_error_message():
    st.session_state['display_error_message'] = None

# Removed login_user and register_user as they are not used in this simplified flow
# Removed logout_user as it's not used


# --- UI Layout and Styling ---
st.set_page_config(layout="wide", page_title="Namaskar")

st.markdown("""
<style>
    /* Overall app styling */
    .main {
        background-color: #ed7d3b !important;  /* Light orange background */
        color: #333333; /* Darker text for readability */
    }
    /* Style for the main title */
    .st-emotion-cache-zt5ig8 { /* This class can change, might need inspection */
        color: #4CAF50; /* Green for title */
        text-align: center;
        font-family: 'Georgia', serif;
        font-size: 3.5em;
        margin-bottom: 20px;
    }
    /* Style for st.header elements */
    h1, h2, h3, h4, h5, h6 {
        color: #6C757D; /* Gray for headers */
        font-family: 'Arial', sans-serif;
    }
    /* Style for form elements (optional) */
    .st-form {
        background-color: #FFFFFF; /* White background for forms */
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    /* Styling for buttons */
    .stButton > button {
        background-color: #007BFF; /* Blue for buttons */
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
</style>
""", unsafe_allow_html=True)

# --- Add Logo, Title, and Astrologer Photo ---
# Adjusted column ratios to fit images and title
col_left_img, col_title, col_right_img = st.columns([1, 4, 1])

with col_left_img:
    # Make sure 'logo.png' is in the same directory as your script
    st.image("logo.png", width=100) # Placeholder: Replace "logo.png" with your actual logo file

with col_title:
    # Wrap st.title in a div with the custom class for centering
    st.markdown("<h1 style='text-align: center;font-size:60px; font-family:Harlow Solid Italic;'>Namaskar</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;font-size:30px; font-family:Harlow Solid Italic;'>Spirituality Unlimited!!</h1>",unsafe_allow_html=True)
with col_right_img:
    # Make sure 'astrologer_photo.png' is in the same directory as your script
    st.image("logo.png", width=100) # Placeholder: Replace "astrologer_photo.png" with your actual photo file
# --- End Logo, Title, and Astrologer Photo ---

# --- Persistent Error Display (kept for general error handling) ---
if st.session_state['display_error_message']:
    st.error(st.session_state['display_error_message'])
# --- End Persistent Error Display ---


# Main app logic - DIRECTLY DISPLAY CONTENT
st.subheader("Explore Cosmic Word!")

#tab_names = ["Numerology", "Astrology", "Tarot Cards", "Vastu Shastra", "Palmistry", "Aura Reading"]


tab_names = ["Numerology", "Astrology", "Tarot Cards", "Vastu Shastra", "Palmistry", "Aura Reading"]
selected_tab = st.tabs(tab_names)

tabs = st.tabs(tab_names)
for i, tab in enumerate(tabs):
    with tab:
        st.write(f"Content for {tab_names[i]}")


with selected_tab[0]:  # Numerology tab
    st.header("Numerology: Uncover Your Life's Blueprint")
    st.write("This is where the Numerology calculations and insights will go.")

    with st.form("numerology_form_public"): # Renamed form key to avoid conflict if you re-add auth
        # Removed reliance on st.session_state['user_profile'] for initial values
        name_input = st.text_input("Your Full Name (as on birth certificate)", value="", key="public_name_input")

        # Removed current_dob, use a default date for the date_input or keep it as is
        birth_date_input = st.date_input("Your Birth Date", value=today, max_value=today,
                                         min_value=min_allowed_dob, key="public_dob_input")

        numerology_submit = st.form_submit_button("Calculate My Numbers")

        if numerology_submit:
            # --- REMOVED PROFILE UPDATE LOGIC (since no login) ---

            if name_input and birth_date_input:
                st.subheader(f"Results for {name_input}, born on {birth_date_input}:")

                dob_str = str(birth_date_input.year) + str(birth_date_input.month) + str(birth_date_input.day)
                life_path_num = sum(int(digit) for digit in dob_str)
                while life_path_num > 9 and life_path_num not in [11, 22, 33]:
                    life_path_num = sum(int(digit) for digit in str(life_path_num))

                st.success(f"Your Life Path Number is: **{life_path_num}**")
                st.write(
                    "*(Note: This is a highly simplified calculation. Real numerology involves more complex methods for name and date.)*")
            else:
                st.warning("Please enter both your full name and birth date.")

with selected_tab[1]:  # Astrology tab
    st.header("Astrology: Cosmic Guidance")
    st.write("Details about Astrology, Natal Charts, Horoscopes, etc.")

with selected_tab[2]:  # Tarot Cards tab
    st.header("Tarot Cards: Intuitive Insights")
    st.write("Virtual Tarot readings and interpretations.")

with selected_tab[3]:  # Vastu Shastra tab
    st.header("Vastu Shastra: Harmonize Your Space")
    st.write("Principles for architectural harmony.")

with selected_tab[4]:  # Palmistry tab
    st.header("Palmistry: The Map in Your Hand")
    st.write("Insights from palm lines and shapes.")

with selected_tab[5]:  # Aura Reading tab
    st.header("Aura Reading: Vibrational Energy")
    st.write("Understanding your energy field.")

st.markdown("---")
st.header("Connect with an Expert (Chat)")
st.write("This will be our dedicated chat module to connect users with astrologers/practitioners.")
st.button("Start a Chat")

# --- Audio Autoplay (Hidden and Muted) ---
# Function to convert the WAV file to a Base64 data URI
def get_base64_audio(audio_path):
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    return f"data:audio/wav;base64,{encoded}"

audio_path = "bgm.wav"  # Replace with your actual file
audio_data_url = get_base64_audio(audio_path)

# Inject hidden <audio> tag with autoplay and loop
st.markdown(
    f"""
    <audio autoplay loop style="display:none;">
        <source src="{audio_data_url}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>
    """,
    unsafe_allow_html=True
)
# --- End Audio Autoplay ---
