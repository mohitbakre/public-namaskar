import streamlit as st
import datetime
import base64
import pyrebase # Make sure you have installed: pip install pyrebase4

# --- Initialize Firebase ---
try:
    # Load Firebase configuration from st.secrets
    firebaseConfig = {
        "apiKey": st.secrets.firebase.apiKey,
        "authDomain": st.secrets.firebase.authDomain,
        "projectId": st.secrets.firebase.projectId,
        "storageBucket": st.secrets.firebase.storageBucket,
        "messagingSenderId": st.secrets.firebase.messagingSenderId,
        "appId": st.secrets.firebase.appId,
        "databaseURL": st.secrets.firebase.databaseURL # Make sure this is in your secrets.toml
    }
    firebase = pyrebase.initialize_app(firebaseConfig)
    auth = firebase.auth()
    db = firebase.database() # Initialize Realtime Database
except AttributeError as e:
    st.error(f"Missing Firebase configuration in .streamlit/secrets.toml. Please ensure all keys are present: {e}")
    st.stop() # Stop the app if Firebase config is missing
except Exception as e:
    st.error(f"Firebase initialization error: {e}")
    st.stop() # Stop the app if Firebase can't be initialized


# --- GLOBAL DATE DEFINITIONS ---
today = datetime.date.today()
min_allowed_dob = today.replace(year=today.year - 100)
# --- END GLOBAL DATE DEFINITIONS ---

# --- Session State Management ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None # Stores Firebase user object
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {'name': '', 'dob': None, 'is_profile_loaded': False} # Added flag
if 'display_error_message' not in st.session_state:
    st.session_state['display_error_message'] = None
if 'current_screen' not in st.session_state:
    st.session_state['current_screen'] = 'login' # 'login', 'register', or 'app'

# --- Helper functions ---
def set_error_message(message):
    st.session_state['display_error_message'] = message

def clear_error_message():
    st.session_state['display_error_message'] = None

# Register function remains the same (simplified)
def register_user(email, password):
    clear_error_message()
    try:
        auth.create_user_with_email_and_password(email, password)
        st.success("Registration successful! Please log in with your new account.")
        st.session_state['current_screen'] = 'login' # Redirect to login
        st.rerun()
    except Exception as e:
        error_message = str(e)
        if "EMAIL_EXISTS" in error_message:
            set_error_message("This email is already registered.")
        elif "WEAK_PASSWORD" in error_message:
            set_error_message("Password should be at least 6 characters.")
        elif "INVALID_EMAIL" in error_message:
            set_error_message("Invalid email format.")
        else:
            set_error_message(f"Registration failed: {error_message}")
        st.rerun()

# MODIFIED: login_user now ONLY authenticates and redirects to app screen
def login_user(email, password):
    clear_error_message()
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        st.session_state['user_info'] = user
        st.session_state['logged_in'] = True
        # NEW: Initialize user_profile to empty and set flag to false,
        # indicating it needs to be loaded when the profile tab is visited.
        st.session_state['user_profile'] = {'name': '', 'dob': None, 'is_profile_loaded': False}
        st.session_state['current_screen'] = 'app'
        st.success("Login successful!")
        st.rerun()
    except Exception as e:
        error_message = str(e)
        if "INVALID_LOGIN_CREDENTIALS" in error_message or "EMAIL_NOT_FOUND" in error_message or "WRONG_PASSWORD" in error_message:
             set_error_message("Invalid email or password.")
        else:
             set_error_message(f"Login failed: {error_message}")
        st.rerun()

def logout_user():
    clear_error_message()
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    # Reset profile state completely on logout
    st.session_state['user_profile'] = {'name': '', 'dob': None, 'is_profile_loaded': False}
    st.session_state['current_screen'] = 'login'
    st.success("Logged out successfully.")
    st.rerun()


# --- Numerology Calculation Logic ---

# Standard Pythagorean Numerology mapping
NUMEROLOGY_MAP = {
    'A': 1, 'J': 1, 'S': 1,
    'B': 2, 'K': 2, 'T': 2,
    'C': 3, 'L': 3, 'U': 3,
    'D': 4, 'M': 4, 'V': 4,
    'E': 5, 'N': 5, 'W': 5,
    'F': 6, 'O': 6, 'X': 6,
    'G': 7, 'P': 7, 'Y': 7,
    'H': 8, 'Q': 8, 'Z': 8,
    'I': 9, 'R': 9
}

VOWELS = "AEIOU"
CONSONANTS = "BCDFGHJKLMNPQRSTVWXYZ"

def sum_digits(number):
    """Sums the digits of a number."""
    return sum(int(digit) for digit in str(number))

def reduce_number(num):
    """
    Reduces a number to a single digit or a master number (11, 22, 33).
    Master numbers are typically not reduced further in primary numerology calculations.
    """
    if not isinstance(num, int): # Ensure input is an integer
        return None
    while num > 9 and num not in [11, 22, 33]:
        num = sum_digits(num)
    return num

def get_numerology_value(char):
    """Returns the numerological value for a letter."""
    return NUMEROLOGY_MAP.get(char.upper(), 0) # Returns 0 for non-alphabetic chars

def calculate_life_path(dob_date):
    """Calculates the Life Path Number from a birth date."""
    if not isinstance(dob_date, datetime.date):
        return None
    month = reduce_number(dob_date.month)
    day = reduce_number(dob_date.day)
    year = reduce_number(dob_date.year)

    if None in [month, day, year]: # Check for valid reduction
        return None

    life_path_sum = month + day + year
    return reduce_number(life_path_sum)

def calculate_expression_number(full_name):
    """Calculates the Expression (Destiny) Number from a full name."""
    total = 0
    for char in full_name:
        total += get_numerology_value(char)
    return reduce_number(total)

def calculate_soul_urge_number(full_name):
    """Calculates the Soul Urge (Heart's Desire) Number from vowels in a full name."""
    total = 0
    for char in full_name:
        if char.upper() in VOWELS:
            total += get_numerology_value(char)
    return reduce_number(total)

def calculate_personality_number(full_name):
    """Calculates the Personality Number from consonants in a full name."""
    total = 0
    for char in full_name:
        if char.upper() in CONSONANTS:
            total += get_numerology_value(char)
    return reduce_number(total)

def calculate_birth_day_number(dob_date):
    """Calculates the Birth Day Number from the day of the month."""
    if not isinstance(dob_date, datetime.date):
        return None
    return reduce_number(dob_date.day)

# Simplified Numerology Interpretations
NUMEROLOGY_INTERPRETATIONS = {
    1: "The Leader: Independent, ambitious, original, and pioneering. Can be self-centered or aggressive.",
    2: "The Peacemaker: Diplomatic, cooperative, sensitive, and intuitive. Can be shy or indecisive.",
    3: "The Communicator: Creative, expressive, optimistic, and social. Can be superficial or scattered.",
    4: "The Builder: Practical, disciplined, stable, and hardworking. Can be rigid or stubborn.",
    5: "The Adventurer: Versatile, freedom-loving, adaptable, and restless. Can be irresponsible or impulsive.",
    6: "The Nurturer: Responsible, loving, compassionate, and family-oriented. Can be self-righteous or meddling.",
    7: "The Seeker: Analytical, spiritual, introspective, and wise. Can be reclusive or cynical.",
    8: "The Executive: Ambitious, powerful, organized, and successful. Can be materialistic or controlling.",
    9: "The Humanitarian: Compassionate, generous, idealistic, and wise. Can be self-sacrificing or emotionally detached.",
    11: "The Master Intuitor: Highly intuitive, inspiring, and charismatic. Can be overly sensitive or impractical.",
    22: "The Master Builder: Visionary, practical, powerful, and capable of grand achievements. Can be overwhelming or self-destructive.",
    33: "The Master Teacher/Healer: Highly compassionate, spiritual, and dedicated to service. Can be overly responsible or martyrdom-prone."
}

# --- End Numerology Calculation Logic ---



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
col_left_img, col_title, col_right_img = st.columns([1, 4, 1])

with col_left_img:
    st.image("logo.png", width=100) # Placeholder: Replace "logo.png" with your actual logo file

with col_title:
    st.markdown("<h1 style='text-align: center;font-size:60px; font-family:Harlow Solid Italic;'>Namaskar</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;font-size:30px; font-family:Harlow Solid Italic;'>Spirituality Unlimited!!</h1>",unsafe_allow_html=True)
with col_right_img:
    st.image("logo.png", width=100) # Placeholder: Replace "astrologer_photo.png" with your actual photo file
# --- End Logo, Title, and Astrologer Photo ---

# --- Persistent Error Display ---
if st.session_state['display_error_message']:
    st.error(st.session_state['display_error_message'])
# --- End Persistent Error Display ---

# --- User Authentication Screens ---
if st.session_state['current_screen'] == 'login':
    st.subheader("Login to Namaskar")
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if email and password:
                login_user(email, password)
            else:
                set_error_message("Please enter both email and password.")

    st.markdown("---")
    st.subheader("Don't have an account?")
    if st.button("Register Here", key="go_to_register"):
        st.session_state['current_screen'] = 'register'
        clear_error_message()
        st.rerun()

elif st.session_state['current_screen'] == 'register':
    st.subheader("Register for Namaskar")
    with st.form("register_form"):
        email = st.text_input("Email", key="register_email")
        password = st.text_input("Password (min 6 characters)", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        register_button = st.form_submit_button("Register")

        if register_button:
            if not email:
                set_error_message("Please enter your email.")
            elif not password:
                set_error_message("Please enter a password.")
            elif password != confirm_password:
                set_error_message("Passwords do not match.")
            else:
                register_user(email, password)

    st.markdown("---")
    st.subheader("Already have an account?")
    if st.button("Login Here", key="go_to_login"):
        st.session_state['current_screen'] = 'login'
        clear_error_message()
        st.rerun()

elif st.session_state['current_screen'] == 'app' and st.session_state['logged_in']:
    # Main app logic - Display content only if logged in
    # Use a generic welcome until profile is loaded
    welcome_name = st.session_state['user_profile'].get('name', 'User') if st.session_state['user_profile']['is_profile_loaded'] else 'User'
    st.sidebar.markdown(f"**Welcome, {welcome_name}!**")

    if st.sidebar.button("Logout"):
        logout_user()

    st.subheader("Explore Cosmic Word!")

    tab_names = ["Numerology", "Astrology", "Tarot Cards", "Vastu Shastra", "Palmistry", "Aura Reading", "My Profile"]
    selected_tab_names = st.tabs(tab_names)

    for i, tab in enumerate(selected_tab_names):
        with tab:
            if tab_names[i] == "Numerology":
                st.header("Numerology: Uncover Your Life's Blueprint")
                st.write("Unlock insights into your personality, destiny, and life's purpose by exploring your core numerology numbers.")

                # Conditional display based on profile completeness
                if not st.session_state['user_profile']['is_profile_loaded'] or \
                        not st.session_state['user_profile'].get('name') or \
                        not st.session_state['user_profile'].get('dob'):
                        st.warning("Please update your Full Name and Date of Birth in the 'My Profile' tab to use Numerology features.")
                else:
                    name_for_numerology = st.session_state['user_profile']['name']
                    dob_for_numerology = st.session_state['user_profile']['dob']

                    # Display the pre-filled, disabled inputs
                    st.text_input("Your Full Name", value=name_for_numerology, disabled=True,
                                  key="numerology_display_name")
                    st.date_input("Your Birth Date", value=dob_for_numerology, disabled=True,
                                  key="numerology_display_dob")
                    st.info("To change Name or Date of Birth, please go to the 'My Profile' tab.")

                    if st.button("Calculate My Numbers", key="calculate_all_numerology"):
                        st.subheader(f"Numerology Report for {name_for_numerology}, born on {dob_for_numerology}:")

                        # --- Calculate and Display Life Path Number ---
                        life_path = calculate_life_path(dob_for_numerology)
                        if life_path is not None:
                            st.markdown(f"**Life Path Number:** `{life_path}`")
                            with st.expander(f"Meaning of Life Path Number {life_path}"):
                                st.write(NUMEROLOGY_INTERPRETATIONS.get(life_path,
                                                                        "No interpretation found for this number."))
                        else:
                            st.error("Could not calculate Life Path Number. Please check your Date of Birth.")

                        # --- Calculate and Display Expression Number ---
                        expression_number = calculate_expression_number(name_for_numerology)
                        if expression_number is not None:
                            st.markdown(f"**Expression/Destiny Number:** `{expression_number}`")
                            with st.expander(f"Meaning of Expression Number {expression_number}"):
                                st.write(NUMEROLOGY_INTERPRETATIONS.get(expression_number,
                                                                        "No interpretation found for this number."))
                        else:
                            st.error(
                                "Could not calculate Expression Number. Please ensure your name is entered correctly.")

                        # --- Calculate and Display Soul Urge Number ---
                        soul_urge_number = calculate_soul_urge_number(name_for_numerology)
                        if soul_urge_number is not None:
                            st.markdown(f"**Soul Urge/Heart's Desire Number:** `{soul_urge_number}`")
                            with st.expander(f"Meaning of Soul Urge Number {soul_urge_number}"):
                                st.write(NUMEROLOGY_INTERPRETATIONS.get(soul_urge_number,
                                                                        "No interpretation found for this number."))
                        else:
                            st.error(
                                "Could not calculate Soul Urge Number. Please ensure your name is entered correctly.")

                        # --- Calculate and Display Personality Number ---
                        personality_number = calculate_personality_number(name_for_numerology)
                        if personality_number is not None:
                            st.markdown(f"**Personality Number:** `{personality_number}`")
                            with st.expander(f"Meaning of Personality Number {personality_number}"):
                                st.write(NUMEROLOGY_INTERPRETATIONS.get(personality_number,
                                                                        "No interpretation found for this number."))
                        else:
                            st.error(
                                "Could not calculate Personality Number. Please ensure your name is entered correctly.")

                        # --- Calculate and Display Birth Day Number ---
                        birth_day_number = calculate_birth_day_number(dob_for_numerology)
                        if birth_day_number is not None:
                            st.markdown(f"**Birth Day Number:** `{birth_day_number}`")
                            with st.expander(f"Meaning of Birth Day Number {birth_day_number}"):
                                st.write(NUMEROLOGY_INTERPRETATIONS.get(birth_day_number,"No interpretation found for this number."))
                        else:
                            st.error("Could not calculate Birth Day Number. Please check your Date of Birth.")

            elif tab_names[i] == "Astrology":
                st.header("Astrology: Cosmic Guidance")
                st.write("Details about Astrology, Natal Charts, Horoscopes, etc.")
            elif tab_names[i] == "Tarot Cards":
                st.header("Tarot Cards: Intuitive Insights")
                st.write("Virtual Tarot readings and interpretations.")
            elif tab_names[i] == "Vastu Shastra":
                st.header("Vastu Shastra: Harmonize Your Space")
                st.write("Principles for architectural harmony.")
            elif tab_names[i] == "Palmistry":
                st.header("Palmistry: The Map in Your Hand")
                st.write("Insights from palm lines and shapes.")
            elif tab_names[i] == "Aura Reading":
                st.header("Aura Reading: Vibrational Energy")
                st.write("Understanding your energy field.")

            # NEW TAB: My Profile - Now loads/updates profile data
            elif tab_names[i] == "My Profile":
                st.header("My Profile")
                st.write("Update your personal information.")


                with st.form("profile_update_form"):
                    current_name = st.session_state['user_profile'].get('name', '')
                    current_dob = st.session_state['user_profile'].get('dob') or today

                    new_name = st.text_input("Full Name (as on birth certificate)", value=current_name, key="profile_name_input")
                    new_dob = st.date_input("Date of Birth", value=current_dob, max_value=today,
                                            min_value=min_allowed_dob, key="profile_dob_input")

                    update_profile_button = st.form_submit_button("Update Profile")

                    if update_profile_button:
                        if new_name and new_dob:
                            if st.session_state.get('user_info') and 'localId' in st.session_state['user_info'] and 'idToken' in st.session_state['user_info']:
                                user_uid = st.session_state['user_info']['localId']
                                id_token = st.session_state['user_info']['idToken']
                                try:
                                    db.child("users").child(user_uid).update({
                                        "name": new_name,
                                        "dob": new_dob.isoformat() # Store as ISO format string
                                    },
                                    id_token
                                    )
                                    st.session_state['user_profile']['name'] = new_name
                                    st.session_state['user_profile']['dob'] = new_dob
                                    st.session_state['user_profile']['is_profile_loaded'] = True # Ensure flag is true
                                    st.success("Your profile information has been updated!")
                                    st.rerun() # Rerun to refresh welcome message and other pre-filled fields
                                except Exception as e:
                                    set_error_message(f"Failed to update profile: {e}. Check database rules.")
                                    st.rerun()
                            else:
                                set_error_message("User information not found. Please log in again.")
                                st.rerun()
                        else:
                            st.warning("Please enter both your full name and birth date.")


    st.markdown("---")
    st.header("Connect with an Expert (Chat)")
    st.write("This will be our dedicated chat module to connect users with astrologers/practitioners.")
    st.button("Start a Chat")

# --- Audio Autoplay (Hidden and Muted) ---
def get_base64_audio(audio_path):
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        encoded = base64.b64encode(audio_bytes).decode("utf-8")
        return f"data:audio/wav;base64,{encoded}"
    except FileNotFoundError:
        st.warning(f"Audio file not found: {audio_path}")
        return None

audio_path = "bgm.wav"
audio_data_url = get_base64_audio(audio_path)

if audio_data_url:
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