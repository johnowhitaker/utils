# utils
Little utilities, mostly AI-made, for my own use.

# Adding Apps

- Standalone HTML files go in their own folder in `static_apps`, as do claude artifacts exported with the tool


# Exporting artifacts

- Clone the tool https://github.com/claudio-silva/claude-artifact-runner
- `npm install`
- Copy code from claude into artifact-component.tsx
- `npx vite build`
- Copy the dist folder to the static_apps folder
- Add an entry to static_apps e.g. `mv dist/ ../utils/static_apps/gravy`
- Optionally test within the folder with `python -m http.server 5454` (or similar)
