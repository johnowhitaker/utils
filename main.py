from fasthtml.common import *
# from fasthtml_apps.about import ar as about_api_router

app = FastHTML(hdrs=(picolink))
# about_api_router.to_app(app)

@app.get("/")
def home():
    return Titled("Hello World", Main(
        P("This is a paragraph"),
        A("See About Page", href="/about"),
        cls="container"
    ))

# Static files from static_apps
static_apps_dir = Path(__file__).parent / "static_apps"
print(static_apps_dir)
for path in static_apps_dir.glob("*"):
    if path.is_dir():
        app_name = path.name
        print(f"Adding route: /{app_name}")
        @app.get(f'/{app_name}')
        def serve_index(app_name: str = app_name):
            return FileResponse(static_apps_dir / app_name / 'index.html')
        
        for asset in (path/'assets').glob("*"):
            asset_name = asset.name
            print(f"Adding asset: {app_name}/{asset_name}")
            @app.get(f'/assets/{app_name}/{asset_name}')
            def serve_asset(asset_name: str = asset_name, app_name: str = app_name):
                return FileResponse(static_apps_dir / app_name / 'assets' / asset_name)
            
        # Modify the index.html to use the asset path with the app name
        index_html = (static_apps_dir / app_name / 'index.html').read_text()
        index_html = index_html.replace('src="/assets/index', f'src="/assets/{app_name}/index')
        index_html = index_html.replace('href="/assets/index', f'href="/assets/{app_name}/index')
        (static_apps_dir / app_name / 'index.html').write_text(index_html)

serve()


