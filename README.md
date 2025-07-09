# full-stack-rule-based-bad-posture-detection-app

A rule-based posture detection web application that evaluates recorded or webcam-captured videos to identify bad posture events (neck bending, back slouching, knee-over-toe) using MediaPipe and OpenCV.

### Tech Stack

## Frontend:

* React.js
* MediaRecorder API
* basic CSS

## Backend:

* FastAPI (Python)
* OpenCV
* MediaPipe Pose

## Deployment:

* Frontend: Vercel
* Backend: Render

## Features

* Upload existing video or record from webcam
* Detect and visualize bad posture:

  * ❌ Neck bent forward (angle > 30°)
  * ❌ Back too bent (angle < 150°)
  * ❌ Knee over toe (only when side-view is visible)
* Summary report with:

  * Total bad posture frames
  * Timestamps of issues
  * Issue count by body part
* Analyzed video with keypoint overlay, angles, and text feedback

## 📁 Project Structure

full-stack-rule-based-bad-posture-detection-app/
├── frontend/
│   └── (React app files)
├── backend/
│   ├── main.py
│   └── (models, utils, etc.)
└── README.md

### Setup Instructions (Run Locally)

## 1. Clone the Repo:

```bash
git clone https://github.com/mehekyadav/full-stack-rule-based-bad-posture-detection-app.git
cd full-stack-rule-based-bad-posture-detection-app
```

## 2. Start Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Start Frontend:

```bash
cd ../frontend
npm install
npm start
```

## 4. Open App:

Visit http://localhost:3000
> Ensure your webcam permissions are enabled.

## 🏠 Live App (Deployed)

**Frontend:** https://full-stack-rule-based-bad-posture-d.vercel.app/
**Backend:** https://full-stack-rule-based-bad-posture-bs2f.onrender.com

## 🎥 Demo Video
Watch the working demo:
**👉 [https://youtu.be/your-demo-link](https://youtu.be/your-demo-link)**


## Sample API Usage

**POST** `/analyze`

* Accepts: `multipart/form-data` with key `video`
* Returns JSON with:

  * `total_frames`
  * `bad_posture_frames`
  * `issue_counts`
  * `bad_posture_timestamps`
  * `video_url`

### Evaluation Highlights

## Rule-Based Logic:

* Angles computed using trigonometry and keypoint coordinates
* Visibility confidence filtering avoids false positives

## Code Structure:

* Modular backend and frontend separation
* Comments and clean function breakdowns

## Web App:

* Fully functional on both webcam and uploads
* Works on Chrome, Edge, Firefox

## Summary:

* Instant feedback + analyzed video + JSON summary

## Future Improvements

* Add right-side detection fallback
* Allow multiple users per session
* Posture correction suggestions
* Add download option for result videos

Built by Mahek Yadav
