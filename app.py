import io
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from PIL import Image, ImageEnhance, ImageOps
from werkzeug.utils import secure_filename

try:
    from moviepy.editor import VideoFileClip
    from moviepy.video.fx.all import colorx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm"}
RESOLUTIONS = {
    "fhd": (1920, 1080),
    "4k": (3840, 2160),
    "8k": (7680, 4320),
}

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "replace-me-with-a-secure-key")


def allowed_extension(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS)


def is_image(filename: str) -> bool:
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def is_video(filename: str) -> bool:
    return filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def process_image(file_data: bytes, target_size: Tuple[int, int]) -> bytes:
    image = Image.open(io.BytesIO(file_data))
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    image = ImageOps.fit(image, target_size, Image.LANCZOS)
    image = ImageEnhance.Color(image).enhance(1.35)
    image = ImageEnhance.Contrast(image).enhance(1.2)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    image = ImageEnhance.Brightness(image).enhance(1.08)

    output = io.BytesIO()
    image.save(output, format="JPEG", quality=94, optimize=True)
    output.seek(0)
    return output.read()


def process_video(file_data: bytes, filename: str, target_size: Tuple[int, int], work_dir: Path) -> Tuple[bytes, str]:
    if not MOVIEPY_AVAILABLE:
        raise RuntimeError("Video conversion requires moviepy/FFmpeg on the server.")

    input_path = work_dir / secure_filename(filename)
    input_path.write_bytes(file_data)

    clip = VideoFileClip(str(input_path))
    enhanced = colorx(clip, 1.08)
    resized = enhanced.resize(newsize=target_size)

    output_name = f"enhanced_{input_path.stem}.mp4"
    output_path = work_dir / output_name
    resized.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
        verbose=False,
        logger=None,
    )
    clip.close()

    return output_path.read_bytes(), output_name


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files")
        if not files or all(file.filename == "" for file in files):
            flash("Please select at least one photo or video to enhance.")
            return redirect(url_for("index"))

        resolution_key = request.form.get("resolution", "fhd")
        if resolution_key not in RESOLUTIONS:
            resolution_key = "fhd"
        target_size = RESOLUTIONS[resolution_key]

        with tempfile.TemporaryDirectory() as work_dir_name:
            work_dir = Path(work_dir_name)
            zip_path = work_dir / "enhanced-media.zip"
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for index, file in enumerate(files, start=1):
                    if file.filename == "":
                        continue

                    filename = secure_filename(file.filename)
                    if not allowed_extension(filename):
                        flash(f"Unsupported file type: {filename}")
                        continue

                    file_data = file.read()
                    if is_image(filename):
                        output_bytes = process_image(file_data, target_size)
                        output_name = f"enhanced_{index}_{Path(filename).stem}.jpg"
                        archive.writestr(output_name, output_bytes)
                    elif is_video(filename):
                        if not MOVIEPY_AVAILABLE:
                            flash("Video conversion is unavailable on this server. Install moviepy and FFmpeg to enable it.")
                            continue
                        output_bytes, output_name = process_video(file_data, filename, target_size, work_dir)
                        archive.writestr(output_name, output_bytes)

            if zip_path.exists() and zip_path.stat().st_size > 0:
                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name="enhanced-media.zip",
                    mimetype="application/zip",
                )

        flash("No valid files were processed. Please upload supported image or video files.")
        return redirect(url_for("index"))

    return render_template("index.html", resolutions=RESOLUTIONS, moviepy_available=MOVIEPY_AVAILABLE)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
