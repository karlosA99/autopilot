from source.environment._map import map, street, intersection
from source.tools.general_tools import distance_from_geo_coord
from source.agents.car import car
from source.agents.client import client
from source.agents.agency import agency
from typing import List, Dict
from scipy.stats import expon, lognorm
from random import randint

import numpy as np

class simulation:
    def __init__(self, map : map, agency : agency, steps : int) -> None:
        self.map = map
        self.agency = agency
        
        self.next_client : client = None
        # List of clients in the sistem
        self.clients : List[client] = []
        # total steps of the simulation
        self.total_time = steps
               
        #region Simulation variables
        
        # simulation time
        self.current_time = 0
        # total clients picked up 
        self.pickups = 0
        # total clients delivered
        self.deliveries = 0
        # total of pickups for each car
        self.cars_pickups : Dict[car, int] = {c : 0 for c in self.agency.cars}
        # total of money for each car
        self.cars_money : Dict[car, float] = {c : 0 for c in self.agency.cars}
        # total of mantainance spent for each car
        self.cars_mantainance : Dict[car, float] = {c : 0 for c in self.agency.cars}
        
        #endregion
    
    def clients_in_movement(self) -> int:
        return self.pickups - self.deliveries

    def get_destination(self, location : street, _distance : float) -> street:
        """Returns a location on the map that is the given distance from the starting location. 
           Euclidean distance is used

        Args:
            location (int): Route origin location
            distance (float): Distance that must exist between the origin and the destination

        Returns:
            street: Location that is at the given distance from the received location
        """
        result = None
        error = np.inf
        
        for _street in self.map.streets:
            distance = distance_from_geo_coord(location.intersection1.geo_coord,_street.intersection1.geo_coord)
            if abs(distance - _distance) < error:
                result = _street
                error = abs(distance - _distance)
        
        return result
        
    
    def generate_client(self) -> None:
        wait_time = round(expon.rvs(size = 1)[0])
        location = self.map.streets[randint(0, len(self.map.streets) - 1)]
        distance = lognorm.rvs(1)*1000
        destination = self.get_destination(location, distance)
        self.next_client = client(location, destination, self.current_time + wait_time)
        
    def client_to_system(self):
        while self.next_client.request_time <= self.current_time:
            self.clients.append(self.next_client)
            self.generate_client()
    
    def car_pickup(self, car : car):
        if not car.busy and self.clients:
            if client := car.pilot.select_client(self.clients, car):
                self.clients.remove(client)
                self.pickups += 1
                self.cars_pickups[car] += 1
    
    def charge_routes(self):
        for car in self.agency.cars:
            self.car_pickup(car)
    
    def move_cars(self):
        for car in self.agency.cars:
            self.map.move_car(car)
    
    def print_status(self):
        print("Time: ", self.current_time)
        print("Clients in movement: ", self.clients_in_movement())
        print("Pickups: ", self.pickups)
        print("Deliveries: ", self.deliveries)
        print("Cars: ")
        for car in self.agency.cars:
            print("Car ", car, " - Pickups: ", self.cars_pickups[car], " - Money: ", self.cars_money[car], " - Mantainance: ", self.cars_mantainance[car])
        print("Next client: ", self.next_client)
    
    def run(self):
        while self.current_time <= self.total_time:
            
            # Generate client if there is none
            if not self.next_client:
                self.generate_client()
            # If next client is in the current time, add it to the sistem and generate a new one
            self.client_to_system()
            # Charge routes for each car
            self.charge_routes()
            # Move cars
            self.move_cars()
            # Print simulation status
            self.print_status()
            
            self.current_time += 1
            
            
    