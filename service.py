import os
import httpx
from geopy.point import Point
from flightplan import (
    Aircraft,
    Airport,
    Cloud,
    FlightPlan,
    Frequency,
    Metar,
    Runway,
    Waypoint,
)


def fetch_metar(icao: str | list[str]) -> list[Metar]:
    if isinstance(icao, str):
        icao_list = icao
    else:
        icao_list = ",".join(icao)
    url = f"https://aviationweather.gov/api/data/metar?ids={icao_list}&format=json&taf=true"

    response = httpx.get(url)
    if response.status_code == 200:
        items = response.json()
        # print(items)

        metars = []
        for item in items:
            if item["mostRecent"] == 0:
                continue

            metar = Metar(
                station=item["icaoId"],
                time=item["reportTime"],
                raw=item["rawOb"],
                raw_taf=item["rawTaf"] if "rawTaf" in item else None,
                wind_direction=item["wdir"],
                wind_speed=item["wspd"],
                wind_gust=item["wgst"],
                visibility=item["visib"],
                weather=item["wxString"],
                temperature=item["temp"],
                dewpoint=item["dewp"],
                pressure=item["altim"],
                remarks=item["rawOb"],
                clouds=[Cloud(c["cover"], c["base"]) for c in item["clouds"]],
            )
            metars.append(metar)
        return metars
    else:
        response.raise_for_status()


def fetch_airport(icao: str) -> Airport:
    url = (
        f"https://api.core.openaip.net/api/airports?search={icao}&private=false&limit=1"
    )
    headers = {"x-openaip-api-key": os.getenv("OPENAIP_API_KEY")}
    response = httpx.get(url, headers=headers)
    if response.status_code == 200:
        items = response.json()

        # TODO: Check if items is not empty

        runways = []
        for runway in items["items"][0]["runways"]:
            runways.append(
                Runway(designator=runway["designator"], heading=runway["trueHeading"])
            )

        frequencies = []
        for frequency in items["items"][0]["frequencies"]:
            frequencies.append(
                Frequency(
                    value=frequency["value"],
                    # unit=frequency["unit"],
                    # type=frequency["type"],
                    name=frequency["name"],
                    primary=frequency["primary"],
                    public=frequency["publicUse"],
                )
            )

        airport = Airport(
            name=items["items"][0]["name"],
            icao=items["items"][0]["icaoCode"],
            magnetic_declination=items["items"][0]["magneticDeclination"],
            country=items["items"][0]["country"],
            center=Waypoint(
                name=items["items"][0]["name"],
                coordinates=Point(
                    items["items"][0]["geometry"]["coordinates"][1],
                    items["items"][0]["geometry"]["coordinates"][0],
                ),
                altitude=items["items"][0]["elevation"],
            ),
            ppr=items["items"][0]["ppr"],
            runways=runways,
            frequencies=frequencies,
        )
        return airport
    else:
        response.raise_for_status()


if __name__ == "__main__":
    import service

    # EGLC, EHMZ, EBSP
    route = ["EHRD", "EHTX", "EHGG"]

    route_aerodromes = [service.fetch_airport(icao) for icao in route]
    # print(route_aerodromes)
    # for aerodrome in route_aerodromes:
    #     print(type(aerodrome), isinstance(aerodrome, Airport))

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

    ehrd_hotel_dep = Waypoint(
        name="EHRD HOTEL",
        coordinates=Point(51.971667, 4.126667),
        altitude=0,
    )

    ehtx_delta_arr = Waypoint(
        name="EHTX DELTA",
        coordinates=Point(53.115556, 4.899167),
        altitude=0,
    )

    ehgg_xray_arr = Waypoint(
        name="EHGG XRAY",
        coordinates=Point(53.209722, 6.460000),
        altitude=0,
    )

    plan = FlightPlan(route_aerodromes, aircraft=aircraft, metar=metar)
    plan.add_waypoint_after(ehrd_hotel_dep, "EHRD")
    plan.add_waypoint_after(ehtx_delta_arr, "EHRD HOTEL")
    plan.add_waypoint_after(ehgg_xray_arr, "EHTX DELTA")
    print(plan)
