import os
import glob
import re

nav_html = """<nav class="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b border-slate-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <!-- Left: Logo & Links -->
                <div class="flex items-center gap-8">
                    <!-- Brand (Text Only, Bold, Larger, Modern Minimal) -->
                    <a href="dashboard.html" class="flex items-center group">
                        <span class="font-bold text-2xl tracking-tighter text-slate-800 group-hover:text-teal-500 transition-colors">UniCollab.</span>
                    </a>

                    <!-- App Navigation -->
                    <div class="flex items-center space-x-1">
                        <a href="dashboard.html" class="px-3 py-2 rounded-lg text-sm font-medium transition-colors text-slate-600 hover:text-teal-600 hover:bg-teal-50">Dashboard</a>
                        <a href="explore.html" class="px-3 py-2 rounded-lg text-sm font-medium transition-colors text-slate-600 hover:text-teal-600 hover:bg-teal-50">Discover</a>
                    </div>
                </div>

                <!-- Right: User & Actions -->
                <div class="flex items-center gap-4">
                    <!-- Profile Icon (Routes to Profile Page) -->
                    <a href="profile.html" class="flex items-center justify-center w-9 h-9 rounded-full bg-slate-100 hover:bg-teal-100 text-slate-600 hover:text-teal-600 transition-colors border border-slate-200 shadow-sm group">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                    </a>
                    
                    <div class="h-4 w-px bg-slate-200 hidden sm:block"></div>
                    
                    <!-- Log Out Button -->
                    <button onclick="API.logout()" class="text-xs text-slate-500 hover:text-red-500 transition-colors uppercase tracking-widest font-bold">
                        Log Out
                    </button>
                </div>
            </div>
        </div>
    </nav>"""

directory = '/Users/harshithakasaraneni/Desktop/unicollab/frontend'
html_files = glob.glob(os.path.join(directory, '*.html'))

for filepath in html_files:
    if "login.html" in filepath or "index.html" in filepath:
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = re.sub(r'<nav(.*?)</nav>', nav_html, content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
print("Navbar updated in all authenticated HTML files.")
