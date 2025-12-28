import numpy as np
import matplotlib.pyplot as plt
import time

class Rocket:
    def __init__(self):
        # --- FALCON 9 FT SPECS (Approximate) ---
        self.mass_dry = 22200.0      # kg
        self.mass_fuel = 5000.0       # kg (Landing reserve)
        self.height = 1500.0          # m
        self.velocity = -130.0        # m/s (Initial descent)
        self.acceleration = -9.81     # m/s^2
        
        self.g0 = 9.81                
        self.isp = 282.0              # Merlin 1D Sea Level
        self.max_thrust = 845000.0    # Newtons (1 Engine)
        self.min_throttle = 0.55      # 55% floor
        self.max_throttle = 1.0

    def get_total_mass(self):
        return self.mass_dry + self.mass_fuel

class FlightComputer:
    def __init__(self):
        self.burn_triggered = False
        
        # PID Gains (Tuned for F9 mass/thrust)
        self.Kp = 1.2    # Proportional: Corrects current velocity error
        self.Ki = 0.05   # Integral: Corrects steady-state bias
        self.Kd = 0.6    # Derivative: Prevents overshoot (damping)
        
        self.integral_error = 0
        self.last_error = 0

    def calculate_throttle(self, h, v, m, rocket_specs, dt):
        # 1. Physics Calculations
        max_a = (rocket_specs.max_thrust / m) - rocket_specs.g0
        # We target 90% of max acceleration to keep a control margin
        target_a = max_a * 0.9 

        # 2. Suicide Burn Logic (When to start the engine)
        # s = v^2 / 2a
        h_required = (v**2) / (2 * target_a)
        
        if h <= h_required:
            self.burn_triggered = True

        if not self.burn_triggered:
            return 0.0

        # 3. PID Control Logic
        # Target velocity based on current height: v = sqrt(2ah)
        target_v = -np.sqrt(2 * target_a * h) if h > 0.1 else 0
        
        error = target_v - v
        self.integral_error += error * dt
        derivative = (error - self.last_error) / dt
        self.last_error = error

        # Base throttle to maintain target_a + PID adjustments
        hover_throttle = (m * (rocket_specs.g0 + target_a)) / rocket_specs.max_thrust
        adjustment = (self.Kp * error) + (self.Ki * self.integral_error) + (self.Kd * derivative)
        
        raw_throttle = hover_throttle + adjustment
        return np.clip(raw_throttle, rocket_specs.min_throttle, rocket_specs.max_throttle)

def run_landing_sim():
    rocket = Rocket()
    computer = FlightComputer()
    
    # Simulation Parameters
    dt = 0.05
    sim_time = 0
    history = {'t':[], 'h':[], 'v':[], 'a':[], 'thr':[]}

    # Setup Live Plotting
    plt.ion()
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    plt.subplots_adjust(hspace=0.4)

    print("--- F9 Telemetry Link Established ---")

    while rocket.height > 0:
        # 1. Sense & Decide
        m = rocket.get_total_mass()
        throttle = computer.calculate_throttle(rocket.height, rocket.velocity, m, rocket, dt)
        
        # 2. Physics Engine (Newton's 2nd Law)
        thrust = throttle * rocket.max_thrust if rocket.mass_fuel > 0 else 0
        
        # Update Mass
        if rocket.mass_fuel > 0:
            m_dot = thrust / (rocket.g0 * rocket.isp)
            rocket.mass_fuel -= m_dot * dt
        
        rocket.acceleration = (thrust / m) - rocket.g0
        rocket.velocity += rocket.acceleration * dt
        rocket.height += rocket.velocity * dt
        sim_time += dt

        # Safety: Catch ground impact
        if rocket.height < 0:
            rocket.height = 0

        # 3. Store Data
        history['t'].append(sim_time)
        history['h'].append(rocket.height)
        history['v'].append(rocket.velocity)
        history['a'].append(rocket.acceleration)
        history['thr'].append(throttle)

        # 4. Update Visualization (Every 4 frames for performance)
        if len(history['t']) % 4 == 0:
            for ax in [ax1, ax2, ax3]: ax.clear()
            
            # Altitude Chart
            ax1.plot(history['t'], history['h'], color='dodgerblue', linewidth=2)
            ax1.set_ylabel("Altitude (m)")
            ax1.set_title("Vehicle Telemetry (Real-Time)")
            ax1.grid(True, alpha=0.3)
            
            # Velocity Chart
            ax2.plot(history['t'], history['v'], color='crimson', linewidth=2)
            ax2.set_ylabel("Velocity (m/s)")
            ax2.grid(True, alpha=0.3)
            
            # Acceleration Chart
            ax3.plot(history['t'], history['a'], color='forestgreen', linewidth=2)
            ax3.set_ylabel("Accel (m/s²)")
            ax3.set_xlabel("Time (s)")
            ax3.grid(True, alpha=0.3)
            plt.suptitle("SpaceX Falcon 9 First Stage Landing Simulation", fontsize=16)
            plt.pause(0.01)

    # --- FINAL REPORT ---
    impact_v = abs(history['v'][-1])
    print("\n--- MISSION TERMINATED ---")
    print(f"Touchdown Velocity: {impact_v:.2f} m/s")
    print(f"Fuel Remaining: {rocket.mass_fuel:.1f} kg")

    if impact_v < 2.0:
        print("STATUS: SUCCESS. LETS FUCKING GO The Falcon LANDED BABY.")
    elif impact_v < 7.0:
        print("STATUS: HARD LANDING. Structural damage Womp Womp")
    else:
        print("STATUS: CRASH (RUD). Vehicle destroyed Big WOMP.")

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    run_landing_sim()
