import numpy as np
import matplotlib.pyplot as plt

class Rocket:
    def __init__(self):
        # --- FALCON 9 FT SPECS ---
        self.mass_dry = 22200.0      # kg (Inert mass)
        self.mass_fuel = 5000.0      # kg (Landing reserve)
        self.height = 1500.0         # m (Starting altitude)
        self.velocity = -120.0       # m/s (Starting downward velocity)
        self.g0 = 9.81               # m/s^2 (Gravity)
        self.isp = 282.0             # s (Sea-level Merlin 1D efficiency)
        self.max_thrust = 845000.0   # N (Thrust of 1 Merlin 1D)
        
        # Hardware Constraints
        self.min_throttle = 0.55     # 55% Minimum throttle
        self.max_throttle = 1.0      # 100% Maximum throttle

    def get_total_mass(self):
        return self.mass_dry + self.mass_fuel
## PID EDIT ##
class FlightComputer:
    def __init__(self):
        self.burn_triggered = False

    def decide_throttle(self, h, v, m, max_t, isp, g):
        # 1. CALCULATE Acceleration max right now
        a_now = (max_t / m) - g # which should be about 21.25617647 I think
        
        # 2. About How much mass is lost throughout
        m_dot_max = max_t / (g * isp)
        t_est = abs(v) / a_now
        m_final = m - (m_dot_max * t_est)
        
        # 3. Calculating the H burn throughout both masses (w/o fuel)
        a_final = (max_t / m_final) - g
        a_avg = (a_now + a_final) / 2
        h_required = (v**2) / (2 * a_avg)

        # 4. TRIGGER LOGIC
        # If we reach the required height, start the burn.
        if h <= (h_required + 1.5): # 1.5m buffer for compute lag
            self.burn_triggered = True

        if not self.burn_triggered:
            return 0.0

        # 5. THROTTLE CONTROL (CompE Lead's logic)
        # We aim for h_required to stay slightly above our current height
        # This is a basic Proportional (P) controller
        error = h_required - h
        raw_output = 1.0 + (error * 0.1) # Try to stay at 100% unless we are too slow

        # 6. APPLY HARDWARE CONSTRAINTS (The 55% Floor)
        if raw_output < 0.55:
            actual_throttle = 0.55
        elif raw_output > 1.0:
            actual_throttle = 1.0
        else:
            actual_throttle = raw_output
            
        # 7. AUTO-SHUTDOWN
        # If velocity is near zero or positive, kill the engine to prevent flying back up
        if v >= -0.1:
            return 0.0
            
        return actual_throttle

def run_simulation():
    rocket = Rocket()
    computer = FlightComputer()
    
    dt = 0.01 
    time = 0
    history = {'time': [], 'height': [], 'velocity': [], 'throttle': [], 'mass': []}

    print("--- F9 FT Landing Burn Sequence Initialized ---")
    
    while rocket.height > 0:
        # Get Sensor Data
        h, v, m = rocket.height, rocket.velocity, rocket.get_total_mass()
        
        # Computer decides throttle
        throttle = computer.decide_throttle(h, v, m, rocket.max_thrust, rocket.isp, rocket.g0)
        
        # PHYSICS ENGINE
        # Calculate Thrust and Mass Flow
        thrust_force = throttle * rocket.max_thrust
        m_dot = thrust_force / (rocket.g0 * rocket.isp)
        
        if rocket.mass_fuel > 0:
            rocket.mass_fuel -= m_dot * dt
        else:
            thrust_force = 0
            
        # Newton's 2nd Law: a = (Thrust - Weight) / mass
        acceleration = (thrust_force - (m * rocket.g0)) / m
        
        # Euler Integration
        rocket.velocity += acceleration * dt
        rocket.height += rocket.velocity * dt
        time += dt
        
        # Save Data
        history['time'].append(time)
        history['height'].append(rocket.height)
        history['velocity'].append(rocket.velocity)
        history['throttle'].append(throttle)
        history['mass'].append(m)

        # Emergency Stop if we start flying back up too much
        if rocket.velocity > 5.0 and rocket.height > 10:
            print("CRITICAL: Rocket is flying back into space! Adjust PID.")
            break

    # Results
    impact_v = history['velocity'][-1]
    print(f"Touchdown at {time:.2f}s | Impact Velocity: {impact_v:.2f} m/s")
    
    # VISUALIZATION
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    ax1.plot(history['time'], history['height'], 'b', label="Altitude (m)")
    ax1.axhline(0, color='black', linestyle='--')
    ax1.set_title("Falcon 9 Landing Burn Profile")
    ax1.legend()
    
    ax2.plot(history['time'], history['velocity'], 'r', label="Velocity (m/s)")
    ax2.plot(history['time'], [t * 10 for t in history['throttle']], 'g--', label="Throttle (10x)")
    ax2.axhline(0, color='black', linestyle='--')
    ax2.legend()
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_simulation()


