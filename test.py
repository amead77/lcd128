
import subprocess

def get_gpu_utilization():
    gpu_utilization = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader"], capture_output=True)
    gpu_utilization = gpu_utilization.stdout.decode("utf-8").strip().split(' ')
    # tidy any whitespace, characters or symbols and convert to float
    #gpu_utilization = [float(x) for x in gpu_utilization if x.strip()]
    # return the first value in the list (which is the GPU utilization)
    return gpu_utilization[0]
    #return round(float(gpu_utilization[0]), 1)

def get_gpu_memory():
    gpu_memory = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader"], capture_output=True)
    gpu_memory = gpu_memory.stdout.decode("utf-8").strip().split(' ')
    # tidy any whitespace, characters or symbols and convert to float
    return gpu_memory[0]
    #return round(float(gpu_memory[0]), 1)



def main():
    gpu = get_gpu_utilization()
    vram = get_gpu_memory()
    print(f"GPU Utilization: {gpu}")
    print(f"VRAM Usage: {vram}")




if __name__ == "__main__":
    main()