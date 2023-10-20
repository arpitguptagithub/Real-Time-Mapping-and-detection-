# Description: This script is used to track objects in a video and send the location data to a web service or JavaScript file.
import cv2
import math
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

class EuclideanDistTracker:
    def __init__(self):
        # Store the center positions of the objects
        self.center_points = {}
        # Keep the count of the IDs
        # each time a new object id is detected, the count will increase by one
        self.id_count = 0

    def update(self, objects_rect):
        # Objects boxes and ids
        objects_bbs_ids = []

        # Get the center point of new objects
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            # Find out if that object was detected already
            lat , long = geocode(cx,cy)
            same_object_detected = False
            for object_id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < 25:
                    self.center_points[object_id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h, object_id])
                    same_object_detected = True
                    break

            # If a new object is detected, we assign a new ID to that object
            if not same_object_detected:
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                self.id_count += 1

        # Clean the dictionary by center points to remove IDs that are not used anymore
        new_center_points = {}
        for obj_bb_id in objects_bbs_ids:
            _, _, _, _, object_id = obj_bb_id
            center = self.center_points[object_id]
            new_center_points[object_id] = center

        # Update the dictionary with removed unused IDs
        self.center_points = new_center_points.copy()
        return objects_bbs_ids
    
    def geocode(self, x, y):
        # Send location data to a web service or JavaScript file
       
        api_key = "YOUR_API_KEY"
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": f"{x}, {y}",
            "key": api_key
        }

        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                lat, lng = location["lat"], location["lng"]
                return lat, lng
        return None
    

# Create a tracker object
tracker = EuclideanDistTracker()

@app.route("/receive_location", methods=["POST"])
def receive_location():
    data = request.get_json()
    latitude = data["latitude"]
    longitude = data["longitude"]
    truck_center_x = data["truck_center_x"]
    truck_center_y = data["truck_center_y"]

    lat, lng = tracker.geocode(truck_center_x, truck_center_y)
    print("Latitude: {lat}, Longitude: {lng}")
    print("Successfully received location data.")

    return jsonify({"success": True})


cap = cv2.VideoCapture("highway.mp4")

# Object detection from a stable camera
object_detector = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=40)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width, _ = frame.shape

    # Extract Region of Interest (ROI)
    roi = frame[340:720, 500:800]

    # 1. Object Detection
    mask = object_detector.apply(roi)
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    detections = []
    for cnt in contours:
        # Calculate area and remove small elements
        area = cv2.contourArea(cnt)
        if area > 100:
            x, y, w, h = cv2.boundingRect(cnt)
            detections.append([x, y, w, h])

    # 2. Object Tracking
    boxes_ids = tracker.update(detections)
    for box_id in boxes_ids:
        x, y, w, h, object_id = box_id
        cv2.putText(roi, str(object_id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)

    cv2.imshow("roi", roi)
    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(30)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()

if __name__ == "__main__":
    app.run(debug=True)
