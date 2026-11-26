# KEJI-FODA Appreciation Letter Studio

A simple Streamlit app that:
- accepts a recipient name and WhatsApp number;
- generates a professional PNG appreciation-letter image using the supplied KEJI-FODA logo;
- provides a PNG download;
- opens a WhatsApp chat with the full letter text prefilled.

## Important WhatsApp limitation
A standard `wa.me` link can open a chat and prefill text, but it cannot automatically attach an image or send a message. Download the generated PNG, open the WhatsApp chat, attach the PNG, review, and press Send manually.

## Run locally

1. Install Python 3.10 or newer.
2. Extract this project folder.
3. Open a terminal inside the folder.
4. Create and activate a virtual environment (recommended):

   **Windows**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

   **Linux / macOS**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Start the app:
   ```bash
   streamlit run app.py
   ```

The app opens in your browser, usually at http://localhost:8501.

## Deploy online
You can deploy this folder to Streamlit Community Cloud:
1. Upload the project to a GitHub repository.
2. In Streamlit Community Cloud, choose **Create app**.
3. Select the repository and `app.py`.
4. Deploy.

Keep `app.py`, `requirements.txt`, and the `assets` folder together.

## Message fidelity
The supplied message is kept as provided, including its double space in “we  hosted”, punctuation, date, signature, telephone number and email. The only inserted text is the recipient name after “Dear”.
