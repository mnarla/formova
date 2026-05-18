from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import time
import mediapipe as mp
import PoseModule as pm
import threading
import queue
from chatbot import get_chatbot_response
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_key_fallback')

camera = None
detector = None
current_exercise = None
is_running = False
frame_queue = queue.Queue(maxsize=2)  
camera_thread = None
count_global = 0  
feedback_message = ""  
bad_form_counter = 0  
almost_top = False
missed_top = False
showed_feedback = False

def camera_worker():
    global camera, detector, current_exercise, is_running, frame_queue, count_global, feedback_message, bad_form_counter, almost_top, missed_top, showed_feedback
    
    count = 0
    dir = 0
    pTime = 0
    feedback_message = ""
    bad_form_counter = 0
    rep_good = False
    almost_top = False
    missed_top = False
    showed_feedback = False
    
    print(f"Camera worker started for exercise: {current_exercise}")
    
    while is_running:
        if not camera or not camera.isOpened():
            print("Camera not available, exiting camera worker")
            break
            
        success, img = camera.read()
        if not success:
            print("Failed to read from camera, exiting camera worker")
            break
            
        try:
            img = detector.findPose(img, False)
            lmList = detector.findPosition(img, False)

            if len(lmList) != 0:
                color = (255, 0, 255)
                angle = 0
                per = 0
                bar = 0

                if current_exercise == "curls":
                    angle = detector.findAngle(img, 12, 14, 16)  # Right arm
                    per = np.interp(angle, (40, 180), (100, 0))
                    bar = np.interp(angle, (40, 180), (100, 650))
                    # Near top logic
                    if 80 < per < 100:
                        almost_top = True
                    if per == 100:
                        almost_top = False
                        missed_top = False
                        showed_feedback = False
                    if almost_top and per < 50 and not showed_feedback:
                        missed_top = True
                        feedback_message = "Curl higher! Arm not fully flexed."
                        showed_feedback = True
                    # Rep Counting Logic for curls
                    if angle >= 170:
                        color = (0, 255, 0)
                        if dir == 0:
                            count += 0.5
                            dir = 1
                            rep_good = False
                            missed_top = False
                            almost_top = False
                            showed_feedback = False
                            feedback_message = ""
                    if angle <= 50:
                        color = (0, 255, 0)
                        if dir == 1:
                            count += 0.5
                            dir = 0
                            rep_good = False
                            missed_top = False
                            almost_top = False
                            showed_feedback = False
                            feedback_message = ""
                    if angle <= 60:
                        rep_good = True
                    count_global = int(count)

                elif current_exercise == "lateral_raises":
                    try:
                        # Check if we have enough landmarks
                        if len(lmList) < 27: 
                            feedback_message = "Please make sure your full body is visible in the camera"
                            per = 0
                            bar = 650
                        else:
                            left_arm_angle = detector.findAngle(img, 24, 12, 14)
                            right_arm_angle = detector.findAngle(img, 23, 11, 13)
                            left_hip_angle = detector.findAngle(img, 26, 24, 12)
                            right_hip_angle = detector.findAngle(img, 25, 23, 11)
                            
                            if left_hip_angle >= 158 and right_hip_angle >= 158:
                                arm_angle = min(left_arm_angle, right_arm_angle)
                                per = np.interp(arm_angle, (20, 120), (0, 100))
                                bar = np.interp(arm_angle, (20, 120), (650, 100))
                                
                                # Rep Counting Logic for lateral raises
                                if arm_angle >= 110: 
                                    color = (0, 255, 0)
                                    if dir == 0:
                                        count += 0.5
                                        dir = 1
                                        rep_good = False
                                        feedback_message = ""
                                if arm_angle <= 30:  # Arms down
                                    color = (0, 255, 0)
                                    if dir == 1:
                                        count += 0.5
                                        dir = 0
                                        rep_good = False
                                        feedback_message = ""
                            else:
                                per = 0
                                bar = 650  # Posture incorrect, so no movement
                                feedback_message = "Stand straight with arms at your sides"
                                
                            if arm_angle <= 40:
                                rep_good = True
                            # Feedback logic
                            if arm_angle > 100:  
                                bad_form_counter += 1
                                if bad_form_counter >= 4:
                                    feedback_message = "Raise arms higher! Arm angle not high enough."
                            else:
                                bad_form_counter = 0
                                feedback_message = ""
                    except Exception as e:
                        print(f"Error in lateral raises: {str(e)}")
                        feedback_message = "Error detecting pose. Please try again."
                        per = 0
                        bar = 650
                    count_global = int(count)

                elif current_exercise == "front_raises":
                    angle = detector.findAngle(img, 24, 12, 16)
                    per = np.interp(angle, (70, 160), (0, 100))
                    bar = np.interp(angle, (70, 160), (650, 100))
                    
                    # Near top logic
                    if 80 < per < 100:
                        almost_top = True
                    if per == 100:
                        almost_top = False
                        missed_top = False
                        showed_feedback = False
                    if almost_top and per < 50 and not showed_feedback:
                        missed_top = True
                        feedback_message = "Raise arms higher! Not fully extended."
                        showed_feedback = True
                    
                    # Rep Counting Logic for front raises
                    if angle >= 150:  
                        color = (0, 255, 0)
                        if dir == 0:
                            count += 0.5
                            dir = 1
                            rep_good = False
                            missed_top = False
                            almost_top = False
                            showed_feedback = False
                            feedback_message = ""
                    if angle <= 80:  # Arms down
                        color = (0, 255, 0)
                        if dir == 1:
                            count += 0.5
                            dir = 0
                            rep_good = False
                            missed_top = False
                            almost_top = False
                            showed_feedback = False
                            feedback_message = ""
                            
                    if angle <= 90:
                        rep_good = True
                    count_global = int(count)

                elif current_exercise == "shoulder_press":
                    angle = detector.findAngle(img, 24, 12, 14)
                    per = np.interp(angle, (60, 170), (0, 100))
                    bar = np.interp(angle, (60, 170), (650, 100))
                    # Near top logic
                    if 80 < per < 100:
                        almost_top = True
                    if per == 100:
                        almost_top = False
                        missed_top = False
                        showed_feedback = False
                    if almost_top and per < 50 and not showed_feedback:
                        missed_top = True
                        feedback_message = "Press higher! Arm not fully extended."
                        showed_feedback = True
                    if angle >= 160:
                        rep_good = True
                    # Rep Counting Logic for shoulder press
                    if angle >= 160:
                        color = (0, 255, 0)
                        if dir == 0:
                            count += 0.5
                            dir = 1
                            rep_good = False
                            missed_top = False
                            almost_top = False
                            showed_feedback = False
                            feedback_message = ""
                    if angle <= 70:
                        color = (0, 255, 0)
                        if dir == 1:
                            count += 0.5
                            dir = 0
                            rep_good = False
                            missed_top = False
                            almost_top = False
                            showed_feedback = False
                            feedback_message = ""
                    count_global = int(count)

                elif current_exercise == "squats":
                    try:
                        # Check if we have enough landmarks
                        if len(lmList) < 29:  
                            feedback_message = "Please make sure your full body is visible in the camera"
                            per = 0
                            bar = 650
                        else:
                            # Calculate angles for both legs
                            right_leg_angle = detector.findAngle(img, 23, 25, 27)
                            
                            # Debug information
                            cv2.putText(img, f"Angle: {int(right_leg_angle)}", (50, 200), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                            
                            per = np.interp(right_leg_angle, (180, 330), (0, 100))
                            bar = np.interp(right_leg_angle, (180, 330), (650, 100))
                            
                            # Near top logic
                            if 80 < per < 100:
                                almost_top = True
                            if per == 100:
                                almost_top = False
                                missed_top = False
                                showed_feedback = False
                            if almost_top and per < 50 and not showed_feedback:
                                missed_top = True
                                feedback_message = "Squat deeper! Not low enough."
                                showed_feedback = True
                            if right_leg_angle >= 315:  
                                rep_good = True
                            # Rep Counting Logic for squats
                            if right_leg_angle <= 190:  # Standing position
                                color = (0, 255, 0)
                                if dir == 0:
                                    count += 0.5
                                    dir = 1
                                    rep_good = False
                                    missed_top = False
                                    almost_top = False
                                    showed_feedback = False
                                    feedback_message = ""
                            if right_leg_angle >= 315:  
                                color = (0, 255, 0)
                                if dir == 1:
                                    count += 0.5
                                    dir = 0
                                    rep_good = False
                                    missed_top = False
                                    almost_top = False
                                    showed_feedback = False
                                    feedback_message = ""
                    except Exception as e:
                        print(f"Error in squats: {str(e)}")
                        feedback_message = "Error detecting pose. Please try again."
                        per = 0
                        bar = 650
                    count_global = int(count)

                elif current_exercise == "lunges":
                    try:
                        # Check if we have enough landmarks
                        if len(lmList) < 29: 
                            feedback_message = "Please make sure your full body is visible in the camera"
                            per = 0
                            bar = 650
                        else:
                            # Calculate right leg angle
                            right_leg_angle = detector.findAngle(img, 23, 25, 27)
                            
                            # Debug information
                            cv2.putText(img, f"Angle: {int(right_leg_angle)}", (50, 200), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                            
                            per = np.interp(right_leg_angle, (180, 240), (0, 100))
                            bar = np.interp(right_leg_angle, (180, 240), (650, 100))
                            
                            # Near top logic
                            if 80 < per < 100:
                                almost_top = True
                            if per == 100:
                                almost_top = False
                                missed_top = False
                                showed_feedback = False
                            if almost_top and per < 50 and not showed_feedback:
                                missed_top = True
                                feedback_message = "Lunge deeper! Not low enough."
                                showed_feedback = True
                            if right_leg_angle >= 234:  
                                rep_good = True
                            # Rep Counting Logic for lunges
                            if right_leg_angle <= 190:  # Standing position
                                color = (0, 255, 0)
                                if dir == 0:
                                    count += 0.5
                                    dir = 1
                                    rep_good = False
                                    missed_top = False
                                    almost_top = False
                                    showed_feedback = False
                                    feedback_message = ""
                            if right_leg_angle >= 234:  
                                color = (0, 255, 0)
                                if dir == 1:
                                    count += 0.5
                                    dir = 0
                                    rep_good = False
                                    missed_top = False
                                    almost_top = False
                                    showed_feedback = False
                                    feedback_message = ""
                    except Exception as e:
                        print(f"Error in lunges: {str(e)}")
                        feedback_message = "Error detecting pose. Please try again."
                        per = 0
                        bar = 650
                    count_global = int(count)

                elif current_exercise == "high_knees":
                    try:
                        # Check if we have enough landmarks
                        if len(lmList) < 27:  
                            feedback_message = "Please make sure your full body is visible in the camera"
                            per = 0
                            bar = 650
                        else:
                            # Calculate both leg angles
                            right_leg_angle = detector.findAngle(img, 23, 25, 27)
                            left_leg_angle = detector.findAngle(img, 24, 26, 28)
                            
                            # Debug information
                            cv2.putText(img, f"R: {int(right_leg_angle)}", (50, 200), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                            cv2.putText(img, f"L: {int(left_leg_angle)}", (50, 250), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                            
                            # Calculate percentage 
                            right_per = np.interp(right_leg_angle, (180, 270), (0, 100))
                            left_per = np.interp(left_leg_angle, (180, 270), (0, 100))
                            per = max(right_per, left_per)
                            bar = np.interp(per, (0, 100), (650, 100))
                            
                            # Near top logic for either leg
                            if 80 < per < 100:
                                almost_top = True
                            if per == 100:
                                almost_top = False
                                missed_top = False
                                showed_feedback = False
                            if almost_top and per < 50 and not showed_feedback:
                                missed_top = True
                                feedback_message = "Lift knees higher!"
                                showed_feedback = True
                            
                            # Rep counting logic for alternating legs
                            if right_leg_angle >= 261 or left_leg_angle >= 261:  # Either knee at 90% height
                                color = (0, 255, 0)
                                if not rep_good:
                                    count += 0.5
                                    rep_good = True
                                    missed_top = False
                                    almost_top = False
                                    showed_feedback = False
                                    feedback_message = ""
                            elif right_leg_angle <= 190 and left_leg_angle <= 190:  # Both legs down
                                if rep_good:
                                    count += 0.5
                                    rep_good = False
                                    missed_top = False
                                    almost_top = False
                                    showed_feedback = False
                                    feedback_message = ""
                    except Exception as e:
                        print(f"Error in high_knees: {str(e)}")
                        feedback_message = "Error detecting pose. Please try again."
                        per = 0
                        bar = 650
                    count_global = int(count)

            # Progress Bar 
            cv2.rectangle(img, (1700, 100), (1775, 650), color, 3)
            cv2.rectangle(img, (1700, int(bar)), (1775, 650), color, cv2.FILLED)
            cv2.putText(img, f"PERCENTAGE: {int(per)}%", (1450, 75), cv2.FONT_HERSHEY_PLAIN, 3, color, 2)
            
            # FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime
            
            # Put the frame in the queue
            try:
                if frame_queue.full():
                    frame_queue.get_nowait()
                frame_queue.put_nowait(img)
            except queue.Full:
                pass
            except queue.Empty:
                pass
        except Exception as e:
            print(f"Error in camera worker: {str(e)}")
            continue

def generate_frames():
    print("Starting generate_frames")
    while is_running:
        try:
            img = frame_queue.get(timeout=1.0)
            
            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except queue.Empty:
            print("Frame queue is empty, waiting for frames...")
            continue
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            continue

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    print("Video feed requested")
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_exercise', methods=['POST'])
def start_exercise():
    global camera, detector, current_exercise, is_running, camera_thread, frame_queue, count_global
    
    # Get the selected exercise
    exercise = request.json.get('exercise')
    if not exercise:
        return jsonify({"error": "No exercise selected"}), 400
    
    # Stop any exercise
    if is_running:
        is_running = False
        if camera_thread and camera_thread.is_alive():
            camera_thread.join(timeout=2.0)
        if camera:
            camera.release()
            camera = None
    
    # Reset the rep counter
    count_global = 0
    
    # Clear the frame queue
    while not frame_queue.empty():
        try:
            frame_queue.get_nowait()
        except queue.Empty:
            break
    
    # Turn on camera and detector
    try:
        for camera_index in range(3):  
            camera = cv2.VideoCapture(camera_index)
            if camera.isOpened():
                ret, _ = camera.read()
                if ret:
                    print(f"Camera opened successfully with index {camera_index}")
                    break
                else:
                    camera.release()
                    camera = None
            else:
                camera = None
        
        if not camera or not camera.isOpened():
            return jsonify({"error": "Failed to open camera"}), 500
            
        detector = pm.poseDetector()
        current_exercise = exercise
        is_running = True
        
        # Start the camera thread
        camera_thread = threading.Thread(target=camera_worker)
        camera_thread.daemon = True
        camera_thread.start()
        
        return jsonify({"status": "success", "exercise": exercise})
    except Exception as e:
        print(f"Error starting exercise: {str(e)}")
        if camera:
            camera.release()
            camera = None
        return jsonify({"error": f"Failed to start exercise: {str(e)}"}), 500

@app.route('/stop_exercise', methods=['POST'])
def stop_exercise():
    global camera, is_running, camera_thread
    
    is_running = False
    if camera_thread and camera_thread.is_alive():
        camera_thread.join(timeout=2.0)
    if camera:
        camera.release()
        camera = None
    
    return jsonify({"status": "success"})

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json.get('message')
    if not message:
        return jsonify({"error": "No message provided"}), 400
    return get_chatbot_response(message)

@app.route('/get_count')
def get_count():
    global count_global, current_exercise
    return jsonify({"count": count_global, "exercise": current_exercise})

@app.route('/get_feedback')
def get_feedback():
    global feedback_message
    return jsonify({"feedback": feedback_message})

if __name__ == '__main__':
    app.run(debug=True) 