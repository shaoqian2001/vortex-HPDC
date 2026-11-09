import os
import sys
import subprocess
from extract_stat import analyze_cache_performance

opencl_bench_apps = ["conv3", "sgemm", "sgemm2", "sgemm3"]

opencl_bench_apps_ai = ["conv3", "sgemm", "sgemm2", "sgemm3", "kmeans", "sfilter", "saxpy", "nearn"]
opencl_bench_apps_ai_broken = ["kmeans", "nearn"]
opencl_bench_apps_ai_complete = list(set(opencl_bench_apps_ai) - set(opencl_bench_apps_ai_broken))
# keep the order of original list
opencl_bench_apps_ai_complete = [app for app in opencl_bench_apps_ai if app in opencl_bench_apps_ai_complete]

# opencl_bench_apps

opencl_bench_apps_hpc = ["stencil", "spmv", "transpose", "vecadd", "dotproduct", "lbm", "bfs", "psum", "psort", "gaussian"]
opencl_bench_apps_hpc_broken = ["stencil", "spmv", "bfs"]
#opencl_bench_apps_hpc_complete 

# remove broken AI and HPC apps from the list
opencl_bench_apps_complete = list((set(opencl_bench_apps_ai) - set(opencl_bench_apps_ai_broken) | set(opencl_bench_apps_hpc)) - set(opencl_bench_apps_hpc_broken))

#opencl_bench_app_hpdc_broken = []

bench_apps_regression = ["conv3x", "sgemmx", "matmul", "sgemm2x", "vecaddx", "stencil3d"]

bench_apps_regression_simple = ["conv3x", "sgemmx", "sgemm2x", "vecaddx"]

# only modify this to set the target apps
#bench_apps = opencl_bench_apps_ai_complete
bench_apps = opencl_bench_apps_ai_complete
#bench_apps = ["sgemm"]

app_args = {
    # "conv3": ["-n32", "-n64", "-n128"],
    # "sgemm": ["-n32", "-n64", "-n128"],
    # "sgemm2": ["-n16", "-n32", "-n64"],
    # "sgemm3": ["-n16", "-n32", "-n64"]
}

vortex_configs = []

# socket size
socket_single_core_config = "-DSOCKET_SIZE=1"
socket_quad_core_config = "-DSOCKET_SIZE=4"

# LSU scaling

# thread
thread_2_params = "--threads=2"   # this will lead to 2 LSU_LANES = 16B lsu line which fits L1_Line_size of 64B
thread_4_params = "--threads=4"   # this will lead to 4 LSU_LANES = 32B lsu line which fits L1_Line_size of 64B
thread_8_params = "--threads=8"   # this will lead to 8 LSU_LANES = 64B lsu line which fits L1_Line_size of 64B
thread_16_params = "--threads=16" # this will lead to 16 LSU_LANES = 128B which exceeds L1_Line_size of 64B
thread_32_params = "--threads=32" # this will lead to 32 LSU_LANES = 256B which exceeds L1_Line_size of 64B

# warp
warp_8_params = "--warp=8"

# FU scaling


# dcache
dcache_cluster_config = "-DNUM_DCACHES=4 -DNUM_ICACHES=2"
dcache_single_bank_config = "-DDCACHE_NUM_BANKS=1"
dcache_dual_bank_config = "-DDCACHE_NUM_BANKS=2"
dcache_quad_bank_config = "-DDCACHE_NUM_BANKS=4"
dcache_write_back_config = "-DDCACHE_WRITEBACK=1"

l2_single_bank_config = "-DL2_NUM_BANKS=1"
l2_dual_bank_config = "-DL2_NUM_BANKS=2"
l2_quad_bank_config = "-DL2_NUM_BANKS=4"
l2_write_back_config = "-DL2_WRITEBACK=1"
l3_single_bank_config = "-DL3_NUM_BANKS=1"
l3_dual_bank_config = "-DL3_NUM_BANKS=2"
l3_quad_bank_config = "-DL3_NUM_BANKS=4"
l3_write_back_config = "-DL3_WRITEBACK=1"

# repl
vortex_random_configs = "-DDCACHE_REPL_POLICY=0"
vortex_plru_configs = "-DDCACHE_REPL_POLICY=2"
vortex_cyclic_configs = "-DDCACHE_REPL_POLICY=1"
vortex_cyclic2_configs = "-DDCACHE_REPL_POLICY=3"
vortex_rrip_configs = "-DDCACHE_REPL_POLICY=4"

vortex_single_core_params = "--cores=1 --clusters=1"
vortex_quad_core_params = "--cores=4 --clusters=1"
vortex_dual_core_params = "--cores=2 --clusters=1"
vortex_dual_core_dual_clusters_params = "--cores=2 --clusters=2"
sim_params = "--driver=rtlsim --debug=1 --rebuild=1 --perf=2"


# ways
dcache_2way_config = "-DDCACHE_NUM_WAYS=2"
dcache_4way_config = "-DDCACHE_NUM_WAYS=4"
dcache_8way_config = "-DDCACHE_NUM_WAYS=8"
dcache_16way_config = "-DDCACHE_NUM_WAYS=16"


other_config = "wbufDirEntries=16, wbufDataEntries=8, rtabEntries=8"

bench = {}

bench_settings_cache_opt_clustering = {
    "VX cache": {
        "param": ["--vxcache", vortex_quad_core_params],
        "config": [socket_quad_core_config, dcache_cluster_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": ["--l1hpdc", vortex_quad_core_params],
        "config": [socket_quad_core_config, dcache_cluster_config, dcache_single_bank_config, vortex_plru_configs]
    }
}

bench_settings_l1_prefetch = {
    "VX cache": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF4": {
        "param": ["--l1hpdc --l1hwpf=4", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF2": {
        "param": ["--l1hpdc --l1hwpf=2", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF1": {
        "param": ["--l1hpdc --l1hwpf=1", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    }
}

bench_settings_l1_wb = {
    "VX cache write-back": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs, dcache_write_back_config]
    },
    "HPDC write-back low-latency": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs, dcache_write_back_config],
        "reference": "VX cache write-back"
    },
    "HPDC write-back ": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs, dcache_write_back_config]
    }
}



bench_settings_l1_wt = {
    "VX cache write-through": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC write-through lowLatency": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs],
        "reference": "VX cache write-through"
    },
    "HPDC write-through": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    }
}

bench_settings_l1_wt_thread = {
    "VX cache 4 threads": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 16 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },

}

bench_settings_l1_wt_8way = {
    "VX cache 4 threads": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_8way_config, vortex_plru_configs]
    },
    "HPDC 4 threads": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_8way_config, vortex_plru_configs]
    },
    "VX cache 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_8way_config, vortex_plru_configs]
    },
    "HPDC 8 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_8way_config, vortex_plru_configs]
    },
    "VX cache 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_8way_config, vortex_plru_configs]
    },
    "HPDC 16 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_8way_config, vortex_plru_configs]
    },

}

bench_settings_l1_wt_16way = {
    "VX cache 4 threads": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_16way_config, vortex_plru_configs]
    },
    "HPDC 4 threads": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_16way_config, vortex_plru_configs]
    },
    "VX cache 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_16way_config, vortex_plru_configs]
    },
    "HPDC 8 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_16way_config, vortex_plru_configs]
    },
    "VX cache 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_16way_config, vortex_plru_configs]
    },
    "HPDC 16 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, dcache_16way_config, vortex_plru_configs]
    },

}



bench_settings_l1_repl = {
    "HPDC PLRU": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC CYCLIC": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_cyclic_configs]
    },
    "HPDC RANDOM": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_random_configs]
    },
    "HPDC_CYCLIC2": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_cyclic2_configs]
    },
    "HPDC_RRIP": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_rrip_configs]
    }
}

bench_settings_l1_bank= {
    "VX cache single bank": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC single bank": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache dual bank": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_dual_bank_config, vortex_plru_configs]
    },
    "VX cache multi bank": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_quad_bank_config, vortex_plru_configs]
    },
    "VX cache single bank 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC single bank 8 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache dual bank 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_dual_bank_config, vortex_plru_configs]
    },
    "VX cache quad bank 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_quad_bank_config, vortex_plru_configs]
    },
    "VX cache single bank 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC single bank 16 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache dual bank 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_dual_bank_config, vortex_plru_configs]
    },
    "VX cache quad bank 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_quad_bank_config, vortex_plru_configs]
    },
    "VX cache single bank 32 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_32_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC single bank 32 threads": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_32_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache dual bank 32 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_32_params],
        "config": [socket_single_core_config, dcache_dual_bank_config, vortex_plru_configs]
    },
    "VX cache quad bank 32 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_32_params],
        "config": [socket_single_core_config, dcache_quad_bank_config, vortex_plru_configs]
    }
}


bench_settings_l1_mshr_size = {
    "VX cache 4 threads mshr 2": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SIZE=2", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 4 threads mshr 4": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SIZE=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 4 threads mshr 8": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SIZE=8", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads mshr 2": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SIZE=2", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads mshr 4": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SIZE=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads mshr 8": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SIZE=8", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    
   "VX cache 8 threads mshr 4": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SIZE=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 8 threads mshr 8": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SIZE=8", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 8 threads mshr 16": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SIZE=16", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads mshr 4": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SIZE=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
     "HPDC 8 threads mshr 8": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SIZE=8", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads mshr 16": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SIZE=16", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
}


# To investigate the impact of MSHR set associativity on cache performance
bench_settings_l1_mshr_assoc = {
    "VX cache 4 threads mshr full assoc": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SET=1", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads mshr full assoc": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SET=1", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads mshr 2 set": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SET=2", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads mshr 4 set": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": ["-DDCACHE_MSHR_SET=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    
   "VX cache 8 threads mshr full assoc": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SET=1", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads mshr full assoc": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SET=1", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads mshr 2 set": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SET=2", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
     "HPDC 8 threads mshr 4 set": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": ["-DDCACHE_MSHR_SET=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "VX cache 16 threads mshr full assoc": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": ["-DDCACHE_MSHR_SET=1", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 16 threads mshr full assoc": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": ["-DDCACHE_MSHR_SET=1", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 16 threads mshr 2 set": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": ["-DDCACHE_MSHR_SET=2", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 16 threads mshr 4 set": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": ["-DDCACHE_MSHR_SET=4", socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    }
}

bench_settings_l1_write_buffer = {
    "VX cache 4 threads": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads wbuf 0dir0data": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    # "HPDC 4 threads wbuf 4dir2data": {
    #     "param": ["--l1hpdc", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC 4 threads wbuf 8dir4data": {
    #     "param": ["--l1hpdc", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC 4 threads wbuf 16dir8data": {
    #     "param": ["--l1hpdc", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
}

bench_settings_l1_rtab = {
    "VX cache 4 threads": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    # "HPDC 4 threads rtab 2": {
    #     "param": ["--l1hpdc", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # },
    "HPDC 4 threads rtab old": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 threads rtab new": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    # "HPDC 8 threads rtab 4": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # },
    "VX cache 8 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads rtab old": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 8 threads rtab new": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    # "HPDC 16 threads rtab 8": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC 16 threads rtab 16": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
    # "HPDC 16 threads rtab 16 with new rtab": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
    "VX cache 16 threads": {
        "param": ["--vxcache", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 16 threads rtab old": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC 16 threads rtab new": {
        "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    }

}



bench_settings_l1_linesize = {
    "VX cache 32B line": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DL1_LINE_SIZE=32", vortex_plru_configs]
    },
    "HPDC 32B line": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DL1_LINE_SIZE=32", vortex_plru_configs]
    },
    # DEFAULT since default memory block is 64B
    "VX cache 64B line": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DL1_LINE_SIZE=64", vortex_plru_configs]
    },
    "HPDC 64B line": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DL1_LINE_SIZE=64", vortex_plru_configs]
    }
    # "VX cache 128B line": {
    #     "param": ["--vxcache", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, "-DL1_LINE_SIZE=128", vortex_plru_configs]
    # },

    # "HPDC 128B line": {
    #     "param": ["--l1hpdc", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, "-DL1_LINE_SIZE=128", vortex_plru_configs]
    # }

}

bench_settings_l1_way = {
    "VX cache 4 thread 2-way": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DDCACHE_NUM_WAYS=2", vortex_plru_configs]
    },
        "VX cache 4 thread 4-way": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DDCACHE_NUM_WAYS=4", vortex_plru_configs]
    },
     "VX cache 4 thread 8-way": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DDCACHE_NUM_WAYS=8", vortex_plru_configs]
    },
    "HPDC 4 thread 2-way": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DDCACHE_NUM_WAYS=2", vortex_plru_configs]
    },
    "HPDC 4 thread 4-way": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DDCACHE_NUM_WAYS=4", vortex_plru_configs]
    },
    "HPDC 4 thread 8-way": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, "-DDCACHE_NUM_WAYS=8", vortex_plru_configs]
    }
}



bench_settings_l1_test = {
    "VX cache 4 threads": {
        "param": ["--vxcache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    # "VX cache 16 threads": {
    #     "param": ["--vxcache", vortex_single_core_params, thread_16_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
    "HPDC 4 threads": {
        "param": ["--l1hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    }
    # "HPDC 16 threads 16 rtab": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
    #    "HPDC 16 threads 16 rtab with new rtab": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_16_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
    #   "VX cache 8 threads": {
    #     "param": ["--vxcache", vortex_single_core_params, thread_8_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
    # "HPDC 8 threads rtab old": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
      # "HPDC 8 threads rtab new": {
    #     "param": ["--l1hpdc", vortex_single_core_params, thread_8_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, vortex_plru_configs]
    # }
}

bench_settings_socket4core = {
    "VX cache": {
        "param": "--vxcache",
        "config": [socket_quad_core_config, dcache_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": "--l1hpdc",
        "config": [socket_quad_core_config, dcache_single_bank_config, vortex_plru_configs]
    }
}



# bench_settings_l1_prefetch = {
    
# }


###############################################
### L2
##########################################


bench_settings_l2_wt_thread = {
    "VX cache": {
        "param": ["--vxcache --l2cache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    # "VX cache write-back": {
    #     "param": ["--vxcache --l2cache", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    # },
    "HPDC": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    
    "VX cache 4 core": {
        "param": ["--vxcache --l2cache", vortex_quad_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC 4 core": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_quad_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    }

    # "HPDC write-back": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC HWPF4": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=4", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC HWPF2": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=2", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC HWPF1": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=1", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # }
}

bench_settings_l2_wt_4core = {
    "VX cache": {
        "param": ["--vxcache --l2cache", vortex_quad_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_quad_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    }
}

bench_settings_l2_test = {
     "VX cache": {
        "param": ["--vxcache --l2cache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
     "HPDC": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
}

bench_settings_l2_wb = {
    # "VX cache": {
    #     "param": ["--vxcache --l2cache", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # },
    "VX cache wb": {
        "param": ["--vxcache --l2cache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    
    "HPDC wb": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    
    "VX cache wb 4 core": {
        "param": ["--vxcache --l2cache", vortex_quad_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    # "HPDC": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc", vortex_dual_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # },
   
    "HPDC wb 4 core": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_quad_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    }
    # "HPDC write-back HWPF4": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=4", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC write-back HWPF2": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=2", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    # },
    # "HPDC write-back HWPF1": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=1", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    # }
}

bench_settings_l2_wt_prefetch = {
    "VX cache": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF4": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=4", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF2": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=2", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF1": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=1", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    }
}

bench_settings_l2_wt_single_core_prefetch = {
    "VX cache": {
        "param": ["--vxcache --l2cache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF4": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=4", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF2": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=2", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC HWPF1": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=1", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    }
}


bench_settings_l2_wb_prefetch = {
    # "VX cache": {
    #     "param": ["--vxcache --l2cache", vortex_single_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # },
    "VX cache write-back": {
        "param": ["--vxcache --l2cache", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    # "HPDC": {
    #     "param": ["--l1hpdc --l2cache --l2hpdc", vortex_dual_core_params],
    #     "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    # },
    "HPDC write-back": {
        "param": ["--l1hpdc --l2cache --l2hpdc", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC write-back HWPF4": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=4", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC write-back HWPF2": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=2", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    "HPDC write-back HWPF1": {
        "param": ["--l1hpdc --l2cache --l2hpdc --l2hwpf=1", vortex_single_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    }
},

bench_settings_cache_opt_l2_bank = {
    "VX cache": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, vortex_plru_configs]
    },
    "VX cache dual bank": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_dual_bank_config, vortex_plru_configs]
    },
    "VX cache quad bank": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_quad_bank_config, vortex_plru_configs]
    },
    "VX cache write-back": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, vortex_plru_configs]
    },
    "VX cache write-back dual bank": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_dual_bank_config, vortex_plru_configs]
    },
    "VX cache write-back quad bank": {
        "param": ["--vxcache --l2cache", vortex_dual_core_params],
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_quad_bank_config, vortex_plru_configs]
    }


},

bench_settings_cache_opt_l3 = {
    "VX cache": {
        "param": "--vxcache --l2cache --l3cache",
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, l3_single_bank_config, vortex_plru_configs]
    },
    "VX cache write-back": {
        "param": "--vxcache --l2cache --l3cache",
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, l3_write_back_config, l3_single_bank_config, vortex_plru_configs]
    },
    "HPDC": {
        "param": "--l1hpdc --l2cache --l2hpdc --l3cache --l3hpdc",
        "config": [socket_single_core_config, dcache_single_bank_config, l2_single_bank_config, l3_single_bank_config, vortex_plru_configs]
    },
    "HPDC write-back": {
        "param": "--l1hpdc --l2cache --l2hpdc --l3cache --l3hpdc",
        "config": [socket_single_core_config, dcache_single_bank_config, l2_write_back_config, l2_single_bank_config, l3_write_back_config, l3_single_bank_config, vortex_plru_configs]
    }
}




# only modify this to set the target benchmark settings
bench_settings = bench_settings_l1_prefetch
    
my_env = os.environ.copy()
#my_env["CONFIG"] = vortex_configs




def plot_ipc(bench_params, bench_results, result_file_name):
    import matplotlib.pyplot as plt

    # apps = list(bench_results.keys())
    # ipc_values = [results['IPC'] for results in bench_results.values() if 'performance' in results]

    # plt.bar(apps, ipc_values)
    # plt.xlabel('Benchmark Applications')
    # plt.ylabel('IPC')
    # plt.title('IPC Comparison of Benchmark Applications')
    # plt.xticks(rotation=45)
    # plt.tight_layout()
    # plt.show()

    # plot IPC for each bench param for each app on the same graph
    # apps = list(bench_results.keys())
    # params = list(bench_params.keys())
    # x = range(len(apps))
    # width = 0.15  # the width of the bars
    # fig, ax = plt.subplots(nrows=2, ncols=2, figsize=(10, 6))
    # for i, param in enumerate(params):
    #     ipc_values = [bench_results[app][param]['IPC'] if param in bench_results[app] and 'IPC' in bench_results[app][param] else 0 for app in apps]
    #     ax[0,0].bar([p + i * width for p in x], ipc_values, width, label=param)

    #     # label the IPC values on top of the bars
    #     for j, v in enumerate(ipc_values):
    #         ax[0,0].text(j + i * width, v + 0.05, f"{v:.2f}", ha='center', va='bottom', fontsize=6)

    # ax[0,0].set_xlabel('Benchmark Applications')
    # ax[0,0].set_ylabel('IPC')
    # ax[0,0].set_title('IPC Comparison of Benchmark Applications')
    # ax[0,0].set_xticks([p + width * (len(params) - 1) / 2 for p in x])
    # ax[0,0].set_xticklabels(apps)
    # ax[0,0].legend()

    # # another subplot for dcache read and write miss rates
    # # plot write miss to the right of read miss
    # miss_width = width / 2
    # for i, param in enumerate(params):
    #     offset = i * (2 * miss_width)
    #     read_positions = [p + offset for p in x]
    #     write_positions = [p + offset + miss_width for p in x]
    #     read_miss_rates = [bench_results[app][param]['dcache_read_miss_rate'] if param in bench_results[app] and 'dcache_read_miss_rate' in bench_results[app][param] else 0 for app in apps]
    #     write_miss_rates = [bench_results[app][param]['dcache_write_miss_rate'] if param in bench_results[app] and 'dcache_write_miss_rate' in bench_results[app][param] else 0 for app in apps]
    #     ax[0,1].bar(read_positions, read_miss_rates, miss_width, label=f"{param} Read Miss Rate", alpha=0.5)
    #     ax[0,1].bar(write_positions, write_miss_rates, miss_width, label=f"{param} Write Miss Rate", alpha=0.5)
    #     # label the miss rate values on top of the bars
    #     for j, (r, w) in enumerate(zip(read_miss_rates, write_miss_rates)):
    #         ax[0,1].text(j + i * width, r + 0.05, f"{r:.2f}%", ha='center', va='bottom', fontsize=6)
    #         ax[0,1].text(j + (i+1) * width, w + 0.05, f"{w:.2f}%", ha='center', va='bottom', fontsize=6)
    # ax[0,1].set_xlabel('Benchmark Applications')
    # ax[0,1].set_ylabel('D-Cache Miss Rates (%)')
    # ax[0,1].set_title('D-Cache Read and Write Miss Rates')
    # ax[0,1].set_xticks([p + width * (len(params) - 1) / 2 for p in x])
    # ax[0,1].set_xticklabels(apps)
    # ax[0,1].legend()

    # plt.xticks(rotation=45)
    # plt.tight_layout()
    # # save the plot
    # plt.savefig(f"results/{result_file_name}.png")
    # plt.show()
    if not bench_results:
        print("No benchmSark results to plot.")
        return

    os.makedirs("results", exist_ok=True)

    apps = list(bench_results.keys())
    params = list(bench_params.keys())
    x_positions = list(range(len(apps)))
    bar_width = 0.8 / max(len(params), 1)

    # Calculate IPC% relative to the first param
    if params:
        baseline_param = params[0]
        for app in apps:
            baseline_ipc = bench_results.get(app, {}).get(baseline_param, {}).get("IPC", 0)
            for param in params:
                if app in bench_results and param in bench_results[app]:
                    ipc = bench_results[app][param].get("IPC", 0)
                    if baseline_ipc > 0:
                        bench_results[app][param]["ipc_percent"] = (ipc / baseline_ipc) * 100
                    else:
                        bench_results[app][param]["ipc_percent"] = 0

    metrics = [
        ("IPC", "IPC", "IPC", False),
        ("IPC%", "ipc_percent", "Relative IPC (%)", True),
        ("L1 Read Miss Rate", "dcache_read_miss_rate", "Miss Rate (%)", True),
        ("L1 Write Miss Rate", "dcache_write_miss_rate", "Miss Rate (%)", True),
        ("L2 Read Miss Rate", "l2cache_read_miss_rate", "Miss Rate (%)", True),
        ("L2 Write Miss Rate", "l2cache_write_miss_rate", "Miss Rate (%)", True),
    ]

    def safe_name(name: str) -> str:
        return name.lower().replace(" ", "_")

    for title, key, ylabel, is_percent in metrics:
        fig, ax = plt.subplots(figsize=(10, 6))
        for idx, param in enumerate(params):
            values = [
                bench_results.get(app, {}).get(param, {}).get(key, 0)
                for app in apps
            ]
            offsets = [pos + idx * bar_width for pos in x_positions]
            ax.bar(offsets, values, bar_width, label=param)

            if values:
                label_offset = 0.01 * max(max(values), 1)
                for pos, val in zip(offsets, values):
                    suffix = "%" if is_percent else ""
                    ax.text(
                        pos,
                        val + label_offset,
                        f"{val:.2f}{suffix}",
                        ha="center",
                        va="bottom",
                        fontsize=6,
                    )

        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(
            [p + bar_width * (len(params) - 1) / 2 for p in x_positions]
        )
        ax.set_xticklabels(apps, rotation=45, ha="right")
        if params:
            ax.legend(fontsize=8)

        plt.tight_layout()
        plt.savefig(f"results/{result_file_name}/{result_file_name}_{safe_name(title)}.png")
        plt.close(fig)

if __name__ == "__main__":
    result_file_name = sys.argv[1]
    full_result_path = f"results/{result_file_name}/{result_file_name}.txt"

    # print list of bench apps
    print(f"Benchmark applications: {bench_apps}")

    # obtain this from argv
    result_recover = sys.argv[2].lower() == "true"

    # optional file path to recover results


    # create .txt file to store results
    if not os.path.exists("results"):
        os.makedirs("results")
    if not os.path.exists(f"results/{result_file_name}"):
        os.makedirs(f"results/{result_file_name}")
    if not os.path.exists(full_result_path) or not result_recover:
        with open(full_result_path, 'w') as f:
            # write the configuration as the header
            #f.write(f"Vortex Configs: {vortex_configs}\n")
            f.write(f"Sim Params: {sim_params}\n")
            f.write("=" * 50 + "\n")


    

    for app in bench_apps:
        # if no args for the app, use empty string
        app_arg_list = app_args.get(app, [""])
        for app_arg in app_arg_list:
            app_name = f"{app}{app_arg}"
            print(f"Running benchmark for {app_name}...")
            try:
                for param, param_value in bench_settings.items(): 
                    if result_recover:
                        found = False
                        # recover results from .txt
                        if os.path.exists(full_result_path):
                            with open(full_result_path, 'r') as f:
                                lines = f.readlines()
                                for line in lines:
                                    if f"--- Results for {app_name} {param}---" in line:
                                        # Found the results for this app and param
                                        results = {}
                                        found = True
                                        for line in lines[lines.index(line) + 1:]:
                                            if line.startswith("---"):
                                                break
                                            metric, value = line.split(": ")
                                            results[metric] = float(value.strip().rstrip("%"))
                                            print(f"Recovered {metric} for {app_name} {param}: {value.strip()}")
                                        # check if result is empty
                                        if not results:
                                            print(f"The result is empty for {app_name} {param}, skipping.")
                                            break
                                        if app_name not in bench:
                                            bench[app_name] = {}
                                        bench[app_name][param] = results
                                        break
                        if found:
                            print(f"Recovered results for {app_name} {param}, skipping simulation.")
                            continue

                    # print(["./ci/blackbox.sh", f"--app={app}", param_value] +
                    #     vortex_params +
                    #     sim_params)
                    #continue
                    custom_configs = " ".join(param_value['config'])
                    custom_params = " ".join(param_value['param'])
                    subprocess.run(
                        f"CONFIGS=\"{custom_configs}\" ./ci/blackbox.sh --app={app} {custom_params} {sim_params} --args=\"{app_arg}\"",
                        shell=True,
                        check=True
                    )

                    with open(f"run.log", 'r') as f:
                        log_data = f.read()
                    results = analyze_cache_performance(log_data)

                    if app_name not in bench:
                        bench[app_name] = {}
                    bench[app_name][param] = results

                    # Print the results for each benchmark application
                    print(f"--- Results for {app_name} {param}---")
                    for metric, value in results.items():
                        print(f"{metric}: {value:.2f}%")
                    print("-" * 30)
                    # Append results to the results file
                    with open(full_result_path, 'a') as f:
                        f.write(f"--- Results for {app_name} {param}---\n")
                        for metric, value in results.items():
                            if metric.endswith("rate"):
                                f.write(f"{metric}: {value:.2f}%\n")
                            else:
                                f.write(f"{metric}: {value:.2f}\n")
                        f.write("-" * 30 + "\n")
            except Exception as e:
                print(f"Error occurred while processing {app_name} {param}: {e}")
                print("Skipping...")

    plot_ipc(bench_settings, bench, result_file_name)