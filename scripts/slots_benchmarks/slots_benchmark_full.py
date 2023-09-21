from multiprocessing import cpu_count
from pathlib import Path
import time

from bgpy import SpecialPercentAdoptions
from bgpy import ROVSimpleAS
from bgpy import Simulation, SubprefixHijack, ScenarioConfig


def main():
    """Runs the defaults"""

    assert False, "Turn asserts off! (With -O flag)"

    # Simulation for the paper
    sim = Simulation(  # type: ignore
        percent_adoptions=(
            SpecialPercentAdoptions.ONLY_ONE,
            0.1,
            0.2,
            0.4,
            0.8,
            SpecialPercentAdoptions.ALL_BUT_ONE,
        ),
        scenario_configs=(
            ScenarioConfig(ScenarioCls=SubprefixHijack, AdoptASCls=ROVSimpleAS),
        ),
        output_dir=Path("~/Desktop/slots_benchmark_graphs").expanduser(),
        num_trials=100,
        parse_cpus=cpu_count(),
        python_hash_seed=1,
    )
    start = time.perf_counter()
    sim.run()
    print(time.perf_counter() - start)


if __name__ == "__main__":
    main()