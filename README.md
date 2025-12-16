# Trip Planner - GitHub Pages Setup

## 📁 File Structure

```
travelplan/
├── index.html              # Landing page (Info/Welcome)
├── plan.html               # Trip planning form
├── result.html             # Results page
├── trip_plan_map.html      # Generated map
├── static/                 # Static assets
│   ├── images/            # Images
│   └── videos/            # Videos
├── tirupati_places_final_updated.csv
└── TRIPPLAN GEO LOC/      # Original Flask app (for local development)
    └── app.py
```

## 🌐 GitHub Pages Navigation Flow

1. **index.html** - First page (Info/Welcome page)
2. **plan.html** - Second page (Trip planner form)
3. **result.html** - Third page (Results and map)

## 🚀 Deployment Instructions

### For GitHub Pages (Static Site):

1. **Commit all files** in the root directory:
   ```bash
   git add index.html plan.html result.html static/ tirupati_places_final_updated.csv
   git commit -m "Setup GitHub Pages with proper navigation flow"
   git push origin main
   ```

2. **Configure GitHub Pages**:
   - Go to your repository settings
   - Navigate to "Pages" section
   - Set source to "Deploy from a branch"
   - Select branch: `main`
   - Select folder: `/ (root)`
   - Click Save

3. **Access your site**:
   - Your site will be available at: `https://[username].github.io/travelplan/`
   - It will automatically open `index.html` first

### For Local Development (Flask App):

1. Navigate to the Flask app directory:
   ```bash
   cd "TRIPPLAN GEO LOC"
   ```

2. Run the Flask app:
   ```bash
   python app.py
   ```

3. Access at: `http://localhost:5000`

## ⚠️ Important Notes

- **GitHub Pages** uses the files in the **root directory** (`index.html`, `plan.html`, `result.html`)
- **Flask app** uses files in the **TRIPPLAN GEO LOC** subdirectory
- Keep both versions in sync if you make changes
- The root HTML files use **static paths** (e.g., `static/images/...`)
- The subdirectory HTML files use **Flask templates** (e.g., `{{ url_for(...) }}`)

## 🔧 Troubleshooting

**Problem**: GitHub Pages shows wrong page first
- **Solution**: Ensure `index.html` is in the repository root

**Problem**: Images not loading on GitHub Pages
- **Solution**: Check that `static/` folder is in the root and paths are correct

**Problem**: Navigation not working
- **Solution**: Verify links use relative paths (`plan.html`, not `/plan`)
