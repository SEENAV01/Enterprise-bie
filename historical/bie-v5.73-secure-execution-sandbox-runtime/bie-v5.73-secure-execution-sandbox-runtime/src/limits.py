def resource_limits(cpu_seconds=60,memory_mb=1024,
                  disk_mb=2048,timeout_seconds=120,
                  max_processes=16,max_output_mb=512):
    return {"cpu_seconds":cpu_seconds,"memory_mb":memory_mb,
            "disk_mb":disk_mb,"timeout_seconds":timeout_seconds,
            "max_processes":max_processes,
            "max_output_mb":max_output_mb}
