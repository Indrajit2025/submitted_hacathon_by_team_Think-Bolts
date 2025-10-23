import pandas as pd
# This import will work correctly when you run it from your local machine
from app import app, db, Student, Company, JobPosting, StudentProject ,INDIAN_IT_CITIES
from werkzeug.security import generate_password_hash
import json
import random

# List of BPUT colleges to assign to students
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

def create_dummy_data():
    """
    Wipes the database and populates it with jobs from the CSV 
    and a set of 50 dummy students.
    """
    with app.app_context():
        print("Dropping all tables from the database...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()

        
        try:
            df = pd.read_csv('internship_posted_data.csv')
            print(f"Successfully loaded {len(df)} jobs from CSV.")
        except FileNotFoundError:
            print("ERROR: 'job_postings22 - Copy.csv' not found. Please make sure it's in the same directory.")
            return

        # --- Create Companies and Job Postings ---
        all_skills = set()
        companies_cache = {} # To avoid querying the DB repeatedly

        for index, row in df.iterrows():
            company_name = row['company']
            
            if company_name not in companies_cache:
                company = Company(
                    company_name=company_name,
                    email=f"{company_name.lower().replace(' ', '').replace('.', '')}@in.com",
                    password_hash=generate_password_hash('pass1234')
                )
                db.session.add(company)
                db.session.commit() # Commit to get the ID
                companies_cache[company_name] = company.id
            
            company_id = companies_cache[company_name]
            
            # Create Job Posting
            try:
                skills_list = [s.strip() for s in row['skills'].split(',')]
                all_skills.update(skills_list)
            except AttributeError:
                skills_list = [] 

            job = JobPosting(
                company_id=company_id,
                job_role=row['role'],
                required_skills=json.dumps(skills_list),
                location=random.choice(INDIAN_IT_CITIES),
                cgpa_required=float(row['cgpa_minimum']),
                description=f"Seeking a talented {row['role']} to join our team. Key skills include {row['skills']}."
            )
            db.session.add(job)

        print("Finished processing companies and job postings.")

        

        # Commit all students and jobs
        db.session.commit()
        print("\nDatabase has been successfully populated with dummy data! ✅")

if __name__ == '__main__':
    create_dummy_data()