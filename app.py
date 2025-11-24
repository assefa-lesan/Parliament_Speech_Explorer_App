import json
from pathlib import Path
from fasthtml.common import *
app, rt = fast_app()

BASE = Path(__file__).parent
MOCK_DIR = BASE / "data" / "mock"
MEDIA_DIR = BASE / "media"
DOWNLOAD_DIR = MEDIA_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---- STATIC FILES ---
@rt('/static/<path>')
def static_files(req, path):
        return static_file(path, static_dir=BASE / "static")

@rt('/media/<path>')
def media_files(req, path):
    return static_file(path, static_dir=BASE / "media")

#-----------------------
# Utilities
#-----------------------
def load_all_sessions():
    """Load all json files inside data/mock and return list of session dicsts"""
    sessions = []
    for json_file in sorted(MOCK_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                #ensure expected keys
                sessions.append(data)
        except Exception as e:
            #skip bad files but continue
            print("faild load", json_file, e)
    return sessions        

def flatten_segments(sessions):
    """Turn sessions -> segments list with session metadata attached"""
    segments = []
    for s in sessions:
        session_id = s.get("session_id") or s.get("id") or "session_unknown"
        speaker = s.get("speaker", "")
        date = s.get("date", "")
        full_session_url = s.get("full_session_url", "")
        for seg in s.get("segments", []):
            segments.append({
                "session_id": session_id,
                "session_speaker": speaker,
                "session_date": date,
                "full_session_url": full_session_url,
                "segment_id": seg.get("id"),
                "audio_url": seg.get("audio_url"),
                #support both keys for backwards compatability
                "transcript_am": seg.get("transcript_am") or "",
                "transcript_en": seg.get("transcript_en") or ""
            })
    return segments        

#------------------------
# ROUTE 1: Landing Page 
#------------------------
@rt('/') 
def get_home(req):
    return Html(
        Head(
            Title("Parliament Speech Explorer"),
            Link(rel="stylesheet", href="/static/style.css") # <-- links CSS
        ),
        Body(
            Div({"class": "container hero"},
                H1("Parliament Speech Explorer"),
                P("A prototype to unlock Ethiopian Parliamentary Speeches using AI"),
                A("Go to Explorer", href="/explorer", cls="btn"),
                Footer(
                    P("Prototype • For Journalists & Researchers • Powered by Lesan AI tools")
                )
            )
        )
    )

#--------------------------
#Route 2: Explorer with pagination + Search + lang Toggle
#--------------------------
@rt('/explorer')
def explorer(req):
    # load and flatten
    sessions = load_all_sessions()
    all_segments = flatten_segments(sessions)

    # query params
    query = req.query_params.get("q", "").strip()
    page = int(req.query_params.get("page", "1") or 1)
    per_page = int(req.query_params.get("per_page", 3))
    lang = req.query_params.get("lang", "am")

    #search -> multilingual (search both transcript + speaker + date)
    def matches(seg, q):
        ql = q.lower()
        # normalize presence; search in both transcripts
        if ql in (seg.get("session_speaker", "") or "").lower():
            return True
        if ql in (seg.get("session_date", "") or "").lower():
            return True
        if ql in (seg.get("transcript_am") or "").lower() or ql in (seg.get("transcript_en") or "").lower():
            return True
        return False 
    if query:
        filtered = [s for s in all_segments if matches(s, query)]
    else:
        filtered = all_segments

    total = len(filtered)
    total_pages = max(1, (total + per_page -1) // per_page)
    #clamp page
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page
    page_segments = filtered[start:end]

    # Build search bar + language toggle
    search_bar_div = Div({"class":"search-bar"},
        Form({"action":"/explorer", "method":"get"},
            Input({
              "type": "text",
              "placeholder": "🔍︎ Search to Explore Speeches in Amharic or English",
              "name": "q",
            }),
            Input({"type": "hidden", "name": "lang", "value": lang}),
            Input({"type": "submit", "value": "Search", "class": "btn"})
        ),
        Div({"class":"lang-toggle"},
            A("AM", href=f"/explorer?q={query}&lang=am&page=1", cls= "small-btn" + (" active" if lang=="am" else "")),
            A("EN", href=f"/explorer?q={query}&lang=en&page=1", cls= "small-btn" + (" active" if lang=="en" else ""))
        )
    )

    # Build Results Card
    results = Div({"id": "results"},
        *[
            Div({"class": "speech-card"},
                Div({"class": "card-header"},
                    Img({"src": "/static/placeholder2.png", "alt": "speaker-thumb"}),
                    Audio({"controls": True, "src": seg["audio_url"], "class": "audio-player"})
                ),
                P(f"Speaker: {seg['session_speaker']} | Date: {seg['session_date']}"),
                #show transcript according to language toggle 
                P(seg["transcript_am"] if lang=="am" else (seg["transcript_en"] or seg["transcript_am"])),
                Div({"class": "card-footer"},
                    A("View Full Session", href=f"/session/{seg['session_id']}?lang={lang}", cls="btn")
                )
            )
            for seg in page_segments
        ]
    )

    # Pagination UI 
    def page_link(p, label=None):
        label = label or str(p)
        qparam = f"?q={query}&lang={lang}&page={p}&per_page={per_page}"
        return A(label, href=f"/explorer{qparam}", cls="page-link" +(" active" if p==page else ""))

    pagination_controls = Div({"class":"pagination"},
        # previous
        (page_link(page-1, "Prev") if page>1 else Span("Prev", {"class":"page-link disabled"})),
        # numeric pages - cap visual pages to nearby numbers
        *([
            page_link(p) for p in range(max(1, page-3), min(total_pages+1, page+4))
        ]),
        (page_link(page+1, "Next") if page<total_pages else Span("Next", {"class":"page-link disabled"})),
        Span(f"  (Page {page} of {total_pages})", {"class":"page-info"})
    )
    
    return Html(
        Head(
            Title("Explore - Parliament Speech Explorer"),
            Link(rel="stylesheet", href="/static/style.css")
        ),
        Body(
            Div({"class":"container"},
                H1("Explore Parliament Speech"),
                search_bar_div,
                results,
                pagination_controls,
                Div({"style":"margin-top:12px; text-align:center;"},
                    A("Back to Home", href="/", cls="btn")
                )
            )
        )
    )

#-------------------------
# Route: Session Detail Page + Transcript Dowload
#-------------------------
@rt('/session/<session_id>')
def session_detail(req, session_id):
    lang = req.query_params.get("lang", "am")
    sessions = load_all_sessions()
    session = next((s for s in sessions if (s.get("session_id") == session_id)), None)
    if not session:
        return Html(
        Head(Title("Not Found")), 
        Body(
            H1("Session Not Found"), 
            A("Back to Explorer", href="/explorer")
        )
    )
    speaker = session.get("speaker", "")
    date = session.get("date", "")
    full_session_url = session.get("full_session_url", "")
    
    # Media embed detection (YouTube vs audio file)
    media_node = None
    if full_session_url and ("youtube.com" in full_session_url or "you.be" in full_session_url):
        # convert to embed link simply
        # naive: convert watch?v= embed/
        embed = full_session_url.replace("watch?v", "embed/").replace("youtu.be/", "youtube.com/embed")
        media_node = Div({"class": "session-media"},
                        HtmlNode(f'<iframe width="100%" height="360" src="{embed}" frameborder="0" allowfullscreen></iframe>')                        
        )
    elif full_session_url:
        # use audio tag (from local path)
        media_node = Audio({"controls": True, "src": full_session_url, "class": "audio-player-larger"})
    else:
        media_node = P("No main media provided for this session") 

    #  Build snippets list
    snippet_nodes = []
    for seg in session.get("segments", []):
        text = seg.get("transcript_am") if lang=="am" else seg.get("transcript_en") or seg.get("transcript_am")
        #option (segments should have 'start' key
        ts = seg.get("start", "")
        header = f"[{ts}] {seg.get('id')}" if ts else f"{seg.get('id')}"
        snippet_nodes.append(Div({"class":"snippet"}, Strong(header), P(text)))
    
    # Download link (writes a text file into media/downloads and serves it) 
    download_href = f"/session/{session_id}/download?lang={lang}"
    
    return Html(
        Head(Title(f"Session {session_id} - {speaker}"), Link(rel="stylesheet", href="/static/style.css")),
        Body(
            Div({"class":"container"},
                Div({"class":"session-header"},
                    H2(f"{speaker} — {date}"),
                    Div({"class":"session-action"},
                        A("Back to Explorer", href=f"/explorer?lang={lang}&page=1", cls="btn small"),
                        A("Download Transcript", href=download_href, cls="btn")
                    )
                ),
                media_node,
                Div({"class":"session-snippets"},
                    H3("Transcript"),
                    *snippet_nodes
                )
            )
        )
    ) 

@rt('/session/<session_id>/download')
def session_download(req, session_id):
    lang = req.query_params.get("lang", "am")
    sessions = load_all_sessions()
    session = next((s for s in sessions if (s.get("session_id") == session_id)), None)
    if not session:
        return Html(Head(Title("Not Found")), Body(H1("Session not found")))
    # Build text content
    lines = []
    for seg in session.get("segments", []):
        text = seg.get("transcript_am") if lang=="am" else seg.get("transcript_en") or seg.get("transcript_am")
        lines.append(f"{seg.get('id')}\n{text}\n")
    content = "\n".join(lines)
    fname = f"{session_id}_{lang}.txt"
    outpath = DOWNLOAD_DIR / fname
    outpath.write_text(content, encoding="utf-8")
    return static_file(str(outpath.name), static_dir=DOWNLOAD_DIR)

serve()