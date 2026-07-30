import "./Card.css";


function SettlementCard({ settlements }) {


    return (

        <div className="analysis-card">


            <div className="card-title">

                Nearby Settlements

            </div>




            {

                Array.isArray(settlements) && settlements.length > 0

                ?

                (

                    <ul>

                    {

                        settlements.map(

                            (settlement, index)=>(

                                <li key={index}>


                                    <strong>

                                    {
                                        settlement.name ||
                                        settlement.settlement ||
                                        "Unknown Area"
                                    }

                                    </strong>


                                    <br />


                                    Distance:

                                    {" "}

                                    {

                                        settlement.distance ||
                                        "N/A"

                                    }

                                    km


                                </li>


                            )

                        )

                    }

                    </ul>

                )


                :


                (

                    <p>
                        No nearby settlements detected.
                    </p>

                )


            }




        </div>

    );


}


export default SettlementCard;