import streamlit as st
import subprocess
import tempfile
import os
import shutil
import time

st.title("CSV Batch Processor")
st.write("Upload your CSV files → run script → download result")

# ────────────────────────────────────────────────
#          CHANGE THESE IF NEEDED
SCRIPT_NAME = "allstat"                    # exact filename as in GitHub (no .sh unless it has one)
OUTPUT_FILE = "Total.csv" # relative path to the file you want to download
# If you prefer total.csv instead → change to: "all-totalstats/total.csv"
# ────────────────────────────────────────────────

uploaded_files = st.file_uploader(
    "Choose your CSV files",
    type="csv",
    accept_multiple_files=True
)

if st.button("Run Script") and uploaded_files:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save uploaded CSVs to temp folder with explicit sync
        for uploaded_file in uploaded_files:
            file_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                f.flush()           # Ensure data is written from buffer
                os.fsync(f.fileno()) # Force OS to write to disk

        # Give the filesystem a moment to catch up (critical on some cloud envs)
        time.sleep(1.0)

        # Copy your bash script into the temp folder
        script_path = os.path.join(tmp_dir, SCRIPT_NAME)
        if not os.path.exists(SCRIPT_NAME):
            st.error(f"Script '{SCRIPT_NAME}' not found in repo!")
            st.stop()

        shutil.copy(SCRIPT_NAME, script_path)
        os.chmod(script_path, 0o755)  # Make executable

        # ─────────────── Debug: Show what's actually on disk ───────────────
        st.write("Files present in temp dir just before running script:")
        files_in_dir = os.listdir(tmp_dir)
        if files_in_dir:
            for fname in files_in_dir:
                fpath = os.path.join(tmp_dir, fname)
                size = os.path.getsize(fpath)
                st.write(f"• {fname}  (size: {size:,} bytes)")
        else:
            st.warning("No files found in temp directory!")

        # Run the bash script
        try:
            result = subprocess.run(
                ["bash", SCRIPT_NAME],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                check=True
            )

            st.success("Script ran successfully!")

            # Look for the output file inside the subfolder the script creates
            output_path = os.path.join(tmp_dir, OUTPUT_FILE)

            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    file_bytes = f.read()

                # Extract just the filename for the download button
                download_name = os.path.basename(output_path)

                st.download_button(
                    label=f"📥 Download {download_name}",
                    data=file_bytes,
                    file_name=download_name,
                    mime="text/csv"
                )
            else:
                st.error(f"Output file not found: {OUTPUT_FILE}")
                st.info("Script ran but didn't create the expected file. Check script logic or debug output above.")

        except subprocess.CalledProcessError as e:
            st.error("Script failed — error output below")
            if e.stderr:
                st.code(e.stderr.strip())
            if e.stdout:
                st.code(e.stdout.strip())

        # Optional: show any console output from the script
        if result.stdout:
            with st.expander("Script console output (stdout)"):
                st.code(result.stdout)
