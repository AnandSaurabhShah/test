import os
import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from google.generativeai import GenerativeModel
import google.generativeai as genai  
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learnempower.db'
db = SQLAlchemy(app)

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = GenerativeModel('gemini-2.0-flash')

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    language = db.Column(db.String(10), default='en')
    skills = db.Column(db.JSON)
    progress = db.Column(db.JSON)
    job_preferences = db.Column(db.JSON)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    language = db.Column(db.String(10))
    difficulty = db.Column(db.String(20))

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    company = db.Column(db.String(100))
    requirements = db.Column(db.JSON)
    remote = db.Column(db.Boolean)

# AI-Powered Learning Engine
class LearningPathGenerator:
    def __init__(self):
        self.skill_graph = {
            'digital_literacy': ['basic_computing', 'internet_skills'],
            'advanced_skills': ['graphic_design', 'data_entry']
        }

    def generate_path(self, user):
        prompt = f"""
        Create personalized learning path for {user.language}-speaking user with skills: {user.skills}.
        Focus on remote job skills. Structure in JSON format with courses and milestones.
        """
        response = model.generate_content(prompt)
        return self._validate_response(response.text)

    def _validate_response(self, response):
        try:
            return json.loads(response)
        except:
            return default_learning_path()

# Multilingual Support System
class TranslationEngine:
    def translate_content(self, content, target_lang):
        prompt = f"Translate this learning content to {target_lang}:\n{content}"
        return model.generate_content(prompt).text

# Job Matching Algorithm
class JobMatcher:
    def match_jobs(self, user):
        prompt = f"""
        Match jobs for user with skills: {user.skills}, preferences: {user.job_preferences}.
        Consider remote opportunities. Return JSON with job IDs and match percentages.
        """
        response = model.generate_content(prompt)
        return json.loads(response.text)

# API Endpoints
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=hashed_password,
        language=data.get('language', 'en'),
        skills=data.get('skills', [])
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201

@app.route('/get-learning-path', methods=['POST'])
def get_learning_path():
    user = User.query.get(request.json['user_id'])
    generator = LearningPathGenerator()
    path = generator.generate_path(user)
    return jsonify(path)

@app.route('/translate-content', methods=['POST'])
def translate_content():
    content = request.json['content']
    target_lang = request.json['target_lang']
    translator = TranslationEngine()
    translated = translator.translate_content(content, target_lang)
    return jsonify({"translated_content": translated})

@app.route('/job-matches', methods=['POST'])
def get_job_matches():
    user = User.query.get(request.json['user_id'])
    matcher = JobMatcher()
    matches = matcher.match_jobs(user)
    return jsonify(matches)

# Progress Tracking System
@app.route('/update-progress', methods=['POST'])
def update_progress():
    user = User.query.get(request.json['user_id'])
    course_id = request.json['course_id']
    progress = request.json['progress']
    
    # Update user progress in database
    user.progress = user.progress or {}
    user.progress[course_id] = progress
    db.session.commit()
    
    # Generate AI feedback
    feedback_prompt = f"""
    Provide constructive feedback in {user.language} for progress update: {progress}
    Focus on encouragement and practical next steps.
    """
    feedback = model.generate_content(feedback_prompt).text
    
    return jsonify({"status": "updated", "feedback": feedback})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)