# streamlit_app.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore # 'auth' from firebase_admin is no longer used for login/register
import json
import requests

# --- Cleaning function for Firebase Admin SDK credentials ---
# This is still used for the Firebase Admin SDK initialization,
# which is needed for Firestore and other server-side features.
def aggressive_clean_json_string(s):
    cleaned_chars = []
    for ch in s:
        # Keep essential whitespace (newline, tab, carriage return)
        if ch in ('\n', '\t', '\r'):
            cleaned_chars.append(ch)
        # Keep standard printable ASCII characters (from space to tilde)
        elif ' ' <= ch <= '~':
            cleaned_chars.append(ch)
    return "".join(cleaned_chars)

# --- Firebase Admin SDK Initialization ---
# 'db' is initialized to None. It will be set to a Firestore client if initialization succeeds.
# If initialization fails (e.g., due to the JSON issue), the app will continue to run,
# but Firestore-dependent features will not work.
db = None

if not firebase_admin._apps:
    try:
        firebase_config_str = st.secrets["FIREBASE_CREDENTIALS"]

        # --- DEBUGGING SNIPPET (Keep this active for now as the JSON issue persists) ---
        st.write("--- DEBUGGING Firebase Credentials String ---")
        st.write(f"Length of raw string from secrets: {len(firebase_config_str)}")
        st.text("First 500 chars (repr):")
        st.code(repr(firebase_config_str[:500]), language='python')
        st.text("Last 500 chars (repr):")
        st.code(repr(firebase_config_str[-500:]), language='python')

        problem_char_index = 222 # Based on "char 223" from latest error message
        if len(firebase_config_str) > problem_char_index:
            char_at_pos = firebase_config_str[problem_char_index]
            st.write(f"Character at reported NEW problem spot (char {problem_char_index + 1}):")
            st.code(repr(char_at_pos), language='python')
            st.write(f"Hex value (ord): {hex(ord(char_at_pos)) if char_at_pos else 'N/A'}")
        else:
            st.write(f"String too short to check char {problem_char_index + 1}")
        st.write("------------------------------------------")

        st.write("Attempting to parse CLEANED Firebase credentials string for Admin SDK...")
        cleaned_firebase_config_str = aggressive_clean_json_string(firebase_config_str)

        firebase_config = json.loads(cleaned_firebase_config_str)
        cred = credentials.Certificate(cert_data=firebase_config)
        firebase_admin.initialize_app(cred)
        db = firestore.client() # Firestore client initialized if Admin SDK init succeeds
        st.success("Firebase Admin SDK (for Firestore etc.) initialized successfully!")

    except KeyError:
        st.error("Firebase credentials (for Admin SDK) not found in Streamlit secrets. Firestore may not work.")
    except json.JSONDecodeError as e:
        st.error(f"WARNING: Firebase Admin SDK initialization failed due to JSON parsing: {e}. Firestore and other server-side features will NOT work.")
    except Exception as e:
        st.error(f"WARNING: An unexpected error occurred during Firebase Admin SDK initialization: {e}. Firestore and other server-side features will NOT work.")


# --- Session State Management for Authentication ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- login_user function using Firebase Auth REST API ---
def login_user(email, password):
    api_key = st.secrets.get("FIREBASE_API_KEY")
    if not api_key:
        st.error("Firebase API Key not found in secrets. Cannot perform client-side authentication.")
        return False

    login_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })

    try:
        response = requests.post(login_url, headers=headers, data=data)
        response.raise_for_status()
        user_data = response.json()
        st.session_state['logged_in'] = True
        st.session_state['user_info'] = {
            'email': email,
            'uid': user_data['localId'],
            'idToken': user_data['idToken']
        }
        st.success(f"Welcome, {email}!")
        st.rerun()
        return True
    except requests.exceptions.HTTPError as e:
        error_response = e.response.json()
        error_message = error_response.get('error', {}).get('message', 'Unknown Error')
        if error_message == "EMAIL_NOT_FOUND" or error_message == "INVALID_PASSWORD":
            st.error("Invalid email or password.")
        else:
            st.error(f"Login failed: {error_message}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during login: {e}")
        return False

# --- register_user function using Firebase Auth REST API ---
def register_user(email, password):
    api_key = st.secrets.get("FIREBASE_API_KEY")
    if not api_key:
        st.error("Firebase API Key not found in secrets. Cannot perform client-side authentication.")
        return False

    signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    })

    try:
        response = requests.post(signup_url, headers=headers, data=data)
        response.raise_for_status()
        user_data = response.json()
        st.success(f"User {email} registered successfully!")
        st.session_state['logged_in'] = True
        st.session_state['user_info'] = {
            'email': email,
            'uid': user_data['localId'],
            'idToken': user_data['idToken']
        }
        st.rerun()
        return True
    except requests.exceptions.HTTPError as e:
        error_response = e.response.json()
        error_message = error_response.get('error', {}).get('message', 'Unknown Error')
        if error_message == "EMAIL_EXISTS":
            st.error("Email already registered. Please login or use a different email.")
        elif error_message == "WEAK_PASSWORD":
            st.error("Password is too weak. Please choose a stronger password (min 6 characters).")
        else:
            st.error(f"Registration failed: {error_message}")
        return False
    except Exception as e:
        st.error(f"An unexpected error occurred during registration: {e}")
        return False

def logout_user():
    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.info("You have been logged out.")
    st.rerun()

# --- UI Layout ---
st.set_page_config(layout="wide", page_title="Namaskar: Spirituality Unlimited")
st.title("Namaskar: Spirituality Unlimited")

if not st.session_state['logged_in']:
    st.subheader("Login / Register")
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        st.write("### Login")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submit_button = st.form_submit_button("Login")
            if submit_button:
                login_user(email, password)

    with register_tab:
        st.write("### Register")
        with st.form("register_form"):
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
            submit_button = st.form_submit_button("Register")
            if submit_button:
                if password == confirm_password:
                    register_user(email, password)
                else:
                    st.error("Passwords do not match.")
else:
    st.sidebar.write(f"Logged in as: {st.session_state['user_info']['email']}")
    st.sidebar.button("Logout", on_click=logout_user)

    st.subheader("Explore Spirituality Unlimited!")

    tab_names = ["Numerology", "Astrology", "Tarot Cards", "Vastu Shastra", "Palmistry", "Aura Reading"]
    selected_tab = st.tabs(tab_names)

    with selected_tab[0]: # Numerology tab
        st.header("Numerology: Uncover Your Life's Blueprint") # This was the duplicate; removed the other one
        st.write("This is where the Numerology calculations and insights will go.")

        with st.form("numerology_form"):
            name = st.text_input("Your Full Name (as on birth certificate)")
            birth_date = st.date_input("Your Birth Date")

            numerology_submit = st.form_submit_button("Calculate My Numbers")

            if numerology_submit:
                if name and birth_date:
                    st.subheader(f"Results for {name}, born on {birth_date}:")
                    life_path_num = sum(
                        int(digit) for digit in str(birth_date.year) + str(birth_date.month) + str(birth_date.day))
                    while life_path_num > 9 and life_path_num not in [11, 22, 33]:
                        life_path_num = sum(int(digit) for digit in str(life_path_num))

                    st.success(f"Your Life Path Number is: **{life_path_num}**")
                    st.write(
                        "*(Note: This is a highly simplified calculation. Real numerology involves more complex methods for name and date.)*")
                else:
                    st.warning("Please enter both your full name and birth date.")

    with selected_tab[1]: # Astrology tab
        st.header("Astrology: Cosmic Guidance")
        st.write("Details about Astrology, Natal Charts, Horoscopes, etc.")

    with selected_tab[2]: # Tarot Cards tab
        st.header("Tarot Cards: Intuitive Insights")
        st.write("Virtual Tarot readings and interpretations.")

    with selected_tab[3]: # Vastu Shastra tab
        st.header("Vastu Shastra: Harmonize Your Space")
        st.write("Principles for architectural harmony.")

    with selected_tab[4]: # Palmistry tab
        st.header("Palmistry: The Map in Your Hand")
        st.write("Insights from palm lines and shapes.")

    with selected_tab[5]: # Aura Reading tab
        st.header("Aura Reading: Vibrational Energy")
        st.write("Understanding your energy field.")

    st.markdown("---")
    st.header("Connect with an Expert (Chat)")
    st.write("This will be our dedicated chat module to connect users with astrologers/practitioners.")
    st.button("Start a Chat")