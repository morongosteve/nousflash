# nousflash

DEPRECATION NOTICE: USE https://github.com/nousresearch/nousflash-agents INSTEAD

hehe
hehe 2 just cuz

(small guest appearance by somewhere systems)

### TODO:

- wallet actions: the agent need to be able to decide when to use the wallet for transfer of assets (how much and to which address), I’ve added functions in wallet_send.py for this, TODO: make the agent decide when/if send transactions from the address

- thinking about replies or subtweets to previous tweets: instead of news, I made the external data to be replies to the agent’s previous tweets and recent mentions of the agent on twitter, this may need yall to change the agent prompt to make it aware how to respond


### basics:

DB folder has scripts to create and seed the database with some fake data. dokcer should automatically run all of this for you.

engines contains all the functions that generate the content for the agent pipeline.

The pipeline.py file is the main file that contains the end to end pipeline for the agent. You can see the flow here.

**run_pipeline.py** is the main file that runs the pipeline. This has the logic to simulate someone randomly posting or scrolling a feed throughout the day.
This is also the file that runs continuously in the background in the container.

### Local Inference with Xortron2025:

NEW: You can now run the agent with local inference using the Xortron2025 model instead of paid API services!

**Benefits:**
- 🆓 Free inference (no API costs)
- 🔒 100% private (runs locally)
- ⚡ Fast generation (after initial setup)
- 🎨 Full control over model parameters
- 🪟 Cross-platform support (Linux, macOS, Windows)

**Quick Setup:**

```bash
# Linux / macOS
cd agent/local_inference
./setup_llama_cpp.sh      # Build llama.cpp
./download_xortron.sh     # Download Xortron2025 (19.3 GB)
python verify_setup.py    # Verify installation

# Windows (PowerShell)
cd agent\local_inference
.\setup_llama_cpp.ps1     # Build llama.cpp
.\download_xortron.ps1    # Download Xortron2025 (19.3 GB)
python verify_setup.py    # Verify installation
```

**Requirements:** 21GB+ RAM for inference

**Documentation:**
- **Quick Start**: `agent/local_inference/README.md`
- **Complete Setup Guide**: `agent/local_inference/SETUP_GUIDE.md` (detailed walkthrough with troubleshooting)
- **Examples**: `agent/local_inference/example_usage.py`

### Running the agent:

docker-compose up -d

This will start the agent in the background and run continuously.

You can also run the agent manually by running:

python run_pipeline.py

This will run the pipeline LOCALLY and not in the container.

enjoy
