import "./Card.css";


function SpreadCard({ spread }) {


    if (!spread) return null;



    return (

        <div className="analysis-card">


            <div className="card-title">

                Fire Spread Prediction

            </div>




            <div className="spread-box">


                <strong>
                    Direction
                </strong>


                <p>

                    {spread.direction || "Unknown"}

                </p>


            </div>





            <div className="spread-box">


                <strong>
                    Estimated Spread Rate
                </strong>


                <div className="spread-value">

                    {spread.rate || "--"}

                </div>


            </div>





            <div className="spread-box">


                <strong>
                    AI Analysis
                </strong>


                <p>

                    {spread.analysis ||
                    "No prediction data available."}

                </p>


            </div>




        </div>

    );


}



export default SpreadCard;