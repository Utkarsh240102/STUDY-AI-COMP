from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
import secrets
from functions import (
    generate_flashcards,
    generate_mcqs,
    create_mind_map,
    generate_learning_path,
    create_sticky_notes,
    generate_exam_questions,
    process_uploaded_file,
    classify_question_importance
)

# Add YouTube functions import
from youtubefunctions import (
    get_video_id,
    get_transcript,
    download_audio,
    transcribe_audio,
    summarize_transcript,
    generate_summary
)

# Add the import for document Q&A routes
from doc_qna_routes import create_doc_qna_routes

# Database models and utilities
from database import User, StudyGroup, GroupMembership, UserDocument, get_db
from sqlalchemy.orm import Session

# Auth utilities
from auth import oauth, get_current_user, create_access_token, verify_token
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Smart Study Tool", version="1.0.0")

# Get the secret key from environment or use a default for development
SECRET_KEY = os.getenv("SECRET_KEY", "temporary-secret-key-for-development")

# Add session middleware (required for OAuth)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class TextInput(BaseModel):
    text: str

class FlashcardResponse(BaseModel):
    id: str
    question: str
    answer: str
    difficulty: str

class MCQResponse(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_answer: int
    explanation: str
    difficulty: str

class MindMapNode(BaseModel):
    id: str
    label: str
    children: List['MindMapNode'] = []
    level: int
    color: str

class LearningStep(BaseModel):
    step_number: int
    title: str
    description: str
    estimated_time: str
    prerequisites: List[str]
    resources: List[str]

class StickyNote(BaseModel):
    id: str
    content: str
    category: str  # red, yellow, green
    priority: int
    tags: List[str]

class ExamQuestion(BaseModel):
    id: str
    question: str
    type: str  # short_answer, long_answer, hots
    probability_score: float
    difficulty: str
    keywords: List[str]

class VideoRequest(BaseModel):
    url: str

class VideoSummaryResponse(BaseModel):
    video_id: str
    title: str
    thumbnail: str
    summary: str
    source: str  # "transcript" or "audio"
    duration: Optional[str] = None

# Add document Q&A routes
app = create_doc_qna_routes(app)

# Helper function to serve HTML files
def serve_html_file(filename: str):
    """Serve HTML files with proper error handling"""
    try:
        # First try templates directory
        template_path = f"templates/{filename}"
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        
        # Then try root directory
        root_path = filename
        if os.path.exists(root_path):
            with open(root_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        
        # File not found
        raise HTTPException(status_code=404, detail=f"Page {filename} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Main homepage route
@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """Serve the main application page"""
    return serve_html_file("index.html")

# Feature page routes
@app.get("/flashcards.html", response_class=HTMLResponse)
async def get_flashcards_page():
    """Serve the flashcards page"""
    return serve_html_file("flashcards.html")

@app.get("/mindmap.html", response_class=HTMLResponse)
async def get_mindmap_page():
    """Serve the mind map page"""
    return serve_html_file("mindmap.html")

@app.get("/learning-path.html", response_class=HTMLResponse)
async def get_learning_path_page():
    """Serve the learning path page"""
    return serve_html_file("learning-path.html")

@app.get("/sticky-notes.html", response_class=HTMLResponse)
async def get_sticky_notes_page():
    """Serve the sticky notes page"""
    return serve_html_file("sticky-notes.html")

@app.get("/exam-booster.html", response_class=HTMLResponse)
async def get_exam_booster_page():
    """Serve the exam booster page"""
    return serve_html_file("exam-booster.html")

@app.get("/youtube-summarizer.html", response_class=HTMLResponse)
async def get_youtube_summarizer_page():
    """Serve the YouTube summarizer page"""
    return serve_html_file("youtube-summarizer.html")

@app.get("/pdf-qa.html", response_class=HTMLResponse)
async def get_pdf_qa_page():
    """Serve the PDF Q&A page"""
    return serve_html_file("pdf-qa.html")

# Add the 7th feature: Document Chat
@app.get("/doc-chat.html", response_class=HTMLResponse)
async def get_doc_chat_page():
    """Serve the document chat page"""
    return serve_html_file("doc-chat.html")

# API Routes

@app.post("/api/generate-flashcards", response_model=List[FlashcardResponse])
async def create_flashcards(file: UploadFile = File(None), text: str = Form(None)):
    """Generate flashcards from uploaded file or text"""
    try:
        if file:
            content = await process_uploaded_file(file)
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="Please provide either a file or text")
        
        flashcards = await generate_flashcards(content)
        return flashcards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating flashcards: {str(e)}")

@app.post("/api/generate-mcqs", response_model=List[MCQResponse])
async def create_mcqs(file: UploadFile = File(None), text: str = Form(None)):
    """Generate MCQs from uploaded file or text"""
    try:
        if file:
            content = await process_uploaded_file(file)
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="Please provide either a file or text")
        
        mcqs = await generate_mcqs(content)
        return mcqs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating MCQs: {str(e)}")

@app.get("/api/quiz/{quiz_id}")
async def get_quiz_interface(quiz_id: str):
    """Get quiz interface for a specific quiz"""
    return {"quiz_id": quiz_id, "status": "active"}

@app.post("/api/generate-mindmap", response_model=dict)
async def create_mindmap(file: UploadFile = File(None), text: str = Form(None)):
    """Generate interactive mind map from content"""
    try:
        if file:
            content = await process_uploaded_file(file)
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="Please provide either a file or text")
        
        mindmap_data = await create_mind_map(content)
        return mindmap_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating mind map: {str(e)}")

@app.get("/api/mindmap/{map_id}")
async def get_mindmap(map_id: str):
    """Get specific mind map data"""
    return {"map_id": map_id, "status": "ready"}

@app.post("/api/generate-learning-path", response_model=List[LearningStep])
async def create_learning_path(file: UploadFile = File(None), text: str = Form(None)):
    """Generate step-by-step learning path"""
    try:
        if file:
            content = await process_uploaded_file(file)
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="Please provide either a file or text")
        
        learning_path = await generate_learning_path(content)
        return learning_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating learning path: {str(e)}")

@app.get("/api/learning-path/{path_id}")
async def get_learning_path(path_id: str):
    """Get specific learning path"""
    return {"path_id": path_id, "status": "active"}

@app.post("/api/generate-sticky-notes", response_model=List[StickyNote])
async def create_smart_sticky_notes(file: UploadFile = File(None), text: str = Form(None)):
    """Generate color-coded sticky notes with smart categorization"""
    try:
        if file:
            content = await process_uploaded_file(file)
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="Please provide either a file or text")
        
        sticky_notes = await create_sticky_notes(content)
        return sticky_notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sticky notes: {str(e)}")

@app.get("/api/sticky-notes/{note_id}")
async def get_sticky_note(note_id: str):
    """Get specific sticky note details"""
    return {"note_id": note_id, "status": "active"}

@app.put("/api/sticky-notes/{note_id}/category")
async def update_sticky_note_category(note_id: str, category: str):
    """Update sticky note category (red/yellow/green)"""
    return {"note_id": note_id, "category": category, "updated": True}

@app.post("/api/generate-exam-questions", response_model=List[ExamQuestion])
async def create_exam_questions(file: UploadFile = File(None), text: str = Form(None)):
    """Generate most likely exam questions with probability scores"""
    try:
        if file:
            content = await process_uploaded_file(file)
        elif text:
            content = text
        else:
            raise HTTPException(status_code=400, detail="Please provide either a file or text")
        
        exam_questions = await generate_exam_questions(content)
        return exam_questions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating exam questions: {str(e)}")

@app.get("/api/exam-questions/by-type/{question_type}")
async def get_questions_by_type(question_type: str):
    """Get questions filtered by type (short_answer, long_answer, hots)"""
    return {"question_type": question_type, "status": "filtered"}

@app.get("/api/exam-questions/by-probability/{min_probability}")
async def get_questions_by_probability(min_probability: float):
    """Get questions with probability score above threshold"""
    return {"min_probability": min_probability, "status": "filtered"}

@app.post("/api/summarize-youtube", response_model=VideoSummaryResponse)
async def summarize_youtube_video(request: VideoRequest):
    """Summarize YouTube video from URL"""
    try:
        video_url = request.url
        video_id = get_video_id(video_url)

        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # Get video info for thumbnail and title
        try:
            import yt_dlp
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'YouTube Video')
                thumbnail = info.get('thumbnail', f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg')
                duration = info.get('duration_string', 'Unknown')
        except:
            title = 'YouTube Video'
            thumbnail = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
            duration = 'Unknown'

        # Try to get transcript first
        transcript = get_transcript(video_id)

        if transcript:
            summary = summarize_transcript(transcript)
            source = "transcript"
        else:
            try:
                audio_path = download_audio(video_url)
                transcript_text = transcribe_audio(audio_path)
                summary = generate_summary(transcript_text)
                source = "audio"
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")

        return VideoSummaryResponse(
            video_id=video_id,
            title=title,
            thumbnail=thumbnail,
            summary=summary,
            source=source,
            duration=duration
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.get("/api/video-info/{video_id}")
async def get_video_info(video_id: str):
    """Get video information including thumbnail"""
    try:
        import yt_dlp
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
        return {
            "video_id": video_id,
            "title": info.get('title', 'YouTube Video'),
            "thumbnail": info.get('thumbnail', f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'),
            "duration": info.get('duration_string', 'Unknown'),
            "channel": info.get('uploader', 'Unknown Channel'),
            "view_count": info.get('view_count', 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching video info: {str(e)}")

# 📊 Analytics and Progress Routes
@app.get("/api/analytics/study-progress")
async def get_study_progress():
    """Get user's study progress analytics"""
    return {
        "flashcards_completed": 0,
        "mcqs_attempted": 0,
        "accuracy_rate": 0.0,
        "study_time": "0h 0m",
        "weak_areas": [],
        "strong_areas": []
    }

@app.get("/api/analytics/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    return {
        "weekly_progress": [],
        "subject_wise_performance": {},
        "difficulty_wise_accuracy": {},
        "time_spent_per_topic": {}
    }

# 🎮 Interactive Features Routes
@app.post("/api/quiz/submit-answer")
async def submit_quiz_answer(quiz_id: str, question_id: str, answer: int):
    """Submit quiz answer and get feedback"""
    return {
        "quiz_id": quiz_id,
        "question_id": question_id,
        "is_correct": True,  # This would be calculated
        "explanation": "Detailed explanation here",
        "next_question": "next_question_id"
    }

@app.post("/api/flashcard/mark-difficulty")
async def mark_flashcard_difficulty(flashcard_id: str, difficulty: str):
    """Mark flashcard as easy/medium/hard for spaced repetition"""
    return {
        "flashcard_id": flashcard_id,
        "difficulty": difficulty,
        "next_review": "2024-01-01T00:00:00Z"
    }

# 🔄 Utility Routes
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": [
            "pdf", "docx", "txt", "pptx", 
            "md", "html", "csv", "json"
        ]
    }

# Authentication routes
@app.get("/auth/login")
async def login(request: Request):
    # Get the redirect URI for the callback
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Get token from Google
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            return RedirectResponse(url="/?error=Failed+to+get+user+info")
        
        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info['sub']).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=user_info['sub'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture', '')
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token = create_access_token(user.id, user.email)
        
        # Redirect and set cookie
        response = RedirectResponse(url="/")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=30 * 24 * 60 * 60  # 30 days
        )
        
        return response
        
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return RedirectResponse(url="/?error=authentication_failed")

@app.post("/auth/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

@app.get("/api/user/profile")
async def get_user_profile(request: Request, db: Session = Depends(get_db)):
    # Get access token from cookie
    token = request.cookies.get("access_token")
    
    if not token:
        return {"user": None}
    
    # Verify token
    payload = verify_token(token)
    if not payload:
        return {"user": None}
    
    # Get user from database
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    
    if not user:
        return {"user": None}
    
    # Return user data
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "picture": user.picture
        }
    }

# Group routes
@app.get("/groups")
async def get_groups_page(request: Request):
    """Serve the groups page"""
    return serve_html_file("groups.html")

@app.get("/group/{group_id}")
async def get_group_page(group_id: int, request: Request):
    """Serve the group detail page"""
    return serve_html_file("group-detail.html")

@app.get("/api/groups")
async def get_user_groups(request: Request, db: Session = Depends(get_db)):
    # Get current user
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload["user_id"]
    
    # Get user's groups
    memberships = db.query(GroupMembership).filter(GroupMembership.user_id == user_id).all()
    
    groups = []
    for membership in memberships:
        group = db.query(StudyGroup).filter(StudyGroup.id == membership.group_id).first()
        if group:
            # Count members
            member_count = db.query(GroupMembership).filter(
                GroupMembership.group_id == group.id
            ).count()
            
            # Count documents (placeholder for now)
            document_count = 0
            
            groups.append({
                "id": group.id,
                "name": group.name,
                "group_key": group.group_key,
                "role": membership.role,
                "member_count": member_count,
                "document_count": document_count
            })
    
    return {"groups": groups}

@app.post("/api/groups/create")
async def create_group(request: Request, db: Session = Depends(get_db)):
    # Get current user
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload["user_id"]
    
    # Get form data
    form = await request.form()
    name = form.get("name")
    
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")
    
    # Generate unique group key
    group_key = secrets.token_hex(4).upper()
    
    # Create group
    group = StudyGroup(
        name=name,
        group_key=group_key,
        created_by=user_id
    )
    
    db.add(group)
    db.commit()
    db.refresh(group)
    
    # Add creator as admin
    membership = GroupMembership(
        user_id=user_id,
        group_id=group.id,
        role="admin"
    )
    
    db.add(membership)
    db.commit()
    
    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name,
            "group_key": group.group_key
        }
    }

@app.post("/api/groups/join")
async def join_group(request: Request, db: Session = Depends(get_db)):
    # Get current user
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload["user_id"]
    
    # Get form data
    form = await request.form()
    group_key = form.get("group_key")
    
    if not group_key:
        raise HTTPException(status_code=400, detail="Group key is required")
    
    # Find group
    group = db.query(StudyGroup).filter(StudyGroup.group_key == group_key).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user is already a member
    existing = db.query(GroupMembership).filter(
        GroupMembership.user_id == user_id,
        GroupMembership.group_id == group.id
    ).first()
    
    if existing:
        return {
            "success": True,
            "group": {
                "id": group.id,
                "name": group.name
            }
        }
    
    # Add user as member
    membership = GroupMembership(
        user_id=user_id,
        group_id=group.id,
        role="member"
    )
    
    db.add(membership)
    db.commit()
    
    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name
        }
    }

@app.get("/api/user/documents")
async def get_user_documents(request: Request, db: Session = Depends(get_db)):
    # Get current user
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload["user_id"]
    
    # Get user's documents
    documents = db.query(UserDocument).filter(UserDocument.user_id == user_id).all()
    
    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "uploaded_at": doc.uploaded_at.isoformat()
            } for doc in documents
        ]
    }