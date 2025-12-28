import numpy as np
import matplotlib.pyplot as plt

class Rocket:
    def __init__(self):
        # --- FALCON 9 FT DATA (From your source) ---
        self.mass_dry = 22200.0      # kg (Inert mass)
        self.mass_fuel = 5000.0      # kg (Landing reserve estimate)
        self.height = 1500.0         # m (Starting altitude for landing burn)
        self.velocity = -120.0       # m/s (Starting downward velocity)
        self.g0 = 9.81               # m/s^2 (Standard gravity)
        self.isp = 282.0             # s (Sea-level Specific Impulse)
        self.max_thrust = 845000.0   # N (Thrust of 1 Merlin 1D engine)
        
        # Hardware Constraints
        self.min_throttle = 0.55     # 55% Minimum throttle
        self.max_throttle = 1.0      # 100% Maximum throttle

    def get_total_mass(self):
        return self.mass_dry + self.mass_fuel

class FlightComputer:
    def decide_throttle(self, height, velocity, mass):
        """
        COMPE TASK: This is where you write the controller.
        Use a PID or a Suicide Burn (Hoverslam) algorithm.
        """
        # --- SIMPLE DUMMY LOGIC FOR TESTING ---
        # (Replace this with PID logic later)
        if height < 500 and velocity < -5:
            return 0.8  # Fire at 80% thrust
        return 0.0

def run_simulation():
    rocket = Rocket()
    computer = FlightComputer()
    
    dt = 0.01  # 100Hz simulation frequency
    time = 0
    history = {'time': [], 'height': [], 'velocity': [], 'thrust': [], 'mass': []}

    print("--- F9 FT Landing Burn Started ---")
    
    while rocket.height > 0:
        # 1. READ SENSORS
        h, v, m = rocket.height, rocket.velocity, rocket.get_total_mass()
        
        # 2. COMPUTE THROTTLE (The Brain)
        raw_throttle = computer.decide_throttle(h, v, m)
        
        # 3. APPLY HARDWARE CONSTRAINTS (Merlin 1D limits)
        if raw_throttle > 0:
            # Clamp between 55% and 100%
            actual_throttle = np.clip(raw_throttle, rocket.min_throttle, rocket.max_throttle)
        else:
            actual_throttle = 0.0
            
        # 4. PHYSICS ENGINE (Newton's 2nd Law)
        thrust_force = actual_throttle * rocket.max_thrust
        
        # Fuel consumption using Isp formula: m_dot = Thrust / (g0 * Isp)
        fuel_burn_rate = thrust_force / (rocket.g0 * rocket.isp)
        if rocket.mass_fuel > 0:
            rocket.mass_fuel -= fuel_burn_rate * dt
        else:
            thrust_force = 0 # No fuel = no thrust
            
        # a = (T - mg) / m
        net_force = thrust_force - (m * rocket.g0)
        acceleration = net_force / m
        
        # Update motion
        rocket.velocity += acceleration * dt
        rocket.height += rocket.velocity * dt
        time += dt
        
        # Record data
        history['time'].append(time)
        history['height'].append(rocket.height)
        history['velocity'].append(rocket.velocity)
        history['thrust'].append(actual_throttle)
        history['mass'].append(m)

    # --- POST-FLIGHT ANALYSIS ---
    impact_v = history['velocity'][-1]
    print(f"Touchdown Time: {time:.2f}s")
    print(f"Landing Velocity: {impact_v:.2f} m/s")
    
    if abs(impact_v) < 5.0:
        print("RESULT: SUCCESSFUL LANDING! ")
    else:
        print("RESULT: Crashed -- Womp Womp")

    # Plot results
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    ax1.plot(history['time'], history['height'], color='blue', label='Altitude')
    ax1.set_ylabel("Height (m)")
    ax1.legend()
    
    ax2.plot(history['time'], history['velocity'], color='red', label='Velocity')
    ax2.plot(history['time'], [t * 10 for t in history['thrust']], '--', color='orange', label='Thrust (scaled)')
    ax2.set_ylabel("Velocity (m/s) / Thrust")
    ax2.legend()
    plt.show()

if __name__ == "__main__":
    run_simulation()
