# Trip Planner - GitHub Pages

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
├── TRIPPLAN GEO LOC/      # Flask backend (optional)
│   └── app.py
└── README.md
```

## 🌐 Navigation Flow

1. **index.html** - Landing page (Info/Welcome)
2. **plan.html** - Trip planner form
3. **result.html** - Results and map

## 🚀 GitHub Pages Deployment

### Your site is live at:
`https://deviprasad101.github.io/travelplan/`

### To update your site:

1. **Make changes** to HTML files
2. **Commit and push**:
   ```bash
   git add .
   git commit -m "Update site"
   git push origin main
   ```
3. **Wait 1-2 minutes** for GitHub Pages to rebuild
4. **Refresh** your site URL

## 📝 How It Works

- **GitHub Pages** automatically serves `index.html` as the landing page
- All files use **static paths** (e.g., `static/images/logo.jpg`)
- Navigation uses **relative links** (e.g., `plan.html`, `result.html`)
- No backend required - fully static site

## 🔧 Optional: Local Flask Backend

If you want to run the Flask backend locally for trip planning:

1. Navigate to Flask directory:
   ```bash
   cd "TRIPPLAN GEO LOC"
   ```

2. Install dependencies:
   ```bash
   pip install flask pandas geopandas folium requests geopy reportlab python-dotenv
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Access at: `http://localhost:5000`

## ⚠️ Important Notes

- The site works as a **static site** on GitHub Pages
- Trip planning features require the **Flask backend** (local only)
- Keep `static/` folder and CSV file in the root
- All image/video paths use `static/` prefix

## 🎯 Quick Links

- **Live Site**: https://deviprasad101.github.io/travelplan/
- **Repository**: https://github.com/Deviprasad101/travelplan
- **Issues**: Report bugs in GitHub Issues

