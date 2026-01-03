from simdrone import Simulator
import threading
import time
import queue

def control_drones(sim):
    """Control logic running in a separate thread."""
    time.sleep(1) # Wait for sim to start
    
    # Drone 0: Hover, Drone 1: Stay
    sim.drones[0].set_control(thrust=0.3)
    sim.drones[1].set_control(thrust=0.0) # Stay on ground
    time.sleep(2)

    # Drone 0: Hover, Drone 1: Takeoff
    sim.drones[0].set_control(thrust=0.28)
    sim.drones[1].set_control(thrust=0.35)
    time.sleep(2)

    # Drone 0: Pitch forward, Drone 1: Hover
    sim.drones[0].set_control(thrust=0.28, pitch=0.01)
    sim.drones[1].set_control(thrust=0.28)
    time.sleep(0.1)

    # Both stop
    sim.drones[0].set_control(thrust=0.0)
    sim.drones[1].set_control(thrust=0.0)
    time.sleep(2)

    # Stop all
    sim.drones[0].set_control(thrust=0.0)
    sim.drones[1].set_control(thrust=0.0)
    time.sleep(1)
    
    sim.running = False

def main():
    num_drones = 2

    # Simulator now manages the plotter internally
    sim = Simulator(num_drones=num_drones)
    
    # Start control thread
    control_thread = threading.Thread(target=control_drones, args=(sim,))
    control_thread.start()

    # Run Simulator in Main Thread
    # (Required for tkinter/matplotlib GUI interaction)
    data = sim.run() 
    
    control_thread.join()

    print('start')
    print(f"Logged {len(data)} entries.")


if __name__ == "__main__":
    main()