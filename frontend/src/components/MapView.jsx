import {
    MapContainer,
    TileLayer,
    Marker,
    Circle,
    Popup,
    Polyline,
    LayersControl,
    useMapEvents
} from "react-leaflet";

import { useState } from "react";

import L from "leaflet";

import "leaflet/dist/leaflet.css";


const { BaseLayer } = LayersControl;



const fireIcon = new L.DivIcon({

    className:"fire-marker",

    html:`

    <div style="
        width:26px;
        height:26px;
        background:#d32f2f;
        border:4px solid white;
        border-radius:50%;
        box-shadow:0 0 20px rgba(211,47,47,0.8);
    "></div>

    `,

    iconSize:[35,35],

    iconAnchor:[17,17]

});





function hotspotIcon(level){


    let color="#ff9800";


    if(level==="Extreme"){
        color="#d32f2f";
    }


    if(level==="Medium"){
        color="#ffc107";
    }



    return new L.DivIcon({

        className:"hotspot-marker",

        html:`

        <div style="
            width:18px;
            height:18px;
            background:${color};
            border:3px solid white;
            border-radius:50%;
            box-shadow:0 0 12px ${color};
        "></div>

        `,


        iconSize:[25,25],

        iconAnchor:[12,12]

    });


}







function MapClick({setCoordinates}){


    useMapEvents({


        click(e){


            setCoordinates({

                latitude:e.latlng.lat,

                longitude:e.latlng.lng

            });


        }


    });



    return null;

}








function MapView({

    setCoordinates,

    analysis,

    radiusKm

}){


    const [position,setPosition]=useState(null);




    function updateLocation(coords){


        setPosition([

            coords.latitude,

            coords.longitude

        ]);


        setCoordinates(coords);


    }







    return(


        <MapContainer


            center={[28.4595,77.0266]}

            zoom={11}

            style={{

                height:"100%",

                width:"100%"

            }}

        >



        <LayersControl position="topright">


            <BaseLayer
            checked
            name="Street Map"
            >


                <TileLayer

                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

                />


            </BaseLayer>





            <BaseLayer

            name="Satellite"

            >


                <TileLayer

                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

                />


            </BaseLayer>



        </LayersControl>






        <MapClick

            setCoordinates={updateLocation}

        />







        {position &&

        <>





        <Marker

            position={position}

            icon={fireIcon}

        >


            <Popup>

                🔥 Active Fire Location

            </Popup>


        </Marker>







        <Circle


            center={position}


            radius={
                radiusKm * 1000
            }


            pathOptions={{

                color:"#2e7d32",

                fillColor:"#81c784",

                fillOpacity:0.25

            }}


        />









        {analysis?.hotspots &&

        analysis.hotspots.map((spot)=>(



            <Marker

                key={spot.id}

                position={[

                    spot.latitude,

                    spot.longitude

                ]}


                icon={
                    hotspotIcon(
                        spot.intensity
                    )
                }


            >


                <Popup>


                    <strong>
                    Hotspot {spot.id}
                    </strong>


                    <br/>


                    Risk:
                    {" "}
                    {spot.risk}%


                    <br/>


                    Intensity:
                    {" "}
                    {spot.intensity}


                    <br/>


                    Distance:
                    {" "}
                    {spot.distance} km


                </Popup>



            </Marker>


        ))}



        </>

        }




        </MapContainer>


    );


}



export default MapView;