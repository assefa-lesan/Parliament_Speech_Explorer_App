import json
from pathlib import Path
from fasthtml.common import *
app, rt = fast_app()

# ---- STATIC FILES ---
@rt('/static/<path>')
def static_files(req, path):
        return static_file(path, static_dir=Path(__file__).parent / "static")

@rt('/media/<path>')
def media_files(req, path):
    return static_file(path, static_dir=Path(__file__).parent/"media")

# ---- ROUTE 1: Landing Page ----
@rt('/') 
def get():
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

# ---- ROUTE 2: Explorer ( TODO ) ----
@rt('/explorer')
def explorer(req):
    # load mock Speech Data
    data_file = Path(__file__).parent / "data" / "mock" / "speeches.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    session_speaker = data.get("speaker", "")
    session_date = data.get("date", "")
    segments = data.get("segments", [])
   

    speeches = [
        {
            "speaker": session_speaker,
            "date": session_date,
            "audio_url": seg["audio_url"],
            "transcript": seg["transcript"],
            "segment_id": seg["id"]
        }
        for seg in segments
    ]

    #handle search
    query = req.query_params.get("q", "").strip()
    if query:
        speeches = [
            s for s in speeches
            if query in s["speaker"]
            or query in s["transcript"]
            or query in s["date"]
        ]
        
    # build a simple Search Input
    search_bar_div = Div({"class":"search-bar"},
        Form({"action": "/explorer", "method": "get"},
            Input({
                "type": "text",
                "placeholder": "🔍︎ Search to explore speech",
                "name": "q",
                "value": query,
            }),
            Input({"type": "submit", "value": "Search", "class": "btn"}) 
        )          
    )

    # build Results Selection
    results = Div(
        {"id": "results"},
        *[
            Div({"class": "speech-card"},
                Div({"class": "card-header"},
                        Img({"src": "/static/placeholder2.png", "alt": "Speaker", "class": "speaker-thumb"}),
                        Audio({"controls": True, "src": speech["audio_url"], "class": "audio-player"}),
                        Div({"class": "waveform"}, Span(), Span(), Span(), Span(), Span())  
                ),
                
                P(f"Speaker: {speech['speaker']} | Date: {speech['date']}"),
                P(speech["transcript"]),
                Div({"class": "card-footer"},
                    A("View Full Session", href=f"/explorer", cls="btn"),  
                    A("Get Translation", href=f"/explorer", cls="btn translate-btn")
                )
            )
            for speech in speeches    
        ]
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
            A("Back to Home", href="/", cls="btn")
            )
        )
    )

serve()