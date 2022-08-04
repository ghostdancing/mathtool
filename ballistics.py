
import inspector as ip

CONST_GRAVITY = 9.80665
def trajectory(plot_x, velocity, distance):
    t = plot_x / velocity
    y = - CONST_GRAVITY  * (t*t) / 2
    return y

inspector = ip.use_function(trajectory, {'velocity': 710.0, 'distance': 100.0}, 'Drop is $result meters')
inspector.plot_enabled = True
inspector.plot_max = 'distance'
inspector.plot_min = 0
ip.start()
