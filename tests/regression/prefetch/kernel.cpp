#include <vx_spawn.h>
#include "common.h"

void kernel_body(kernel_arg_t* __UNIFORM__ arg) {
	uint32_t count    = arg->task_size;
	int32_t* src0_ptr = (int32_t*)arg->src0_addr;
	int32_t* src1_ptr = (int32_t*)arg->src1_addr;
	int32_t* dst_ptr  = (int32_t*)arg->dst_addr;

	uint32_t offset = blockIdx.x * count;

	const uint32_t elements_per_line = 16; // ADD: 64 bytes cache size / 4 bytes per int_32
    
  for (uint32_t i = 0; i < count; ++i) {
	  // ADD: Only prefetch at cache line boundaries
    if (i % elements_per_line == 0) {
		vx_prefetch(&src0_ptr[offset + i]);
      	vx_prefetch(&src1_ptr[offset + i]);
    }
        
    dst_ptr[offset+i] = src0_ptr[offset+i] + src1_ptr[offset+i];
  }

	vx_fence();

}

int main() {
	kernel_arg_t* arg = (kernel_arg_t*)csr_read(VX_CSR_MSCRATCH);
	return vx_spawn_threads(1, &arg->num_tasks, nullptr, (vx_kernel_func_cb)kernel_body, arg);
}
