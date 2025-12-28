import numpy as np
import matplotlib.pyplot as plt

class Rocket:
    def __init__(self):
        self.mass_dry = 25000.0  # kg
        self.mass_fuel = 10000.0 # kg
        self.height = 1000.0     # m
        self.velocity = 0.0      # m/s
        self.gravity = 9.81      # m/s^2
        self.max_thrust = 800000.0 # Newtons
        self.fuel_consumption_rate = 150.0 # kg/s at full thrust
        
    def get_total_mass(self):
        return self.mass_dry + self.mass_fuel

class FlightComputer:
    def decide_throttle(self, height, velocity):
        """
        COMPE FRIEND: This is your brain.
        Return a value between 0.0 (off) and 1.0 (full blast).
        Currently, it returns 0, so the rocket crashes.
        """
        # Logic goes here! 
        # Example: if velocity < -10: return 0.8
        return 0.0 

def run_simulation():
    rocket = Rocket()
    computer = FlightComputer()
    
    dt = 0.01  # Time step (100Hz)
    time = 0
    
    # Data storage for plotting
    history = {'time': [], 'height': [], 'velocity': [], 'thrust': []}

    print("--- Simulation Started ---")
    
    while rocket.height > 0:
        # 1. SENSING: Get data from rocket
        h = rocket.height
        v = rocket.velocity
        
        # 2. THINKING: Computer decides what to do
        throttle = computer.decide_throttle(h, v)
        
        # 3. ACTING: Apply physics (Newton's 2nd Law)
        # Calculate Thrust Force
        if rocket.mass_fuel > 0:
            thrust_force = throttle * rocket.max_thrust
            fuel_burned = throttle * rocket.fuel_consumption_rate * dt
            rocket.mass_fuel -= fuel_burned
        else:
            thrust_force = 0
            
        # F = ma  ->  a = F/m
        net_force = thrust_force - (rocket.get_total_mass() * rocket.gravity)
        acceleration = net_force / rocket.get_total_mass()
        
        # Update Velocity and Height (Euler Integration)
        rocket.velocity += acceleration * dt
        rocket.height += rocket.velocity * dt
        time += dt
        
        # Store data
        history['time'].append(time)
        history['height'].append(rocket.height)
        history['velocity'].append(rocket.velocity)
        history['thrust'].append(throttle)

    print(f"--- Simulation Ended at {time:.2f}s ---")
    if abs(rocket.velocity) > 5:
        print(f"CRASHED! Impact Velocity: {rocket.velocity:.2f} m/s")
    else:
        print("TOUCHDOWN! Successful landing.")
        
    # --- VISUALIZATION ---
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history['time'], history['height'])
    plt.title("Altitude (m)")
    
    plt.subplot(1, 2, 2)
    plt.plot(history['time'], history['velocity'])
    plt.title("Velocity (m/s)")
    plt.show()

if __name__ == "__main__":
    run_simulation()