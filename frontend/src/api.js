import axios from "axios";

const API = axios.create({
    baseURL: "http://127.0.0.1:8000"
});

export const analyzeFire = async (
    latitude,
    longitude,
    fireStartTime,
    radiusKm
) => {

    const response = await API.post("/analyze", {
        latitude: latitude,
        longitude: longitude,
        fire_start_time: fireStartTime,
        radius_km: radiusKm
    });

    return response.data;
};

export default API;