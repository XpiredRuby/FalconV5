import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.gridspec as gridspec

# --- 1. ROCKET PHYSICS ENGINE ---
class Falcon_Heavy_Block5:
    def __init__(self):
        self.mass_dry = 22200.0
        self.mass_fuel = 9500.0       
        self.max_thrust = 845000.0    
        self.g0 = 9.81
        self.isp = 282.0
        
        # Initial State: [x, y, z, vx, vy, vz]
        # Starting high with a nasty crosswind drift setup
        self.state = np.array([0.0, 0.0, 1800.0, 0.0, 0.0, -80.0])
        self.max_tilt = np.radians(30.0) 

    def get_mass(self):
        return self.mass_dry + self.mass_fuel

# --- 2. GUIDANCE COMPUTER (The Brain) ---
class FlightComputer:
    def __init__(self):
        self.mode = "FALL"
        # Vertical P-D-K (K=Kick)
        self.Kp_z = 2.4
        self.Kd_z = 1.8
        
        # Lateral PI-D (I=Integral wind learning)
        self.Kp_xy = 0.15 
        self.Ki_xy = 0.008 
        self.accum_x = 0.0
        self.accum_y = 0.0

    # FIX: Renamed from 'compute' to 'get_commands' to match the main loop
    def get_commands(self, rocket, dt):
        x, y, z, vx, vy, vz = rocket.state
        m = rocket.get_mass()
        
        # A. SUICIDE BURN TRIGGER
        # Safety Margin: We assume we only have 90% thrust (0.9)
        a_avail = (rocket.max_thrust * 0.9 / m) - rocket.g0
        burn_start = (vz**2) / (2 * a_avail) + 150.0
        
        if z < burn_start: self.mode = "LAND"
        if self.mode == "FALL": return 0.0, 0.0, 0.0

        # B. VERTICAL CONTROL
        # Dynamic Limit: "Don't fall faster than this"
        if z > 15.0:
            target_vz = -np.sqrt(2 * a_avail * z * 0.8)
        else:
            target_vz = -1.0 # Touchdown Goal
            
        # CLIMB PREVENTION (Anti-Bounce)
        if vz > -0.1 and z > 3.0: return 0.0, 0.0, 0.0

        # EMERGENCY KICK: If falling too fast near ground, DOUBLE POWER
        kp_boost = 1.0
        if z < 15.0 and vz < -3.0: kp_boost = 3.0 
            
        hover_thr = (m * rocket.g0) / rocket.max_thrust
        err_vz = target_vz - vz
        throttle = hover_thr + (err_vz * self.Kp_z * kp_boost * 0.05)

        # C. LATERAL CONTROL (Wind Fighter)
        # Below 20m, stop hunting for X=0, just hold the angle (Lean into wind)
        if z < 20.0:
            pitch = self.accum_x * self.Ki_xy
            yaw   = self.accum_y * self.Ki_xy
        else:
            target_vx = -x * 0.25
            target_vy = -y * 0.25
            
            self.accum_x += (target_vx - vx) * dt
            self.accum_y += (target_vy - vy) * dt
            
            pitch = ((target_vx - vx) * self.Kp_xy) + (self.accum_x * self.Ki_xy)
            yaw   = ((target_vy - vy) * self.Kp_xy) + (self.accum_y * self.Ki_xy)

        # D. PROTECTION
        pitch = np.clip(pitch, -rocket.max_tilt, rocket.max_tilt)
        yaw   = np.clip(yaw, -rocket.max_tilt, rocket.max_tilt)
        
        # Boost throttle to compensate for tilt loss
        throttle /= np.cos(np.sqrt(pitch**2 + yaw**2))

        return np.clip(throttle, 0.0, 1.0), pitch, yaw

# --- 3. MISSION CONTROL DASHBOARD ---
def run_dashboard():
    r = Falcon_Heavy_Block5()
    cpu = FlightComputer()
    dt = 0.02
    
    # Data Recorders
    hist = {k: [] for k in ['t', 'x', 'y', 'z', 'vx', 'vy', 'vz', 'thr', 'accel', 'limit']}
    
    # STORM SETUP: 35kN Wind (Pushing East)
    WIND_VEC = np.array([0.0, 35000.0, 0.0]) 
    
    # --- PLOT SETUP (GridSpec) ---
    plt.ion()
    fig = plt.figure(figsize=(16, 9), facecolor='#1e1e1e') # Dark Mode Background
    gs = gridspec.GridSpec(2, 4, figure=fig)
    
    # The Main Stage (3D) - Takes up left half
    ax3d = fig.add_subplot(gs[:, :2], projection='3d')
    ax3d.set_facecolor('#1e1e1e')
    
    # The Instruments - Right half
    ax_vel  = fig.add_subplot(gs[0, 2]) # Top Left of Right Side
    ax_thr  = fig.add_subplot(gs[0, 3]) # Top Right of Right Side
    ax_pos  = fig.add_subplot(gs[1, 2]) # Bot Left
    ax_acc  = fig.add_subplot(gs[1, 3]) # Bot Right
    
    # Styling Helper
    def style_ax(ax, title, ylab, color):
        ax.set_facecolor('#2b2b2b')
        ax.grid(True, color='#444444', linestyle='--', alpha=0.5)
        ax.set_title(title, color='white', fontsize=10, fontweight='bold')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        ax.set_ylabel(ylab, color=color, fontsize=9)

    style_ax(ax_vel, "Vertical Velocity", "m/s", "cyan")
    style_ax(ax_thr, "Throttle Command", "%", "red")
    style_ax(ax_pos, "Lateral Drift", "Meters", "lime")
    style_ax(ax_acc, "G-Force Load", "G", "orange")

    step = 0
    print("--- MISSION DASHBOARD ONLINE ---")
    
    while r.state[2] > 0:
        # Guidance - Calling the FIXED method name
        thr, pitch, yaw = cpu.get_commands(r, dt)
        
        # Physics + Wind
        m = r.get_mass()
        gust = np.random.uniform(-8000, 8000, 3); gust[2] = 0
        total_wind = WIND_VEC + gust
        
        F_eng = thr * r.max_thrust
        Fx = F_eng * np.sin(pitch) + total_wind[0]
        Fy = F_eng * np.sin(yaw) + total_wind[1]
        Fz = F_eng * np.cos(np.sqrt(pitch**2 + yaw**2))
        
        # Accel (For Graph)
        accel_g = (F_eng / m) / r.g0
        
        r.state[3] += (Fx/m)*dt
        r.state[4] += (Fy/m)*dt
        r.state[5] += ((Fz/m)-r.g0)*dt
        
        r.state[0] += r.state[3]*dt
        r.state[1] += r.state[4]*dt
        r.state[2] += r.state[5]*dt
        r.mass_fuel -= (F_eng/(r.g0*282.0))*dt

        # Safety Limit Calculation (For Graph)
        a_safe = (r.max_thrust * 0.9 / m) - r.g0
        if r.state[2] > 10:
            limit_v = -np.sqrt(2 * a_safe * r.state[2] * 0.8)
        else:
            limit_v = -1.0
        
        # Logging
        t = step*dt
        hist['t'].append(t); hist['z'].append(r.state[2]); hist['vz'].append(r.state[5])
        hist['thr'].append(thr); hist['accel'].append(accel_g); hist['limit'].append(limit_v)
        hist['x'].append(r.state[0]); hist['y'].append(r.state[1])
        
        step += 1
        
        # Visualization Refresh (Every 20 frames for smoother UI)
        if step % 20 == 0:
            # 1. 3D Plot
            ax3d.clear()
            ax3d.set_facecolor('#1e1e1e')
            ax3d.plot(hist['x'], hist['y'], hist['z'], color='cyan', linewidth=1.5, alpha=0.8)
            
            # Ground & LZ
            ax3d.plot([-300, 300], [0, 0], [0, 0], 'w--', alpha=0.3)
            ax3d.plot([0, 0], [-300, 300], [0, 0], 'w--', alpha=0.3)
            ax3d.scatter([0],[0],[0], color='lime', s=200, marker='X', label='LZ')
            ax3d.scatter([r.state[0]], [r.state[1]], [r.state[2]], color='red', s=50)
            
            # Draw Wind Arrow
            ax3d.quiver(0, -200, 1000, 0, 500, 0, color='yellow', length=200)
            ax3d.text(0, 300, 1000, "WIND ->", color='yellow')
            
            ax3d.set_xlim(-300, 300); ax3d.set_ylim(-300, 300); ax3d.set_zlim(0, 1800)
            ax3d.set_title(f"ALT: {r.state[2]:.0f}m | DIST: {np.sqrt(r.state[0]**2+r.state[1]**2):.0f}m", color='white')
            ax3d.tick_params(colors='white')
            
            # 2. Velocity Graph
            ax_vel.clear(); style_ax(ax_vel, "Vertical Velocity", "m/s", "cyan")
            ax_vel.plot(hist['t'], hist['vz'], 'cyan', linewidth=1.5)
            ax_vel.plot(hist['t'], hist['limit'], 'r--', linewidth=1, alpha=0.6, label='Limit')
            ax_vel.legend(facecolor='#2b2b2b', labelcolor='white', fontsize=8)
            
            # 3. Throttle Graph
            ax_thr.clear(); style_ax(ax_thr, "Throttle Output", "%", "red")
            ax_thr.plot(hist['t'], hist['thr'], 'red', linewidth=1.5)
            ax_thr.set_ylim(0, 1.1)
            
            # 4. Position Graph (Lateral Distance)
            dist_hist = np.sqrt(np.array(hist['x'])**2 + np.array(hist['y'])**2)
            ax_pos.clear(); style_ax(ax_pos, "Distance from Target", "m", "lime")
            ax_pos.plot(hist['t'], dist_hist, 'lime', linewidth=1.5)
            
            # 5. G-Force Graph
            ax_acc.clear(); style_ax(ax_acc, "G-Force", "G", "orange")
            ax_acc.plot(hist['t'], hist['accel'], 'orange', linewidth=1.5)
            
            plt.pause(0.001)

    plt.ioff()
    analyze_landing(r)
    plt.show()

# --- 4. POST-FLIGHT FORENSICS ---
def analyze_landing(r):
    vz = abs(r.state[5])
    v_xy = np.sqrt(r.state[3]**2 + r.state[4]**2)
    dist = np.sqrt(r.state[0]**2 + r.state[1]**2)
    
    print("\n" + "="*50)
    print("FLIGHT DATA RECORDER: FINAL REPORT")
    print("="*50)
    
    # Logic Checks
    safe_vz = vz < 5.0
    safe_vxy = v_xy < 2.5 # No drifting/tipping
    safe_dist = dist < 20.0
    
    print(f"VERTICAL SPEED:   {vz:.2f} m/s  \t[{'PASS' if safe_vz else 'FAIL'}]")
    print(f"LATERAL SLIDE:    {v_xy:.2f} m/s  \t[{'PASS' if safe_vxy else 'FAIL'}]")
    print(f"TARGET ACCURACY:  {dist:.2f} m    \t[{'PASS' if safe_dist else 'FAIL'}]")
    
    print("-" * 50)
    if safe_vz and safe_vxy:
        if safe_dist:
            print("MISSION STATUS: [ BULLSEYE LANDING ]")
        else:
            print("MISSION STATUS: [ SAFE LANDING (OFF TARGET) ]")
    else:
        if not safe_vz:
            print("MISSION STATUS: [ CRASH - HARD IMPACT ]")
        elif not safe_vxy:
            print("MISSION STATUS: [ CRASH - TIPPED OVER ]")

if __name__ == "__main__":
    run_dashboard()
