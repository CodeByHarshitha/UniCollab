from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlalchemy.orm import Session
import json

from models import LoginRequest, ProfileData, ProjectCreate, SkillAddRequest, DBUser, DBProfile, DBProject, DBProjectMember, DBJoinRequest
from database import engine, Base, get_db

app = FastAPI(title="UniCollab API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

projects_db = [] # Keeping projects in memory for now as per prompt scope

@app.on_event("startup")
def startup_event():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Seed DB from CSV if users table is empty
    db = next(get_db())
    if db.query(DBUser).count() == 0:
        import csv
        import os
        csv_path = os.path.join(os.path.dirname(__file__), "test_users.csv")
        if os.path.exists(csv_path):
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    email = row['email'].strip()
                    password = row['password'].strip()
                    name = row['name'].strip()
                    db_user = DBUser(email=email, password=password, name=name)
                    db.add(db_user)
            db.commit()
            print("Seeded test_users.csv into SQLite.")

@app.get("/")
def read_root():
    return {"status": "UniCollab API is running with SQLite!"}

def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token. Please log out and log in again.")
    email = auth_header.split(" ")[1]
    db_user = db.query(DBUser).filter(DBUser.email == email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return db_user

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.email == request.email).first()
    if not db_user or db_user.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "message": "Login successful",
        "user": {
            "email": db_user.email, 
            "name": db_user.name, 
            "profile_completed": db_user.profile_completed
        },
        "token": db_user.email
    }

@app.get("/profile")
def get_profile(current_user: DBUser = Depends(get_current_user)):
    if not current_user.profile_completed or not current_user.profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    p = current_user.profile
    return {
        "full_name": p.full_name,
        "department": p.department,
        "course": p.course,
        "specialization": p.specialization,
        "year_of_study": p.year_of_study,
        "graduation_year": p.graduation_year,
        "skills": p.skills
    }

@app.post("/create-profile")
def create_profile(profile: ProfileData, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Update Full Name in User table dynamically if changed
    current_user.name = profile.name
    
    db_profile = current_user.profile
    if not db_profile:
        db_profile = DBProfile(user_id=current_user.id)
        db.add(db_profile)
        
    db_profile.full_name = profile.name
    db_profile.department = profile.department
    db_profile.course = profile.course
    db_profile.specialization = profile.specialization
    db_profile.year_of_study = profile.year_of_study
    db_profile.graduation_year = profile.graduation_year
    db_profile.skills = profile.skills
    
    current_user.profile_completed = True
    db.commit()
    
    return {
        "message": "Profile updated successfully", 
        "user": {"email": current_user.email, "name": current_user.name, "profile_completed": True}
    }

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).filter(DBUser.profile_completed == True).all()
    return [{"email": u.email, "name": u.name} for u in users]

@app.post("/skills")
def add_skills(req: SkillAddRequest, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    if not current_user.profile_completed or not current_user.profile:
        raise HTTPException(status_code=400, detail="Profile not created yet")
    
    current_user.profile.skills = req.skills
    db.commit()
    return {"message": "Skills updated successfully", "skills": current_user.profile.skills}

@app.get("/discover")
def discover(db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    if not current_user.profile_completed or not current_user.profile:
        return []
        
    my_skills = set(current_user.profile.skills)
    results = []
    
    # Find everyone else who completed their profile
    other_users = db.query(DBUser).filter(DBUser.id != current_user.id, DBUser.profile_completed == True).all()
    
    for u in other_users:
        u_skills = set(u.profile.skills) if u.profile else set()
        overlap = len(my_skills.intersection(u_skills))
        
        results.append({
            "user": {
                "email": u.email,
                "name": u.name,
                "department": u.profile.department if u.profile else "",
                "skills": list(u_skills)
            },
            "overlap_score": overlap
        })
        
    results.sort(key=lambda x: x["overlap_score"], reverse=True)
    return [{"user": r["user"], "score": r["overlap_score"]} for r in results]

@app.post("/project/create")
def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    db_project = DBProject(
        creator_id=current_user.id,
        title=project.title,
        description=project.description,
        required_skills=project.skills_needed,
        team_size=project.team_size
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    # Automatically add creator as a member
    member = DBProjectMember(
        project_id=db_project.id,
        user_id=current_user.id,
        role="Creator"
    )
    db.add(member)
    db.commit()
    
    return {"message": "Project created successfully!", "project_id": db_project.id}

@app.get("/project/list")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(DBProject).filter(DBProject.status == "Open").all()
    results = []
    for p in projects:
        results.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "required_skills": p.required_skills,
            "team_size": p.team_size,
            "current_members": len(p.members),
            "creator_name": p.creator.name,
            "creator_email": p.creator.email
        })
    return results

@app.get("/project/my")
def my_projects(db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Fetch projects created by this user
    projects = db.query(DBProject).filter(DBProject.creator_id == current_user.id).all()
    results = []
    for p in projects:
        pending_requests = db.query(DBJoinRequest).filter(
            DBJoinRequest.project_id == p.id,
            DBJoinRequest.status == "pending"
        ).count()
        
        results.append({
            "id": p.id,
            "title": p.title,
            "description": p.description[:100] + "..." if len(p.description) > 100 else p.description,
            "required_skills": p.required_skills,
            "team_size": p.team_size,
            "current_members": len(p.members),
            "pending_requests_count": pending_requests,
            "status": p.status
        })
    return results

@app.get("/project/{project_id}/status")
def project_status(project_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    p = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if p.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can view full status dashboard")

    members = []
    for m in p.members:
        members.append({
            "user_id": m.user.id,
            "name": m.user.name,
            "email": m.user.email,
            "role": m.role,
            "skills": m.user.profile.skills if m.user.profile else []
        })
        
    join_requests = []
    pending_reqs = db.query(DBJoinRequest).filter(
        DBJoinRequest.project_id == p.id, 
        DBJoinRequest.status == "pending"
    ).all()
    
    for r in pending_reqs:
        prof = r.requester.profile
        join_requests.append({
            "request_id": r.id,
            "user_id": r.requester.id,
            "name": r.requester.name,
            "email": r.requester.email,
            "department": prof.department if prof else "N/A",
            "year_of_study": prof.year_of_study if prof else "N/A",
            "skills": prof.skills if prof else []
        })

    return {
        "project": {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "required_skills": p.required_skills,
            "team_size": p.team_size,
            "status": p.status
        },
        "members": members,
        "join_requests": join_requests
    }

@app.post("/project/{project_id}/request")
def request_to_join(project_id: int, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    p = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if p.status != "Open":
        raise HTTPException(status_code=400, detail="This project is no longer accepting members")
        
    # Check if already a member
    is_member = db.query(DBProjectMember).filter(
        DBProjectMember.project_id == project_id,
        DBProjectMember.user_id == current_user.id
    ).first()
    if is_member:
        raise HTTPException(status_code=400, detail="You are already a member of this project")
        
    # Check if already requested
    existing_req = db.query(DBJoinRequest).filter(
        DBJoinRequest.project_id == project_id,
        DBJoinRequest.requester_id == current_user.id,
        DBJoinRequest.status == "pending"
    ).first()
    if existing_req:
        raise HTTPException(status_code=400, detail="You have already requested to join this project")
        
    req = DBJoinRequest(
        project_id=project_id,
        requester_id=current_user.id
    )
    db.add(req)
    db.commit()
    
    return {"message": "Join request sent successfully!"}

@app.post("/project/{project_id}/request/{req_id}/respond")
def respond_to_request(project_id: int, req_id: int, action: str, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    p = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not p or p.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    req = db.query(DBJoinRequest).filter(DBJoinRequest.id == req_id, DBJoinRequest.project_id == project_id).first()
    if not req or req.status != "pending":
        raise HTTPException(status_code=404, detail="Request not found or already processed")
        
    if action == "accept":
        # Check team size
        current_members = len(p.members)
        if current_members >= p.team_size:
            p.status = "Team Full"
            db.commit()
            raise HTTPException(status_code=400, detail="Team is already full")
            
        req.status = "accepted"
        member = DBProjectMember(
            project_id=project_id,
            user_id=req.requester_id,
            role="Member"
        )
        db.add(member)
        
        # update status if full now
        if current_members + 1 >= p.team_size:
            p.status = "Team Full"
            
    elif action == "reject":
        req.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    db.commit()
    return {"message": f"Request {action}ed successfully"}
