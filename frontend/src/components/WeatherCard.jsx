import "./card.css";


function WeatherCard({ weather }) {


    if (!weather) return null;



    return (

        <div className="analysis-card">


            <div className="card-title">

                Weather Conditions

            </div>




            <div className="weather-grid">


                <div className="weather-item">

                    <span>
                        Temperature
                    </span>

                    <strong>
                        {weather.temperature || "--"} °C
                    </strong>

                </div>




                <div className="weather-item">

                    <span>
                        Wind Speed
                    </span>

                    <strong>
                        {weather.wind_speed || "--"} km/h
                    </strong>

                </div>




                <div className="weather-item">

                    <span>
                        Humidity
                    </span>

                    <strong>
                        {weather.humidity || "--"} %
                    </strong>

                </div>




                <div className="weather-item">

                    <span>
                        Condition
                    </span>

                    <strong>
                        {weather.condition || "Unknown"}
                    </strong>

                </div>


            </div>



        </div>

    );

}



export default WeatherCard;