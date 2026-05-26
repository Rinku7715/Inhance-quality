# Photo & Video Quality Enhancer

A server-backed website that lets users upload old photos and improve quality in bulk.

## What it does
- Upload many photos at once
- Enhance image color, contrast, brightness, and sharpness
- Resize photos to FHD, 4K, or 8K
- Download all enhanced results in a single ZIP file
- Optional video conversion if moviepy and FFmpeg are installed

## Files
- `app.py` — Flask backend and enhancement logic
- `templates/index.html` — website UI
- `static/style.css` — page styling
- `static/script.js` — file selection UI behavior
- `requirements.txt` — Python dependencies

## Run the website locally
1. Open PowerShell in the project folder:
   ```powershell
   cd "c:\Users\rinku\Desktop\215"
   ```
2. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Start the app:
   ```powershell
   python app.py
   ```
5. Open in browser:
   ```text
   http://127.0.0.1:5000
   ```

## Deploy to Render
1. Push the project to GitHub.
2. Sign up on https://render.com and connect your GitHub repository.
3. Create a new Web Service and choose your repo.
4. Set the build command to:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the start command to:
   ```bash
   gunicorn app:app
   ```
6. Deploy and open the generated URL.

## Notes
- The app can handle large photo batches, but 1000+ files may take time depending on your server hardware.
- For video conversion, ensure FFmpeg is installed on the host and `moviepy` is available.
- Set `SECRET_KEY` in your host environment for production security.
