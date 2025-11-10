from fasthtml.common import *

app, rt = fast_app()

# ---- STATIC FILES ---
@rt('/static/<path>')
def static_files(req, path):
        return static_file(path, static_dir=path(__file__).parent / "static")

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
                P("A prototype to unlock Ethiopian Parliamentary Speechs using AI"),
                A("Go to Explorer", href="/explorer", cls="btn"),
                Footer(
                    P("Prototype • For Journalists & Researchers • Powered by Lesan AI tools")
                )
            )
        )
    )

# ---- ROUTE 2: Explorer ( TODO ) ----
@rt('/explorer')
def explorer():
    return Div(
        H2("Explorer Page"),
        P("This will later show searchable Speeches"),
        A("Back to Home", href="/")
    )

serve()