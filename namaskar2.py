import streamlit as st
import json
import requests
import datetime
from supabase import create_client, Client

# --- GLOBAL DATE DEFINITIONS ---
import datetime # Ensure datetime is imported at the top if not already

today = datetime.date.today() # This correctly initializes 'today' as a datetime.date object
min_allowed_dob = today.replace(year=today.year - 100) # 'today' is already a date object, so no .date() needed
# --- END GLOBAL DATE DEFINITIONS ---

# --- Supabase Client Initialization ---
supabase_url = st.secrets.get("SUPABASE_URL")
supabase_key = st.secrets.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    st.error("Supabase URL or Key not found in Streamlit secrets. Please configure .streamlit/secrets.toml")
    st.stop()

supabase: Client = create_client(supabase_url, supabase_key)

# --- Session State Management for Authentication ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None
if 'user_profile' not in st.session_state:
    st.session_state['user_profile'] = {'name': '', 'dob': None}

# New session state variable for persistent error messages
if 'display_error_message' not in st.session_state:
    st.session_state['display_error_message'] = None


# --- Helper to set error and prevent clearing on rerun immediately ---
def set_error_message(message):
    st.session_state['display_error_message'] = message

def clear_error_message():
    st.session_state['display_error_message'] = None


# --- login_user function using Supabase Native Auth ---
def login_user(email, password):
    clear_error_message()  # Clear any previous error when attempting new login

    try:
        # Use Supabase native sign_in_with_password
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session = auth_response.session
        user = auth_response.user

        if session and user:
            st.session_state['logged_in'] = True
            st.session_state['user_info'] = {
                'email': user.email,
                'uid': user.id,  # Supabase user ID
                'access_token': session.access_token  # Supabase access token
            }
            st.session_state['supabase_session'] = session
            st.success(f"Welcome, {user.email}!")

            # --- Retrieve User Profile from Supabase ---
            profile_response = supabase.table('profiles').select('*').eq('id', user.id).single().execute()

            if profile_response.data:
                profile_data = profile_response.data
                st.session_state['user_profile']['name'] = profile_data.get('name', '')
                dob_str = profile_data.get('dob')
                if dob_str:
                    try:
                        st.session_state['user_profile']['dob'] = datetime.date.fromisoformat(dob_str)
                    except ValueError:
                        st.warning("Stored DOB format is invalid.")
                else:
                    st.session_state['user_profile']['dob'] = None
                st.info("User profile data loaded from Supabase.")
            else:
                set_error_message(
                    "Profile not found in Supabase after successful login. Data integrity issue. Please contact support.")

        st.rerun()
        return True
    except Exception as e:
        # Supabase errors often include specific messages in the exception
        set_error_message(f"Login failed: {e}")
        st.session_state['logged_in'] = False
        st.session_state['user_info'] = None
        st.session_state['user_profile'] = {'name': '', 'dob': None}
        return False # Return False on failure

# --- register_user function using Supabase Native Auth ---
def register_user(email, password, full_name, dob):
    clear_error_message()  # Clear any previous error when attempting new registration

    try:
        # Use Supabase native sign_up
        auth_response = supabase.auth.sign_up({"email": email, "password": password})
        user = auth_response.user

        if user:
            st.success(f"User {user.email} registered successfully with Supabase!")
            st.info("You are now logged in. Please verify your email if required by Supabase settings.")

            # --- Save User Profile to Supabase immediately after successful registration ---
            st.session_state['logged_in'] = True  # Auto-login after registration
            st.session_state['user_info'] = {
                'email': user.email,
                'uid': user.id,  # Supabase user ID
                'access_token': auth_response.session.access_token  # Supabase access token
            }
            st.session_state['supabase_session'] = auth_response.session
            st.session_state['user_profile']['name'] = full_name
            st.session_state['user_profile']['dob'] = dob

            try:
                profile_data = {
                    'id': user.id,  # Supabase user ID is the primary key for profiles table
                    'name': full_name,
                    'dob': dob.isoformat()  # Convert date to ISO format string
                }

                # --- DEBUGGING LINES (These should appear on your webpage) ---
                print("--- ATTEMPTING PROFILE UPSERT DEBUG ---")  # ADD THIS LINE
                st.write("Attempting to upsert profile data to Supabase:", profile_data)
                st.write("Supabase User ID (for profile 'id'):", user.id)

                response = supabase.table('profiles').upsert(profile_data, on_conflict='id').execute()

                if response.error:
                    # Supabase client returns error property on the response if there's an API error
                    raise Exception(f"Supabase upsert API error: {response.error}")

                st.success("User profile data saved to Supabase successfully!")
                st.write("Raw Supabase upsert response data:", response.data)
                st.write("Supabase upsert error (if any):", response.error)
                # --- END DEBUGGING LINES ---

            except Exception as e:
                # If profile saving fails after successful registration, show an error but keep user logged in.
                set_error_message(
                    f"Registration was successful, but failed to save user profile details: {e}. You can update your profile from the numerology tab. Please re-check Supabase RLS policies for the 'profiles' table (specifically, the INSERT policy with 'authenticated' role and WITH CHECK (true) expression).")

        else:
            set_error_message("Registration failed: No user object returned from Supabase.")

        st.rerun()
        return True
    except Exception as e:
        # Supabase errors often include specific messages in the exception
        set_error_message(f"Registration failed: {e}")
        return False


def logout_user():
    clear_error_message()  # Clear error message on logout
    if 'supabase_session' in st.session_state and st.session_state['supabase_session']:
        try:
            supabase.auth.sign_out()
            del st.session_state['supabase_session']
            st.info("Logged out from Supabase.")
        except Exception as e:
            st.warning(f"Failed to log out from Supabase: {e}")

    st.session_state['logged_in'] = False
    st.session_state['user_info'] = None
    st.session_state['user_profile'] = {'name': '', 'dob': None}
    st.info("You have been logged out.")
    st.rerun()


# --- UI Layout (Mostly Unchanged) ---
st.set_page_config(layout="wide", page_title="Namaskar: Spirituality Unlimited")

# Adjusted today() to today.date() for consistency with min_allowed_dob
# min_allowed_dob = today.replace(year=today.year - 100) # Global definition
if isinstance(today, datetime.datetime): # Ensure 'today' is a date object for date calculations
    today_for_calc = today.date()
else:
    today_for_calc = today


st.markdown("""
<style>
    /* Overall app styling */
    .main {
        background-color: #F0F2F6; /* Light gray background */
        color: #333333; /* Darker text for readability */
    }
    /* Style for the main title */
    .st-emotion-cache-zt5ig8 {
        color: #4CAF50;
        text-align: center;
        font-family: 'Georgia', serif;
        font-size: 3.5em;
        margin-bottom: 20px;
    }
    /* Style for st.header elements */
    h1, h2, h3, h4, h5, h6 {
        color: #6C757D;
        font-family: 'Arial', sans-serif;
    }
    /* Style for form elements (optional) */
    .st-form {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    /* Styling for buttons */
    .stButton > button {
        background-color: #007BFF;
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

# --- Add Logo and Title ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # st.image("logo.png", width=200) # Uncomment this if you have a logo image
    st.title("Namaskar: Spirituality Unlimited")
# --- End Logo and Title ---

# --- Persistent Error Display ---
if st.session_state['display_error_message']:
    st.error(st.session_state['display_error_message'])
# --- End Persistent Error Display ---


# Main app logic
if not st.session_state['logged_in']:
    st.subheader("Login / Register")
    login_tab, register_tab = st.tabs(["Login", "Register"])  # Removed default_tab for compatibility

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
            full_name = st.text_input("Full Name", key="register_full_name")
            dob = st.date_input(
                "Date of Birth",
                key="register_dob",
                value=today, # Use the date object
                min_value=min_allowed_dob,
                max_value=today
            )
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")
            submit_button = st.form_submit_button("Register")
            if submit_button:
                if not full_name:
                    set_error_message("Please enter your Full Name.")
                elif not dob:
                    set_error_message("Please enter your Date of Birth.")
                elif password != confirm_password:
                    set_error_message("Passwords do not match.")
                else:
                    register_user(email, password, full_name, dob)
else:
    st.sidebar.write(f"Logged in as: {st.session_state['user_info']['email']}")
    if st.session_state['user_profile']['name']:
        st.sidebar.write(f"Name: {st.session_state['user_profile']['name']}")
    st.sidebar.button("Logout", on_click=logout_user)

    st.subheader("Explore Spirituality Unlimited!")

    tab_names = ["Numerology", "Astrology", "Tarot Cards", "Vastu Shastra", "Palmistry", "Aura Reading"]
    selected_tab = st.tabs(tab_names)

    with selected_tab[0]:  # Numerology tab
        st.header("Numerology: Uncover Your Life's Blueprint")
        st.write("This is where the Numerology calculations and insights will go.")

        with st.form("numerology_form"):
            current_name = st.session_state['user_profile']['name']
            current_dob = st.session_state['user_profile']['dob']

            name_input = st.text_input("Your Full Name (as on birth certificate)", value=current_name)

            default_dob_value = current_dob if current_dob else datetime.date(2000, 1, 1)
            birth_date_input = st.date_input("Your Birth Date", value=default_dob_value, max_value=today,
                                             min_value=min_allowed_dob)

            numerology_submit = st.form_submit_button("Calculate My Numbers")

            if numerology_submit:
                # --- UPDATE PROFILE ON SUBMISSION (If changed) ---
                if name_input != st.session_state['user_profile']['name'] or \
                        (birth_date_input and birth_date_input != st.session_state['user_profile'][
                            'dob']):  # Added check for birth_date_input

                    st.info("Updating your profile in Supabase...")
                    try:
                        if st.session_state.get('user_info') and st.session_state['user_info'].get('uid'):
                            update_data = {
                                'name': name_input,
                                'dob': birth_date_input.isoformat() if birth_date_input else None
                            }
                            # Ensure RLS policies in Supabase 'profiles' table allow authenticated users to update their own row
                            update_response = supabase.table('profiles').update(update_data).eq('id', st.session_state[
                                'user_info']['uid']).execute()

                            if update_response.data:
                                st.success("Profile updated successfully in Supabase!")
                                st.session_state['user_profile']['name'] = name_input
                                st.session_state['user_profile']['dob'] = birth_date_input
                            else:
                                st.error(
                                    f"Failed to update profile: {update_response.get('error', 'Unknown Supabase error')}")
                        else:
                            st.warning("User not logged in or UID missing. Cannot save profile. Please re-login.")
                    except Exception as e:
                        st.error(f"Error updating profile: {e}")
                # --- END UPDATE PROFILE ---

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