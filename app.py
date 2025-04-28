import streamlit as st
from streamlit.components.v1 import html
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import unary_union
import json
import pandas as pd

st.set_page_config(layout="wide")



MAPTILER_KEY = "EtcjLZyGgesPnUV8Gyik" # Replace if needed


flyto_df = pd.read_csv("flyto_config.csv")
flyto_df = flyto_df.fillna('')
flyto_events = flyto_df.to_dict(orient="records")

flyto_events_json = json.dumps(flyto_events)

# Load GeoJSONs
# (Using your original loading logic)
try:
    with open("geojsons/mask_wgs84.geojson") as f:
        mask_geojson = json.load(f)
    with open("geojsons/tsp.geojson") as f:
        tsp_geojson = json.load(f)
    with open("geojsons/streets.geojson") as f:
        streets_geojson = json.load(f)
    with open("geojsons/buildings.geojson") as f:
        buildings_geojson = json.load(f)
    with open("geojsons/Restaurants.geojson") as f:
        restaurants_geojson = json.load(f)
except FileNotFoundError as e:
    st.error(f"GeoJSON file not found: {e}. Please ensure the 'geojsons' folder exists and contains the required files.")
    st.stop()
except Exception as e:
    st.error(f"Error loading GeoJSON data: {e}")
    st.stop()

# --- Define the text for the scrollable box using flyto_config.csv ---
long_text = ""
for _, row in flyto_df.iterrows():
    id = row.get("numb", "N/A")
    name = row.get("name", "Unnamed")
    text = row.get("long_text", "No description available.")
    is_food = row.get("is_food", 1)  # Default to 1 if missing

    # Skip if is_food is 0 or if both name and text are empty
    if int(is_food) != 1 or (str(name).strip() == "" and str(text).strip() == ""):
        continue

    # --- Fix id to be int if possible ---
    try:
        id_display = str(int(float(id)))  # force into int, then string
    except:
        id_display = str(id)

    entry_id = f"entry-{id_display}"

    long_text += f"""
<div id="{entry_id}" class="restaurant-entry">
<h3 style='text-align:center; font-weight:bold; font-size: 16px; line-height: 1.1; margin: 0; padding: 0;'>{id_display}. {name}</h3>    
<p style='text-align:left; margin: 0px 0px 10px 10px;'>{text}</p>
</div>
"""






# Reproject from EPSG:2263 to 4326
# (Using your original reprojection logic)
transformer = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)
def reproject_geom(geom):
    # --- Keeping your original reprojection function ---
    t = geom["type"]
    coords = geom["coordinates"]
    if t == "Polygon":
        return {"type": "Polygon", "coordinates": [[list(transformer.transform(*pt)) for pt in ring] for ring in coords]}
    elif t == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": [[[list(transformer.transform(*pt)) for pt in ring] for ring in poly] for poly in coords]}
    elif t == "LineString":
        return {"type": "LineString", "coordinates": [list(transformer.transform(*pt)) for pt in coords]}
    elif t == "MultiLineString":
        return {"type": "MultiLineString", "coordinates": [[list(transformer.transform(*pt)) for pt in line] for line in coords]}
    elif t == "Point":
        return {"type": "Point", "coordinates": list(transformer.transform(*coords))}
    return geom
# --- Apply reprojection as in your original code ---
try:
    for f in tsp_geojson["features"]:
        if f.get("geometry"): f["geometry"] = reproject_geom(f["geometry"])
    for f in streets_geojson["features"]:
        if f.get("geometry"): f["geometry"] = reproject_geom(f["geometry"])
    for f in restaurants_geojson["features"]:
        if f.get("geometry"): f["geometry"] = reproject_geom(f["geometry"])
    # Apply to buildings if needed in your original logic
    # for f in buildings_geojson["features"]:
    #    if f.get("geometry"): f["geometry"] = reproject_geom(f["geometry"])

    # Filter out park labels
    # (Using your original filtering logic)
    park_union = unary_union([shape(f["geometry"]) for f in tsp_geojson["features"] if f.get("geometry")])
    label_features = [f for f in streets_geojson["features"] if f.get("geometry") and not shape(f["geometry"]).intersects(park_union)]
    label_geojson = {"type": "FeatureCollection", "features": label_features}
except Exception as e:
    st.error(f"Error during geometry processing or filtering: {e}")
    st.stop()


# Legend content
# (Using your original legend logic)
legend_items = "".join([
    f"<div class='legend-item'><strong>{f['properties'].get('Numb')}</strong>: {f['properties'].get('name', 'Unnamed')}</div>"
    for f in restaurants_geojson["features"]
])
# --- Setup color map ---
color_map = {
    "Restaurant": "#6BCB77",
    "Bar": "#8a7367",
    "Cafe": "#FFD93D",
    "Fast Food": "#FFB347",
    "Ice Cream": "#B28DFF",
    "Candy Store": "#F67280",
    "Deli": "#00B8A9"
}

# --- Build the color legend dynamically ---
color_legend = "<div class='legend-row'>"
for amenity, color in color_map.items():
    color_legend += f"""
    <div class="legend-item">
        <div class="blur-aura"></div>
        <span class="legend-swatch" style="background:{color};"></span> {amenity}
    </div>
    """
color_legend += "</div>"



# Use json.dumps for safety when embedding in JS within the f-string
# (This matches your original code's approach)
mask_geojson_str = json.dumps(mask_geojson)
tsp_geojson_str = json.dumps(tsp_geojson)
streets_geojson_str = json.dumps(streets_geojson)
label_geojson_str = json.dumps(label_geojson)
buildings_geojson_str = json.dumps(buildings_geojson)
restaurants_geojson_str = json.dumps(restaurants_geojson)


# --- HTML Component - MINIMAL CHANGES ---
html(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Map with Video Sync</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://unpkg.com/maplibre-gl@2.4.0/dist/maplibre-gl.css" rel="stylesheet" />
  <script src="https://unpkg.com/maplibre-gl@2.4.0/dist/maplibre-gl.js"></script>
  <script src="https://www.youtube.com/iframe_api"></script> <style>
    /* --- Your Original CSS --- */
    html, body {{
     height: 100%;
      margin: 0;
      padding: 0;
      font-family: sans-serif;
      overflow: hidden; /* Added to prevent body scroll */
    }}

     :root {{
      --panel-width: 30vw; /* or any percent-based value, e.g., 25% */
     }}

    #map {{
      position: absolute;
      top: 0;
      right: calc(-1 * var(--panel-width)); /* Shift map right */
      bottom: 0;
      left: 0;
      width: calc(100% + var(--panel-width)) !important;
      margin: 0 !important;
      padding: 0 !important;
      z-index: 0;
    }}

    #video-panel {{
      position: absolute;
      top: 0;
      left: 0;
      width: var(--panel-width);
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: start;
      box-sizing: border-box;
      background: transparent !important;
      backdrop-filter: none !important;
      -webkit-backdrop-filter: none !important;
      z-index: 10;
    }}

    #ytplayer {{
      width: 100%;             /* Take full width of panel */
      height: 270px;           /* Fixed height */
      border: none;
      flex-shrink: 0; /* Prevent player from shrinking */
    }}
    #legend-right {{
    position: fixed;                /* Use fixed so it’s anchored to screen */
    top: 0;
    left: 100%;                     /* Start completely off-screen */
    width: 250px;
    height: 100vh;
    background: rgba(255, 255, 255, 0.3);
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    padding: 20px;
    overflow-y: auto;
    transition: left 0.3s ease;
    z-index: 9999;
    border-left: 1px solid #ccc;
  }}
   #legend-right.open {{
  left: calc(100% - 250px);       /* Slide in so right edge aligns with screen edge */
}}
#map.shifted {{
  left: -250px !important; /* same as width of the menu */
}}

#map {{
  transition: left 0.3s ease;
}}

#map.shifted {{
  left: -250px !important;
}}


#legend-toggle {{
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  background: white;
  border-left: 1px solid #ccc;
  border-radius: 4px 0 0 4px;
  font-size: 24px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10000;

  /* Ensure no margin/border shift on ancestor containers */
  box-sizing: border-box;
}}


    #legend-bottom {{
      position: absolute;
      bottom: 0;
      left: 480px;
      width: calc(100% - 480px);
      font-size: 13px;
      padding: 8px 20px;
      display: flex;
      justify-content: center;
      z-index: 9999;
      box-sizing: border-box;

      background: none;
      border: none;
      box-shadow: none;
    }}
    .legend-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 24px;
      justify-content: center;
      align-items: center;
      padding: 10px 0;
      position: relative;
      z-index: 1;
    }}
    .legend-swatch {{
      width: 14px; /* Diameter of circle */
      height: 14px; /* Diameter of circle */
      display: inline-block;
      margin-right: 5px; /* Spacing after swatch */
      border: 1px solid #888;
      vertical-align: middle;
      border-radius: 50%; /* THIS MAKES IT A CIRCLE */
    }}
    .legend-item {{
  display: block;              /* ← force full-width line */
  font-size: 14px;
  padding: 4px 0;
  margin: 0;
  white-space: normal;         /* allow wrapping inside each line if needed */
}}
     
    .blur-aura {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 90px;  /* tighter area */
      height: 90px;
      transform: translate(-50%, -50%);
      pointer-events: none;
      z-index: -1;
      backdrop-filter: blur(14px);           /* stronger blur */
      -webkit-backdrop-filter: blur(14px);
      mask: radial-gradient(circle, black 0%, transparent 60%);  /* faster falloff */
      -webkit-mask: radial-gradient(circle, black 0%, transparent 60%);
    }}
     

    #legend-right h4 {{ /* Style for consistency */
        margin-top: 0;
        margin-bottom: 5px;
    }}

    /* --- ADDED CSS FOR SCROLLABLE TEXTBOX --- */
    /* IMPORTANT: Escape literal braces {{ }} inside f-string */
    #scrollable-text {{
    width: 100%;
    overflow-y: scroll;
    padding: 10px;
    margin-top: 0; 
    font-size: 14px;
    line-height: 1.5;
    flex-shrink: 0;
    white-space: pre-wrap;

    background-color: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    color: black;

    z-index: 5;
    border: none;
    box-sizing: border-box;

    scrollbar-width: none;
    -ms-overflow-style: none;
  }}
  #scrollable-text::-webkit-scrollbar {{
    display: none;
  }}
.restaurant-entry {{
    padding: 20px 20px 10px 20px;
    transition: background-color 0.3s;
}}

     .restaurant-entry h3, .restaurant-entry p {{
    line-height: 1.2; /* tighter vertical spacing */
}}



  </style>
</head>
<body>
  <div id="video-panel">
    <iframe id="ytplayer" src="https://www.youtube.com/embed/MILdLWASrlI?enablejsapi=1" allow="autoplay; encrypted-media" allowfullscreen></iframe>
    <div id="scrollable-text">{long_text}</div>
  </div>

  <div id="map"></div>
  <div id="legend-toggle" onclick="toggleLegend()">+</div>
  <div id="legend-right">
    <h4 style="margin-top:0;">Restaurants</h4>
    {legend_items}
  </div>
  <div id="legend-bottom">
    {color_legend}
  </div>

  <script>
  // --- Toggle Legend Button ---
  function toggleLegend() {{
    const legend = document.getElementById('legend-right');
    const map = document.getElementById('map');
    const toggle = document.getElementById('legend-toggle');
    const isOpen = legend.classList.contains('open');

    if (isOpen) {{
      legend.classList.remove('open');
      map.classList.remove('shifted');
      toggle.innerHTML = '+';
    }} else {{
      legend.classList.add('open');
      map.classList.add('shifted');
      toggle.innerHTML = '–';
    }}
  }}

  // --- Resize Map, Video Panel, Scrollable Text ---
  function resizeLayout() {{
    const mapElement = document.getElementById('map');
    const videoPanel = document.getElementById('video-panel');
    const scrollableText = document.getElementById('scrollable-text');
    const ytPlayer = document.getElementById('ytplayer');

    if (mapElement && videoPanel && scrollableText && ytPlayer) {{
      const windowHeight = window.innerHeight;
      const videoHeight = ytPlayer.offsetHeight;

      mapElement.style.height = windowHeight + 'px';
      videoPanel.style.height = windowHeight + 'px';
      scrollableText.style.height = (windowHeight - videoHeight) + 'px';
    }}

    const parentFrame = window.frameElement;
    if (parentFrame) {{
      parentFrame.style.height = window.innerHeight + 'px';
    }}
  }}

  window.addEventListener('load', resizeLayout);
  window.addEventListener('resize', resizeLayout);

  // --- Initialize Map ---
  const map = new maplibregl.Map({{
    container: 'map',
    style: 'https://api.maptiler.com/maps/satellite/style.json?key=EtcjLZyGgesPnUV8Gyik',
    center: [-73.9819, 40.7265],
    zoom: 16.75,
    minZoom: 16,
    bearing: 29.2,
    pitch: 0
  }});

  map.on('load', () => {{
    map.addSource('mask', {{ type: 'geojson', data: {mask_geojson_str} }});
    map.addLayer({{
  id: 'mask-fill',
  type: 'fill',
  source: 'mask',
  layout: {{}},   // <--- important for visibility toggling!
  paint: {{ 'fill-color': '#fff', 'fill-opacity': 0.9 }}
}});


    map.addSource('tsp', {{ type: 'geojson', data: {tsp_geojson_str} }});
    map.addLayer({{ id: 'tsp-fill', type: 'fill', source: 'tsp', paint: {{ 'fill-color': '#ff69b4', 'fill-opacity': 0 }} }});

    map.addSource('streets', {{ type: 'geojson', data: {streets_geojson_str} }});
    map.addLayer({{ id: 'streets-lines', type: 'line', source: 'streets', paint: {{ 'line-color': '#ffff00', 'line-width': 3 }} }});

    map.addSource('labels', {{ type: 'geojson', data: {label_geojson_str} }});
    map.addLayer({{
      id: 'street-labels',
      type: 'symbol',
      source: 'labels',
      layout: {{
        'symbol-placement': 'line',
        'text-field': ['get', 'Street_NM'],
        'text-size': 12,
        'symbol-spacing': 180,
        'text-font': ['Helvetica', 'Arial Unicode MS', 'sans-serif']
      }},
      paint: {{
        'text-color': '#ffffff',
        'text-halo-color': '#000000',
        'text-halo-width': 1
      }}
    }});

    map.addSource('buildings', {{ type: 'geojson', data: {buildings_geojson_str} }});
    map.addLayer({{ id: 'buildings', type: 'fill', source: 'buildings', paint: {{ 'fill-color': '#aaa', 'fill-opacity': 0.6 }} }});
    map.addLayer({{ id: 'building-borders', type: 'line', source: 'buildings', paint: {{ 'line-color': '#fff', 'line-width': 0.3 }} }});
    map.addLayer({{
      id: '3d-buildings',
      type: 'fill-extrusion',
      source: 'buildings',
      paint: {{
        'fill-extrusion-color': '#aaa',
        'fill-extrusion-height': ['get', 'heightroof'],
        'fill-extrusion-base': 0,
        'fill-extrusion-opacity': 0.9
      }}
    }});

    map.addSource('restaurants', {{ type: 'geojson', data: {restaurants_geojson_str} }});
    map.addLayer({{
      id: 'restaurants',
      type: 'circle',
      source: 'restaurants',
      paint: {{
        'circle-radius': 10,
        'circle-color': [
  'match',
  ['get', 'amenity'],
  'Restaurant', colorMap['Restaurant'],
  'Bar', colorMap['Bar'],
  'Cafe', colorMap['Cafe'],
  'Fast Food', colorMap['Fast Food'],
  'Ice Cream', colorMap['Ice Cream'],
  'Candy Store', colorMap['Candy Store'],
  'Deli', colorMap['Deli'],
  /* default */ '#4D96FF'
],

        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 1.5
      }}
    }});

    map.addLayer({{
      id: 'restaurant-labels',
      type: 'symbol',
      source: 'restaurants',
      layout: {{
        'text-field': ['get', 'Numb'],
        'text-size': 11,
        'text-font': ['Arial Unicode MS'],
        'text-anchor': 'center',
        'text-allow-overlap': true,
        'text-ignore-placement': true
      }},
      paint: {{ 'text-color': '#000000' }}
    }});
  }});

  // --- Make restaurants GeoJSON accessible ---
const restaurantsData = {restaurants_geojson_str};

// --- Setup color map ---
const colorMap = {{
  "Restaurant": "#6BCB77",
  "Bar": "#8a7367",
  "Cafe": "#FFD93D",
  "Fast Food": "#FFB347",
  "Ice Cream": "#B28DFF",
  "Candy Store": "#F67280",
  "Deli": "#00B8A9"
}};



// --- YouTube Player API ---
var player;
window.onYouTubeIframeAPIReady = function () {{
  player = new YT.Player('ytplayer', {{
    events: {{
      'onReady': function () {{
        const flytoEvents = {flyto_events_json};
        const eventFlags = new Array(flytoEvents.length * 2).fill(false);

const interval = setInterval(() => {{
  if (!player || !map || typeof player.getCurrentTime !== 'function' || !map.isStyleLoaded()) return;

  const time = player.getCurrentTime();

  // --- Manhattan zoom at 56s - 59s ---
if (time >= 56 && time < 59) {{
    map.fitBounds([
      [-74.020, 40.700], // Southwest corner of Manhattan
      [-73.930, 40.880]  // Northeast corner of Manhattan
    ], {{
      padding: 80,
      bearing: 0,
      pitch: 0,
      duration: 3000,
      essential: true
    }});
    return;
}}

// --- East Village zoom at 59s - 1:33s ---
if (time >= 59 && time < 93) {{
    map.fitBounds([
      [-73.9886, 40.7219], // Southwest East Village
      [-73.9730, 40.7308]  // Northeast East Village
    ], {{
      padding: 80,
      bearing: 0,
      pitch: 0,
      duration: 3000,
      essential: true
    }});
    return;
}}

// --- Greenwich Village zoom at 1:33s and after ---
if (time >= 93) {{
    map.fitBounds([
      [-74.0076, 40.7260], // Southwest Greenwich Village
      [-73.9950, 40.7375]  // Northeast Greenwich Village
    ], {{
      padding: 80,
      bearing: 0,
      pitch: 0,
      duration: 3000,
      essential: true
    }});
    return;
}}


  let activeFlyto = null;
  let needReset = true;

  for (let i = 0; i < flytoEvents.length; i++) {{
    const event = flytoEvents[i];
    const cue = parseFloat(event.cue);
    const reset = parseFloat(event.reset);

    if (!isNaN(cue) && !isNaN(reset) && time >= cue && time < reset) {{
      activeFlyto = event;
      needReset = false;
      break;
    }}
  }}

  

// --- HARD-CODED LAYER TOGGLING ---
if (time < 101.5) {{ // 0:00 - 1:40
    map.setLayoutProperty('mask-fill', 'visibility', 'none');
    map.setLayoutProperty('streets-lines', 'visibility', 'none');
    map.setLayoutProperty('street-labels', 'visibility', 'none');
    map.setLayoutProperty('buildings', 'visibility', 'none');
    map.setLayoutProperty('3d-buildings', 'visibility', 'none');
    map.setLayoutProperty('restaurants', 'visibility', 'none');
    map.setLayoutProperty('restaurant-labels', 'visibility', 'none');
}} else if (time >= 101.5 && time < 169) {{ // 1:40 - 2:49
    map.setLayoutProperty('mask-fill', 'visibility', 'visible');
    map.setLayoutProperty('streets-lines', 'visibility', 'none');
    map.setLayoutProperty('street-labels', 'visibility', 'none');
    map.setLayoutProperty('buildings', 'visibility', 'none');
    map.setLayoutProperty('3d-buildings', 'visibility', 'none');
    map.setLayoutProperty('restaurants', 'visibility', 'none');
    map.setLayoutProperty('restaurant-labels', 'visibility', 'none');
}} else if (time >= 169 && time < 171) {{ // 2:49 - 2:51
    map.setLayoutProperty('mask-fill', 'visibility', 'visible');
    map.setLayoutProperty('streets-lines', 'visibility', 'none');
    map.setLayoutProperty('street-labels', 'visibility', 'none');
    map.setLayoutProperty('buildings', 'visibility', 'visible');
    map.setLayoutProperty('3d-buildings', 'visibility', 'visible');
    map.setLayoutProperty('restaurants', 'visibility', 'none');
    map.setLayoutProperty('restaurant-labels', 'visibility', 'none');
}} else if (time >= 171 && time < 178) {{ // 2:51 - 2:58
    map.setLayoutProperty('mask-fill', 'visibility', 'visible');
    map.setLayoutProperty('streets-lines', 'visibility', 'none');
    map.setLayoutProperty('street-labels', 'visibility', 'none');
    map.setLayoutProperty('buildings', 'visibility', 'visible');
    map.setLayoutProperty('3d-buildings', 'visibility', 'visible');
    map.setLayoutProperty('restaurants', 'visibility', 'visible');
    map.setLayoutProperty('restaurant-labels', 'visibility', 'visible');
}} else if (time >= 178) {{ // after 2:58
    map.setLayoutProperty('mask-fill', 'visibility', 'visible');
    map.setLayoutProperty('streets-lines', 'visibility', 'visible');
    map.setLayoutProperty('street-labels', 'visibility', 'visible');
    map.setLayoutProperty('buildings', 'visibility', 'visible');
    map.setLayoutProperty('3d-buildings', 'visibility', 'visible');
    map.setLayoutProperty('restaurants', 'visibility', 'visible');
    map.setLayoutProperty('restaurant-labels', 'visibility', 'visible');
}}


  if (activeFlyto) {{
    const center = map.getCenter();
    const mapX = center.lng;
    const mapY = center.lat;
    const targetX = parseFloat(activeFlyto.x);
    const targetY = parseFloat(activeFlyto.y);
    const targetZoom = parseFloat(activeFlyto.zoom) || 16.75;

    const distance = Math.sqrt(Math.pow(mapX - targetX, 2) + Math.pow(mapY - targetY, 2));

    if (distance > 0.0001) {{
      map.flyTo({{
        center: [targetX, targetY],
        zoom: targetZoom,
        essential: true
      }});

      // --- Scroll text and highlight ---
      const scrollBox = document.getElementById('scrollable-text');
      let entryElement = null;
      if (activeFlyto.numb && activeFlyto.numb !== '') {{
        entryElement = document.getElementById(`entry-${{activeFlyto.numb}}`);
      }} else if (activeFlyto.name && activeFlyto.name !== '') {{
        entryElement = Array.from(document.querySelectorAll('.restaurant-entry')).find(el =>
          el.textContent.includes(activeFlyto.name)
        );
      }}
      if (entryElement && scrollBox) {{
        const scrollBoxTop = scrollBox.getBoundingClientRect().top;
        const entryTop = entryElement.getBoundingClientRect().top;
        const scrollOffset = scrollBox.scrollTop + (entryTop - scrollBoxTop) - scrollBox.clientHeight/2 + entryElement.clientHeight/2;
        scrollBox.scrollTo({{ top: scrollOffset, behavior: 'smooth' }});

        document.querySelectorAll('.restaurant-entry').forEach(el => {{
          el.style.backgroundColor = '';
        }});

        let amenityType = null;
        if (activeFlyto.name) {{
          const matched = restaurantsData.features.find(f =>
            f.properties.name && f.properties.name.trim() === activeFlyto.name.trim()
          );
          if (matched && matched.properties.amenity) {{
            amenityType = matched.properties.amenity;
          }}
        }}
        const highlightColor = colorMap[amenityType] || '#cccccc';
        entryElement.style.backgroundColor = highlightColor + '66';
        entryElement.style.borderRadius = '8px';
      }}

      if (activeFlyto.name && activeFlyto.name !== '') {{
        map.setPaintProperty('restaurants', 'circle-radius', [
          'case', ['==', ['get', 'name'], activeFlyto.name], 30, 10
        ]);
        map.setLayoutProperty('restaurant-labels', 'text-field', [
          'case', ['==', ['get', 'name'], activeFlyto.name], ['get', 'Numb']
        ]);
        map.setLayoutProperty('restaurant-labels', 'text-size', [
          'case', ['==', ['get', 'name'], activeFlyto.name], 22, 11
        ]);
        map.setLayoutProperty('restaurant-labels', 'text-font', [
          'case', ['==', ['get', 'name'], activeFlyto.name], ['literal', ['Arial Unicode MS Bold']], ['literal', ['Arial Unicode MS']]
        ]);
      }} else if (activeFlyto.numb && activeFlyto.numb !== '') {{
        map.setPaintProperty('restaurants', 'circle-radius', [
          'case', ['==', ['get', 'Numb'], parseInt(activeFlyto.numb)], 30, 10
        ]);
        map.setLayoutProperty('restaurant-labels', 'text-field', [
          'case', ['==', ['get', 'Numb'], parseInt(activeFlyto.numb)], ['get', 'name'], ['get', 'Numb']
        ]);
        map.setLayoutProperty('restaurant-labels', 'text-size', [
          'case', ['==', ['get', 'Numb'], parseInt(activeFlyto.numb)], 22, 11
        ]);
        map.setLayoutProperty('restaurant-labels', 'text-font', [
          'case', ['==', ['get', 'Numb'], parseInt(activeFlyto.numb)], ['literal', ['Arial Unicode MS Bold']], ['literal', ['Arial Unicode MS']]
        ]);
      }}
    }}
  }} else if (needReset) {{
    const center = map.getCenter();
    const mapX = center.lng;
    const mapY = center.lat;
    const resetX = -73.9819;
    const resetY = 40.7265;

    const distance = Math.sqrt(Math.pow(mapX - resetX, 2) + Math.pow(mapY - resetY, 2));

    if (distance > 0.0001) {{
      map.flyTo({{
        center: [resetX, resetY],
        zoom: 16.75,
        bearing: 29.2,
        pitch: 0,
        essential: true
      }});
      map.setPaintProperty('restaurants', 'circle-radius', 10);
      map.setLayoutProperty('restaurant-labels', 'text-field', ['get', 'Numb']);
      map.setLayoutProperty('restaurant-labels', 'text-size', 11);
      map.setLayoutProperty('restaurant-labels', 'text-font', ['literal', ['Arial Unicode MS']]);
    }}
  }}
}}, 300);

      }}
    }}
  }});
}};

  // --- Scroll Highlight Active Section ---
  const scrollBox = document.getElementById('scrollable-text');
  const entries = document.querySelectorAll('.restaurant-entry');

  function highlightCenteredEntry() {{
    const boxCenter = scrollBox.scrollTop + scrollBox.clientHeight / 2;
    let closestEntry = null;
    let closestDistance = Infinity;

    entries.forEach(entry => {{
      const rect = entry.getBoundingClientRect();
      const entryCenter = rect.top + rect.height / 2;
      const distance = Math.abs(entryCenter - window.innerHeight / 2);

      if (distance < closestDistance) {{
        closestDistance = distance;
        closestEntry = entry;
      }}
    }});

    entries.forEach(entry => entry.classList.remove('active'));
    if (closestEntry) {{
      closestEntry.classList.add('active');
    }}
  }}

  scrollBox.addEventListener('scroll', highlightCenteredEntry);
  window.addEventListener('load', highlightCenteredEntry);

function reportResize() {{
  const height = document.body.scrollHeight;
  const parentFrame = window.parent;
  if (parentFrame) {{
    parentFrame.postMessage({{isStreamlitMessage: true, type: "streamlit:resize", height: height}}, "*");
    setTimeout(() => {{
      parentFrame.postMessage({{isStreamlitMessage: true, type: "streamlit:rendered"}}, "*");
    }}, 100); // small delay to make sure resize is processed first
  }}
}}

window.addEventListener("load", reportResize);
window.addEventListener("resize", reportResize);

</script>

</body>
</html>
""", height=825, scrolling=False) # Adjust height as needed for the overall component frame

st.markdown("""
<style>
    html, body, #root, .stApp {
        margin: 0 !important;
        padding: 0 !important;
        height: 100vh !important;
        background: transparent !important;
        overflow: auto !important;
    }

    header, footer, [data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .block-container, .main, .stAppViewContainer, .stMain, .stAppViewBlockContainer {
        margin: 0 !important;
        padding: 0 !important;
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
        background: transparent !important;
    }

    .st-emotion-cache-1dp5vir.e1f1d6gn3,
    .st-emotion-cache-13ln4jf.e1f1d6gn3 {
        padding: 0 !important;
        margin: 0 !important;
    }

    iframe, .element-container {
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        display: block !important;
    }

    .main > div:first-child,
    .main > div:last-child {
        margin: 0 !important;
        padding: 0 !important;
        height: 0 !important;
    }

    .stApp {
        padding: 0 !important;
        margin: 0 !important;
    }

    #ytplayer {
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        display: block;
    }
            

</style>
""", unsafe_allow_html=True)