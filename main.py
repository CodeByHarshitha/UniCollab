from fastapi import FastAPI, Form, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import json
from matching_engine import get_top_matches
from database import engine, get_db
import models

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UniCollab")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# The get_db function is already imported from database.py.
# The instruction implies adding get_total_new_requests after a get_db definition,
# but since it's imported, we'll place it after the templates definition and before dummy_users,
# which is a logical place for utility functions related to DB access.

def get_total_new_requests(db: Session, user_email: str) -> int:
    """Gets the count of pending join requests for all projects created by the user."""
    count = (
        db.query(models.JoinRequest)
        .join(models.Project, models.JoinRequest.project_id == models.Project.project_id)
        .filter(models.Project.creator_id == user_email)
        .filter(models.JoinRequest.status == "pending")
        .count()
    )
    return count

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

dummy_users = {
  "harshitha@srmist.edu.in": "12345",
  "maneesh@srmist.edu.in": "abc123",
  "student@srmist.edu.in": "password"
}

# In-memory storage for user profiles and skills
dummy_profiles = {}
dummy_skills = {}
dummy_interests = {}
dummy_looking_for = {}
dummy_requests = [] # List of dicts: {"id": int, "sender_email": str, "receiver_email": str, "message": str, "status": str}
request_id_counter = 1

dummy_projects = [] # {"id": int, "creator_email": str, "title": str, "type": str, "skills": list, "team_size": int, "description": str, "members": list[str]}
dummy_project_requests = [] # {"id": int, "project_id": int, "sender_email": str, "status": str}
project_id_counter = 1
project_request_id_counter = 1

dummy_ideas = [] # {"id": int, "creator_email": str, "title": str, "category": str, "skills": list, "team_size": int, "description": str, "members": list[str]}
idea_id_counter = 1

dummy_tasks = [] # {"id": int, "project_id": int, "title": str, "status": str} # statuses: "todo", "in_progress", "completed"
task_id_counter = 1

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Clean up any accidental trailing/leading spaces especially from auto-fill
    clean_email = email.strip()
    
    # Print what the server actually got to the terminal for debugging
    print(f"Login attempt received - Email: '{clean_email}', Password: '{password}'")

    if not clean_email.endswith("@srmist.edu.in"):
        return {"error": "Only SRM emails allowed"}

    # Fallback checking dummy_users for simplicity if not in DB yet
    if clean_email not in dummy_users:
        print(f"Email '{clean_email}' not found in dummy_users.")
        return {"error": "Invalid email or password"}

    if dummy_users[clean_email] != password:
        print(f"Password mismatch for '{clean_email}'. Expected '{dummy_users[clean_email]}', got '{password}'")
        return {"error": "Invalid email or password"}

    print(f"Login successful for '{clean_email}'")
    
    # Fetch user from DB or create if doesn't exist (simulating signup/login for this demo)
    user = db.query(models.User).filter(models.User.email == clean_email).first()
    if not user:
         user = models.User(email=clean_email, password=password)
         db.add(user)
         db.commit()
         db.refresh(user)
         
    # Explicitly check for Profile existence to trigger onboarding
    has_profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first() is not None
    
    # Create a redirect response instead of JSON dict, to securely set a browser cookie
    # See https://fastapi.tiangolo.com/advanced/response-cookies/
    target_url = "/dashboard" if has_profile else "/edit-profile"
    response = RedirectResponse(url=target_url, status_code=303)
    response.set_cookie(key="user_email", value=clean_email, httponly=True)
    return response

@app.get("/logout")
async def logout(response: Response):
    # Simply redirects back to login and clears the cookie
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_email")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    # Retrieve the user email from cookies to verify they are logged in
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    has_profile = profile is not None
    
    skills = []
    if has_profile and profile.skills:
        skills = profile.skills.split(",")
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "email": user_email,
        "has_profile": has_profile,
        "profile": profile, # This is now a SQLAlchemy object or None
        "skills": skills,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "dashboard"
    })

@app.get("/edit-profile", response_class=HTMLResponse)
async def edit_profile_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    
    # Pre-fill form if profile exists
    return templates.TemplateResponse("edit_profile.html", {"request": request, "email": user_email, "profile": profile})

@app.post("/edit-profile")
async def edit_profile_post(
    request: Request,
    full_name: str = Form(...),
    year_of_study: str = Form(...),
    department: str = Form(...),
    course: str = Form(...),
    specialization: str = Form(...),
    graduation_year: str = Form(...),
    skills: str = Form(""), # Comma-separated
    db: Session = Depends(get_db)
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    user = db.query(models.User).filter(models.User.email == user_email).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first()
    
    clean_skills = ""
    if skills:
        clean_skills = ",".join([s.strip() for s in skills.split(",") if s.strip()])
    
    if profile:
        profile.full_name = full_name
        profile.year_of_study = year_of_study
        profile.department = department
        profile.course = course
        profile.specialization = specialization
        profile.graduation_year = graduation_year
        profile.skills = clean_skills
    else:
        profile = models.Profile(
            user_id=user.id,
            full_name=full_name,
            year_of_study=year_of_study,
            department=department,
            course=course,
            specialization=specialization,
            graduation_year=graduation_year,
            skills=clean_skills
        )
        db.add(profile)
        
    db.commit()
    
    # Redirect to profile view with success query param
    return RedirectResponse(url="/profile?updated=true", status_code=303)

@app.get("/profile", response_class=HTMLResponse)
async def view_profile_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    user = db.query(models.User).filter(models.User.email == user_email).first()
    profile = db.query(models.Profile).filter(models.Profile.user_id == user.id).first() if user else None
    
    # If no profile, they must be new and forced to create it
    if not profile:
        return RedirectResponse(url="/edit-profile", status_code=303)
        
    skills_list = profile.skills.split(",") if profile.skills else []
    
    updated = request.query_params.get("updated") == "true"
    
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "email": user_email,
        "profile": profile,
        "skills": skills_list,
        "updated": updated,
        "total_new_requests": get_total_new_requests(db, user_email)
    })

import json
import os

@app.get("/skills", response_class=HTMLResponse)
async def skills_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Ensure profile was created before proceeding to skills
    if user_email not in dummy_profiles:
        return RedirectResponse(url="/create-profile", status_code=303)
        
    # Read the skills.json file
    predefined_skills = []
    skills_file_path = "skills.json"
    if os.path.exists(skills_file_path):
        with open(skills_file_path, "r") as f:
            predefined_skills = json.load(f)
            
    # Load any existing skills user might have already added
    user_skills = dummy_skills.get(user_email, [])
            
    return templates.TemplateResponse("skills.html", {
        "request": request, 
        "email": user_email,
        "predefined_skills": predefined_skills,
        "user_skills": user_skills
    })

@app.post("/skills")
async def skills_post(
    request: Request,
    skills: str = Form("") # We'll expect a comma-separated list of skills from a hidden input
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Process the skills (they come in as a comma-separated string)
    skill_list = [s.strip() for s in skills.split(",")] if skills else []
    
    # Store them
    dummy_skills[user_email] = skill_list
    
    # Send user to the new interests page
    return RedirectResponse(url="/interests", status_code=303)

@app.get("/interests", response_class=HTMLResponse)
async def interests_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    return templates.TemplateResponse("interests.html", {"request": request, "email": user_email})

@app.post("/interests")
async def interests_post(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Using form data parsing directly from request since we have dynamic multiple selected checkboxes
    form_data = await request.form()
    
    # Extract all checkbox values with name 'interests' and 'looking_for'
    interests = form_data.getlist("interests")
    looking_for = form_data.getlist("looking_for")
    
    dummy_interests[user_email] = interests
    dummy_looking_for[user_email] = looking_for
    
    return RedirectResponse(url="/discover", status_code=303)

# Dummy users for the Discover page
discover_users = [
    {
        "email": "maneesh@srmist.edu.in",
        "name": "Maneesh",
        "skills": ["Python", "React"],
        "interests": ["Web Development"],
        "looking_for": ["Hackathon Teammates"]
    },
    {
        "email": "aisha@srmist.edu.in",
        "name": "Aisha",
        "skills": ["Machine Learning", "OpenCV"],
        "interests": ["Artificial Intelligence"],
        "looking_for": ["Research Partner"]
    }
]

@app.get("/discover", response_class=HTMLResponse)
async def discover_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
    
    # Filter out the current user so they don't see themselves
    other_users = [u for u in discover_users if u["email"] != user_email]
    
    return templates.TemplateResponse("discover.html", {
        "request": request, 
        "email": user_email,
        "users": other_users,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "discover"
    })

@app.post("/request-collaboration")
async def request_collaboration(
    request: Request,
    receiver_email: str = Form(...),
    message: str = Form("")
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    global request_id_counter
    
    new_request = {
        "id": request_id_counter,
        "sender_email": user_email,
        "receiver_email": receiver_email,
        "message": message,
        "status": "pending"
    }
    dummy_requests.append(new_request)
    request_id_counter += 1
    
    # Redirect back to discover page (could optionally add a success message parameter)
    return RedirectResponse(url="/discover", status_code=303)

@app.get("/requests", response_class=HTMLResponse)
async def requests_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Aggregate all "pending" requests for projects created by this user
    db_incoming_requests = (
        db.query(models.JoinRequest, models.Project)
        .join(models.Project, models.JoinRequest.project_id == models.Project.project_id)
        .filter(models.Project.creator_id == user_email)
        .filter(models.JoinRequest.status == "pending")
        .all()
    )
    
    incoming_requests = []
    for req, proj in db_incoming_requests:
        sender_name = req.requester_id.split("@")[0].capitalize()
        sender_dept = "Unknown"
        sender_year = "Unknown"
        sender_skills = []
        
        # Check DB for Profile info
        sender_user = db.query(models.User).filter(models.User.email == req.requester_id).first()
        if sender_user:
            sender_prof = db.query(models.Profile).filter(models.Profile.user_id == sender_user.id).first()
            if sender_prof:
                sender_name = sender_prof.full_name
                sender_dept = sender_prof.department
                sender_year = sender_prof.year_of_study
                if sender_prof.skills:
                    sender_skills = sender_prof.skills.split(",")
                    
        # Fallback to dummy_profiles if DB profile is missing but they exist in dummy
        if req.requester_id in dummy_profiles and sender_name == req.requester_id.split("@")[0].capitalize():
            prof = dummy_profiles[req.requester_id]
            sender_name = prof.get("full_name", sender_name)
            sender_dept = prof.get("department", sender_dept)
            sender_year = prof.get("year_of_study", sender_year)
            sender_skills = dummy_skills.get(req.requester_id, [])
            
        incoming_requests.append({
            "request_id": req.request_id,
            "project_title": proj.title,
            "sender_email": req.requester_id,
            "sender_name": sender_name,
            "sender_department": sender_dept,
            "sender_year": sender_year,
            "sender_skills": sender_skills
        })

    return templates.TemplateResponse("requests.html", {
        "request": request, 
        "email": user_email,
        "incoming_requests": incoming_requests,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "requests"
    })

@app.post("/respond-request")
async def respond_request(
    request: Request,
    request_id: int = Form(...),
    action: str = Form(...) # expected 'accept' or 'decline'
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    for req in dummy_requests:
        if req["id"] == request_id and req["receiver_email"] == user_email:
            if action == 'accept':
                req["status"] = "accepted"
            elif action == 'decline':
                req["status"] = "declined"
            break
            
    return RedirectResponse(url="/requests", status_code=303)

@app.get("/create-project", response_class=HTMLResponse)
async def create_project_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
    
    # Load available skills for the multi-select dropdown
    try:
        with open("skills.json", "r") as f:
            all_skills = json.load(f)
    except Exception:
        all_skills = {
            "technical": ["Python", "JavaScript", "React", "AI/ML"],
            "soft": ["Leadership", "Communication"]
        }
    
    # Generate Top Matches for Smart Team Builder
    top_matches = get_top_matches(
        user_email, 
        dummy_profiles, 
        dummy_skills, 
        dummy_interests, 
        dummy_looking_for
    )
    # Give them top 3 suggestions
    suggested_teammates = top_matches[:3]
            
    return templates.TemplateResponse("create_project.html", {
        "request": request, 
        "email": user_email,
        "skills": all_skills,
        "suggestions": suggested_teammates
    })

@app.post("/create-project")
async def create_project_post(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    form_data = await request.form()
    
    selected_skills = form_data.getlist("skills")
    
    new_project = models.Project(
        creator_id=user_email,
        title=form_data.get("title"),
        description=form_data.get("description"),
        required_skills=",".join(selected_skills) if selected_skills else "",
        team_size=int(form_data.get("team_size", 4))
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    creator_member = models.ProjectMember(
        project_id=new_project.project_id,
        user_id=user_email,
        role="Creator"
    )
    db.add(creator_member)
    db.commit()
    
    return RedirectResponse(url=f"/project-broadcasted/{new_project.project_id}", status_code=303)

@app.get("/project-broadcasted/{project_id}", response_class=HTMLResponse)
async def project_broadcasted(request: Request, project_id: int, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)

    project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if not project or project.creator_id != user_email:
        # If project not found or doesn't belong to this user, fall back to my-projects
        return RedirectResponse(url="/my-projects", status_code=303)

    return templates.TemplateResponse("project_broadcasted.html", {
        "request": request,
        "email": user_email,
        "project": project,
        "active_page": "my_projects"
    })

@app.get("/my-projects", response_class=HTMLResponse)
async def my_projects_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    user_projects = db.query(models.Project).filter(models.Project.creator_id == user_email).all()
    
    enriched_projects = []
    total_new_requests = 0
    for proj in user_projects:
        member_count = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == proj.project_id).count()
        join_reqs = db.query(models.JoinRequest).filter(
            models.JoinRequest.project_id == proj.project_id,
            models.JoinRequest.status == "pending"
        ).count()
        
        total_new_requests += join_reqs
        status_label = "Open"
        if member_count >= proj.team_size:
            status_label = "Team Full"
            
        enriched_projects.append({
            "project_id": proj.project_id,
            "title": proj.title,
            "description": proj.description,
            "required_skills": proj.required_skills,
            "team_size": proj.team_size,
            "member_count": member_count,
            "join_requests": join_reqs,
            "status_label": status_label
        })
        
    return templates.TemplateResponse("my_projects.html", {
        "request": request,
        "email": user_email,
        "projects": enriched_projects,
        "total_new_requests": total_new_requests,
        "active_page": "my_projects"
    })

@app.get("/projects", response_class=HTMLResponse)
async def projects_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Fetch all projects from DB to display here
    all_db_projects = db.query(models.Project).all()
    
    enriched_projects = []
    for proj in all_db_projects:
        # Find creator name — check DB Profile first, then dummy_profiles, then derive from email
        creator_name = proj.creator_id.split("@")[0].capitalize()
        creator_user = db.query(models.User).filter(models.User.email == proj.creator_id).first()
        if creator_user:
            creator_prof = db.query(models.Profile).filter(models.Profile.user_id == creator_user.id).first()
            if creator_prof:
                creator_name = creator_prof.full_name
        elif proj.creator_id in dummy_profiles:
            creator_name = dummy_profiles[proj.creator_id].get("full_name", creator_name)
             
        # Fetch members
        db_members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == proj.project_id).all()
        member_emails = [m.user_id for m in db_members]
        member_names = []
        for mem_email in member_emails:
            name = mem_email.split("@")[0].capitalize()
            if mem_email == proj.creator_id:
                name += " (Creator)"
            elif mem_email in dummy_profiles:
                name = dummy_profiles[mem_email].get("full_name", name)
            member_names.append(name)
            
        # Has user requested to join?
        has_requested = db.query(models.JoinRequest).filter(
            models.JoinRequest.project_id == proj.project_id,
            models.JoinRequest.requester_id == user_email,
            models.JoinRequest.status == "pending"
        ).first() is not None
            
        enriched_projects.append({
            "id": proj.project_id, # for template compatibility
            "title": proj.title,
            "description": proj.description,
            "required_skills": proj.required_skills,
            "team_size": proj.team_size,
            "creator_name": creator_name,
            "members": member_emails, # template expects 'members' list
            "member_names": member_names,
            "has_requested": has_requested
        })
            
    return templates.TemplateResponse("projects.html", {
        "request": request, 
        "email": user_email,
        "projects": enriched_projects,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "projects"
    })

@app.post("/request-project-join")
async def request_project_join(
    request: Request,
    project_id: int = Form(...),
    db: Session = Depends(get_db)
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Check if already requested or member
    existing_req = db.query(models.JoinRequest).filter(
        models.JoinRequest.project_id == project_id,
        models.JoinRequest.requester_id == user_email,
        models.JoinRequest.status == "pending"
    ).first()
    
    if not existing_req:
        new_req = models.JoinRequest(
            project_id=project_id,
            requester_id=user_email,
            status="pending"
        )
        db.add(new_req)
        db.commit()
    
    return RedirectResponse(url="/projects", status_code=303)

@app.get("/project-status/{project_id}", response_class=HTMLResponse)
async def project_status_get(request: Request, project_id: int, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if not project or project.creator_id != user_email:
        return HTMLResponse("Unauthorized or Project Not Found", status_code=403)
        
    # Fetch team members
    db_members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).all()
    team_members = []
    for mem in db_members:
        name = mem.user_id.split("@")[0].capitalize()
        skills = []
        if mem.user_id in dummy_profiles:
            name = dummy_profiles[mem.user_id].get("full_name", name)
            skills = dummy_skills.get(mem.user_id, [])
        team_members.append({
            "email": mem.user_id,
            "name": name,
            "skills": skills,
            "role": mem.role
        })
        
    # Fetch join requests
    db_requests = db.query(models.JoinRequest).filter(
        models.JoinRequest.project_id == project_id,
        models.JoinRequest.status == "pending"
    ).all()
    
    join_requests = []
    for req in db_requests:
        sender_name = req.requester_id.split("@")[0].capitalize()
        sender_dept = "Unknown"
        sender_year = "Unknown"
        sender_skills = []
        
        if req.requester_id in dummy_profiles:
            prof = dummy_profiles[req.requester_id]
            sender_name = prof.get("full_name", sender_name)
            sender_dept = prof.get("department", sender_dept)
            sender_year = prof.get("year_of_study", sender_year)
            sender_skills = dummy_skills.get(req.requester_id, [])
            
        join_requests.append({
            "request_id": req.request_id,
            "sender_email": req.requester_id,
            "sender_name": sender_name,
            "sender_department": sender_dept,
            "sender_year": sender_year,
            "sender_skills": sender_skills
        })
        
    return templates.TemplateResponse("project_status.html", {
        "request": request,
        "email": user_email,
        "project": project,
        "team_members": team_members,
        "join_requests": join_requests,
        "active_page": "my_projects"
    })

@app.post("/respond-project-request")
async def respond_project_request(
    request: Request,
    request_id: int = Form(...),
    action: str = Form(...), # expected 'accept' or 'reject'
    db: Session = Depends(get_db)
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    join_req = db.query(models.JoinRequest).filter(models.JoinRequest.request_id == request_id).first()
    if not join_req:
        return RedirectResponse(url="/my-projects", status_code=303)
        
    project = db.query(models.Project).filter(models.Project.project_id == join_req.project_id).first()
    if not project or project.creator_id != user_email:
        return RedirectResponse(url="/my-projects", status_code=303)
        
    if action == 'accept':
        join_req.status = "accepted"
        
        # Check team size
        current_members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project.project_id).count()
        if current_members < project.team_size:
            # Check if already a member
            existing_member = db.query(models.ProjectMember).filter(
                models.ProjectMember.project_id == project.project_id,
                models.ProjectMember.user_id == join_req.requester_id
            ).first()
            if not existing_member:
                new_member = models.ProjectMember(
                    project_id=project.project_id,
                    user_id=join_req.requester_id,
                    role="Member"
                )
                db.add(new_member)
    elif action == 'reject':
        join_req.status = "rejected"
        
    db.commit()
            
    return RedirectResponse(url=f"/project-status/{project.project_id}", status_code=303)

@app.get("/matches", response_class=HTMLResponse)
async def matches_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    all_matches = get_top_matches(
        user_email, 
        dummy_profiles, 
        dummy_skills, 
        dummy_interests, 
        dummy_looking_for
    )
        
    return templates.TemplateResponse("matches.html", {
        "request": request, 
        "email": user_email,
        "matches": all_matches,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "matches"
    })

@app.get("/ideas", response_class=HTMLResponse)
async def ideas_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    enriched_ideas = []
    for idea in dummy_ideas:
        creator_name = "Unknown Creator"
        if idea["creator_email"] in dummy_profiles:
            creator_name = dummy_profiles[idea["creator_email"]].get("full_name", creator_name)
        elif idea["creator_email"] in dummy_users:
             creator_name = idea["creator_email"].split("@")[0].capitalize()
             
        enriched_ideas.append({
            **idea,
            "creator_name": creator_name,
            "members_count": len(idea["members"])
        })
        
    return templates.TemplateResponse("ideas.html", {
        "request": request,
        "email": user_email,
        "ideas": enriched_ideas,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "hackathon_feed"
    })

# /hackathon-feed is the canonical URL for the hackathon board
@app.get("/hackathon-feed", response_class=HTMLResponse)
async def hackathon_feed_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)

    enriched_ideas = []
    for idea in dummy_ideas:
        creator_name = "Unknown Creator"
        if idea["creator_email"] in dummy_profiles:
            creator_name = dummy_profiles[idea["creator_email"]].get("full_name", creator_name)
        elif idea["creator_email"] in dummy_users:
            creator_name = idea["creator_email"].split("@")[0].capitalize()

        enriched_ideas.append({
            **idea,
            "creator_name": creator_name,
            "members_count": len(idea["members"])
        })

    return templates.TemplateResponse("ideas.html", {
        "request": request,
        "email": user_email,
        "ideas": enriched_ideas,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "hackathon_feed"
    })

@app.get("/my-hackathons", response_class=HTMLResponse)
async def my_hackathons_get(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)

    # Filter only this user's hackathon posts
    my_ideas = [idea for idea in dummy_ideas if idea["creator_email"] == user_email]
    enriched = []
    for idea in my_ideas:
        enriched.append({
            **idea,
            "creator_name": user_email.split("@")[0].capitalize(),
            "members_count": len(idea["members"])
        })

    return templates.TemplateResponse("ideas.html", {
        "request": request,
        "email": user_email,
        "ideas": enriched,
        "total_new_requests": get_total_new_requests(db, user_email),
        "active_page": "my_hackathons",
        "my_hackathons_view": True
    })

@app.post("/create-idea")
async def create_idea_post(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    form_data = await request.form()
    
    global idea_id_counter
    
    # Process skills if they come as a comma-separated string
    skills_input = form_data.get("skills", "")
    skills_list = [s.strip() for s in skills_input.split(",") if s.strip()]
    
    new_idea = {
        "id": idea_id_counter,
        "creator_email": user_email,
        "title": form_data.get("title"),
        "category": form_data.get("category"),
        "skills": skills_list,
        "team_size": int(form_data.get("team_size", 4)),
        "description": form_data.get("description"),
        "members": [user_email]
    }
    dummy_ideas.append(new_idea)
    idea_id_counter += 1
    
    return RedirectResponse(url="/hackathon-feed", status_code=303)

@app.post("/join-idea")
async def join_idea_post(request: Request, idea_id: int = Form(...)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    for idea in dummy_ideas:
        if idea["id"] == idea_id:
             if len(idea["members"]) < idea["team_size"] and user_email not in idea["members"]:
                 idea["members"].append(user_email)
             break
             
    return RedirectResponse(url="/ideas", status_code=303)

@app.get("/workspace/{project_id}", response_class=HTMLResponse)
async def workspace_get(request: Request, project_id: int, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Find Project
    project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if not project:
         return HTMLResponse("Project Not Found", status_code=404)
         
    # Check Access
    is_member = db.query(models.ProjectMember).filter(
        models.ProjectMember.project_id == project_id,
        models.ProjectMember.user_id == user_email
    ).first()
    if not is_member:
         return HTMLResponse("Unauthorized. Only confirmed team members can access this workspace.", status_code=403)
         
    # Collect Team Details
    db_members = db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project_id).all()
    team_members = []
    for mem in db_members:
        name = mem.user_id.split("@")[0].capitalize()
        if mem.user_id == project.creator_id:
            name += " (Creator)"
        elif mem.user_id in dummy_profiles:
            name = dummy_profiles[mem.user_id].get("full_name", name)
        team_members.append(name)
        
    # Collect Tasks for this project (keep dummy_tasks for now as requested by scope implicitly, but we need project.id to match)
    proj_tasks = [t for t in dummy_tasks if t["project_id"] == project_id]
    
    todo_tasks = [t for t in proj_tasks if t["status"] == "todo"]
    in_progress_tasks = [t for t in proj_tasks if t["status"] == "in_progress"]
    completed_tasks = [t for t in proj_tasks if t["status"] == "completed"]
    
    # Needs to match template signature
    template_proj = {
        "id": project.project_id,
        "title": project.title,
        "creator_email": project.creator_id,
        "description": project.description
    }

    return templates.TemplateResponse("workspace.html", {
        "request": request,
        "email": user_email,
        "project": template_proj,
        "team_names": team_members,
        "todo": todo_tasks,
        "in_progress": in_progress_tasks,
        "completed": completed_tasks
    })

@app.post("/workspace/{project_id}/add-task")
async def add_task_post(request: Request, project_id: int, title: str = Form(...)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    global task_id_counter
    
    dummy_tasks.append({
        "id": task_id_counter,
        "project_id": project_id,
        "title": title,
        "status": "todo"
    })
    task_id_counter += 1
    
    return RedirectResponse(url=f"/workspace/{project_id}", status_code=303)

@app.post("/workspace/{project_id}/update-task")
async def update_task_post(request: Request, project_id: int, task_id: int = Form(...), status: str = Form(...)):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    for task in dummy_tasks:
        if task["id"] == task_id and task["project_id"] == project_id:
             # Validate status boundaries
             if status in ["todo", "in_progress", "completed"]:
                 task["status"] = status
             break
             
    return RedirectResponse(url=f"/workspace/{project_id}", status_code=303)
