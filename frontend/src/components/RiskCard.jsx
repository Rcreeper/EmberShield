import "./card.css";


function RiskCard({ risk }) {


    if (!risk) return null;



    return (

        <div className="analysis-card">


            <div className="card-title">

                Risk Assessment

            </div>



            <div className="risk-score">

                {risk.risk_level || "Unknown"}

            </div>



            <div className="card-section">


                <strong>
                    Risk Reason
                </strong>


                <p>
                    {risk.reason || "No risk explanation available."}
                </p>


            </div>




            <div className="card-section">


                <strong>
                    Recommended Actions
                </strong>


                <p>
                    {risk.recommendation ||
                    "Monitor the area and prepare response teams."}
                </p>


            </div>



        </div>

    );


}


export default RiskCard;