"""
JARVIS AI — Windows Automation & Command Execution Engine
Handles opening websites, YouTube searches, launching Windows apps,
navigating file folders, and executing system directives.
"""

import os
import re
import sys
import datetime
import urllib.parse
import webbrowser
import subprocess
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("jarvis.automation")

# 1. Special Known Folders Resolver
def get_windows_folder(folder_name: str) -> Optional[str]:
    """Resolve standard Windows user folders (handles OneDrive redirection as well)."""
    name = folder_name.lower().strip()
    home = os.path.expanduser("~")

    folder_map = {
        "desktop": ["Desktop", os.path.join("OneDrive", "Desktop")],
        "downloads": ["Downloads"],
        "documents": ["Documents", os.path.join("OneDrive", "Documents")],
        "pictures": ["Pictures", os.path.join("OneDrive", "Pictures")],
        "photos": ["Pictures", os.path.join("OneDrive", "Pictures")],
        "videos": ["Videos"],
        "movies": ["Videos"],
        "music": ["Music"],
    }

    # Drive root checks
    if name in ("c", "c drive", "drive c", "c:"):
        return "C:\\"
    if name in ("d", "d drive", "drive d", "d:"):
        if os.path.exists("D:\\"):
            return "D:\\"
        return "C:\\"

    if name in folder_map:
        for rel in folder_map[name]:
            full = os.path.join(home, rel)
            if os.path.exists(full):
                return full

    # Try checking direct subdirectory in user home or current project
    direct_path = os.path.join(home, folder_name)
    if os.path.exists(direct_path):
        return direct_path

    # Try checking relative to current directory
    if os.path.exists(folder_name):
        return os.path.abspath(folder_name)

    return None

def open_folder(path_or_name: str) -> tuple[bool, str]:
    """Open a folder in Windows File Explorer."""
    resolved = get_windows_folder(path_or_name)
    if not resolved:
        # Check if it's already an absolute path
        if os.path.exists(path_or_name):
            resolved = os.path.abspath(path_or_name)
        else:
            resolved = os.path.expanduser("~")

    try:
        logger.info(f"Opening folder: {resolved}")
        os.startfile(resolved)
        return True, resolved
    except Exception as exc:
        logger.error(f"Failed to open folder {resolved}: {exc}")
        try:
            subprocess.Popen(["explorer.exe", resolved])
            return True, resolved
        except Exception as exc2:
            return False, str(exc2)

# 2. Application Launcher
APP_COMMANDS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "vs code": ["code"],
    "vscode": ["code"],
    "code": ["code"],
    "chrome": ["chrome"],
    "google chrome": ["chrome"],
    "edge": ["msedge"],
    "microsoft edge": ["msedge"],
    "cmd": ["cmd.exe", "/c", "start", "cmd.exe"],
    "command prompt": ["cmd.exe", "/c", "start", "cmd.exe"],
    "terminal": ["cmd.exe", "/c", "start", "cmd.exe"],
    "powershell": ["powershell.exe", "-NoExit"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "my computer": ["explorer.exe"],
    "this pc": ["explorer.exe"],
    "control panel": ["control.exe"],
    "settings": ["start", "ms-settings:"],
    "windows settings": ["start", "ms-settings:"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "paint": ["mspaint.exe"],
}

def open_application(app_name: str) -> tuple[bool, str]:
    """Launch a Windows application."""
    clean_name = app_name.lower().strip()
    cmd = APP_COMMANDS.get(clean_name)

    try:
        if clean_name in ("settings", "windows settings"):
            os.startfile("ms-settings:")
            return True, "Settings"

        if cmd:
            subprocess.Popen(cmd, shell=True)
            return True, clean_name.title()

        # Fallback: try launching directly by name
        subprocess.Popen([clean_name], shell=True)
        return True, clean_name.title()
    except Exception as exc:
        logger.error(f"Failed to launch application '{app_name}': {exc}")
        return False, str(exc)

# 3. Known Web Destinations
WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "github": "https://www.github.com",
    "gmail": "https://mail.google.com",
    "chatgpt": "https://chat.openai.com",
    "whatsapp": "https://web.whatsapp.com",
    "wikipedia": "https://www.wikipedia.org",
    "reddit": "https://www.reddit.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
}

def open_url(url: str) -> bool:
    """Open URL in the default browser."""
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return True
    except Exception as exc:
        logger.error(f"Failed to open URL '{url}': {exc}")
        return False

def search_youtube(query: str) -> bool:
    """Open YouTube search results for query."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    return open_url(url)

def search_google(query: str) -> bool:
    """Open Google search results for query."""
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)

# 4. Voice Directives Intent Parser
def parse_voice_directive(command_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses natural voice command. If it matches a Windows automation action,
    it executes the action and returns a polite JARVIS spoken response.
    """
    raw = command_text.strip()
    text = raw.lower()

    # Strip conversational lead-ins (e.g. "jarvis please", "can you", "could you")
    clean = re.sub(r'^(?:jarvis\s*,?\s*|hey\s+jarvis\s*,?\s*|ok\s+jarvis\s*,?\s*|please\s+|could\s+you\s+(?:please\s+)?|can\s+you\s+(?:please\s+)?)', '', text).strip()

    # ---------------------------------------------------------
    # A. YouTube Search & Play Intent
    # Examples:
    # "youtube open then waz open"
    # "open youtube and search waz"
    # "search waz on youtube"
    # "play waz on youtube"
    # "waz on youtube"
    # "youtube search waz"
    # ---------------------------------------------------------
    if "youtube" in clean:
        # Check if user wants a specific search on YouTube
        # 1. "youtube open then <query> open" or "youtube open <query>"
        m_then = re.search(r'youtube\s+(?:open\s+)?then\s+(.+?)(?:\s+open|\s+play)?$', clean)
        if m_then:
            q = m_then.group(1).strip()
            # Clean unwanted tokens
            q = re.sub(r'\b(search|open|play|for)\b', '', q).strip()
            if q:
                search_youtube(q)
                return {
                    "action": "youtube_search",
                    "query": q,
                    "response": f"Opening YouTube and searching for {q}, sir."
                }

        # 2. "(search|play|find) <query> on youtube"
        m_on = re.search(r'(?:search|play|find|listen\s+to|watch)\s+(.+?)\s+(?:on|in)\s+youtube', clean)
        if m_on:
            q = m_on.group(1).strip()
            search_youtube(q)
            return {
                "action": "youtube_search",
                "query": q,
                "response": f"Playing {q} on YouTube, sir."
            }

        # 3. "<query> on youtube"
        m_q_yt = re.search(r'^(.+?)\s+(?:on|in)\s+youtube$', clean)
        if m_q_yt:
            q = m_q_yt.group(1).strip()
            q = re.sub(r'\b(open|play|search|for)\b', '', q).strip()
            if q:
                search_youtube(q)
                return {
                    "action": "youtube_search",
                    "query": q,
                    "response": f"Searching YouTube for {q}, sir."
                }

        # 4. "youtube search <query>" or "open youtube and search <query>"
        m_search = re.search(r'(?:open\s+)?youtube\s+(?:and\s+)?(?:search|play|find)\s+(.+)', clean)
        if m_search:
            q = m_search.group(1).strip()
            search_youtube(q)
            return {
                "action": "youtube_search",
                "query": q,
                "response": f"Searching YouTube for {q}, sir."
            }

        # 5. Just open YouTube home: "open youtube", "youtube open", "launch youtube"
        if clean in ("open youtube", "youtube open", "youtube", "launch youtube", "go to youtube"):
            open_url(WEBSITES["youtube"])
            return {
                "action": "open_url",
                "url": WEBSITES["youtube"],
                "response": "Opening YouTube right away, sir."
            }

        # 6. YouTube with leftover words: "youtube <query>"
        m_leftover = re.search(r'youtube\s+(.+)', clean)
        if m_leftover:
            q = m_leftover.group(1).strip()
            q = re.sub(r'\b(open|play|search|then)\b', '', q).strip()
            if q:
                search_youtube(q)
                return {
                    "action": "youtube_search",
                    "query": q,
                    "response": f"Searching YouTube for {q}, sir."
                }

    # ---------------------------------------------------------
    # B. General Google Search Intent
    # Examples:
    # "search waz"
    # "google waz"
    # "search for python tutorials"
    # "google search react documentation"
    # ---------------------------------------------------------
    m_google = re.search(r'^(?:google|search|google\s+search|search\s+for|search\s+google\s+for)\s+(.+)$', clean)
    if m_google and not any(w in clean for w in ("folder", "app", "application", "file")):
        q = m_google.group(1).strip()
        # Avoid simple "open" queries
        if q not in ("youtube", "google", "notepad", "calculator"):
            search_google(q)
            return {
                "action": "google_search",
                "query": q,
                "response": f"Searching Google for {q}, sir."
            }

    # ---------------------------------------------------------
    # C. Open Websites
    # Examples: "open google", "open facebook", "open github", "open chatgpt"
    # ---------------------------------------------------------
    for site, url in WEBSITES.items():
        pattern = rf'^(?:open|launch|go\s+to)\s+{re.escape(site)}(?:\.com)?$'
        pattern_rev = rf'^{re.escape(site)}\s+open$'
        if re.search(pattern, clean) or re.search(pattern_rev, clean):
            open_url(url)
            return {
                "action": "open_url",
                "url": url,
                "response": f"Opening {site.title()}, sir."
            }

    # ---------------------------------------------------------
    # D. Open Folders
    # Examples:
    # "open downloads folder", "downloads open", "open downloads"
    # "open desktop folder", "desktop open", "open desktop"
    # "open documents", "documents folder open"
    # "open pictures", "open videos", "open music"
    # "open c drive", "open folder <name>"
    # ---------------------------------------------------------
    folder_keywords = ["downloads", "desktop", "documents", "pictures", "photos", "videos", "movies", "music", "c drive", "d drive"]

    for fk in folder_keywords:
        if (
            re.search(rf'\bopen\s+{re.escape(fk)}(?:\s+folder)?\b', clean)
            or re.search(rf'\b{re.escape(fk)}(?:\s+folder)?\s+open\b', clean)
            or clean == f"open {fk}"
            or clean == f"{fk} open"
        ):
            success, resolved_path = open_folder(fk)
            if success:
                return {
                    "action": "open_folder",
                    "target": resolved_path,
                    "response": f"Opening your {fk.title()} folder now, sir."
                }

    # Generic "open folder <name>" or "<name> folder open"
    m_generic_folder = re.search(r'(?:open\s+folder\s+(.+)|(.+?)\s+folder\s+open)', clean)
    if m_generic_folder:
        target = (m_generic_folder.group(1) or m_generic_folder.group(2)).strip()
        success, resolved_path = open_folder(target)
        if success:
            return {
                "action": "open_folder",
                "target": resolved_path,
                "response": f"Opening folder {target}, sir."
            }

    # ---------------------------------------------------------
    # E. Launch Windows Applications
    # Examples:
    # "open notepad", "notepad open"
    # "open calculator", "calculator open"
    # "open vs code", "open code", "code open"
    # "open chrome", "chrome open"
    # "open cmd", "open terminal"
    # "open settings", "open task manager"
    # ---------------------------------------------------------
    for app in APP_COMMANDS:
        pattern = rf'^(?:open|launch|start|run)\s+{re.escape(app)}$'
        pattern_rev = rf'^{re.escape(app)}\s+open$'
        if re.search(pattern, clean) or re.search(pattern_rev, clean):
            success, name = open_application(app)
            if success:
                return {
                    "action": "open_app",
                    "app": name,
                    "response": f"Launching {name}, sir."
                }

    # ---------------------------------------------------------
    # F. Time & Date Inquiries
    # ---------------------------------------------------------
    if clean in ("what time is it", "what's the time", "tell me the time", "current time", "time"):
        now_str = datetime.datetime.now().strftime("%I:%M %p")
        return {
            "action": "time_info",
            "response": f"The current time is {now_str}, sir."
        }

    if clean in ("what date is it", "what's the date", "today's date", "date"):
        today_str = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return {
            "action": "date_info",
            "response": f"Today is {today_str}, sir."
        }

    # If no rule-based system automation was detected
    return None

def execute_action_tag(response_text: str) -> tuple[str, Optional[Dict[str, Any]]]:
    """
    Parses and executes an [ACTION: ...] directive emitted by the LLM,
    then cleans it from the spoken/displayed response.
    Format:
      [ACTION: OPEN_URL url="https://..."]
      [ACTION: YOUTUBE_SEARCH query="..."]
      [ACTION: GOOGLE_SEARCH query="..."]
      [ACTION: OPEN_FOLDER path="..."]
      [ACTION: OPEN_APP name="..."]
    """
    pattern = r'\[ACTION:\s*([A-Z_]+)\s+([a-zA-Z_]+)="([^"]+)"\]'
    match = re.search(pattern, response_text)

    if not match:
        return response_text, None

    action_type = match.group(1).upper()
    param_val = match.group(3).strip()

    action_info = {"type": action_type, "param": param_val}

    if action_type == "OPEN_URL":
        open_url(param_val)
    elif action_type == "YOUTUBE_SEARCH":
        search_youtube(param_val)
    elif action_type == "GOOGLE_SEARCH":
        search_google(param_val)
    elif action_type == "OPEN_FOLDER":
        open_folder(param_val)
    elif action_type == "OPEN_APP":
        open_application(param_val)

    # Clean the action tag from the text
    cleaned_text = re.sub(pattern, '', response_text).strip()
    return cleaned_text, action_info
