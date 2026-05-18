# Formova

I built this project during high school. 

Formova is a real-time, AI-powered workout form analyzer and virtual personal trainer. Using computer vision, it tracks your body movements through a webcam, calculates your joint angles on the fly, counts your repetitions, warns you if your form is slipping, and even lets you chat with an AI personal trainer powered by Google's Gemini API!

I designed this project to explore how advanced computer vision and generative AI can be brought together into a simple, helpful web app. I'm hoping to continue building and expanding on these concepts as I head into college!

---

## What It Does (Features)

*   **Real-Time Pose Tracking:** Uses Google's MediaPipe framework to detect 33 key landmarks on your body in real-time.
*   **Rep Counter & Form Analyzer:** Tracks 7 different exercises across upper body, legs, and cardio:
    *   *Arms & Shoulders:* Bicep Curls, Lateral Raises, Front Raises, Shoulder Press
    *   *Legs:* Squats, Lunges
    *   *Cardio/Core:* High Knees
*   **Form Correction Alerts:** The app monitors your range of motion and gives you on-screen feedback if you aren't completing the full rep (like *"Squat deeper!"* or *"Curl higher!"*).
*   **AI Fitness Coach:** An interactive chat window powered by Gemini to ask for workout plans, diet tips, or healthy food replacements.
*   **Web Dashboard:** A clean, single-page web interface built using Flask, HTML, and CSS.


## How to Set Up & Run Formova

### Prerequisites
*   Python 3.8 to 3.11 installed.
*   A webcam connected to your computer.

### 1. Clone this repository
```bash
git clone https://github.com/your-username/formova.git
cd formova
```

### 2. Set up a Virtual Environment
```bash
# Create the environment
python -m venv venv

# Activate it (Mac/Linux):
source venv/bin/activate

# Activate it (Windows):
venv\Scripts\activate
```

### 3. Install the dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your API Keys
Copy the example template file:
```bash
cp OpenCV_AIworkout/.env.example OpenCV_AIworkout/.env
```
Open `OpenCV_AIworkout/.env` in your text editor and add your keys:
```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
FLASK_SECRET_KEY=create_some_random_secret_password
```

### 5. Start the Web Server
```bash
cd OpenCV_AIworkout
python app.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**!

