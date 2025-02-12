from fasthtml.common import *
from monsterui.all import *
from fasthtml.svg import *
from claudette import *
from ghapi.core import GhApi

# Claude bits
model = models[2]
cli = Client(model)
system_prompt = """You are a witty roast master with a good sense of humor. 
Your roasts should be playful and lighthearted, never mean-spirited. 
Make clever observations based on the information provided, and end with a 
compliment to show it's all in good fun."""
def roast_user(user_info):
    return (contents(cli("Please create a playful roast of this GitHub user based on their profile: "+user_info, sp=system_prompt)))

# GitHub bits
api = GhApi()
def get_user_github_profile(username):
    user = api.users.get_by_username(username)
    repos = api.repos.list_for_user(username, sort='updated', per_page=10)
    repo_info = []
    for repo in repos:
        info = {
            'name': repo.name,
            'description': repo.description,
            'stars': repo.stargazers_count,
            'language': repo.language,
            'updated_at': repo.updated_at,
            'is_fork': repo.fork
        }
        
        try:
            commits = api.repos.list_commits(repo.owner.login, repo.name, per_page=3)
            info['recent_commits'] = [{'message': c.commit.message, 'date': c.commit.author.date} for c in commits]
        except Exception as e: info['recent_commits'] = []
        repo_info.append(info)
    
    return {
        'user': {
            'name': user.name,
            'bio': user.bio,
            'followers': user.followers,
            'following': user.following,
            'public_repos': user.public_repos,
            'created_at': user.created_at
        },
        'repos': repo_info
    }
def get_gh_summary(username):
    profile = get_user_github_profile(username)
    
    # Start with user info
    md = f"# GitHub Profile: {profile['user']['name']}\n\n"
    md += f"{profile['user']['bio']}\n\n"
    md += f"* {profile['user']['followers']} followers\n"
    md += f"* {profile['user']['public_repos']} public repositories\n\n"
    
    # Add repo summaries
    md += "## Recent Repositories\n\n"
    for repo in profile['repos']:
        stars = "⭐" * min(3, repo['stars']) if repo['stars'] else ""
        lang = f" `{repo['language']}`" if repo['language'] else ""
        latest = repo['recent_commits'][0]['date'].split('T')[0] if repo['recent_commits'] else 'No recent commits'
        
        md += f"### {repo['name']} {stars}{lang}\n"
        if repo['description']:
            md += f"{repo['description']}\n"
        md += f"Last updated: {latest}\n"
        
        if repo['recent_commits']:
            md += "\nRecent commits:\n"
            for commit in repo['recent_commits']:
                md += f"- {commit['message']}\n"
        md += "\n"
    
    return md

# App
app, rt = fast_app(hdrs=Theme.orange.headers())
style = """#loading-indicator { display: none; }
    #loading-indicator.htmx-request { display: block; }
    """
@rt
def index():
    return Title("GitHub Roaster"), Style(style), Container(
        DivVStacked(
            DivCentered(H1("Roast My GitHub", cls=TextT.lg), cls="space-y-2 mb-8 max-w-md mx-auto"),
            Card(
                DivVStacked(
                    LabelInput("GitHub Username", id='username', placeholder='e.g. johnowhitaker', name='username'),
                    Button(
                        DivLAligned(UkIcon('github', cls='mr-2'), "Roast Me!"),
                        hx_post="/roast", 
                        hx_target="#result", 
                        hx_include="#username", 
                        hx_swap="outerHTML",
                        hx_indicator="#loading-indicator",
                        cls=(ButtonT.primary, "w-full mt-4"),
                    ),
                    Div('Loading...', id="loading-indicator", cls="text-center mt-2")
                ),
                id="result", cls="max-w-md mx-auto"
            ),
            Footer(P("Created with 💀 by a very judgmental AI", cls=(TextPresets.muted_sm, "text-center mt-8"))),
            cls="py-12"
        )
    )
@app.post("/roast")
def roast(username: str):
    gh_info = get_gh_summary(username)
    roast_text = roast_user(gh_info)
    return Card(
        DivCentered(H3(username, cls="text-lg")),
        P(roast_text),
        DivCentered(A(Button("Another Roast", cls=ButtonT.primary), href="/")),
        cls="max-w-lg mx-auto"
    )

serve(port=5005)