import "./Card.css";


function CommanderCard({ commander }) {


    if (!commander) return null;



    return (

        <div className="analysis-card">


            <div className="card-title">

                Emergency Commander

            </div>





            <div className="command-box">


                <p>

                    {commander.message ||

                    commander.recommendation ||

                    "No emergency response generated."}

                </p>


            </div>





            {

                commander.actions && (


                    <div className="card-section">


                        <strong>
                            Recommended Actions
                        </strong>




                        <ul>


                            {

                                commander.actions.map(
                                    
                                    (action,index)=>(

                                        <li key={index}>

                                            {action}

                                        </li>

                                    )

                                )

                            }


                        </ul>


                    </div>


                )

            }



        </div>

    );


}



export default CommanderCard;