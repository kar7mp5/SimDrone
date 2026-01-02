from simdrone import Simulator
import threading
import time

def main():
    sim = Simulator()
    thread = threading.Thread(target=sim.run)
    thread.start()

    sim.drone.set_control(thrust=0.3)
    time.sleep(2)

    # Hover
    sim.drone.set_control(thrust=0.28)
    time.sleep(2)

    # Pitch forward
    sim.drone.set_control(thrust=0.28, pitch=0.5)
    time.sleep(2)

    # Stop pitching, turn yaw
    sim.drone.set_control(thrust=0.28, pitch=0.0, yaw=0.5)
    time.sleep(2)

    # Stop all
    sim.drone.set_control(thrust=0.0, yaw=0.0)

    thread.join()


if __name__ == "__main__":
    main()