from simdrone import Simulator
import threading
import time
import queue
from multiprocessing import Process, Queue
from simdrone.plotter import run_plotter

def main():
    num_drones = 2
    plot_queue = Queue()
    
    # Start Plotter Process
    plot_process = Process(target=run_plotter, args=(plot_queue, num_drones))
    plot_process.start()

    sim = Simulator(num_drones=num_drones, plot_queue=plot_queue)
    result_queue = queue.Queue()
    thread = threading.Thread(target=sim.run, args=(result_queue,))
    thread.start()

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

    # Stop all (high thrust? original code had 100, assuming it stops or crashes)
    sim.drones[0].set_control(thrust=0.0)
    sim.drones[1].set_control(thrust=0.0)
    time.sleep(1)
    
    sim.running = False

    thread.join()
    plot_process.terminate() # Ensure plotter closes
    
    result = result_queue.get()  # Queue에서 data 꺼냄

    print('start')
    # print(result) # result is now a list of dicts from logger, which might be large.
    print(f"Logged {len(result)} entries.")


if __name__ == "__main__":
    main()