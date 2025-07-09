
import React, { useRef, useState, useEffect } from "react";
import "./styles.css";

export default function App() {
  const [videoFile, setVideoFile] = useState(null);
  const [videoURL, setVideoURL] = useState("");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [stream, setStream] = useState(null);
  const [shouldAttachStream, setShouldAttachStream] = useState(false);
  const [mode, setMode] = useState("upload"); // or "record"

  const previewRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recordedChunks = useRef([]);

  const handleFileChange = (e) => {
    setVideoFile(e.target.files[0]);
  };

  const handleUpload = async (file) => {
    if (!file) return;
    setLoading(true);
    setVideoURL("");
    setSummary(null);

    const formData = new FormData();
    formData.append("video", file);

    try {
      const res = await fetch("https://full-stack-rule-based-bad-posture-bs2f.onrender.com/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setVideoURL(data.video_url);
      setSummary(data);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setLoading(false);
      setVideoFile(null); 
      if(mode === "upload"){
        document.getElementById("fileInput").value = ""; 
      }
    }
  };

  const startRecording = async () => {
    setSummary(null);
    setVideoURL("");
    setVideoFile(null);
    recordedChunks.current = [];

    const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
    setStream(mediaStream);

    setShouldAttachStream(true); 
    const mediaRecorder = new MediaRecorder(mediaStream, { mimeType: "video/webm" });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunks.current.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const blob = new Blob(recordedChunks.current, { type: "video/webm" });
      const file = new File([blob], "recorded.webm", { type: "video/webm" });

      await handleUpload(file);
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    setRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }

    if (previewRef.current) {
      previewRef.current.srcObject = null;
    }

    setRecording(false);
  };

  useEffect(() => {
    if (shouldAttachStream && stream && previewRef.current) {
      previewRef.current.srcObject = stream;
      previewRef.current.play().catch(err => console.error("preview play error:", err));
      setShouldAttachStream(false); 
    }
  }, [shouldAttachStream, stream]);

  useEffect(() => {
    setVideoFile(null);
    setSummary(null);
    setVideoURL("");
  }, [mode]);

  return (
    <div className="container">
      <h1>Posture Analysis App</h1>

      <label>Select Mode : </label>
      <select value={mode} onChange={(e) => setMode(e.target.value)} 
      style={{
        width: '200px',
        height: '25px',
        borderRadius: '5px',
        border: '2px solid blue', 
        padding: '2px'
      }}>
        <option value="upload">Upload Video</option>
        <option value="record">Record with Webcam</option>
      </select>

      {mode === "upload" && (
        <div>
          <input
            id="fileInput"
            type="file"
            accept="video/*"
            onClick={(e) => (e.target.value = null)}
            onChange={handleFileChange}
          />
          <button
            onClick={() => handleUpload(videoFile)}
            disabled={loading || recording}
          >
            Upload & Analyze
          </button>
        </div>
      )}

      {mode === "record" && (
        <div>
          {!recording ? (
            <button onClick={startRecording}>🎥 Start Webcam Recording</button>
          ) : (
            <button onClick={stopRecording}>🛑 Stop & Analyze</button>
          )}
        </div>
      )}


      <div className="content">
        <div>
          <h2>{recording ? "Live Preview" : "Analyzed Video"}</h2>
          <div className="video-section">
            {recording ? (
              <video
                ref={previewRef}
                autoPlay
                muted
                playsInline
                style={{ width: "100%", height: "100%", objectFit: "contain" }}
              />
            ) : (
              loading ? (
                <div className="overlay">
                  <div className="loader"></div>
                  <p>Analyzing video, please wait...</p>
                </div>
              ) :
                videoURL && (
                  <video
                    key={videoURL}
                    src={videoURL}
                    controls
                    style={{ width: "100%", height: "100%", objectFit: "contain" }}
                  />
                )
            )}
          </div>
        </div>

        {summary && (
          <div>
            <h2 style={{ "marginLeft": '20px' }}>Posture Summary</h2>
            <div className="summary-card">
              <p><strong>Total Frames:</strong> {summary.total_frames}</p>
              <p><strong>Bad Posture Frames:</strong> {summary.bad_posture_frames}</p>
              <p><strong>Issues Detected:</strong></p>
              <ul>
                {Object.entries(summary.issue_counts).map(([key, value]) => (
                  <li key={key}>{key}: {value} times</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
