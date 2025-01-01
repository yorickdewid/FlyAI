import ai
import service
from dataclasses import asdict

from flask import request
from flask import Flask, Response, render_template, jsonify

from flightplan import Aircraft, FlightPlan

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    data = request.get_json()
    message = data.get("message")
    response = ai.chat(message)
    return jsonify({"message": response})


@app.get("/api/metar/<icao>")
def metar(icao):
    metar = service.fetch_metar(icao)
    return metar


# TODO: Does not work yet
@app.get("/api/airport/<icao>")
def airport(icao):
    airport = service.fetch_airport(icao)
    return asdict(airport)


@app.route("/api/flight-plan/<icao>")
def flight_plan(icao):
    # EGLC, EHMZ, EBSP
    # route = ["EHRD", "EHTX", "EHGG"]
    route = icao.split(",")

    route_aerodomes = [service.fetch_airport(icao) for icao in route]
    # print(route_aerodomes)
    # for aerodome in route_aerodomes:
    #     print(type(aerodome), isinstance(aerodome, Airport))

    metar = service.fetch_metar(route)

    aircraft = Aircraft(
        registration="PH-HLR",
        type="DR40",
        callsign="PH-HLR",
        cruise_speed=105,
        climb_speed=80,
        descent_speed=80,
        rate_of_climb=1000,
        rate_of_descent=500,
        fuel_capacity=100,
        fuel_consumption=20,
        mtow=980,
    )

    plan = FlightPlan(route_aerodomes, aircraft=aircraft, metar=metar)
    # plan.add_waypoint(ehtx)
    # plan.print_report()

    return Response(str(plan), mimetype="text/plain")


if __name__ == "__main__":
    app.run()
