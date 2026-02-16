# Test Coverage Analysis

## Current State

**The codebase has zero test coverage.** There are no test files, no test framework
configured, no test dependencies, and no CI/CD pipeline. This is a significant risk
given the project handles real ETH transfers and interacts with multiple external APIs.

---

## Priority 1 (Critical) -- Financial & Blockchain Logic

These modules handle real money. Bugs here can cause irreversible financial loss.

### `agent/engines/wallet_send.py`

- **`wallet_address_in_post()`** -- The regex that extracts ETH addresses/ENS names
  from posts parses user-generated content. Tests should verify it correctly extracts
  valid addresses, rejects partial matches, and handles edge cases (addresses embedded
  in URLs, multiple addresses in one post, `.eth` names with special characters).
- **`transfer_eth()`** -- Should be tested with a mocked Web3 provider to verify:
  correct nonce handling, gas price calculation (`gas_price * 1.1`), ENS resolution
  fallback logic, and return values on success vs. failure.
- **`get_wallet_balance()`** -- Verify correct wei-to-ether conversion with mocked
  responses.

### `agent/engines/coin_creator.py`

- **`create_coin()`** -- Complex transaction construction with multiple steps (pool
  config fetch, salt generation, gas estimation, signing). Each step should be tested
  in isolation with mocks.
- **`generate_coin_salt()`** -- Deterministic salt generation; verify consistent
  output for the same inputs (with `time.time()` patched).
- **`get_pool_config()`** -- Verify correct API call construction, error handling for
  non-200 responses, and hex parsing of pool config bytes.
- **`get_coin_address_from_receipt()`** -- Verify correct parsing of the
  `CoinCreatedV4` event from transaction logs.

### `agent/pipeline.py` -- `_handle_wallet_transactions()`

- Tests should verify the balance check threshold (`min_eth_balance`) correctly gates
  transactions, JSON parsing of wallet data handles malformed responses, and the retry
  loop (max 2 attempts) works correctly.

---

## Priority 2 (High) -- Core Pipeline Decision Logic

These modules control the agent's behavior. Bugs mean the agent posts at wrong times,
replies to wrong content, or makes bad follow/coin decisions.

### `agent/pipeline.py` -- `PostingPipeline`

- **`_should_reply()`** -- Self-reply prevention, probabilistic rate limiting, and
  significance score threshold. Pure logic function once `score_reply_significance`
  is mocked.
- **`_handle_replies()`** -- The regex for extracting usernames from tweet content
  should be tested with various tweet formats.
- **`_handle_follows()`** -- JSON parsing of follow decisions, score threshold
  filtering, and retry logic.
- **`_handle_coin_creation()`** -- Probabilistic gate, JSON decision parsing, base64
  metadata URI construction, and conditional coin announcement tweet.
- **`run()`** -- Integration test with all external calls mocked to verify full
  pipeline orchestration.

### `agent/run_pipeline.py` -- `HumanBehaviorSimulator`

- **`is_active_hour()`** -- Day-transition logic (active until 1 AM crosses midnight)
  deserves dedicated tests with mocked `datetime.now()`.
- **`get_post_probability()`** -- Complex probability calculation with burst mode,
  peak hours, minimum gap, and daily target adjustments.
- **`should_post()`** -- Daily reset logic and state mutation.

---

## Priority 3 (High) -- Memory System

The memory system is central to the agent's personality and decision-making.

### `agent/engines/long_term_mem.py`

- **`cosine_similarity()`** -- Pure math function. Verify with known vectors:
  identical -> 1.0, orthogonal -> 0.0, opposite -> -1.0.
- **`retrieve_relevant_memories()`** -- Uses `eval()` on stored embeddings (security
  risk). Tests should verify threshold filtering, top-k selection, and correct
  deserialization.
- **`store_memory()`** -- Verify correct `LongTermMemory` record creation.
- **`format_long_term_memories()`** -- Test sorting logic (70% similarity + 30%
  significance) and empty-list handling.

---

## Priority 4 (Medium) -- Data Processing & Formatting

### `agent/engines/post_retriever.py`

- **`parse_tweet_data()`** -- Deeply nested JSON parsing of Twitter API responses.
  Test with sample responses and with incomplete/malformed data.
- **`format_post_list()`** -- Multiple input types (string, list of dicts, list of
  strings, None). Each branch should be tested.
- **`get_root_tweet_id()` / `format_conversation_for_llm()` /
  `find_all_conversations()`** -- Conversation tree traversal. Test with linear
  threads, branching replies, and circular reference protection.

### `agent/engines/follow_user.py`

- **`decide_to_follow_users()`** -- Username regex, deduplication logic, and database
  filtering of already-known users.

---

## Priority 5 (Medium) -- LLM Interaction & Prompt Construction

### `agent/engines/significance_scorer.py`

- **`score_significance()` / `score_reply_significance()`** -- Score extraction regex
  should be tested with various response formats. The clamping logic
  (`max(1, min(10, score))`) should be verified. Missing return value when all retries
  fail (returns `None`) needs to be addressed.

### `agent/engines/post_maker.py`

- **`generate_post()`** -- Retry logic (3 attempts per stage). Note: the first retry
  loop has a bug where `tries` is only incremented in the `except` block, creating a
  potential infinite loop on non-200 responses.

### `agent/engines/prompts.py`

- **`get_short_term_memory_prompt()`** -- Has a bug: `posts_data` is accepted but
  never interpolated into the template. Tests would catch this.
- All prompt functions should have basic tests verifying correct string interpolation.

---

## Priority 6 (Lower) -- Database Layer

### `agent/db/db_setup.py`

- Test table creation with an in-memory SQLite database and proper session lifecycle.

### `agent/db/models.py` vs `agent/models.py`

- Two separate `models.py` files with overlapping but divergent definitions. Tests
  should ensure the correct models are used throughout.

---

## Bugs Discovered During Analysis

1. **`eval()` usage** in `long_term_mem.py:136` -- `eval(memory.embedding)` is a
   code injection risk. Should be replaced with `json.loads()`.
2. **Infinite loop potential** in `post_maker.py` -- The first retry loop only
   increments `tries` in the `except` block. Non-200 status codes without exceptions
   loop forever.
3. **Silent data loss** in `prompts.py:get_short_term_memory_prompt()` -- `posts_data`
   is accepted but never inserted into the template.
4. **Duplicate model definitions** -- `agent/models.py` and `agent/db/models.py` both
   define the same SQLAlchemy models with different `Base` instances.
5. **Missing return value** in `score_significance()` and `score_reply_significance()`
   -- If all retries fail, returns `None` implicitly, but callers compare with `>=`
   against a float, which raises `TypeError`.

---

## Priority 7 (Lower) -- Deployment Infrastructure

### `deploy/gcp_deploy.sh` / `deploy/digitalocean_deploy.sh`

- Shell scripts that provision VMs, upload secrets, and bootstrap Docker containers.
  While not unit-testable in the traditional sense, they should be validated with:
  - **Shellcheck** linting to catch quoting bugs, unset variable issues, and portability
    problems.
  - **Dry-run mode** tests that verify argument parsing (`--local-inference` flag
    correctly sets `MACHINE_TYPE`, `SIZE`, and `WITH_LOCAL_INFERENCE`).
  - **Prerequisite checks** (`.env` file exists, CLI tools authenticated) should be
    tested with mocked filesystem state.

### `deploy/render.yaml`

- YAML config validation: verify structure matches Render's schema and that all
  required env vars are declared.

### `agent/Dockerfile` / `agent/docker-compose.yml`

- **Dockerfile**: The conditional `WITH_LOCAL_INFERENCE` build arg creates two distinct
  image variants. Both should be validated in CI with `docker build` (no run required).
- **docker-compose.yml**: The `pipeline-local` profile and volume mounts should be
  tested with `docker compose config --profiles local` to verify valid configuration.

### `agent/.env.example`

- A simple test should verify that `.env.example` documents every environment variable
  that the codebase reads via `os.getenv()`, and vice versa. This prevents config drift
  where new code reads a variable that isn't in the template.

---

## Recommended Test Infrastructure

1. Add `pytest`, `pytest-cov`, and `responses` (HTTP mocking) to dev dependencies
2. Create `conftest.py` with fixtures for in-memory SQLite and common test data
3. Mirror source layout: `tests/engines/test_wallet_send.py`, `tests/test_pipeline.py`
4. Target 80%+ coverage on Priority 1-3 modules first
5. Add a CI pipeline (GitHub Actions) to run tests on every push/PR
6. Add `shellcheck` to CI for linting deployment scripts
