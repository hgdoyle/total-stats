import streamlit as st
import subprocess
import tempfile
import os
import shutil

st.title("CSV Batch Processor")
st.write("Upload your CSV files → run script → download result")

# ────────────────────────────────────────────────
#          CHANGE THESE TWO LINES ONLY
SCRIPT_NAME = "allstat"          # ← your bash script's exact name (e.g. myscript.sh)
OUTPUT_NAME = "All-TotalStats/Total.csv" # ← exact name of the file your script creates
# ────────────────────────────────────────────────

uploaded_files = st.file_uploader(
    "Choose your CSV files",
    type="csv",
    accept_multiple_files=True
)

if st.button("Run Script") and uploaded_files:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded CSVs to temp folder
        for uploaded_file in uploaded_files:
            file_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        # Copy your bash script into the temp folder
        script_path = os.path.join(tmp_dir, SCRIPT_NAME)
        if not os.path.exists(SCRIPT_NAME):
            st.error(f"Script '{SCRIPT_NAME}' not found in repo!")
            st.stop()
        shutil.copy(SCRIPT_NAME, script_path)

        # Make script executable (usually not needed on cloud, but safe)
        os.chmod(script_path, 0o755)

        try:
            result = subprocess.run(
                ["bash", SCRIPT_NAME],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                check=True
            )
            st.success("Script ran successfully!")

            output_path = os.path.join(tmp_dir, OUTPUT_NAME)
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.download_button(
                        "Download Result",
                        data=f,
                        file_name=OUTPUT_NAME,
                        mime="text/csv"
                    )
            else:
                st.error(f"Output file '{OUTPUT_NAME}' was not created.")

        except subprocess.CalledProcessError as e:
            st.error("Script failed — check the error below")
            st.code(e.stderr or "No error output captured")
