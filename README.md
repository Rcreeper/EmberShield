\# EmberShield



\## Overview



EmberShield is an AI-assisted wildfire emergency analysis platform that helps visualize fire incidents, analyze environmental conditions, and identify nearby settlements at risk using live geospatial and weather data.



\## Features



\- Interactive map with Street and Satellite views

\- Fire incident selection

\- Live weather analysis

\- Fire spread prediction based on wind

\- Nearby settlement detection

\- Emergency risk assessment

\- Interactive analysis dashboard

\- Adjustable analysis radius



\## Tech Stack



\### Frontend

\- React (Vite)

\- React Leaflet

\- Axios

\- CSS



\### Backend

\- FastAPI

\- Python



\### APIs

\- Open-Meteo API

\- OpenStreetMap (Overpass API)

\- ArcGIS World Imagery



\## Installation



\### Frontend



```bash

cd frontend

npm install

npm run dev

```



\### Backend



```bash

cd backend

pip install -r requirements.txt

uvicorn main:app --reload

```



\## Folder Structure



```

EmberShield/

├── frontend/

├── backend/

├── LICENSE

├── README.md

└── .gitignore

```



\## Future Improvements



\- Satellite vegetation analysis (NDVI)

\- NASA FIRMS integration

\- Terrain-aware fire spread prediction

\- Historical wildfire analysis

\- AI-based evacuation recommendations



\## Authors



Ruaan Sharma

