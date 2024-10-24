from fasthtml.common import *

ar = APIRouter()

@ar("/about")
def about():
    return Titled("About", Main(
        P("This is the about page"),
        A("Go Back Home", href="/",),
        cls="container"
    ))

