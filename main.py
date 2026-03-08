from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from matching_engine import get_top_matches

app = FastAPI(title="UniCollab")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

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
async def login(email: str = Form(...), password: str = Form(...)):
    # Clean up any accidental trailing/leading spaces especially from auto-fill
    clean_email = email.strip()
    
    # Print what the server actually got to the terminal for debugging
    print(f"Login attempt received - Email: '{clean_email}', Password: '{password}'")

    if not clean_email.endswith("@srmist.edu.in"):
        return {"error": "Only SRM emails allowed"}

    if clean_email not in dummy_users:
        print(f"Email '{clean_email}' not found in dummy_users.")
        return {"error": "Invalid email or password"}

    if dummy_users[clean_email] != password:
        print(f"Password mismatch for '{clean_email}'. Expected '{dummy_users[clean_email]}', got '{password}'")
        return {"error": "Invalid email or password"}

    print(f"Login successful for '{clean_email}'")
    
    # Create a redirect response instead of JSON dict, to securely set a browser cookie
    # See https://fastapi.tiangolo.com/advanced/response-cookies/
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="user_email", value=clean_email, httponly=True)
    return response

@app.get("/logout")
async def logout(response: Response):
    # Simply redirects back to login and clears the cookie
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_email")
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Retrieve the user email from cookies to verify they are logged in
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Check if the user has a profile
    has_profile = user_email in dummy_profiles
    profile = dummy_profiles.get(user_email)
    skills = dummy_skills.get(user_email, [])
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "email": user_email,
        "has_profile": has_profile,
        "profile": profile,
        "skills": skills,
        "active_page": "dashboard"
    })

@app.get("/create-profile", response_class=HTMLResponse)
async def create_profile_get(request: Request):
    # Protected route check
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    return templates.TemplateResponse("create_profile.html", {"request": request, "email": user_email})

@app.post("/create-profile")
async def create_profile_post(
    request: Request,
    full_name: str = Form(...),
    year_of_study: str = Form(...),
    department: str = Form(...),
    course: str = Form(...),
    specialization: str = Form(...),
    graduation_year: str = Form(...)
):
    # Protected route check
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Save the profile data
    dummy_profiles[user_email] = {
        "full_name": full_name,
        "year_of_study": year_of_study,
        "department": department,
        "course": course,
        "specialization": specialization,
        "graduation_year": graduation_year
    }
    
    # Redirect to the add skills page
    return RedirectResponse(url="/skills", status_code=303)

@app.get("/profile", response_class=HTMLResponse)
async def view_profile_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Check if they have set up a profile yet
    if user_email not in dummy_profiles:
        return RedirectResponse(url="/create-profile", status_code=303)
        
    profile = dummy_profiles.get(user_email)
    skills = dummy_skills.get(user_email, [])
    interests = dummy_interests.get(user_email, [])
    looking_for = dummy_looking_for.get(user_email, [])
    
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "email": user_email,
        "profile": profile,
        "skills": skills,
        "interests": interests,
        "looking_for": looking_for
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
async def discover_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
    
    # Filter out the current user so they don't see themselves
    other_users = [u for u in discover_users if u["email"] != user_email]
    
    return templates.TemplateResponse("discover.html", {
        "request": request, 
        "email": user_email,
        "users": other_users,
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
async def requests_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Find requests sent to this user
    incoming_requests = []
    for req in dummy_requests:
        if req["receiver_email"] == user_email:
            # We need to enrich the request with the sender's details for UI display
            sender_name = "Unknown User"
            sender_skills = []
            
            # Check if sender is in our dummy discover users
            for u in discover_users:
                if u["email"] == req["sender_email"]:
                    sender_name = u["name"]
                    sender_skills = u["skills"]
                    break
            # Or if it's the current user (if testing with themselves, though filtered above)
            # Or check dummy_profiles (for actual registered test users)
            if req["sender_email"] in dummy_profiles:
                 sender_name = dummy_profiles[req["sender_email"]].get("full_name", sender_name)
                 sender_skills = dummy_skills.get(req["sender_email"], [])
            
            enriched_req = {
                **req,
                "sender_name": sender_name,
                "sender_skills": sender_skills
            }
            incoming_requests.append(enriched_req)
            
    # Also find requests sent BY this user to see status
    outgoing_requests = [req for req in dummy_requests if req["sender_email"] == user_email]
    for req in outgoing_requests:
         receiver_name = req["receiver_email"]
         for u in discover_users:
             if u["email"] == req["receiver_email"]:
                 receiver_name = u["name"]
                 break
         req["receiver_name"] = receiver_name

    return templates.TemplateResponse("requests.html", {
        "request": request, 
        "email": user_email,
        "incoming_requests": incoming_requests,
        "outgoing_requests": outgoing_requests,
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
async def create_project_post(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    form_data = await request.form()
    
    global project_id_counter
    
    new_project = {
        "id": project_id_counter,
        "creator_email": user_email,
        "title": form_data.get("title"),
        "type": form_data.get("type"),
        "skills": form_data.getlist("skills"),
        "team_size": int(form_data.get("team_size", 4)),
        "description": form_data.get("description"),
        "members": [user_email]  # Creator is automatically the first member
    }
    dummy_projects.append(new_project)
    project_id_counter += 1
    
    return RedirectResponse(url="/projects", status_code=303)

@app.get("/projects", response_class=HTMLResponse)
async def projects_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Enrich projects with human-readable names
    enriched_projects = []
    for proj in dummy_projects:
        # Find creator name
        creator_name = "Unknown Creator"
        if proj["creator_email"] in dummy_profiles:
            creator_name = dummy_profiles[proj["creator_email"]].get("full_name", creator_name)
        elif proj["creator_email"] in dummy_users:
             creator_name = proj["creator_email"].split("@")[0].capitalize() # fallback simple name
             
        # Find member names
        member_names = []
        for mem_email in proj["members"]:
            name = mem_email.split("@")[0].capitalize()
            if mem_email == proj["creator_email"]:
                name += " (Creator)"
            elif mem_email in dummy_profiles:
                name = dummy_profiles[mem_email].get("full_name", name)
            member_names.append(name)
            
        enriched_projects.append({
            **proj,
            "creator_name": creator_name,
            "member_names": member_names
        })
            
    return templates.TemplateResponse("projects.html", {
        "request": request, 
        "email": user_email,
        "projects": enriched_projects,
        "active_page": "projects"
    })

@app.post("/request-project-join")
async def request_project_join(
    request: Request,
    project_id: int = Form(...)
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    global project_request_id_counter
    
    dummy_project_requests.append({
        "id": project_request_id_counter,
        "project_id": project_id,
        "sender_email": user_email,
        "status": "pending"
    })
    project_request_id_counter += 1
    
    return RedirectResponse(url="/projects", status_code=303)

@app.get("/project-requests", response_class=HTMLResponse)
async def project_requests_get(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Find projects this user has created
    my_project_ids = [p["id"] for p in dummy_projects if p["creator_email"] == user_email]
    
    # Find all requests targeted at those projects
    incoming_reqs = []
    for req in dummy_project_requests:
        if req["project_id"] in my_project_ids:
            # find project title
            proj_title = next((p["title"] for p in dummy_projects if p["id"] == req["project_id"]), "Unknown Project")
            
            # Enrich sender profile
            sender_name = "Unknown User"
            sender_dept = "Unknown Dept"
            sender_skills = []
            
            if req["sender_email"] in dummy_profiles:
                 prof = dummy_profiles[req["sender_email"]]
                 sender_name = prof.get("full_name", sender_name)
                 sender_dept = prof.get("department", sender_dept)
                 sender_skills = dummy_skills.get(req["sender_email"], [])
                 
            incoming_reqs.append({
                **req,
                "project_title": proj_title,
                "sender_name": sender_name,
                "sender_department": sender_dept,
                "sender_skills": sender_skills
            })
            
    return templates.TemplateResponse("project_requests.html", {
        "request": request, 
        "email": user_email,
        "requests": incoming_reqs
    })

@app.post("/respond-project-request")
async def respond_project_request(
    request: Request,
    request_id: int = Form(...),
    action: str = Form(...) # expected 'accept' or 'reject'
):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    for req in dummy_project_requests:
        if req["id"] == request_id:
            # Verify the logged in user actually owns this project
            project = next((p for p in dummy_projects if p["id"] == req["project_id"]), None)
            if project and project["creator_email"] == user_email:
                if action == 'accept':
                    req["status"] = "accepted"
                    # Add them to the project members if space permits
                    if len(project["members"]) < project["team_size"] and req["sender_email"] not in project["members"]:
                         project["members"].append(req["sender_email"])
                elif action == 'reject':
                    req["status"] = "rejected"
            break
            
    return RedirectResponse(url="/project-requests", status_code=303)

@app.get("/matches", response_class=HTMLResponse)
async def matches_get(request: Request):
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
        "active_page": "matches"
    })

@app.get("/ideas", response_class=HTMLResponse)
async def ideas_get(request: Request):
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
        "active_page": "ideas"
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
    
    return RedirectResponse(url="/ideas", status_code=303)

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
async def workspace_get(request: Request, project_id: int):
    user_email = request.cookies.get("user_email")
    if not user_email or user_email not in dummy_users:
        return RedirectResponse(url="/login", status_code=303)
        
    # Find Project
    project = next((p for p in dummy_projects if p["id"] == project_id), None)
    if not project:
         return HTMLResponse("Project Not Found", status_code=404)
         
    # Check Access
    if user_email not in project["members"]:
         return HTMLResponse("Unauthorized. Only confirmed team members can access this workspace.", status_code=403)
         
    # Collect Team Details
    team_members = []
    for mem_email in project["members"]:
        name = mem_email.split("@")[0].capitalize()
        if mem_email == project["creator_email"]:
            name += " (Creator)"
        elif mem_email in dummy_profiles:
            name = dummy_profiles[mem_email].get("full_name", name)
        team_members.append(name)
        
    # Collect Tasks for this project
    proj_tasks = [t for t in dummy_tasks if t["project_id"] == project_id]
    
    todo_tasks = [t for t in proj_tasks if t["status"] == "todo"]
    in_progress_tasks = [t for t in proj_tasks if t["status"] == "in_progress"]
    completed_tasks = [t for t in proj_tasks if t["status"] == "completed"]
    
    return templates.TemplateResponse("workspace.html", {
        "request": request,
        "email": user_email,
        "project": project,
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
