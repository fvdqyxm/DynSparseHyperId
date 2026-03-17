import wandb

# Start a new run
wandb.init(
    project="DynSparseHyperId",
    name="test-run-phase0-step6",
    config={"test": "hello world"}
)

# Log a simple metric
wandb.log({"test_metric": 42, "another_value": 3.14159})

# Log something else
for i in range(10):
    wandb.log({"counter": i, "squared": i**2})

# Finish the run
wandb.finish()

print("Done! Check https://wandb.ai/yourusername/DynSparseHyperId")
