from flask import Flask, render_template_string, request, send_file
import qrcode
from PIL import Image, ImageDraw
from io import BytesIO
import base64

app = Flask(__name__)

qr_buffer = None

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Pro QR Generator</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI';
            background: linear-gradient(135deg, #0f2027, #2c5364);
            color: white;
            text-align: center;
        }
        h1 {
            margin-top: 20px;
        }
        .card {
            backdrop-filter: blur(15px);
            background: rgba(255,255,255,0.1);
            padding: 25px;
            border-radius: 20px;
            width: 320px;
            margin: auto;
            box-shadow: 0 0 20px rgba(0,0,0,0.4);
        }
        input, select {
            width: 90%;
            padding: 10px;
            margin: 10px;
            border-radius: 10px;
            border: none;
            outline: none;
        }
        input[type="color"] {
            height: 40px;
        }
        button {
            padding: 12px 20px;
            border-radius: 12px;
            border: none;
            background: #00dbde;
            color: black;
            font-weight: bold;
            cursor: pointer;
        }
        img {
            margin-top: 20px;
            width: 200px;
            border-radius: 20px;
            box-shadow: 0 0 15px black;
        }
    </style>
</head>
<body>

<h1>⚡ Pro QR Generator</h1>

<div class="card">
    <form method="POST" enctype="multipart/form-data">
        <input type="text" name="data" placeholder="Enter text or URL" required>

        QR Color:
        <input type="color" name="fill" value="#000000">

        Background:
        <input type="color" name="back" value="#ffffff">

        Upload Logo:
        <input type="file" name="logo">

        <button type="submit">Generate</button>
    </form>

    {% if img %}
        <img src="{{ img }}">
        <br><br>
        <a href="/download"><button>Download</button></a>
    {% endif %}
</div>

</body>
</html>
"""

def add_logo(qr_img, logo_file):
    if not logo_file:
        return qr_img

    logo = Image.open(logo_file)

    # Resize logo
    qr_w, qr_h = qr_img.size
    logo_size = qr_w // 4
    logo = logo.resize((logo_size, logo_size))

    pos = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)

    qr_img.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)
    return qr_img

@app.route("/", methods=["GET", "POST"])
def home():
    global qr_buffer
    img_data = None

    if request.method == "POST":
        data = request.form["data"]
        fill = request.form["fill"]
        back = request.form["back"]
        logo = request.files.get("logo")

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2,
        )

        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill, back_color=back).convert("RGBA")

        # Make rounded corners
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=40, fill=255)
        img.putalpha(mask)

        # Add logo if provided
        img = add_logo(img, logo)

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        qr_buffer = buffer

        img_data = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

    return render_template_string(HTML, img=img_data)

@app.route("/download")
def download():
    global qr_buffer
    return send_file(qr_buffer, mimetype='image/png', as_attachment=True, download_name="pro_qr.png")

if __name__ == "__main__":
    app.run(debug=True)