import streamlit as st
import pandas as pd
import os
from pathlib import Path
from requests import request

# === Streamlit Page Config ===
st.set_page_config(
    page_title="Coupa Invoice Downloader",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# === Custom Dark Theme Styling ===
st.markdown("""
    <style>
        body {
            color: white;
            background-color: #121212;
        }
        .stApp {
            background-color: #1E1E1E;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4, h5 {
            color: #E1E1E1;
        }
        .stButton>button {
            background-color: #007ACC;
            color: white;
            border-radius: 6px;
            height: 3em;
            width: 100%;
            font-weight: bold;
            margin-top: 1em;
        }
        .stTextInput>div>input {
            background-color: #2A2A2A;
            color: #E1E1E1;
        }
        .top-right {
            position: absolute;
            top: 10px;
            right: 20px;
            color: #888;
            font-weight: 500;
        }
    </style>
    <div class='top-right'>Hayden Meyer</div>
""", unsafe_allow_html=True)

# === UI Title ===
st.markdown("<h1 style='color:#56C1FF;'>📄 Coupa Invoice Scan Downloader</h1>", unsafe_allow_html=True)
st.markdown("Upload your invoice CSV and automatically save PDF scans to your Downloads folder.")

# === Step 1: Upload CSV ===
st.subheader("📁 Step 1: Upload CSV File")
uploaded_file = st.file_uploader("Choose a CSV file with an 'Invoice ID' column", type=["csv"])

# === Step 2: Destination Folder (Downloads) ===
st.subheader("📂 Step 2: Destination Folder")
downloads_path = str(Path.home() / "Downloads")
st.markdown(f"PDFs will be saved to your Downloads folder:")
st.code(downloads_path, language="bash")
destination_folder = downloads_path

# === Step 3: Run Script ===
st.subheader("🚀 Step 3: Run Script")

if uploaded_file and destination_folder and st.button("▶️ Run"):
    try:
        st.success("Running script...")

        # === Step 1: Authenticate with Coupa ===
        CLIENT_ID = "aa6e9be0a787f3883fb43a14c1bbbbf4"
        CLIENT_SECRET = "0569ccb540eff709775e36fa01881f3272cf629a1ae7f088293bb74ea39dfbba"
        COUPA_INSTANCE = "evt-test"

        token_url = f"https://{COUPA_INSTANCE}.coupahost.com/oauth2/token"
        token_data = {
            "grant_type": "client_credentials",
            "scope": "core.invoice.read"
        }
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}

        with st.spinner("🔐 Authenticating with Coupa..."):
            response = request("POST", token_url, auth=(CLIENT_ID, CLIENT_SECRET), data=token_data, headers=token_headers)
            response.raise_for_status()

        access_token = response.json()["access_token"]
        token_type = response.json().get("token_type", "Bearer")
        headers = {
            "Authorization": f"{token_type} {access_token}",
            "Accept": "application/json"
        }

        # === Step 2: Process Invoice IDs from CSV ===
        df = pd.read_csv(uploaded_file)
        if "Invoice ID" not in df.columns:
            st.error("❌ CSV must contain a column named 'Invoice ID'")
        else:
            invoice_ids = df["Invoice ID"].dropna().astype(str).tolist()
            os.makedirs(destination_folder, exist_ok=True)

            # === Step 3: Download PDF Scans ===
            progress = st.progress(0)
            status = st.empty()

            for i, invoice_id in enumerate(invoice_ids):
                scan_url = f"https://{COUPA_INSTANCE}.coupahost.com/api/invoices/{invoice_id}/retrieve_image_scan"
                response = request("GET", scan_url, headers=headers)

                if response.status_code == 200:
                    file_path = os.path.join(destination_folder, f"{invoice_id}_scan.pdf")
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    status.success(f"✅ Downloaded {invoice_id}")
                else:
                    status.warning(f"⚠️ Failed to download {invoice_id} (Status: {response.status_code})")

                progress.progress((i + 1) / len(invoice_ids))

            st.success(f"✅ All done! PDFs saved to: {destination_folder}")
            st.markdown(f"[📁 Open Folder]({destination_folder})", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error: {e}")