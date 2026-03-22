import streamlit as st
import subprocess
import tempfile
import os
import shutil
import time

st.title("Marauder's Ultimate Frisbee League Total Stat Generator")
st.write("")

# ────────────────────────────────────────────────
SCRIPT_NAME = "allstat"                     # your script filename
OUTPUT_FILE  = "Total.csv"  # main result file to offer for download
# You can also offer Total.csv later if needed
# ────────────────────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    csv_files = st.file_uploader(
        "Upload your CSV files (Download each sheet from the regular season stats spreadsheet as a .csv file and upload them here.",
        type="csv",
        accept_multiple_files=True,
        key="csv_uploader"
    )

with col2:
    names_file = st.file_uploader(
        """Upload file named names.txt. This file should contain every players name in the following format:
        \n John Smith
        \n Billy Brown
        \n Harrison Ford""",
        type="txt",
        accept_multiple_files=False,
        key="names_uploader"
    )

if st.button("Run Script") and csv_files and names_file:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Save all CSV files
        for uploaded in csv_files:
            path = os.path.join(tmp_dir, uploaded.name)
            with open(path, "wb") as f:
                f.write(uploaded.getbuffer())
                f.flush()
                os.fsync(f.fileno())

        # 2. Save names.txt — force the name to be exactly "names.txt"
        names_path = os.path.join(tmp_dir, "names.txt")
        with open(names_path, "wb") as f:
            f.write(names_file.getbuffer())
            f.flush()
            os.fsync(f.fileno())

        time.sleep(1.0)  # filesystem settle time

        # Debug: show what's in the folder
        st.write("Files saved in temporary directory:")
        for fname in sorted(os.listdir(tmp_dir)):
            size = os.path.getsize(os.path.join(tmp_dir, fname))
            st.write(f"• {fname}  ({size:,} bytes)")

        # Copy the bash script
        script_path = os.path.join(tmp_dir, SCRIPT_NAME)
        if not os.path.exists(SCRIPT_NAME):
            st.error(f"Script '{SCRIPT_NAME}' not found in repo")
            st.stop()

        shutil.copy(SCRIPT_NAME, script_path)
        os.chmod(script_path, 0o755)

        # Run the script
        try:
            result = subprocess.run(
                ["bash", SCRIPT_NAME],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                check=True
            )

            st.success("Script completed successfully")

            if result.stdout:
                with st.expander("Script output (stdout)"):
                    st.code(result.stdout.strip())

            # Offer download of the main result file
            output_path = os.path.join(tmp_dir, OUTPUT_FILE)
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Allstate.csv",
                        data=f,
                        file_name="Allstate.csv",
                        mime="text/csv",
                        key="dl_allstate"
                    )
            else:
                st.error(f"Expected output not found: {OUTPUT_FILE}")

            # Optional: also offer Total.csv
            total_path = os.path.join(tmp_dir, "All-TotalStats/Total.csv")
            if os.path.exists(total_path):
                with open(total_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Total.csv",
                        data=f,
                        file_name="Total.csv",
                        mime="text/csv",
                        key="dl_total"
                    )

        except subprocess.CalledProcessError as e:
            st.error("Script failed")
            if e.stdout:
                st.code(e.stdout.strip(), language="bash")
            if e.stderr:
                st.code(e.stderr.strip(), language="bash")

elif st.button("Run Script"):
    st.warning("Please upload both CSV files and names.txt")
