from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from models import LoginRequest, ProfileData, ProjectCreate, User, SkillAddRequest
from users import load_test_users, users_db, projects_db

app = FastAPI(title="UniCollab API - Test Version", version="1.0.0")

# Setup CORS for Frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for test deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    load_test_users()
    print(f"Loaded {len(users_db)} test users from CSV.")

@app.get("/")
def read_root():
    return {"status": "UniCollab API is running"}

@app.post("/login")
def login(request: LoginRequest):
    record = users_db.get(request.email)
    if not record or record["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {
        "message": "Login successful",
        "user": record["user"].dict(),
        "token": request.email # Using email as dummy token for this test version
    }

def get_current_user_from_header(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    email = auth_header.split(" ")[1]
    record = users_db.get(email)
    if not record:
        raise HTTPException(status_code=401, detail="Invalid session")
    return record["user"]

@app.post("/create-profile")
def create_profile(profile: ProfileData, request: Request):
    user = get_current_user_from_header(request)
    user.profile_data = profile
    user.name = profile.name
    user.profile_completed = True
    return {"message": "Profile updated successfully", "user": user.dict()}

@app.get("/users")
def get_users():
    return [record["user"].dict() for record in users_db.values() if record["user"].profile_completed]

@app.post("/skills")
def add_skills(req: SkillAddRequest, request: Request):
    user = get_current_user_from_header(request)
    if not user.profile_data:
        raise HTTPException(status_code=400, detail="Profile not created yet")
    user.profile_data.skills = req.skills
    return {"message": "Skills updated successfully", "skills": user.profile_data.skills}

@app.get("/discover")
def discover(request: Request):
    current = get_current_user_from_header(request)
    if not current.profile_data:
        return []
        
    my_skills = set(current.profile_data.skills)
    results = []
    
    for record in users_db.values():
        u = record["user"]
        if u.email == current.email or not u.profile_completed:
            continue
            
        u_skills = set(u.profile_data.skills)
        overlap = len(my_skills.intersection(u_skills))
        
        results.append({
            "user": u.dict(),
            "overlap_score": overlap
        })
        
    # Sort by overlap score descending
    results.sort(key=lambda x: x["overlap_score"], reverse=True)
    return [{"user": r["user"], "score": r["overlap_score"]} for r in results]

@app.post("/project/create")
def create_project(project: ProjectCreate, request: Request):
    user = get_current_user_from_header(request)
    p_dict = project.dict()
    p_dict["creator_name"] = user.name
    p_dict["creator_email"] = user.email
    user.created_projects.append(project)
    projects_db.append(p_dict)
    return {"message": "Project created successfully!", "project": p_dict}

@app.get("/project/list")
def list_projects():
    return projects_db
