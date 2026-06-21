🎓 Face Recognition Attendance System

An intelligent attendance management system that automates student attendance tracking using Facial Recognition Technology. This project is built with Python, Streamlit, OpenCV, and Face Recognition libraries to provide a secure, efficient, and user-friendly attendance solution for educational institutions.

---

 📌 Overview

Traditional attendance systems are time-consuming and prone to errors. This project leverages facial recognition to automatically identify students and record attendance in real-time.

The system supports:

- Student Registration
- Teacher Registration & Approval
- Face Enrollment
- Automated Attendance Marking
- Attendance Reports
- User Management
- Analytics Dashboard

---

🚀 Features

 👨‍🎓 Student Module
- Student account registration
- Face image enrollment
- Secure login system
- View attendance history
- Profile management

 👨‍🏫 Teacher Module
- Teacher registration
- Teacher approval workflow
- Attendance monitoring
- Student management
- Attendance report generation

 🤖 Face Recognition
- Face detection using OpenCV
- Face encoding and recognition
- Multiple face image capture
- Real-time attendance marking
- Automatic attendance storage

 📊 Reports & Analytics
- Daily attendance reports
- Attendance statistics
- Student attendance tracking
- Data visualization dashboard

---

 🛠️ Tech Stack

| Technology | Purpose |
|------------|----------|
| Python | Backend Development |
| Streamlit | Web Application Interface |
| OpenCV | Image Processing |
| Face Recognition | Facial Recognition |
| SQLite | Database Management |
| Pandas | Data Handling |
| NumPy | Numerical Operations |
| Pillow | Image Processing |
| Plotly | Data Visualization |

---

 📂 Project Structure

```text
FaceRecognitionAttendance/
│
├── backend/
│   ├── authentication.py
│   ├── attendance.py
│   └── database.py
│
├── pages/
│   ├── 1_Register_Face.py
│   ├── 2_Mark_Attendance.py
│   ├── 3_Manage_Users.py
│   ├── 4_Reports.py
│   ├── 5_Data_Viewer.py
│   └── 6_Settings.py
│
├── utils/
│
├── data/
│   ├── students/
│   ├── attendance/
│   └── encodings/
│
├── screenshots/
│
├── streamlit_app.py
├── requirements_streamlit.txt
└── README.md
```

---

 ⚙️ Installation

1. Clone Repository

```bash
git clone https://github.com/yourusername/face-recognition-attendance.git
cd face-recognition-attendance
```

 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements_streamlit.txt
```

---

## ▶️ Run the Application

```bash
streamlit run streamlit_app.py
```

After running, open:

```text
http://localhost:8501
```

in your browser.

---

## 🔄 System Workflow

### Step 1: Register User
- Student or teacher creates an account.
- Personal information is stored securely.

### Step 2: Face Enrollment
- Capture multiple face images.
- Generate face encodings.
- Save encodings for future recognition.

### Step 3: Login
- User logs into the system.
- Authentication verifies credentials.

### Step 4: Attendance Marking
- Camera captures live image.
- Face is detected and recognized.
- Attendance is automatically recorded.

### Step 5: Reports
- Generate attendance reports.
- View attendance history and analytics.

---

## 📊 Dashboard Features

The dashboard provides:

- Total Students
- Total Teachers
- Attendance Statistics
- Present/Absent Count
- Attendance Trends
- Recent Attendance Logs

---

## 🔒 Security Features

- Password Authentication
- Role-Based Access Control
- Teacher Approval System
- Face Biometric Verification
- Secure Attendance Storage

---

## 📸 Screenshots

### Login Page

Add screenshot here:

```markdown
![Login](screenshots/login.png)
```

### Face Registration

```markdown
![Face Registration](screenshots/register_face.png)
```

### Attendance Marking

```markdown
![Attendance](screenshots/attendance.png)
```

### Dashboard

```markdown
![Dashboard](screenshots/dashboard.png)
```

---

## 🎯 Advantages

- Contactless attendance system
- Reduces proxy attendance
- Fast and accurate recognition
- User-friendly interface
- Real-time attendance tracking
- Scalable for educational institutions

---

## 🔮 Future Enhancements

- Email Notifications
- Mobile Application
- Cloud Database Integration
- Multi-Campus Support
- AI Anti-Spoofing Detection
- QR Code Backup Attendance
- Attendance Prediction Analytics

---

## 🧪 Testing

To test the application:

1. Register a student.
2. Capture face images.
3. Train face encodings.
4. Open attendance page.
5. Verify attendance is recorded automatically.

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a new feature branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Added new feature"
```

4. Push changes

```bash
git push origin feature-name
```

5. Create a Pull Request

---

## 📄 License

This project is developed for academic and educational purposes.

---

## 👨‍💻 Developer

**Hitarth Patel**

Bachelor of Computer Science

Face Recognition Attendance System Project

GitHub: https://github.com/hitarth-patel-hp


