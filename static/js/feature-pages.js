// Feature Pages JavaScript
let uploadedFiles = [];
let isDayMode = localStorage.getItem('dayMode') === 'true';

// Initialize theme
if (isDayMode) {
    document.body.classList.add('day-mode');
    const themeIcon = document.querySelector('.theme-toggle i');
    if (themeIcon) themeIcon.classList.replace('fa-moon', 'fa-sun');
}

// Theme toggle function
function toggleTheme() {
    document.body.classList.toggle('day-mode');
    isDayMode = document.body.classList.contains('day-mode');
    localStorage.setItem('dayMode', isDayMode);
    const icon = document.querySelector('.theme-toggle i');
    icon.classList.toggle('fa-moon');
    icon.classList.toggle('fa-sun');
}

// Drag and Drop Functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadZone && fileInput) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        // Highlight drop area when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, unhighlight, false);
        });
        
        // Handle dropped files
        uploadZone.addEventListener('drop', handleDrop, false);
        
        // Handle file input change
        fileInput.addEventListener('change', function(e) {
            handleFiles(e.target.files);
        });
    }
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    document.getElementById('uploadZone').classList.add('dragover');
}

function unhighlight(e) {
    document.getElementById('uploadZone').classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    [...files].forEach(handleFile);
    displayUploadedFiles();
}

function handleFile(file) {
    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.txt', '.md'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        alert(`File type ${fileExtension} is not supported. Please upload PDF, DOCX, TXT, or MD files.`);
        return;
    }
    
    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }
    
    // Add to uploaded files array
    const fileInfo = {
        id: Date.now() + Math.random(),
        file: file,
        name: file.name,
        size: formatFileSize(file.size),
        type: fileExtension
    };
    
    uploadedFiles.push(fileInfo);
}

function displayUploadedFiles() {
    if (uploadedFiles.length === 0) return;
    
    let uploadedFilesDiv = document.querySelector('.uploaded-files');
    if (!uploadedFilesDiv) {
        uploadedFilesDiv = document.createElement('div');
        uploadedFilesDiv.className = 'uploaded-files';
        document.querySelector('.upload-zone').after(uploadedFilesDiv);
    }
    
    uploadedFilesDiv.innerHTML = `
        <h3><i class="fas fa-files"></i> Uploaded Files (${uploadedFiles.length})</h3>
        ${uploadedFiles.map(file => `
            <div class="file-item" data-file-id="${file.id}">
                <div class="file-info">
                    <div class="file-icon">
                        <i class="fas ${getFileIcon(file.type)}"></i>
                    </div>
                    <div class="file-details">
                        <h4>${file.name}</h4>
                        <p>${file.size} • ${file.type.toUpperCase()}</p>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="remove-file" onclick="removeFile('${file.id}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('')}
    `;
}

function removeFile(fileId) {
    uploadedFiles = uploadedFiles.filter(file => file.id != fileId);
    displayUploadedFiles();
    
    if (uploadedFiles.length === 0) {
        const uploadedFilesDiv = document.querySelector('.uploaded-files');
        if (uploadedFilesDiv) uploadedFilesDiv.remove();
    }
}

function getFileIcon(type) {
    switch(type) {
        case '.pdf': return 'fa-file-pdf';
        case '.docx': return 'fa-file-word';
        case '.txt': return 'fa-file-alt';
        case '.md': return 'fa-file-code';
        default: return 'fa-file';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Feature-specific generation functions
function generateFlashcards() {
    generateContent('flashcards');
}

function generateMindMap() {
    generateContent('mindmap');
}

function generateLearningPath() {
    generateContent('learning-path');
}

function generateStickyNotes() {
    generateContent('sticky-notes');
}

function generateExamBooster() {
    generateContent('exam-questions');
}

function generateYouTubeSummary() {
    generateContent('youtube');
}

function generatePDFQA() {
    generateContent('pdf-qa');
}

// Universal content generation function
async function generateContent(type) {
    const textContent = document.getElementById('textContent').value.trim();
    
    if (uploadedFiles.length === 0 && !textContent) {
        alert('Please upload files or enter text content first!');
        return;
    }
    
    showLoading(type);
    
    try {
        const formData = new FormData();
        
        // Add uploaded files
        uploadedFiles.forEach((fileInfo, index) => {
            formData.append('files', fileInfo.file);
        });
        
        // Add text content
        if (textContent) {
            formData.append('text', textContent);
        }
        
        const endpoint = `/api/generate-${type}`;
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayResults(type, data);
        
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while generating content. Please try again.');
        hideLoading();
    }
}

function showLoading(type) {
    const resultsArea = document.getElementById('resultsArea');
    resultsArea.style.display = 'block';
    resultsArea.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <h3>Generating ${type.replace('-', ' ')}...</h3>
            <p>Please wait while our AI processes your content</p>
        </div>
    `;
    resultsArea.scrollIntoView({ behavior: 'smooth' });
}

function hideLoading() {
    const resultsArea = document.getElementById('resultsArea');
    resultsArea.style.display = 'none';
}

function displayResults(type, data) {
    const resultsArea = document.getElementById('resultsArea');
    let html = '';
    
    switch(type) {
        case 'flashcards': html = createFlashcardsHTML(data); break;
        case 'mcqs': html = createMCQsHTML(data); break;
        case 'mindmap': html = createMindMapHTML(data); break;
        case 'learning-path': html = createLearningPathHTML(data); break;
        case 'sticky-notes': html = createStickyNotesHTML(data); break;
        case 'exam-questions': html = createExamQuestionsHTML(data); break;
        case 'youtube': html = createYouTubeSummaryHTML(data); break;
        case 'pdf-qa': html = createPDFQAHTML(data); break;
    }
    
    resultsArea.innerHTML = html;
    resultsArea.style.display = 'block';
    
    // Animate results
    setTimeout(() => {
        resultsArea.querySelectorAll('.animate-in').forEach((el, index) => {
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }, 100);
}

// Use the same HTML generation functions from your main script.js
// Copy all the createFlashcardsHTML, createMCQsHTML, etc. functions here
// (I'll include a few examples)

function createFlashcardsHTML(flashcards) {
    let html = `
        <div style="background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(12px); border-radius: 20px; padding: 2.5rem;">
            <h2 class="text-center" style="color: var(--text-primary); margin-bottom: 2rem;">
                <i class="fas fa-brain" style="color: #f87171;"></i> Smart Flashcards
            </h2>
            <p class="text-center" style="color: var(--text-secondary); margin-bottom: 2rem;">
                Click cards to flip and reveal answers
            </p>
            <div class="flashcards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
    `;

    flashcards.forEach((card, index) => {
        html += `
            <div class="flashcard animate-in" style="opacity: 0; transform: translateY(20px); background: white; border-radius: 15px; padding: 2rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1); cursor: pointer; transition: all 0.3s ease;" onclick="flipCard(this)">
                <div class="flashcard-inner">
                    <div class="flashcard-front">
                        <div style="font-weight: 600; color: #333; font-size: 1.1rem; line-height: 1.5;">
                            ${card.question}
                        </div>
                        <div style="position: absolute; top: 15px; right: 15px; background: ${getDifficultyColor(card.difficulty)}; color: white; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.7rem; font-weight: 600;">
                            ${card.difficulty ? card.difficulty.toUpperCase() : 'MEDIUM'}
                        </div>
                        <div style="position: absolute; bottom: 15px; left: 50%; transform: translateX(-50%); color: #999; font-size: 0.8rem;">
                            <i class="fas fa-sync-alt"></i> Click to flip
                        </div>
                    </div>
                    <div class="flashcard-back" style="display: none;">
                        <div style="font-weight: 500; line-height: 1.6; color: #333;">
                            ${card.answer}
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    html += `
            </div>
            <div class="text-center mt-2" style="margin-top: 2rem;">
                <button class="btn btn-primary" onclick="shuffleFlashcards()" style="background: var(--accent); color: white; border: none; padding: 1rem 2rem; border-radius: 12px; cursor: pointer;">
                    <i class="fas fa-random"></i> Shuffle Cards
                </button>
            </div>
        </div>
    `;
    return html;
}

function flipCard(card) {
    const front = card.querySelector('.flashcard-front');
    const back = card.querySelector('.flashcard-back');
    
    if (front.style.display === 'none') {
        front.style.display = 'block';
        back.style.display = 'none';
    } else {
        front.style.display = 'none';
        back.style.display = 'block';
    }
}

function getDifficultyColor(difficulty) {
    const colors = {
        easy: '#34d399',
        medium: '#f59e0b',
        hard: '#f87171'
    };
    return colors[difficulty?.toLowerCase()] || '#6b7280';
}

function shuffleFlashcards() {
    const container = document.querySelector('.flashcards-grid');
    const cards = Array.from(container.children);
    
    for (let i = cards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [cards[i], cards[j]] = [cards[j], cards[i]];
    }
    
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        container.appendChild(card);
    });
}

// Add other HTML generation functions as needed...