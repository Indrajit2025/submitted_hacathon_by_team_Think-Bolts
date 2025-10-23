from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import random
import spacy
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


GEMINI_MODEL = None
MODEL_NAMES = [
    'gemini-2.0-flash-exp',     
    'gemini-2.0-flash',           
    'gemini-1.5-flash-latest',   
    'models/gemini-2.0-flash-exp',
    'models/gemini-1.5-flash',
]

for model_name in MODEL_NAMES:
    try:
        GEMINI_MODEL = genai.GenerativeModel(model_name)
        print(f"✅ Successfully loaded: {model_name}")
        break
    except Exception as e:
        print(f"❌ Failed to load {model_name}: {e}")
        continue

if not GEMINI_MODEL:
    print("⚠️ Warning: No Gemini model could be loaded!")






app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_super_secret_key_bput')
WHEREBY_API_KEY = os.getenv('WHEREBY_API_KEY', 'your_default_key')
                                                                     
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:pass1234@localhost/bput15')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)



generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
}
safety_settings = [
  {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
  {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]



class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(10), nullable=True)
    college = db.Column(db.String(200), nullable=False)
    registration_number = db.Column(db.String(10), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    cgpa = db.Column(db.Float, default=0.0)
    profile_photo = db.Column(db.String(100))
    skills = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    projects = db.relationship('StudentProject', backref='student', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='student', lazy=True, cascade='all, delete-orphan')
    certificates = db.relationship('Certificate', backref='student', lazy=True, cascade='all, delete-orphan')

class StudentProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    project_title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    github_link = db.Column(db.String(500))
    site_link = db.Column(db.String(500))
    youtube_link = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    logo = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    job_postings = db.relationship('JobPosting', backref='company', lazy=True, cascade='all, delete-orphan')

class JobPosting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_role = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    required_skills = db.Column(db.Text, nullable=False)
    cgpa_required = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary_min = db.Column(db.Float)
    salary_max = db.Column(db.Float)
    contact_email = db.Column(db.String(120))
    contact_mobile = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('JobApplication', backref='job_posting', lazy=True, cascade='all, delete-orphan')

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posting.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Applied') 
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
   
    messages = db.relationship('Message', backref='application', lazy=True, cascade='all, delete-orphan')
    video_room_url = db.Column(db.String(500), nullable=True)

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    sender_id = db.Column(db.Integer, nullable=False)
    sender_role = db.Column(db.String(20), nullable=False) 
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UniversityUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CollegeUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    college_name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

BPUT_COLLEGES = [
    "Raajdhani Engineering College, Bhubaneswar",
    "College of Engineering and Technology, Bhubaneswar (CETB)",
    "Indira Gandhi Institute of Technology, Sarang (IGIT)",
    "Silicon Institute of Technology, Bhubaneswar",
    "Trident Academy of Technology, Bhubaneswar",
    "Gandhi Engineering College, Bhubaneswar (GEC)",
    "CV Raman Global University, Bhubaneswar",
    "Orissa Engineering College, Bhubaneswar (OEC)",
]
SKILL_RESOURCES = {

    'python': 'https://www.youtube.com/watch?v=rfscVS0vtbw',
    'flask': 'https://www.youtube.com/watch?v=oQ5UfJqW5Jo',
    'pandas': 'https://www.youtube.com/watch?v=EhYC02PD_gc',
    'numpy': 'https://www.youtube.com/watch?v=YqUcT-BFUM0',
    'machine learning': 'https://www.youtube.com/watch?v=SQkaBIP2JoA',
    'javascript': 'https://www.youtube.com/watch?v=FtaQSdrl7YA',
    'react': 'https://www.youtube.com/watch?v=lAFbKzO-fss',
    'html': 'https://www.youtube.com/watch?v=kUMe1FH4CHE',
    'css': 'https://www.youtube.com/watch?v=OEV8gHsKqL4',
    'sql': 'https://www.youtube.com/watch?v=NTgejLheGeU',
    'c++': 'https://www.youtube.com/watch?v=vLnPwxZdW4Y',
    'java': 'https://www.youtube.com/watch?v=A74TOX803D0'
}
INDIAN_IT_CITIES = [
    "Bangalore", "Hyderabad", "Pune", "Chennai", "Gurgaon", 
    "Noida", "Mumbai", "Kolkata", "Ahmedabad", "Bhubaneswar", "Kochi"
]

@app.template_filter('fromjson')
def fromjson_filter(value):
    """A template filter to parse a JSON string."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return [] 

#                                          RECOMMENDATION    model   is hard   ( still   i will do it )



def get_recommendations(student_id):
    
    student = Student.query.get(student_id)
    if not student:
        return []

    all_jobs = JobPosting.query.all()
    applied_job_ids = {app.job_id for app in student.applications}
    
    if not all_jobs:
        return []

    
    try:
        student_skills_list = json.loads(student.skills) if student.skills else []
    except (json.JSONDecodeError, TypeError):
        student_skills_list = []
    student_skills_set = {s.lower().strip() for s in student_skills_list} 
    # --------------------------------------------------------------------------

    student_projects_text = ' '.join([p.description for p in student.projects if p.description])
    student_doc = f"{' '.join(student_skills_list)} {student_projects_text}"

    job_docs = []
    for job in all_jobs:
        skills = ' '.join(json.loads(job.required_skills) if job.required_skills else [])
        job_doc = f"{job.job_role} {job.description} {skills}"
        job_docs.append(job_doc)

    try:
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        corpus = [student_doc] + job_docs
        tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
        content_scores = cosine_sim[0]
    except ValueError:
        content_scores = [0] * len(all_jobs)

    recommendations = []
    num_projects = len(student.projects)

    for i, job in enumerate(all_jobs):
        if job.id not in applied_job_ids:
            
            content_score = content_scores[i] * 70
            
            cgpa_score = 0
            if student.cgpa and student.cgpa >= job.cgpa_required:
                cgpa_score = 10 
            
            project_score = min(num_projects * 10, 20)
           
            total_score = content_score + cgpa_score + project_score
            
          
            roadmap = []
            try:
                job_skills_list = json.loads(job.required_skills) if job.required_skills else []
            except (json.JSONDecodeError, TypeError):
                job_skills_list = []
                
            job_skills_set = {s.lower().strip() for s in job_skills_list} 
            
            missing_skills = list(job_skills_set - student_skills_set) 
            
            for skill in missing_skills:
                resource_link = SKILL_RESOURCES.get(skill) 
                if resource_link:
                    roadmap.append({
                        'skill': skill.capitalize(), 
                        'link': resource_link
                    })
            # -----------------------------------------------

            if total_score > 25:
                
                 recommendations.append({
                     'job': job, 
                     'score': round(total_score, 2),
                     'roadmap': roadmap  
                 })

    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:5]

def get_fit_score_for_application(student_id, job_id):
    
    student = Student.query.get(student_id)
    job = JobPosting.query.get(job_id)

    if not student or not job:
        return 0

    
    student_skills = ' '.join(json.loads(student.skills) if student.skills else [])
    student_projects_text = ' '.join([p.description for p in student.projects if p.description])
    student_doc = f"{student_skills} {student_projects_text}"

    job_skills = ' '.join(json.loads(job.required_skills) if job.required_skills else [])
    job_doc = f"{job.job_role} {job.description} {job_skills}"

    content_score_percentage = 0
    try:
        tfidf_vectorizer = TfidfVectorizer(stop_words='english')
        corpus = [student_doc, job_doc] 
        tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
        
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2]) 
        content_score_percentage = cosine_sim[0][0]
    except ValueError:
        content_score_percentage = 0 

   
    total_score = 0

   
    total_score += content_score_percentage * 100
    
   
    if student.cgpa and student.cgpa >= job.cgpa_required:
        total_score += 10
   
    num_projects = len(student.projects)
    total_score += min(num_projects * 10, 20) 

    return round(total_score, 2)

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')




def calculate_placement_stats(students):
    total_students = len(students)
    if total_students == 0:
        return {'total': 0, 'placed': 0, 'rate': 0.0}

    placed_student_ids = db.session.query(JobApplication.student_id)\
        .filter(JobApplication.student_id.in_([s.id for s in students]))\
        .filter(JobApplication.status == 'Accepted')\
        .distinct().count()

    rate = (placed_student_ids / total_students) * 100
    return {'total': total_students, 'placed': placed_student_ids, 'rate': round(rate, 1)}



@app.route('/update_application_status/<int:application_id>', methods=['POST'])
def update_application_status(application_id):
    if session.get('role') != 'company':
      
        return redirect(url_for('company_login'))

    application = JobApplication.query.get_or_404(application_id)
    job = JobPosting.query.get(application.job_id)

    if not job or job.company_id != session['user_id']:
        
        return redirect(url_for('company_profile'))

    new_status = request.form.get('status')
    if new_status == 'Accepted':
        application.status = 'Accepted'

        #                                 API CALL TO WHEREBY    📲 >  📳    i am tired 😒
        
        if not application.video_room_url:
            headers = {
                "Authorization": f"Bearer {WHEREBY_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "endDate": "2099-02-18T14:23:00.000Z",
                "fields": ["hostRoomUrl"],
            }
            response = requests.post("https://api.whereby.dev/v1/meetings", headers=headers, json=payload)

            if response.status_code == 201:
                data = response.json()
                application.video_room_url = data.get('roomUrl')
                flash('Applicant accepted and a video call room has been created.', 'success')
            else:
                flash('Applicant accepted, but failed to create a video room.', 'error')
        # ---------------------------

    elif new_status == 'Rejected':
        application.status = 'Rejected'
        flash('Applicant has been rejected.', 'success')

    else:
        flash('Invalid status update.', 'error')

    db.session.commit()
    return redirect(url_for('applicants', job_id=job.id))

@app.route('/chatbot_api', methods=['POST'])
def chatbot_api():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please type a message!"})

    if not GEMINI_MODEL:
        return jsonify({"reply": "Sorry, the chatbot is currently unavailable. Please try again later."})

    try:
    
        prompt = f"""You are ElevatR Assistant, a helpful placement chatbot for BPUT students. 
Be friendly, helpful, and concise.

User: {user_message}
Assistant:"""
        
      
        response = GEMINI_MODEL.generate_content(prompt)
        bot_reply = response.text.strip()
        
        return jsonify({"reply": bot_reply})
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return jsonify({"reply": "Sorry, I'm having trouble connecting. Please try again later."})
   

@app.route('/my_applications')
def my_applications():
    if session.get('role') != 'student':
        flash('Please log in to view your applications.', 'error')
        return redirect(url_for('student_login'))

    student_id = session['user_id']
    applications = JobApplication.query.filter_by(student_id=student_id).order_by(JobApplication.applied_at.desc()).all()

    return render_template('my_applications.html', applications=applications)

@app.route('/conversation/<int:application_id>', methods=['GET', 'POST'])
def conversation(application_id):
    if not session.get('logged_in'):
        return redirect(url_for('landing'))

    application = JobApplication.query.get_or_404(application_id)

 
    is_student_applicant = (session.get('role') == 'student' and application.student_id == session.get('user_id'))
    is_company_owner = (session.get('role') == 'company' and application.job_posting.company_id == session.get('user_id'))

    if not (is_student_applicant or is_company_owner):
        flash('You are not authorized to view this conversation.', 'error')
        return redirect(url_for('landing'))

    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            new_message = Message(
                application_id=application_id,
                sender_id=session['user_id'],
                sender_role=session['role'],
                content=content
            )
            db.session.add(new_message)
            db.session.commit()
        return redirect(url_for('conversation', application_id=application_id))

    messages = Message.query.filter_by(application_id=application_id).order_by(Message.timestamp.asc()).all()

    
    if session['role'] == 'student':
        other_party_name = application.job_posting.company.company_name
    else: 
        other_party_name = application.student.full_name

    return render_template('conversation.html', 
                           application=application, 
                           messages=messages, 
                           other_party_name=other_party_name)

@app.route('/student_profile')
def student_profile():
    if session.get('role') != 'student':
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('student_login'))
    
    student = Student.query.get(session['user_id'])
    projects = StudentProject.query.filter_by(student_id=student.id).all()
    
   
    try:
        student_skills = json.loads(student.skills) if student.skills else []
    except (json.JSONDecodeError, TypeError):
        student_skills = []

    recommendations = get_recommendations(student.id)
    certificates = Certificate.query.filter_by(student_id=student.id).order_by(Certificate.uploaded_at.desc()).all()
    
    return render_template('student_profile.html', 
                           student=student, 
                           projects=projects, 
                           skills=student_skills, 
                           recommendations=recommendations,
                           certificates=certificates)


@app.route('/resources')
def resources():
    return render_template('resources.html')


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
       
        college = request.form['college']
        registration_number = request.form['registration_number']
        
        password = request.form['password']
        
      
        if Student.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('student_register'))
        
        if Student.query.filter_by(registration_number=registration_number).first():
            flash('Registration number already exists.', 'error')
            return redirect(url_for('student_register'))
            
       
        hashed_password = generate_password_hash(password)
        
        
        new_student = Student(
            full_name=full_name,
            email=email,
          
            college=college,
            registration_number=registration_number,
            password_hash=hashed_password,  
            skills=json.dumps([]) 
        )
        
        db.session.add(new_student)
        db.session.commit()
        
       
        session['logged_in'] = True
        session['user_id'] = new_student.id
        session['role'] = 'student'
        session['full_name'] = new_student.full_name

        flash('Registration successful! Welcome to your profile.', 'success')
        return redirect(url_for('student_profile'))
    
    return render_template('student_register.html', colleges=BPUT_COLLEGES)

@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        student = Student.query.filter_by(email=email).first()
        
        if student and check_password_hash(student.password_hash, password):
            session['logged_in'] = True
            session['user_id'] = student.id
            session['role'] = 'student'
            session['full_name'] = student.full_name
            flash('Login successful!', 'success')
            return redirect(url_for('student_profile'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('student_login.html')

@app.route('/student_edit_profile', methods=['GET', 'POST'])
def student_edit_profile():
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    
    student = Student.query.get(session['user_id'])
    
    if request.method == 'POST':
        student.full_name = request.form['full_name']
        student.email = request.form['email']
        student.mobile = request.form['mobile']
        student.cgpa = float(request.form['cgpa'])
        
        skills_input = request.form.get('skills', '')
        skills_list = [s.strip() for s in skills_input.split(',') if s.strip()]
        student.skills = json.dumps(skills_list)
        
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"student_{student.id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                student.profile_photo = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))
    
    student_skills_str = ', '.join(json.loads(student.skills)) if student.skills else ""
    return render_template('student_edit_profile.html', student=student, skills=student_skills_str)


@app.route('/add_project', methods=['POST'])
def add_project():
    if session.get('role') != 'student':
        return redirect(url_for('landing'))
    
    if request.method == 'POST':
        project = StudentProject(
            student_id=session['user_id'],
            project_title=request.form['project_title'],
            description=request.form['description'],
            github_link=request.form.get('github_link'),
            site_link=request.form.get('site_link'),
            youtube_link=request.form.get('youtube_link')
        )
        db.session.add(project)
        db.session.commit()
        flash('Project added successfully!', 'success')

    return redirect(url_for('student_edit_profile'))

@app.route('/add_certificate', methods=['POST'])
def add_certificate():
    if session.get('role') != 'student':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('landing'))

    student_id = session['user_id']
    title = request.form.get('title')
    file = request.files.get('certificate_image')

    if not title or not file or not file.filename:
        flash('Certificate title and image are required.', 'error')
        return redirect(url_for('student_edit_profile'))

    if allowed_file(file.filename):
        filename = secure_filename(f"cert_{student_id}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_certificate = Certificate(
            student_id=student_id,
            title=title,
            filename=filename
        )
        db.session.add(new_certificate)
        db.session.commit()
        flash('Certificate added successfully!', 'success')
    else:
        flash('Invalid file type for certificate.', 'error')

    return redirect(url_for('student_edit_profile'))

@app.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    if session.get('role') != 'student':
        return redirect(url_for('landing'))
    
    project = StudentProject.query.get_or_404(project_id)
    if project.student_id != session['user_id']:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('student_profile'))
    
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted!', 'success')
    return redirect(url_for('student_edit_profile'))


@app.route('/all_internship_opportunity')
def all_internship_opportunity():
    if session.get('role') != 'student':
        flash('Please log in to view internship opportunities.', 'error')
        return redirect(url_for('student_login'))

    student_id = session['user_id'] 
    selected_location = request.args.get('location')
    page_title = "Browse Job & Internship Opportunities"
    jobs_with_scores = [] 
    if selected_location:
        
        all_jobs_in_location = JobPosting.query.filter_by(location=selected_location).order_by(JobPosting.created_at.desc()).all()
        page_title = f"Jobs in {selected_location}"
        for job in all_jobs_in_location:
            fit_score = get_fit_score_for_application(student_id, job.id)
            jobs_with_scores.append({'job': job, 'score': fit_score})
        
        jobs_with_scores.sort(key=lambda x: x['score'], reverse=True)

    else:
        
        recommendations = get_recommendations(student_id)
      
        jobs_with_scores = recommendations
        page_title = "Jobs Recommended For You"
       

    student = Student.query.get(student_id)
    applied_job_ids = {app.job_id for app in student.applications}

    return render_template('all_internship_opportunity.html',
                           jobs_with_scores=jobs_with_scores, 
                           applied_job_ids=applied_job_ids,
                           cities=INDIAN_IT_CITIES,
                           selected_location=selected_location,
                           page_title=page_title)


@app.route('/apply_job/<int:job_id>')
def apply_job(job_id):
    if session.get('role') != 'student':
        return redirect(url_for('student_login'))
    
    existing_application = JobApplication.query.filter_by(
        student_id=session['user_id'], 
        job_id=job_id
    ).first()
    
    if existing_application:
        flash('You have already applied for this job.', 'info')
        return redirect(request.referrer or url_for('all_internship_opportunity'))

    application = JobApplication(student_id=session['user_id'], job_id=job_id)
    db.session.add(application)
    db.session.commit()
    flash('Application submitted successfully!', 'success')
    return redirect(request.referrer or url_for('all_internship_opportunity'))



@app.route('/company_register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        company_name = request.form['company_name']
        email = request.form['email']
        password = request.form['password']
        
        if Company.query.filter_by(email=email).first() or Company.query.filter_by(company_name=company_name).first():
            flash('Email or company name already exists.', 'error')
            return redirect(url_for('company_register'))
        
        hashed_password = generate_password_hash(password)
        new_company = Company(company_name=company_name, email=email, password_hash=hashed_password)
        db.session.add(new_company)
        db.session.commit()
        
        session['logged_in'] = True
        session['user_id'] = new_company.id
        session['role'] = 'company'
        session['company_name'] = new_company.company_name

        flash('Registration successful! Welcome.', 'success')
        return redirect(url_for('company_profile'))

    return render_template('company_register.html')

@app.route('/company_login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        company = Company.query.filter_by(email=email).first()
        
        if company and check_password_hash(company.password_hash, password):
            session['logged_in'] = True
            session['user_id'] = company.id
            session['role'] = 'company'
            session['company_name'] = company.company_name
            flash('Login successful!', 'success')
            return redirect(url_for('company_profile'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('company_login.html')

@app.route('/company_profile')
def company_profile():
    if session.get('role') != 'company':
        return redirect(url_for('company_login'))
    
    company = Company.query.get(session['user_id'])
    jobs = JobPosting.query.filter_by(company_id=company.id).order_by(JobPosting.created_at.desc()).all()
    
    return render_template('company_profile.html', company=company, jobs=jobs)

@app.route('/company_edit_profile', methods=['GET', 'POST'])
def company_edit_profile():
    if session.get('role') != 'company':
        return redirect(url_for('company_login'))
        
    company = Company.query.get(session['user_id'])
    
    if request.method == 'POST':
        company.description = request.form.get('description', '')
        
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"company_{company.id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                company.logo = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('company_profile'))

    return render_template('company_edit_profile.html', company=company)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') != 'company':
        return redirect(url_for('company_login'))
        
    if request.method == 'POST':
        skills_input = request.form['required_skills']
        skills_list = [s.strip() for s in skills_input.split(',') if s.strip()]
        
        job = JobPosting(
            company_id=session['user_id'],
            job_role=request.form['job_role'],
            description=request.form.get('description', ''),
            required_skills=json.dumps(skills_list),
            cgpa_required=float(request.form['cgpa_required']),
            location=request.form['location'], # --- NEW ---
            salary_min=float(request.form.get('salary_min', 0) or 0),
            salary_max=float(request.form.get('salary_max', 0) or 0),
            contact_email=request.form.get('contact_email'),
            contact_mobile=request.form.get('contact_mobile')
        )
        
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('company_profile'))

    return render_template('post_job.html',cities=INDIAN_IT_CITIES)

@app.route('/applicants/<int:job_id>')
def applicants(job_id):
    if session.get('role') != 'company':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_login'))

    job = JobPosting.query.get_or_404(job_id)
    if job.company_id != session['user_id']:
        flash('You are not authorized to view applicants for this job.', 'error')
        return redirect(url_for('company_dashboard'))

   
    applications = JobApplication.query.filter_by(job_id=job_id).order_by(JobApplication.applied_at.asc()).all()
    

    applications_with_scores = []
    for app in applications:
        fit_score = get_fit_score_for_application(app.student_id, job_id)
        applications_with_scores.append({
            'application': app,
            'fit_score': fit_score
        })
    # -----------------------------------------------------------

    return render_template('applicants.html', job=job, applications_with_scores=applications_with_scores)

@app.route('/view_applicant/<int:student_id>')
def view_applicant(student_id):

    allowed_roles = {'company', 'college', 'university'}
    if session.get('role') not in allowed_roles:
        flash('You are not authorized to view this profile.', 'error')
        return redirect(url_for('landing')) 
    
    student = Student.query.get_or_404(student_id)
    projects = StudentProject.query.filter_by(student_id=student.id).all()
    student_skills = json.loads(student.skills) if student.skills else []
    certificates = Certificate.query.filter_by(student_id=student.id).order_by(Certificate.uploaded_at.desc()).all()


    return render_template('view_applicant.html', student=student, projects=projects, skills=student_skills, certificates=certificates)

@app.route('/university_register', methods=['GET', 'POST'])
def university_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        password = request.form['password']

        if UniversityUser.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('university_register'))

        hashed_password = generate_password_hash(password)
        new_user = UniversityUser(
            username=username, email=email, role=role, password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('university_login'))
    
    return render_template('university_register.html')

@app.route('/university_login', methods=['GET', 'POST'])
def university_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = UniversityUser.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['role'] = 'university'
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('university_dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('university_login.html')

@app.route('/university_dashboard')
def university_dashboard():
    if session.get('role') != 'university':
        flash('Please log in to access the university dashboard.', 'error')
        return redirect(url_for('university_login'))

    college_stats = []
    
    fake_company_participation = [random.randint(5, 15) for _ in BPUT_COLLEGES]
    fake_avg_package = [round(random.uniform(4.5, 8.5), 1) for _ in BPUT_COLLEGES]
   

    for i, college in enumerate(BPUT_COLLEGES):
       
        students = Student.query.filter_by(college=college).all()
        stats = calculate_placement_stats(students) 

        college_stats.append({
            'name': college,
            'total_students': stats['total'],
            'placed_students': stats['placed'],
            
            'companies_participated': fake_company_participation[i],
             'avg_package': fake_avg_package[i]
        })

    overall_placed = sum(cs['placed_students'] for cs in college_stats)
    overall_total = sum(cs['total_students'] for cs in college_stats)
    overall_rate = (overall_placed / overall_total * 100) if overall_total > 0 else 0

    return render_template('university_dashboard.html',
                           college_stats=college_stats,
                           overall_rate=round(overall_rate, 1))

@app.route('/university_dashboard/<college_name>')
def college_placement_details(college_name):
    if session.get('role') != 'university':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('university_login'))

    if college_name not in BPUT_COLLEGES:
        flash('Invalid college specified.', 'error')
        return redirect(url_for('university_dashboard'))

    students = Student.query.filter_by(college=college_name).order_by(Student.full_name).all()

    student_placement_data = []
    for student in students:
        
        accepted_app = JobApplication.query\
            .join(JobPosting, JobApplication.job_id == JobPosting.id)\
            .join(Company, JobPosting.company_id == Company.id)\
            .filter(JobApplication.student_id == student.id)\
            .filter(JobApplication.status == 'Accepted')\
            .add_columns(Company.company_name)\
            .first()

        student_placement_data.append({
            'info': student,
            'is_placed': bool(accepted_app),
            'company_name': accepted_app.company_name if accepted_app else None
        })

    return render_template('college_placement_details.html',
                           college_name=college_name,
                           student_data=student_placement_data)

@app.route('/college_register', methods=['GET', 'POST'])
def college_register():
    if request.method == 'POST':
        college_name = request.form['college_name']
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']
        password = request.form['password']

        if CollegeUser.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('college_register'))

        hashed_password = generate_password_hash(password)
        new_user = CollegeUser(
            college_name=college_name, username=username, email=email, role=role, password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('college_login'))
        
    return render_template('college_register.html', colleges=BPUT_COLLEGES)

@app.route('/college_login', methods=['GET', 'POST'])
def college_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = CollegeUser.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['role'] = 'college'
            session['username'] = user.username
            session['college_name'] = user.college_name
            flash('Login successful!', 'success')
            return redirect(url_for('college_dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('college_login.html')

@app.route('/college_dashboard')
def college_dashboard():
    if session.get('role') != 'college':
        flash('Please log in to access the college dashboard.', 'error')
        return redirect(url_for('college_login'))
    college_name = session['college_name']
    students = Student.query.filter_by(college=college_name).order_by(Student.full_name).all()
    student_data = []
    for student in students:
        applications = JobApplication.query.filter_by(student_id=student.id).all()
        placement_status = "N/A" 
        placed_company = None
        has_applied = False
        has_rejected = False

        if applications:
             has_applied = True 
             accepted_app = next((app for app in applications if app.status == 'Accepted'), None)
             if accepted_app:
                 placement_status = 'Accepted'
                 
                 job_posting = JobPosting.query.get(accepted_app.job_id)
                 if job_posting and job_posting.company: 
                     placed_company = job_posting.company.company_name
             else:
                 
                 if any(app.status == 'Rejected' for app in applications):
                      placement_status = 'Rejected'
                 else:
                      placement_status = 'Applied' 

        student_data.append({
            'info': student,
            'application_count': len(applications),
            'placement_status': placement_status,
            'placed_company': placed_company
           
        })

    return render_template('college_dashboard.html',
                           student_data=student_data,
                           college_name=college_name)
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('landing'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404                      # work part ends here 
                                             #now we are going to deploy this app              😱   

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)             # i am so tired , for to present on presentation ,                i am going to sleep but i need to fix the deployment issue 