import { useState } from "react";
import axios from "axios";

import MapView from "./components/MapView";
import RiskCard from "./components/RiskCard";
import WeatherCard from "./components/WeatherCard";
import SpreadCard from "./components/SpreadCard";
import SettlementCard from "./components/SettlementCard";
import CommanderCard from "./components/CommanderCard";

function App() {
  const [coordinates, setCoordinates] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [mode, setMode] = useState("fire");
  const [radiusKm, setRadiusKm] = useState(5);
  const [loading, setLoading] = useState(false);
  const [fireDate, setFireDate] = useState("");
  const [fireTime, setFireTime] = useState("");
  const [analysisLocked, setAnalysisLocked] = useState(false);

  function getWindDirection(degrees) {
    const directions = [
      "North",
      "North-East",
      "East",
      "South-East",
      "South",
      "South-West",
      "West",
      "North-West"
    ];
    return directions[Math.round(degrees / 45) % 8];
  }

  function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  async function getWeather(lat, lon) {
    const response = await axios.get(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m`
    );

    const current = response.data.current;

    return {
      temperature: current.temperature_2m,
      humidity: current.relative_humidity_2m,
      wind_speed: current.wind_speed_10m,
      wind_direction: getWindDirection(current.wind_direction_10m)
    };
  }

  async function getNearbySettlements(lat, lon) {
    try {
      const query = `
        [out:json];
        (
          node["place"="village"](around:10000,${lat},${lon});
          node["place"="town"](around:10000,${lat},${lon});
          node["place"="city"](around:10000,${lat},${lon});
        );
        out;
      `;

      const response = await axios.post(
        "https://overpass-api.de/api/interpreter",
        query,
        {
          headers: {
            "Content-Type": "text/plain"
          }
        }
      );

      return response.data.elements.slice(0, 5).map((place) => {
        const distance = calculateDistance(lat, lon, place.lat, place.lon);

        return {
          name: place.tags?.name || "Unknown",
          latitude: place.lat,
          longitude: place.lon,
          distance: distance.toFixed(1),
          risk: distance < 3 ? "HIGH" : distance < 7 ? "MEDIUM" : "LOW"
        };
      });
    } catch (error) {
      console.error(error);
      return [];
    }
  }

  function calculateRisk(weather) {
    let score = 0;
    let reasons = [];

    if (weather.temperature >= 40) {
      score += 30;
      reasons.push("Extreme temperature");
    } else if (weather.temperature >= 35) {
      score += 20;
      reasons.push("High temperature");
    }

    if (weather.humidity <= 20) {
      score += 25;
      reasons.push("Very low humidity");
    } else if (weather.humidity <= 35) {
      score += 15;
      reasons.push("Dry conditions");
    }

    if (weather.wind_speed >= 30) {
      score += 25;
      reasons.push("Strong winds");
    } else if (weather.wind_speed >= 15) {
      score += 15;
      reasons.push("Moderate winds");
    }

    score += 20;
    reasons.push("Dry vegetation risk");

    return {
      score: Math.min(score, 100),
      reasons
    };
  }

  async function generateAnalysis() {
    if (!coordinates) {
      alert("Select a location first.");
      return;
    }

    setLoading(true);

    try {
      const weather = await getWeather(
        coordinates.latitude,
        coordinates.longitude
      );

      const risk = calculateRisk(weather);

      const settlements = await getNearbySettlements(
        coordinates.latitude,
        coordinates.longitude
      );

      // 1. Renamed variable from hotspots to settlementsOnMap
      const settlementsOnMap = settlements.slice(0, 5).map((settlement, index) => {
        const lat =
          coordinates.latitude +
          (settlement.latitude - coordinates.latitude) * 0.75;

        const lon =
          coordinates.longitude +
          (settlement.longitude - coordinates.longitude) * 0.75;

        return {
          id: index + 1,
          latitude: lat,
          longitude: lon,
          settlement: settlement.name,
          risk: Math.max(45, 90 - index * 10),
          intensity:
            index === 0
              ? "Extreme"
              : index <= 2
              ? "High"
              : "Moderate",
          distance: settlement.distance
        };
      });

      setAnalysis({
        weather,
        // 2. Renamed key from hotspots to map_settlements
        map_settlements: settlementsOnMap,
        spread_prediction: {
          direction: weather.wind_direction,
          rate: (weather.wind_speed / 12).toFixed(1) + " km/hour",
          analysis: `Fire expected to spread towards ${weather.wind_direction}`
        },
        nearby_settlements: settlements,
        risk_analysis: {
          risk_level:
            risk.score >= 85
              ? "CRITICAL"
              : risk.score >= 70
              ? "HIGH"
              : "MODERATE",
          score: risk.score,
          reason: risk.reasons.join(", "),
          recommendation:
            "Create containment zones and prepare evacuation routes."
        },
        commander_response: {
          message:
            mode === "fire"
              ? `Active fire response towards ${weather.wind_direction}`
              : "Multi hotspot scan completed.",
          actions: [
            "Deploy response teams",
            "Protect settlements",
            "Monitor spread"
          ]
        }
      });

      setAnalysisLocked(true);

    } catch (error) {
      console.error(error);
      alert("Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <h1>EmberShield</h1>
        <div className="status">System Online</div>
      </header>

      <div className="main">
        <div className="map-section">
          <MapView
            setCoordinates={setCoordinates}
            analysis={analysis}
            radiusKm={radiusKm}
            analysisLocked={analysisLocked}
          />
        </div>

        <div className="side-panel">
          <div className="card">
            <h2>Analysis Control</h2>

            <button onClick={() => setMode("fire")}>
              Active Fire Tracking
            </button>

            <button onClick={() => setMode("scan")}>
              Multi-Hotspot Scan
            </button>

            <label>Fire Date</label>
            <input
              type="date"
              value={fireDate}
              onChange={(e) => setFireDate(e.target.value)}
            />

            <label>Fire Time</label>
            <input
              type="time"
              value={fireTime}
              onChange={(e) => setFireTime(e.target.value)}
            />

            <label>Radius</label>
            <select
              value={radiusKm}
              onChange={(e) => setRadiusKm(Number(e.target.value))}
            >
              <option value={1}>1 km</option>
              <option value={5}>5 km</option>
              <option value={10}>10 km</option>
            </select>

            <button onClick={generateAnalysis}>
              {loading ? "Analyzing..." : "Generate Emergency Analysis"}
            </button>

            <button
              onClick={() => {
                setAnalysis(null);
                setAnalysisLocked(false);
              }}
            >
              New Analysis
            </button>
          </div>

          {analysis && (
            <>
              <WeatherCard weather={analysis.weather} />
              <SpreadCard spread={analysis.spread_prediction} />
              <SettlementCard settlements={analysis.nearby_settlements} />
              <CommanderCard commander={analysis.commander_response} />
              <RiskCard risk={analysis.risk_analysis} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;