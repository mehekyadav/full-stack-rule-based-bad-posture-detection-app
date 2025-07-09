from fastapi import FastAPI, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import cv2
import mediapipe as mp
import numpy as np
import tempfile
import uuid
import os

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MediaPipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return angle if angle <= 180 else 360 - angle

@app.get("/")
def root():
    return {"message": "Backend is running successfully!"}

@app.post("/analyze")
async def analyze_video(request: Request, video: UploadFile = File(...)):
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(await video.read())
        temp_path = temp_file.name

    cap = cv2.VideoCapture(temp_path)
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read the video")

    height, width, _ = frame.shape
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    output_name = f"annotated_{uuid.uuid4().hex}.webm"
    output_path = f"./{output_name}"
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'vp80'), fps, (width, height))

    frame_num = 0
    bad_frames = 0
    issue_counter = {"Neck": 0, "Back": 0, "Knee": 0}
    bad_frame_times = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1
        timestamp = round(frame_num / fps, 2)

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(img_rgb)
        issues = []

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            def get_xy(i): return (lm[i].x, lm[i].y)

            hip = get_xy(mp_pose.PoseLandmark.LEFT_HIP.value)
            knee = get_xy(mp_pose.PoseLandmark.LEFT_KNEE.value)
            ankle = get_xy(mp_pose.PoseLandmark.LEFT_ANKLE.value)
            shoulder = get_xy(mp_pose.PoseLandmark.LEFT_SHOULDER.value)
            ear = get_xy(mp_pose.PoseLandmark.LEFT_EAR.value)

            back_angle = calculate_angle(shoulder, hip, knee)
            if back_angle < 150:
                issues.append("Back too bent (<150°)")
                issue_counter["Back"] += 1

            visibility_thresh = 0.5
            if (lm[mp_pose.PoseLandmark.LEFT_KNEE].visibility > visibility_thresh and
                lm[mp_pose.PoseLandmark.LEFT_ANKLE].visibility > visibility_thresh):

                if knee[0] > ankle[0]:  # Only for side-view detection
                    issues.append("Knee over toe")
                    issue_counter["Knee"] += 1

            neck_angle = calculate_angle(shoulder, ear, (ear[0], ear[1] - 0.2))
            if neck_angle > 30:
                issues.append("Neck bent forward")
                issue_counter["Neck"] += 1

            # Draw pose
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Draw labels
            keypoints = {
                "Ear": mp_pose.PoseLandmark.LEFT_EAR,
                "Shoulder": mp_pose.PoseLandmark.LEFT_SHOULDER,
                "Hip": mp_pose.PoseLandmark.LEFT_HIP,
                "Knee": mp_pose.PoseLandmark.LEFT_KNEE,
                "Ankle": mp_pose.PoseLandmark.LEFT_ANKLE
            }

            for label, idx in keypoints.items():
                pt = lm[idx]
                x, y = int(pt.x * width), int(pt.y * height)
                cv2.circle(frame, (x, y), 5, (255, 255, 255), -1)
                cv2.putText(frame, label, (x+5, y-5), cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 255, 255), 2)

            ear_pt = (int(ear[0] * width), int(ear[1] * height))
            shoulder_pt = (int(shoulder[0] * width), int(shoulder[1] * height))
            neck_tip = (int(ear[0] * width), int((ear[1] - 0.2) * height))

            cv2.line(frame, shoulder_pt, ear_pt, (0, 255, 255), 2)
            cv2.line(frame, ear_pt, neck_tip, (0, 255, 255), 2)

            neck_msg = f"Neck bent forward: {int(neck_angle)}°" if neck_angle > 30 else f"Neck OK: {int(neck_angle)}°"
            text_x = min(ear_pt[0] + 30, width - 200)
            text_y = max(ear_pt[1] - 40, 20)

            cv2.putText(frame, neck_msg, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if issues:
            bad_frames += 1
            bad_frame_times.append(timestamp)
            for i, msg in enumerate(issues):
                cv2.putText(frame, msg, (10, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Good posture", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Show frame info
        cv2.putText(frame, f"Frame: {frame_num} | Time: {timestamp:.2f}s", (10, height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        out.write(frame)

    cap.release()
    out.release()

    base_url = str(request.base_url).rstrip("/")
    summary = {
        "total_frames": frame_num,
        "bad_posture_frames": bad_frames,
        "issue_counts": issue_counter,
        "bad_posture_timestamps": bad_frame_times,
        "video_filename": output_name,
        "video_url": f"{base_url}/video/{output_name}"
    }

    return JSONResponse(content=summary)

# Serve annotated video
app.mount("/video", StaticFiles(directory="."), name="video")
