import sys
sys.path.append('../../stationsim')
from particle_filter_gcs import ParticleFilter
from stationsim_gcs_model import Model
import multiprocessing

model_params = {
    'pop_total': 100,
    'batch_iterations': 10000,
    'do_history': False,
    'do_print': False,
    'station': 'Grand_Central',
}

filter_params = {
    'number_of_particles': 1000,
    'number_of_runs': 1,
    'resample_window': 100,
    'multi_step': True,
    'particle_std': 0.5, # Particle noise read from task array variable
    'model_std': 1.0,  # was 2 or 10
    'agents_to_visualise': 100,
    'do_save': True,
    'plot_save': False,
    'do_ani': False,
    'show_ani': False, # Don't actually show the animation. They can be extracted later from self.animation
    'external_data': True
}
filter_params['model_step_time_limit_secs'] = 1 # 10 set a time limit minute time limit
pf = ParticleFilter(Model, model_params, filter_params, numcores = int(multiprocessing.cpu_count()))

import numpy as np
for model in pf.models:
    for agent in model.agents:
        speed_max = 0
        while speed_max <= model.speed_min:
            speed_max = np.random.normal(model.speed_mean, model.speed_std)
        agent.speeds = np.arange(speed_max, model.speed_min, - model.speed_step)
        agent.speed = np.random.choice((agent.speeds))
result = pf.step()
pf.pool.close()