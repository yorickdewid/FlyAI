import math
import datetime
from geopy.point import Point
from geopy.distance import geodesic
from dataclasses import dataclass
from io import StringIO

# from shapely import Point
# from shapely.geometry import LineString, Point

# Aircraft: Robin DR40 Diesel (Jet A1)
# Base: EHRD (Rotterdam Airport)
# Operator: Vliegclub Rotterdam (VCR)
# Operation: VFR
# Cruise Speed: 105 knots
# Fuel: Jet A1
# POB: Max 3
# Fuel Capacity: 110 liters
# MTOW: 980 kg
# Fuel Consumption: 20 liters per hour at cruise
# Default Enroute Altitude: 1500 feet
# Minimum Reserve Fuel: 30 minutes
# Taxi Time Addition: 10 minutes to flight time
# Alternate Airport for EHRD: EHMZ (Midden Zeeland)
# Flight Plan Filing: 1 hour in advance
# Primary Navigation Tool: SkyDemon
# Fuel calculations Includes the 30-minute safety margin.


# TODO: Add max pax
# TODO: Add operator
# TODO: Add limitations to the aircraft
@dataclass
class Aircraft:
    registration: str
    type: str
    callsign: str
    cruise_speed: int
    climb_speed: int
    descent_speed: int
    rate_of_climb: int
    rate_of_descent: int
    fuel_capacity: int
    fuel_consumption: int
    mtow: int = None

    def __str__(self):
        return f"{self.registration} ({self.type})"

    def __repr__(self):
        return f"{self.registration} ({self.type})"


@dataclass
class RunwayWindVector:
    angle: float
    headwind: float
    crosswind: float

    @property
    def headwind2(self) -> int:
        return round(self.headwind)

    @property
    def crosswind2(self) -> int:
        return abs(round(self.crosswind))

    @property
    def direction(self) -> str:
        return "from the right" if self.crosswind > 0 else "from the left"


@dataclass
class Runway:
    designator: str
    heading: int

    def wind(self, wind_direction, wind_speed) -> RunwayWindVector:
        """Calculate the headwind and crosswind components for a runway"""
        wind_angle = math.radians(wind_direction - self.heading)
        headwind = wind_speed * math.cos(wind_angle)
        crosswind = wind_speed * math.sin(wind_angle)
        return RunwayWindVector(wind_angle, headwind, crosswind)


@dataclass
class Waypoint:
    name: str
    coordinates: Point
    altitude: int

    def distance(self, other: "Waypoint") -> float:
        """Calculate the distance between two waypoints"""
        return geodesic(self.coordinates, other.coordinates).nm

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.name}"


@dataclass
class Frequency:
    value: str
    # unit: int
    # type: int
    name: str
    primary: bool
    public: bool


@dataclass
class Airport:
    name: str
    icao: str
    magnetic_declination: float
    country: str
    center: Waypoint
    ppr: bool
    runways: list[Runway] = None
    frequencies: list[Frequency] = None

    def runway_in_use(self, metar: "Metar") -> tuple[Runway, RunwayWindVector]:
        """Find the runway in use based on the wind direction"""
        in_use = min(
            self.runways,
            key=lambda r: abs(r.wind(metar.wind_direction, metar.wind_speed).angle),
        )
        return (in_use, in_use.wind(metar.wind_direction, metar.wind_speed))

    def __str__(self):
        return f"{self.name} ({self.icao})"

    def __repr__(self):
        return f"{self.name} ({self.icao})"


@dataclass
class Cloud:
    cover: str
    base: int

    def __str__(self):
        name = self.cover
        if self.cover == "BKN":
            name = "Broken"
        elif self.cover == "OVC":
            name = "Overcast"
        elif self.cover == "SCT":
            name = "Scattered"
        elif self.cover == "FEW":
            name = "Few"

        return f"{name} at {self.base} ft"


@dataclass
class Metar:
    station: str
    time: str
    raw: str
    raw_taf: str
    wind_direction: int
    wind_speed: int
    wind_gust: int
    visibility: str
    weather: str
    temperature: int
    dewpoint: int
    pressure: int
    remarks: str
    clouds: list[Cloud] = None


class FlightPlan:
    def __init__(
        self,
        route: list[Airport | Waypoint],
        aircraft: None | Aircraft = None,
        metar: list[Metar] = [],
        **kwargs,
    ):
        self.route = route
        self.aircraft = aircraft
        self.metar = metar
        self.kwargs = kwargs

    def find_metar(self, icao: str) -> Metar | None:
        metar = next((m for m in self.metar if m.station == icao), None)
        return metar

    def find_waypoint(self, name: str) -> Waypoint | None:
        for waypoint in self.route:
            if waypoint.name == name:
                return waypoint
            elif isinstance(waypoint, Airport):
                if waypoint.icao == name:
                    return waypoint

    def add_waypoint(self, waypoint: Waypoint | Airport):
        self.route.insert(-1, waypoint)

    def add_waypoint_after(self, waypoint: Waypoint | Airport, after: str):
        self.route.insert(self.route.index(self.find_waypoint(after)) + 1, waypoint)

    @property
    def departure(self) -> Airport | Waypoint:
        return self.route[0]

    @property
    def arrival(self) -> Airport | Waypoint:
        return self.route[-1]

    def __str__(self):
        output = StringIO()

        current_utc_time = datetime.datetime.now(datetime.timezone.utc)
        formatted_utc_time = current_utc_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        output.write(
            f"Flight plan from {self.departure} to {self.arrival} generated at {formatted_utc_time}\n"
        )
        output.write(
            f"\nNOTE: This flightplan is based on actual (calculated) data and must be used as is.\n"
        )
        if self.aircraft:
            output.write(f"\nAircraft:\n")
            output.write(f"  Registration: {self.aircraft.registration}\n")
            output.write(f"  Type: {self.aircraft.type}\n")
            output.write(f"  Callsign: {self.aircraft.callsign}\n")
            output.write(f"  Cruise speed: {self.aircraft.cruise_speed} kt\n")
            output.write(f"  Climb speed: {self.aircraft.climb_speed} kt\n")
            output.write(f"  Descent speed: {self.aircraft.descent_speed} kt\n")
            output.write(f"  Rate of climb: {self.aircraft.rate_of_climb} ft/min\n")
            output.write(f"  Rate of descent: {self.aircraft.rate_of_descent} ft/min\n")
            output.write(f"  Fuel capacity: {self.aircraft.fuel_capacity} liters\n")
            output.write(
                f"  Fuel consumption: {self.aircraft.fuel_consumption} liters/hour\n"
            )
            output.write(f"  Maximum takeoff weight: {self.aircraft.mtow} kg\n")

        output.write(f"\nRoute:\n")
        for i, waypoint in enumerate(self.route):
            output.write(f"  {i+1}. {waypoint}\n")
            if i < len(self.route) - 1:
                if isinstance(waypoint, Airport):
                    current_waypoint = waypoint.center
                else:
                    current_waypoint = waypoint
                if isinstance(self.route[i + 1], Airport):
                    next_waypoint = self.route[i + 1].center
                else:
                    next_waypoint = self.route[i + 1]
                distance = current_waypoint.distance(next_waypoint)
                output.write(f"     + Distance: {round(distance)} nm\n")

                if self.aircraft:
                    time = distance / self.aircraft.cruise_speed
                    time_in_min = round(time * 60)
                    output.write(f"     + Time: {time_in_min} minutes\n")
                    fuel_required = time * self.aircraft.fuel_consumption
                    output.write(
                        f"     + Fuel required: {math.ceil(fuel_required)} liters\n"
                    )

        for i, waypoint in enumerate(self.route):
            # if i == 0:
            #     output.write(f"\nDeparture:\n")
            # elif i == len(self.route) - 1:
            #     output.write(f"\nArrival:\n")
            # else:
            #     output.write(f"\nWaypoint {i+1}:\n")

            if isinstance(waypoint, Airport):
                output.write(f"\nAerodrome: {waypoint}\n")
                output.write(f"  ICAO: {waypoint.icao}\n")
                output.write(f"  Type: Airport\n")
                output.write(f"  PPR required: {'Yes' if waypoint.ppr else 'No'}\n")
                output.write(f"  Frequencies:\n")
                for frequency in waypoint.frequencies:
                    output.write(f"    {frequency.name} ({frequency.value})\n")

                # TODO: Add an option to bind multiple METARs to an waypoint
                metar = self.find_metar(waypoint.icao)
                if metar:
                    runway_in_use, runway_wind = waypoint.runway_in_use(metar)

                    output.write(f"  Runway in use: {runway_in_use.designator}\n")
                    output.write(f"    Headwind: {runway_wind.headwind2} kt\n")
                    output.write(
                        f"    Crosswind: {runway_wind.crosswind2} kt {runway_wind.direction}\n"
                    )

                    output.write(f"  METAR:\n")
                    output.write(f"    Station: {metar.station}\n")
                    output.write(f"    Time: {metar.time}\n")
                    output.write(f"    RAW: {metar.raw}\n")
                    output.write(
                        f"    Wind: {metar.wind_direction} degrees at {metar.wind_speed} kt\n"
                    )
                    if metar.wind_gust:
                        output.write(f"    Wind gust: {metar.wind_gust} kt\n")
                    # TODO: Find the actual visibility
                    if metar.visibility == "6+":
                        output.write(f"    Visibility: 10+ km\n")
                    else:
                        output.write(f"    Visibility: {metar.visibility}\n")
                    output.write(f"    Temperature: {metar.temperature}°C\n")
                    output.write(f"    Dewpoint: {metar.dewpoint}°C\n")
                    output.write(f"    Pressure (QNH): {metar.pressure} hPa\n")
                    output.write(f"    Clouds:\n")
                    for cloud in metar.clouds:
                        output.write(f"      {cloud}\n")

                    output.write(f"  TAF:\n")
                    output.write(f"    RAW: {metar.raw_taf}\n")

        return output.getvalue()


def print_flight_plan(dep: Airport, arr: Airport, metar: list[Metar], craft: Aircraft):
    print(
        f"\nFlight plan {dep.name} ({dep.icao}) to {arr.name} ({arr.icao}) with {craft.registration}"
    )

    # TODO: Add weater information (wind, temperature, pressure) + runway in use + risks

    dist = dep.center.distance(arr.center)

    time = dist / craft.cruise_speed
    time_in_min = round(time * 60)
    time_in_min_total = time_in_min + 10  # 10 minutes for taxi, takeoff and landing

    fuel_consumed = time * craft.fuel_consumption

    print(f"\n  Enroute:")
    print(f"    Distance between the airports: {dist:.2f} nm")
    print(f"    Estimated time enroute: {time_in_min} minutes")
    print(f"    Estimated time total: {time_in_min_total} minutes")
    print(f"    Fuel consumed during flight: {math.ceil(fuel_consumed)} liters")

    print(f"\n  Remarks:")
    # print(f"    Magnetic declination: {dep.magnetic_declination} degrees")
    if fuel_consumed > craft.fuel_capacity:
        print(f"    - Refuel between departure and arrival")
    elif fuel_consumed > (craft.fuel_capacity / 2):
        print(f"    - Refuel before departure")

    # TODO: Check crosswind and headwind
    if dep_metar.wind_speed > 20:
        print(f"    - Strong winds at departure")
    if arr_metar.wind_speed > 20:
        print(f"    - Strong winds at arrival")

    if dep_metar.temperature < 0:
        print(f"    - Cold temperatures at departure")
    if arr_metar.temperature < 0:
        print(f"    - Cold temperatures at arrival")
    if dep_metar.temperature > 30:
        print(f"    - Hot temperatures at departure")
    if arr_metar.temperature > 30:
        print(f"    - Hot temperatures at arrival")
    # if dep_metar.temperature - arr_metar.temperature > 10:
    #     print(f"    - Temperature difference between departure and arrival")
    # if dep_metar.temperature - arr_metar.temperature < -10:
    #     print(f"    - Temperature difference between departure and arrival")
